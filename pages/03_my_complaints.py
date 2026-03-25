"""
My Complaints Page
Citizen can view all their complaints
"""

import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="My Complaints", page_icon="📝", layout="wide")

from mysql_database import MunicipalDatabase

if 'my_db' not in st.session_state:
    try:
        st.session_state.my_db = MunicipalDatabase()
    except Exception:
        st.session_state.my_db = None

db = st.session_state.my_db

# Custom CSS
st.markdown("""
    <style>
    .profile-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    .complaint-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="profile-header">
        <h1>📝 My Complaints</h1>
        <p>View all complaints you have filed</p>
    </div>
""", unsafe_allow_html=True)

if not db:
    st.error("❌ Database not connected.")
    st.stop()

# Search by citizen ID
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    citizen_id = st.text_input("🆔 Enter your Citizen ID", placeholder="CITIZEN_0001")
    search = st.button("🔍 View My Complaints", use_container_width=True)

if search and citizen_id:
    complaints = db.get_complaints_by_citizen(citizen_id)
    
    if complaints:
        # Summary stats
        total = len(complaints)
        pending = sum(1 for c in complaints if c.get('status') in ['Registered', 'In Progress'])
        resolved = sum(1 for c in complaints if c.get('status') == 'Resolved')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📋 Total Filed", total)
        with col2:
            st.metric("⏳ Pending", pending)
        with col3:
            st.metric("✅ Resolved", resolved)
        
        st.divider()
        
        # Complaint list
        for c in complaints:
            status = c.get('status', 'Unknown')
            status_colors = {
                'Registered': '#3b82f6',
                'In Progress': '#f59e0b',
                'Verified': '#10b981',
                'Resolved': '#059669',
                'Rejected': '#ef4444'
            }
            color = status_colors.get(status, '#64748b')
            
            v_status = c.get('verification_status') or ''
            v_badge = ""
            if v_status:
                v_conf = c.get('verification_confidence')
                conf_str = f"{round(float(v_conf)*100)}%" if v_conf else ""
                v_badge = f" | 🛰️ {v_status} {conf_str}"
            
            st.markdown(f"""
                <div class="complaint-card" style="border-left: 5px solid {color};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <strong style="color: #1e293b;">🎫 {c['complaint_id']}</strong>
                        <span style="background: {color}22; color: {color}; padding: 0.3rem 0.8rem; border-radius: 12px; font-weight: 600; font-size: 0.85rem;">
                            {status}
                        </span>
                    </div>
                    <p style="margin: 0.3rem 0; color: #475569;">{(c.get('description') or 'No description')[:120]}</p>
                    <div style="display: flex; gap: 1.5rem; margin-top: 0.5rem; font-size: 0.85rem; color: #94a3b8;">
                        <span>🏢 {c.get('department', 'N/A')}</span>
                        <span>📍 {(c.get('location') or 'N/A')[:30]}</span>
                        <span>📅 {str(c.get('created_at', ''))[:10]}</span>
                        {f'<span>{v_badge}</span>' if v_badge else ''}
                    </div>
                    {f'<div style="margin-top: 0.5rem; font-size: 0.85rem; color: #64748b;"><em>Remarks: {c.get("remarks", "")}</em></div>' if c.get('remarks') else ''}
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No complaints found for this Citizen ID.")

elif search:
    st.warning("Please enter your Citizen ID")

# Footer
st.divider()
st.caption("🏛️ Municipal Services • Your complaint history")
