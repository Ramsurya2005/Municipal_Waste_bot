"""
Track Complaint Page
Citizens can search and track their complaints
"""

import streamlit as st
import json
from datetime import datetime

st.set_page_config(page_title="Track Complaint", page_icon="🔍", layout="wide")

from mysql_database import MunicipalDatabase

if 'track_db' not in st.session_state:
    try:
        st.session_state.track_db = MunicipalDatabase()
    except Exception:
        st.session_state.track_db = None

db = st.session_state.track_db

# Custom CSS
st.markdown("""
    <style>
    .track-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    .status-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .status-registered { background: #dbeafe; color: #1d4ed8; }
    .status-progress { background: #fef3c7; color: #d97706; }
    .status-verified { background: #d1fae5; color: #059669; }
    .status-resolved { background: #d1fae5; color: #047857; }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="track-header">
        <h1>🔍 Track Your Complaint</h1>
        <p>Enter your complaint tracking ID to see the current status</p>
    </div>
""", unsafe_allow_html=True)

if not db:
    st.error("❌ Database not connected.")
    st.stop()

# Search
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    complaint_id = st.text_input("🎫 Enter Tracking ID", placeholder="CMP20260323...", label_visibility="visible")
    search = st.button("🔍 Track", use_container_width=True)

if search and complaint_id:
    complaint = db.get_complaint(complaint_id)
    
    if complaint:
        st.divider()
        
        # Status header
        status = complaint.get('status', 'Unknown')
        status_icons = {
            'Registered': '📝',
            'In Progress': '🔄',
            'Verified': '✅',
            'Resolved': '🎉'
        }
        icon = status_icons.get(status, '📋')
        
        st.markdown(f"""
            <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                        border-radius: 15px; border: 2px solid #0284c7; margin-bottom: 1.5rem;">
                <div style="font-size: 2.5rem;">{icon}</div>
                <h2 style="margin: 0.5rem 0; color: #0c4a6e;">Status: {status}</h2>
                <p style="color: #0369a1; margin: 0;">Tracking ID: <strong>{complaint['complaint_id']}</strong></p>
            </div>
        """, unsafe_allow_html=True)
        
        # Details
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Complaint Details")
            st.write(f"**Description:** {complaint.get('description', 'N/A')}")
            st.write(f"**Department:** {complaint.get('department', 'N/A')}")
            st.write(f"**Location:** {complaint.get('location', 'N/A')}")
            st.write(f"**Filed On:** {str(complaint.get('created_at', 'N/A'))[:19]}")
            if complaint.get('remarks'):
                st.write(f"**Remarks:** {complaint.get('remarks')}")
        
        with col2:
            st.subheader("🛰️ Verification Info")
            v_status = complaint.get('verification_status')
            if v_status:
                st.write(f"**Verification:** {v_status}")
                v_conf = complaint.get('verification_confidence')
                if v_conf:
                    conf_pct = round(float(v_conf) * 100)
                    color = "🟢" if conf_pct >= 80 else "🟡" if conf_pct >= 60 else "🔴"
                    st.write(f"**Confidence:** {color} {conf_pct}%")
                if complaint.get('last_verified_at'):
                    st.write(f"**Verified At:** {str(complaint.get('last_verified_at'))[:19]}")
            else:
                st.info("Satellite verification not yet performed")
            
            if complaint.get('latitude') and complaint.get('longitude'):
                st.write(f"**Coordinates:** {complaint['latitude']}, {complaint['longitude']}")
        
        # Timeline
        st.divider()
        st.subheader("📅 Timeline")
        
        timeline_items = []
        timeline_items.append(("📝 Complaint Registered", str(complaint.get('created_at', ''))[:19]))
        
        if complaint.get('last_checked_date'):
            timeline_items.append(("🛰️ Satellite Image Fetched", str(complaint.get('last_checked_date'))[:19]))
        
        if complaint.get('last_verified_at'):
            timeline_items.append(("✅ Verification Completed", str(complaint.get('last_verified_at'))[:19]))
        
        if complaint.get('updated_at') and complaint.get('status') in ['In Progress', 'Verified', 'Resolved']:
            timeline_items.append((f"{icon} Status: {status}", str(complaint.get('updated_at'))[:19]))
        
        for label, time in timeline_items:
            st.markdown(f"""
                <div style="padding: 0.8rem 1.2rem; margin: 0.4rem 0; border-left: 4px solid #667eea;
                            background: #f8fafc; border-radius: 0 8px 8px 0;">
                    <strong>{label}</strong><br>
                    <span style="color: #64748b; font-size: 0.85rem;">{time}</span>
                </div>
            """, unsafe_allow_html=True)
        
        # Verification details
        if complaint.get('verification_result_json'):
            st.divider()
            st.subheader("🔬 Verification Details")
            try:
                v_data = json.loads(complaint['verification_result_json'])
                
                if v_data.get('matched_issues'):
                    st.write("**Matched Issues:**")
                    for issue in v_data['matched_issues']:
                        sat = issue.get('satellite', {})
                        st.write(f"  ✅ {sat.get('type', 'Unknown')} — Confidence: {round(issue.get('average_confidence', 0)*100)}%")
                
                if v_data.get('recommendation'):
                    st.info(f"💡 **Recommendation:** {v_data['recommendation']}")
                
                if v_data.get('nearby_complaints'):
                    st.write(f"📍 Found **{len(v_data['nearby_complaints'])}** similar complaints nearby")
            except:
                pass
    
    else:
        st.error("❌ No complaint found with that tracking ID. Please check and try again.")

elif search:
    st.warning("Please enter a tracking ID")

# Footer
st.divider()
st.caption("🏛️ Municipal Issue Tracking • Enter your CMP tracking ID above")
