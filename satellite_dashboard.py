"""
Satellite Monitoring Dashboard - Streamlit UI
Real-time satellite verification and monitoring interface
"""

import streamlit as st
import os
import json
from datetime import datetime
from PIL import Image
import pandas as pd

# Use MySQL database
from mysql_database import MunicipalDatabase

# Initialize session state
if 'sat_integration' not in st.session_state:
    try:
        from satellite_integration import SatelliteIntegration
        st.session_state.sat_integration = SatelliteIntegration()
    except Exception as e:
        st.session_state.sat_integration = None
        print(f"⚠️ Satellite integration not available: {e}")

if 'sat_db' not in st.session_state:
    try:
        st.session_state.sat_db = MunicipalDatabase()
    except Exception:
        st.session_state.sat_db = None

# Page configuration
st.set_page_config(
    page_title="🛰️ Satellite Verification System",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .satellite-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .verification-badge {
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: bold;
        font-size: 0.9rem;
        display: inline-block;
        margin: 0.5rem;
    }
    .verified { background-color: #d1e7dd; color: #0f5132; }
    .partial { background-color: #cfe2ff; color: #084298; }
    .needs-review { background-color: #f8d7da; color: #842029; }
    .verified-proximity { background-color: #d1ecf1; color: #0c5460; }
    .confidence-high { color: #28a745; }
    .confidence-medium { color: #ffc107; }
    .confidence-low { color: #dc3545; }
    .process-step {
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
        background-color: #f8f9fa;
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)

# Main title
st.markdown("""
    <div class="satellite-header">
        <h1>🛰️ Satellite Verification & Monitoring System</h1>
        <p>AI-powered satellite image analysis and complaint verification</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Page", [
    "📊 Dashboard",
    "🔍 Verify Complaint",
    "📸 View Images",
    "📋 Process Logs",
    "⚙️ Settings"
])


def get_db():
    """Get database instance"""
    return st.session_state.sat_db


# ==================== DASHBOARD ====================
if page == "📊 Dashboard":
    st.header("Satellite System Dashboard")
    
    db = get_db()
    
    col1, col2, col3, col4 = st.columns(4)
    
    if db:
        try:
            stats = db.get_statistics()
            total = stats.get('total', 0)
            pending = stats.get('pending', 0)
            resolved = stats.get('resolved', 0)
        except Exception:
            total, pending, resolved = 0, 0, 0
    else:
        total, pending, resolved = 0, 0, 0
    
    with col1:
        st.metric("Total Complaints", total)
    
    with col2:
        st.metric("✅ Resolved", resolved)
    
    with col3:
        st.metric("⏳ Pending", pending)
    
    with col4:
        sat_status = "Active" if st.session_state.sat_integration else "Inactive"
        st.metric("Satellite System", sat_status)
    
    # Recent complaints
    st.subheader("Recent Complaints")
    
    if db:
        try:
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    complaint_id,
                    description,
                    department,
                    status,
                    verification_status,
                    verification_confidence,
                    created_at
                FROM complaints
                ORDER BY created_at DESC
                LIMIT 15
            """)
            
            complaints = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if complaints:
                data = []
                for c in complaints:
                    v_status = c.get('verification_status') or 'Not verified'
                    v_conf = c.get('verification_confidence')
                    conf_str = f"{round(float(v_conf)*100)}%" if v_conf else "N/A"
                    status_icon = "✅" if v_status == 'verified_auto' else "⚠️" if 'partial' in str(v_status) else "⏳"
                    
                    data.append({
                        "ID": c['complaint_id'],
                        "Description": (c.get('description') or '')[:60],
                        "Department": c.get('department', 'N/A'),
                        "Status": c.get('status', 'N/A'),
                        "Verification": f"{status_icon} {v_status}",
                        "Confidence": conf_str,
                        "Date": str(c.get('created_at', ''))[:19]
                    })
                
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No complaints found yet")
                
        except Exception as e:
            st.error(f"Error loading data: {e}")
    else:
        st.warning("Database not connected. Check MySQL configuration.")
    
    # Department breakdown
    st.subheader("Complaints by Department")
    if db:
        try:
            dept_data = db.get_complaints_by_department()
            if dept_data:
                dept_dict = {d.get('_id', 'Unknown'): d.get('count', 0) for d in dept_data}
                st.bar_chart(dept_dict)
            else:
                st.info("No department data yet")
        except Exception as e:
            st.error(f"Error: {e}")

# ==================== VERIFY COMPLAINT ====================
elif page == "🔍 Verify Complaint":
    st.header("Verify Complaint with Satellite Images")
    
    complaint_id = st.text_input("Enter Complaint ID:", placeholder="CMP...")
    db = get_db()
    
    if complaint_id and st.button("Load Complaint") and db:
        try:
            complaint = db.get_complaint(complaint_id)
            
            if complaint:
                # Display complaint details
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Complaint Details")
                    st.write(f"**ID:** {complaint['complaint_id']}")
                    st.write(f"**Description:** {complaint.get('description', 'N/A')}")
                    st.write(f"**Location:** {complaint.get('location', 'N/A')}")
                    st.write(f"**Status:** {complaint.get('status', 'N/A')}")
                    
                    if complaint.get('latitude') and complaint.get('longitude'):
                        st.write(f"**Coordinates:** {complaint['latitude']}, {complaint['longitude']}")
                
                with col2:
                    st.subheader("Verification Status")
                    v_status = complaint.get('verification_status') or 'Not verified'
                    st.write(f"**Status:** {v_status}")
                    
                    if complaint.get('verification_confidence'):
                        confidence = float(complaint['verification_confidence'])
                        color = "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.6 else "🔴"
                        st.write(f"**Confidence:** {color} {round(confidence*100)}%")
                
                # Display images
                st.subheader("Images")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Satellite Image**")
                    sat_path = complaint.get('satellite_image_path')
                    if sat_path and os.path.exists(sat_path):
                        image = Image.open(sat_path)
                        st.image(image, use_container_width=True)
                    else:
                        st.info("No satellite image available")
                
                with col2:
                    st.write("**User Image**")
                    usr_path = complaint.get('user_image_path')
                    if usr_path and os.path.exists(usr_path):
                        image = Image.open(usr_path)
                        st.image(image, use_container_width=True)
                    else:
                        st.info("No user image available")
                
                # Display verification results
                if complaint.get('verification_result_json'):
                    st.subheader("Verification Details")
                    verification_data = json.loads(complaint['verification_result_json'])
                    
                    if verification_data.get('matched_issues'):
                        st.write("**Matched Issues:**")
                        for issue in verification_data['matched_issues']:
                            st.write(f"  - {issue['satellite']['type']}: {round(issue['average_confidence']*100)}%")
                    
                    if verification_data.get('nearby_complaints'):
                        st.write("**Nearby Complaints:**")
                        for nearby in verification_data['nearby_complaints']:
                            st.write(f"  - {nearby['complaint_id']} ({nearby['distance_km']}km away)")
                        
                        st.info(f"Found {len(verification_data['nearby_complaints'])} nearby complaints")
                
                # Admin actions
                st.subheader("Admin Actions")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("✅ Mark as Verified"):
                        db.update_complaint_status(complaint_id, "Verified", "Manually verified by admin")
                        st.success("Complaint marked as Verified")
                        st.rerun()
                with col2:
                    if st.button("🔄 Mark In Progress"):
                        db.update_complaint_status(complaint_id, "In Progress", "Under investigation")
                        st.success("Complaint marked as In Progress")
                        st.rerun()
                with col3:
                    if st.button("✅ Mark Resolved"):
                        db.update_complaint_status(complaint_id, "Resolved", "Issue has been resolved")
                        st.success("Complaint marked as Resolved")
                        st.rerun()
            
            else:
                st.error("Complaint not found")
                
        except Exception as e:
            st.error(f"Error: {e}")

# ==================== VIEW IMAGES ====================
elif page == "📸 View Images":
    st.header("Satellite & User Images Storage")
    
    tab1, tab2 = st.tabs(["Satellite Images", "User Images"])
    
    with tab1:
        st.subheader("Satellite Images")
        
        sat_folder = "./satellite_images"
        if os.path.exists(sat_folder):
            image_files = [f for f in os.listdir(sat_folder) if f.endswith(('.png', '.jpg', '.jpeg'))]
            
            if image_files:
                st.write(f"**Total images:** {len(image_files)}")
                
                selected_image = st.selectbox("Select Image:", image_files, key="sat_select")
                
                image_path = os.path.join(sat_folder, selected_image)
                image = Image.open(image_path)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.image(image, use_container_width=True)
                
                with col2:
                    file_size = os.path.getsize(image_path) / 1024
                    st.metric("File Size", f"{file_size:.1f} KB")
                    
                    complaint_id = selected_image.split('_')[0]
                    st.write(f"**Complaint:** {complaint_id}")
            else:
                st.info("No satellite images found")
        else:
            st.warning("Satellite images folder not found")
    
    with tab2:
        st.subheader("User Images")
        
        user_folder = "./user_images"
        if os.path.exists(user_folder):
            image_files = [f for f in os.listdir(user_folder) if f.endswith(('.png', '.jpg', '.jpeg'))]
            
            if image_files:
                st.write(f"**Total images:** {len(image_files)}")
                
                selected_image = st.selectbox("Select Image:", image_files, key="usr_select")
                
                image_path = os.path.join(user_folder, selected_image)
                image = Image.open(image_path)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.image(image, use_container_width=True)
                
                with col2:
                    file_size = os.path.getsize(image_path) / 1024
                    st.metric("File Size", f"{file_size:.1f} KB")
                    
                    complaint_id = selected_image.split('_')[0]
                    st.write(f"**Complaint:** {complaint_id}")
            else:
                st.info("No user images found")
        else:
            st.warning("User images folder not found")

# ==================== PROCESS LOGS ====================
elif page == "📋 Process Logs":
    st.header("Process Logs & History")
    
    complaint_id = st.text_input("Search logs by complaint ID:", placeholder="CMP...")
    
    if complaint_id:
        results_folder = "./detection_results"
        matching_files = []
        
        if os.path.exists(results_folder):
            for file in os.listdir(results_folder):
                if complaint_id in file and file.endswith('_process.json'):
                    matching_files.append(file)
        
        if matching_files:
            selected_file = st.selectbox("Select Process Log:", matching_files)
            
            log_path = os.path.join(results_folder, selected_file)
            
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            # Display process summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                pid = log_data.get('process_id', '')
                st.metric("Process ID", pid[:20] + "..." if len(pid) > 20 else pid)
            
            with col2:
                st.metric("Status", log_data.get('status', 'unknown'))
            
            with col3:
                st.metric("Steps Completed", len(log_data.get('steps', [])))
            
            # Display steps
            st.subheader("Process Steps")
            
            for i, step in enumerate(log_data.get('steps', []), 1):
                status_icon = "✅" if step.get('success') else "❌"
                
                with st.expander(f"{status_icon} Step {i}: {step.get('step', 'Unknown')}"):
                    st.write(f"**Timestamp:** {step.get('timestamp')}")
                    st.write(f"**Message:** {step.get('message')}")
                    
                    if step.get('confidence'):
                        st.write(f"**Confidence:** {round(step['confidence']*100)}%")
        
        else:
            st.info("No process logs found for this complaint")

# ==================== SETTINGS ====================
elif page == "⚙️ Settings":
    st.header("Satellite System Settings")
    
    # Load current config
    config_path = "satellite_config.json"
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        st.subheader("Configuration")
        
        # API Keys section
        st.write("**API Keys**")
        
        api_key = config.get('google_maps_api_key', '')
        masked = api_key[:20] + "***" if len(api_key) > 20 else api_key
        st.text_input(
            "Google Maps API Key",
            value=masked,
            disabled=True,
            help="Use satellite_config.json to configure API keys"
        )
        
        # Detection thresholds
        thresholds = config.get('detection_thresholds', {})
        st.write("**Detection Thresholds**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            garbage_threshold = st.slider(
                "Garbage Detection",
                0.0, 1.0,
                thresholds.get('garbage_confidence', 0.6),
                0.05
            )
        
        with col2:
            road_threshold = st.slider(
                "Road Damage",
                0.0, 1.0,
                thresholds.get('road_damage_confidence', 0.65),
                0.05
            )
        
        with col3:
            match_threshold = st.slider(
                "Verification Match",
                0.0, 1.0,
                thresholds.get('verification_match_threshold', 0.7),
                0.05
            )
        
        # Monitoring settings
        monitoring = config.get('monitoring_settings', {})
        st.write("**Monitoring Settings**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            auto_scan = st.checkbox(
                "Auto Scan Enabled",
                value=monitoring.get('auto_scan_enabled', False)
            )
        
        with col2:
            scan_interval = st.number_input(
                "Scan Interval (hours)",
                value=monitoring.get('scan_interval_hours', 24),
                min_value=1,
                max_value=168
            )
        
        # Database info
        st.subheader("Database Information")
        
        db = get_db()
        if db:
            try:
                stats = db.get_statistics()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Complaints", stats.get('total', 0))
                
                with col2:
                    st.metric("Pending", stats.get('pending', 0))
                
                with col3:
                    st.metric("Resolved", stats.get('resolved', 0))
            
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Database not connected")
    
    else:
        st.error("Configuration file not found. Please ensure satellite_config.json exists.")

# Footer
st.divider()
st.markdown("""
    <div style="text-align: center; color: gray; font-size: 0.8rem; margin-top: 2rem;">
        🛰️ Satellite Verification System v2.0 | 
        Municipal Chatbot Integration
    </div>
""", unsafe_allow_html=True)
