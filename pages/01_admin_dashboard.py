"""
Admin Dashboard Page
View all complaints, manage statuses, see analytics
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json

# Page config
st.set_page_config(page_title="Admin Dashboard", page_icon="📊", layout="wide")

# Import database
from mysql_database import MunicipalDatabase
import config

# Initialize database
if 'admin_db' not in st.session_state:
    try:
        st.session_state.admin_db = MunicipalDatabase()
    except Exception:
        st.session_state.admin_db = None

db = st.session_state.admin_db

# Custom CSS
st.markdown("""
    <style>
    .admin-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .stat-card h2 {
        margin: 0;
        color: #667eea;
        font-size: 2rem;
    }
    .stat-card p {
        margin: 0.5rem 0 0;
        color: #64748b;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="admin-header">
        <h1>📊 Admin Dashboard</h1>
        <p>Municipal Complaint Management System</p>
    </div>
""", unsafe_allow_html=True)

if not db:
    st.error("❌ Database not connected. Please check MySQL configuration.")
    st.stop()

# ==================== STATISTICS ====================
stats = db.get_statistics()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📋 Total Complaints", stats.get('total', 0))
with col2:
    st.metric("⏳ Pending", stats.get('pending', 0))
with col3:
    st.metric("✅ Resolved", stats.get('resolved', 0))
with col4:
    total = stats.get('total', 0)
    resolved = stats.get('resolved', 0)
    rate = f"{(resolved/total*100):.0f}%" if total > 0 else "0%"
    st.metric("📈 Resolution Rate", rate)

st.divider()

# ==================== TABS ====================
tab1, tab2, tab3 = st.tabs(["📋 All Complaints", "📈 Analytics", "🔧 Manage"])

# ==================== ALL COMPLAINTS ====================
with tab1:
    st.subheader("All Complaints")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "Registered", "In Progress", "Verified", "Resolved"])
    with col2:
        dept_filter = st.selectbox("Filter by Department", ["All"] + [d['name'] for d in config.DEPARTMENT_MAPPING.values()])
    with col3:
        sort_by = st.selectbox("Sort by", ["Newest First", "Oldest First"])
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM complaints"
        conditions = []
        params = []
        
        if status_filter != "All":
            conditions.append("status = %s")
            params.append(status_filter)
        if dept_filter != "All":
            conditions.append("department = %s")
            params.append(dept_filter)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        order = "DESC" if sort_by == "Newest First" else "ASC"
        query += f" ORDER BY created_at {order} LIMIT 100"
        
        cursor.execute(query, params)
        complaints = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if complaints:
            data = []
            for c in complaints:
                v_status = c.get('verification_status') or '-'
                v_conf = c.get('verification_confidence')
                conf_str = f"{round(float(v_conf)*100)}%" if v_conf else "-"
                
                data.append({
                    "ID": c['complaint_id'],
                    "Description": (c.get('description') or '')[:80],
                    "Department": c.get('department', '-'),
                    "Status": c.get('status', '-'),
                    "Location": (c.get('location') or '-')[:40],
                    "Verification": v_status,
                    "Confidence": conf_str,
                    "Date": str(c.get('created_at', ''))[:16]
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Showing {len(complaints)} complaints")
        else:
            st.info("No complaints found matching filters")
    
    except Exception as e:
        st.error(f"Error loading complaints: {e}")

# ==================== ANALYTICS ====================
with tab2:
    st.subheader("Complaint Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Complaints by Department**")
        dept_data = db.get_complaints_by_department()
        if dept_data:
            chart_data = {d.get('_id', 'Unknown'): d.get('count', 0) for d in dept_data}
            st.bar_chart(chart_data)
        else:
            st.info("No data available")
    
    with col2:
        st.write("**Status Distribution**")
        try:
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM complaints 
                GROUP BY status
            """)
            status_data = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if status_data:
                chart = {s['status']: s['count'] for s in status_data}
                st.bar_chart(chart)
            else:
                st.info("No data available")
        except Exception as e:
            st.error(f"Error: {e}")
    
    # Verification stats
    st.write("**Verification Statistics**")
    try:
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN verification_status IS NOT NULL THEN 1 ELSE 0 END) as verified,
                AVG(CASE WHEN verification_confidence IS NOT NULL THEN verification_confidence ELSE NULL END) as avg_confidence
            FROM complaints
        """)
        v_stats = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if v_stats:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Complaints", v_stats.get('total', 0))
            with col2:
                st.metric("Satellite Verified", v_stats.get('verified', 0))
            with col3:
                avg_conf = v_stats.get('avg_confidence')
                st.metric("Avg Confidence", f"{round(float(avg_conf)*100)}%" if avg_conf else "N/A")
    except Exception as e:
        st.error(f"Error: {e}")

# ==================== MANAGE ====================
with tab3:
    st.subheader("Manage Complaint Status")
    
    complaint_id = st.text_input("Enter Complaint ID to manage:", placeholder="CMP...")
    
    if complaint_id:
        complaint = db.get_complaint(complaint_id)
        
        if complaint:
            st.success(f"Found: {complaint['complaint_id']}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Description:** {complaint.get('description', 'N/A')}")
                st.write(f"**Department:** {complaint.get('department', 'N/A')}")
                st.write(f"**Current Status:** {complaint.get('status', 'N/A')}")
            with col2:
                st.write(f"**Location:** {complaint.get('location', 'N/A')}")
                st.write(f"**Remarks:** {complaint.get('remarks', 'N/A')}")
                st.write(f"**Created:** {complaint.get('created_at', 'N/A')}")
            
            st.divider()
            
            col1, col2 = st.columns(2)
            with col1:
                new_status = st.selectbox("Update Status", ["Registered", "In Progress", "Verified", "Resolved", "Rejected"])
            with col2:
                remarks = st.text_input("Remarks", placeholder="Add notes...")
            
            if st.button("🔄 Update Status", use_container_width=True):
                db.update_complaint_status(complaint_id, new_status, remarks or None)
                st.success(f"Status updated to: {new_status}")
                st.rerun()
        else:
            st.warning("Complaint not found")

# Footer
st.divider()
st.caption("🏛️ Municipal Admin Dashboard • Powered by AI")
