"""
Enhanced AI-Powered Complaint Submission Page
Smart chatbot-driven complaint filing with location tagging and image upload
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime
import json
import os
from pathlib import Path
import base64

# Page configuration
st.set_page_config(
    page_title="File Complaint",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import required modules
from mysql_database import MunicipalDatabase
from smart_chatbot import SmartChatbot
from classifier import IssueClassifier

# Try to import satellite integration
try:
    from satellite_integration import SatelliteIntegration
    SATELLITE_AVAILABLE = True
except:
    SATELLITE_AVAILABLE = False

# Initialize session state
if 'complaint_db' not in st.session_state:
    try:
        st.session_state.complaint_db = MunicipalDatabase()
    except:
        st.session_state.complaint_db = None

if 'chatbot' not in st.session_state:
    st.session_state.chatbot = SmartChatbot()

if 'classifier' not in st.session_state:
    st.session_state.classifier = IssueClassifier()

if 'complaint_form' not in st.session_state:
    st.session_state.complaint_form = {
        'citizen_id': '',
        'citizen_name': '',
        'phone': '',
        'email': '',
        'location': None,
        'latitude': None,
        'longitude': None,
        'issue_type': '',
        'department': '',
        'description': '',
        'priority': 'Medium',
        'image_path': None,
        'image_uploaded': False,
        'submission_method': None,  # 'manual' or 'image'
        'status': 'draft'
    }

# Custom CSS
st.markdown("""
<style>
.complaint-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2.5rem;
    border-radius: 20px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
}

.complaint-header h1 {
    margin: 0;
    font-size: 2.2rem;
    font-weight: 700;
}

.submission-method-card {
    background: white;
    padding: 1.5rem;
    border-radius: 15px;
    border: 2px solid #e2e8f0;
    cursor: pointer;
    transition: all 0.3s ease;
    text-align: center;
}

.submission-method-card:hover {
    border-color: #667eea;
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
    transform: translateY(-5px);
}

.submission-method-card.selected {
    border-color: #667eea;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05));
}

.form-section {
    background: white;
    padding: 1.5rem;
    border-radius: 15px;
    border: 1px solid #e2e8f0;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.form-section h3 {
    color: #667eea;
    margin-top: 0;
    border-bottom: 2px solid #667eea;
    padding-bottom: 0.5rem;
}

.success-badge {
    background: #d1fae5;
    color: #047857;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-weight: 600;
    display: inline-block;
}

.priority-badge {
    display: inline-block;
    padding: 0.4rem 0.8rem;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9rem;
}

.priority-high {
    background: #fee2e2;
    color: #991b1b;
}

.priority-medium {
    background: #fef3c7;
    color: #92400e;
}

.priority-low {
    background: #d1fae5;
    color: #065f46;
}

.issue-type-btn {
    background: white;
    padding: 0.8rem;
    border-radius: 8px;
    border: 2px solid #e2e8f0;
    cursor: pointer;
    transition: all 0.2s;
}

.issue-type-btn:hover {
    border-color: #667eea;
}

.issue-type-btn.selected {
    background: #667eea;
    color: white;
    border-color: #667eea;
}
</style>
""", unsafe_allow_html=True)

# Main Header
st.markdown("""
<div class="complaint-header">
    <h1>📝 File a Complaint</h1>
    <p>Help us improve your city! Report issues with the help of our AI Assistant</p>
</div>
""", unsafe_allow_html=True)

# Main Content
db = st.session_state.complaint_db
chatbot = st.session_state.chatbot
form = st.session_state.complaint_form

if not db:
    st.error("❌ Database connection failed. Unable to file complaint.")
    st.stop()

# ============= STEP 0: CITIZEN INFO =============
st.markdown("### 👤 Step 1: Your Information")

col1, col2 = st.columns(2)
with col1:
    form['citizen_id'] = st.text_input(
        "🆔 Citizen ID",
        value=form['citizen_id'],
        placeholder="CITIZEN_0001"
    )
    form['citizen_name'] = st.text_input(
        "👤 Full Name",
        value=form['citizen_name'],
        placeholder="John Doe"
    )

with col2:
    form['phone'] = st.text_input(
        "📱 Phone Number",
        value=form['phone'],
        placeholder="+91 98765 43210"
    )
    form['email'] = st.text_input(
        "📧 Email Address",
        value=form['email'],
        placeholder="john@example.com"
    )

# ============= STEP 1: SUBMISSION METHOD =============
st.markdown("### 🎯 Step 2: Choose Submission Method")

st.write("**How would you like to report the issue?**")

col1, col2 = st.columns(2)

with col1:
    manual_selected = st.radio(
        "Submission Method",
        ["✍️ Manual Entry", "📸 Upload Picture"],
        horizontal=False,
        index=0 if form['submission_method'] is None or form['submission_method'] == 'manual' else 1,
        label_visibility="collapsed"
    )
    form['submission_method'] = 'manual' if manual_selected == "✍️ Manual Entry" else 'image'

# Show AI Chat for guidance
with st.expander("💡 Need Help? Ask Our AI Assistant", expanded=True):
    st.write("**Our AI Assistant can help you describe the issue better:**")
    
    user_query = st.text_input(
        "What's the issue you want to report?",
        placeholder="e.g., 'There's a pothole on Main Street' or 'Street light is broken'",
        key="ai_chat_input"
    )
    
    if user_query:
        # Get AI response
        ai_response = chatbot.chat(user_query)
        
        st.markdown("---")
        st.markdown(f"**🤖 AI Assistant:** {ai_response['message']}")

        followups = ai_response.get('follow_up_questions') or []
        if followups:
            st.markdown("**❓ Follow-up Questions:**")
            for question in followups:
                st.markdown(f"- {question}")
        
        # Extract and pre-fill information
        extracted = ai_response.get('extracted_info', {})
        
        if extracted.get('issue_type'):
            form['issue_type'] = extracted['issue_type']
        
        if ai_response.get('department'):
            form['department'] = ai_response['department']
        
        if extracted.get('priority'):
            form['priority'] = extracted['priority'].capitalize()
        
        # Show confidence and sentiment
        col1, col2 = st.columns(2)
        with col1:
            confidence = ai_response.get('confidence', 0)
            st.metric("Confidence", f"{confidence*100:.0f}%")
        with col2:
            sentiment = ai_response.get('sentiment', {})
            sent_label = sentiment.get('label', 'unknown') if isinstance(sentiment, dict) else sentiment
            sent_score = sentiment.get('score') if isinstance(sentiment, dict) else None
            if isinstance(sent_score, (int, float)):
                st.write(f"**Sentiment:** {sent_label.upper()} ({sent_score:+.2f})")
            else:
                st.write(f"**Sentiment:** {sent_label.upper()}")

# ============= STEP 2: LOCATION SELECTION =============
st.markdown("### 📍 Step 3: Select Location")

location_method = st.radio(
    "How would you like to select the location?",
    ["🗺️ Pick from Map", "📍 Enter Coordinates", "🔍 Text Location"],
    horizontal=True
)

if location_method == "🗺️ Pick from Map":
    st.write("**Click on the map to mark the location of the issue:**")
    
    # Center map on India (or user's last location)
    center_lat = form['latitude'] or 20.5937
    center_lon = form['longitude'] or 78.9629
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles="OpenStreetMap"
    )
    
    if form['latitude'] and form['longitude']:
        folium.Marker(
            location=[form['latitude'], form['longitude']],
            popup="Complaint Location",
            icon=folium.Icon(color='red', icon='exclamation')
        ).add_to(m)
    
    map_data = st_folium(m, width=700, height=400)
    
    if map_data and 'last_clicked' in map_data and map_data['last_clicked']:
        form['latitude'] = map_data['last_clicked']['lat']
        form['longitude'] = map_data['last_clicked']['lng']
        st.success(f"✅ Location marked: {form['latitude']:.4f}, {form['longitude']:.4f}")

elif location_method == "📍 Enter Coordinates":
    col1, col2 = st.columns(2)
    with col1:
        form['latitude'] = st.number_input(
            "Latitude",
            value=form['latitude'] or 20.5937,
            format="%.4f"
        )
    with col2:
        form['longitude'] = st.number_input(
            "Longitude",
            value=form['longitude'] or 78.9629,
            format="%.4f"
        )
    
    if form['latitude'] and form['longitude']:
        st.success(f"✅ Coordinates set: {form['latitude']:.4f}, {form['longitude']:.4f}")

else:  # Text location
    location_text = st.text_input(
        "Enter location (street name, area, landmark, etc.)",
        placeholder="e.g., Main Street near Town Hall",
        key="location_text"
    )
    if location_text:
        form['location'] = location_text
        st.info(f"📍 Location: {location_text}")

# ============= STEP 3: ISSUE DETAILS =============
st.markdown("### 📋 Step 4: Describe the Issue")

if form['submission_method'] == 'manual':
    # Manual Entry Form
    form['description'] = st.text_area(
        "📝 Detailed Description",
        value=form['description'],
        placeholder="Describe the issue in detail. What exactly is the problem? When did you notice it? Has it gotten worse?",
        height=150
    )
    
    # Issue Type Selection
    st.write("**What type of issue is this?**")
    
    issue_categories = {
        '🕳️ Pothole/Road Damage': 'Pothole',
        '💧 Water/Flooding': 'Water Issue',
        '🌳 Vegetation': 'Vegetation',
        '💡 Street Light': 'Street Light',
        '🗑️ Garbage/Waste': 'Garbage',
        '🚰 Drainage': 'Drainage',
        '🏗️ Infrastructure': 'Infrastructure',
        '❓ Other': 'Other'
    }
    
    cols = st.columns(4)
    for idx, (display, value) in enumerate(issue_categories.items()):
        with cols[idx % 4]:
            if st.button(display, key=f"issue_{idx}", use_container_width=True):
                form['issue_type'] = value
    
    if form['issue_type']:
        st.info(f"✅ Issue type: **{form['issue_type']}**")
    
    # Department auto-detection
    issue_to_dept = {
        'Pothole': 'Public Works',
        'Road Damage': 'Public Works',
        'Water Issue': 'Water Supply',
        'Vegetation': 'Parks & Gardens',
        'Street Light': 'Electrical',
        'Garbage': 'Sanitation',
        'Drainage': 'Drainage',
        'Infrastructure': 'Public Works',
        'Other': 'General'
    }
    
    form['department'] = issue_to_dept.get(form['issue_type'], 'General')
    st.write(f"📂 **Department:** {form['department']}")
    
    # Priority
    form['priority'] = st.selectbox(
        "⚠️ Priority Level",
        ['Low', 'Medium', 'High'],
        index=(['Low', 'Medium', 'High'].index(form['priority']) if form['priority'] in ['Low', 'Medium', 'High'] else 1)
    )

else:
    # Image Upload Flow
    st.write("**📸 Upload a picture of the issue:**")
    
    uploaded_file = st.file_uploader(
        "Choose an image",
        type=['jpg', 'jpeg', 'png', 'bmp'],
        help="Supported formats: JPG, PNG, BMP"
    )
    
    if uploaded_file is not None:
        # Save image
        image_dir = Path("user_images")
        image_dir.mkdir(exist_ok=True)
        
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
        filepath = image_dir / filename
        
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        form['image_path'] = str(filepath)
        form['image_uploaded'] = True
        
        # Display image
        st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
        st.success(f"✅ Image uploaded: {filename}")
        
        # AI Image Analysis
        with st.spinner("🤖 Analyzing image with AI..."):
            try:
                # Extract issue details from image using classifier
                analysis = st.session_state.classifier.classify_image_issue(str(filepath))
                
                if analysis:
                    st.markdown("**🤖 AI Analysis Results:**")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        form['issue_type'] = analysis.get('issue_type', 'Unknown')
                        st.write(f"**Issue:** {form['issue_type']}")
                    
                    with col2:
                        form['department'] = analysis.get('department', 'General')
                        st.write(f"**Department:** {form['department']}")
                    
                    with col3:
                        form['priority'] = analysis.get('priority', 'Medium')
                        priority_class = f"priority-{form['priority'].lower()}"
                        st.markdown(f"<span class='priority-badge {priority_class}'>⚠️ {form['priority']}</span>", unsafe_allow_html=True)
                    
                    st.markdown("**Description from Image Analysis:**")
                    form['description'] = analysis.get('description', 'Issue detected from uploaded image')
                    st.write(form['description'])
                    
            except Exception as e:
                st.warning(f"⚠️ Could not analyze image automatically: {str(e)}")
                
                # Manual input
                form['description'] = st.text_area(
                    "📝 Describe what you see in the image",
                    placeholder="Describe the issue shown in the image...",
                    height=100
                )
                
                form['issue_type'] = st.selectbox(
                    "Issue Type",
                    ['Pothole', 'Water Issue', 'Vegetation', 'Street Light', 'Garbage', 'Drainage', 'Infrastructure', 'Other']
                )
                
                form['priority'] = st.selectbox(
                    "Priority",
                    ['Low', 'Medium', 'High']
                )

# ============= SUMMARY =============
st.markdown("### ✅ Summary")

summary_cols = st.columns(3)

with summary_cols[0]:
    st.write("**📋 Complaint Info:**")
    st.write(f"Type: {form['issue_type']}")
    st.write(f"Department: {form['department']}")

with summary_cols[1]:
    st.write("**📍 Location:**")
    if form['latitude'] and form['longitude']:
        st.write(f"Lat: {form['latitude']:.4f}")
        st.write(f"Lon: {form['longitude']:.4f}")
    else:
        st.write("Not set")

with summary_cols[2]:
    st.write("**👤 Citizen:**")
    st.write(f"Name: {form['citizen_name']}")
    st.write(f"ID: {form['citizen_id']}")

# ============= SATELLITE VERIFICATION =============
if SATELLITE_AVAILABLE:
    st.markdown("### 🛰️ Optional: Satellite Verification")
    
    if form['latitude'] and form['longitude']:
        if st.button("🛰️ Verify with Satellite Image", use_container_width=True):
            st.info("🛰️ Fetching satellite image for verification...")
            try:
                sat_integration = SatelliteIntegration()
                sat_result = sat_integration.detector.scan_area(
                    form['latitude'],
                    form['longitude'],
                    zoom=18
                )
                
                if sat_result['status'] == 'success':
                    st.success("✅ Satellite verification successful!")
                    analysis = sat_result.get('analysis', {}).get('analysis', {})
                    
                    if analysis.get('problems_detected'):
                        st.warning(f"🔴 Problems detected: {len(analysis.get('detected_issues', []))} issue(s) found")
                    else:
                        st.info("✅ No significant problems detected")
            except Exception as e:
                st.warning(f"⚠️ Satellite verification unavailable: {str(e)}")

# ============= SUBMIT =============
st.markdown("---")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("📤 Submit Complaint", use_container_width=True, type="primary"):
        # Validation
        if not form['citizen_id'] or not form['citizen_name']:
            st.error("❌ Please fill in citizen information")
        elif not form['issue_type']:
            st.error("❌ Please select an issue type")
        elif not form['description']:
            st.error("❌ Please describe the issue")
        elif not (form['latitude'] and form['longitude']):
            st.error("❌ Please select a location")
        else:
            # Create complaint
            try:
                complaint = db.create_complaint(
                    citizen_id=form['citizen_id'],
                    citizen_name=form['citizen_name'],
                    phone=form['phone'],
                    email=form['email'],
                    issue_type=form['issue_type'],
                    description=form['description'],
                    location=form['location'] or f"{form['latitude']}, {form['longitude']}",
                    latitude=form['latitude'],
                    longitude=form['longitude'],
                    priority=form['priority'],
                    department=form['department'],
                    image_path=form['image_path']
                )
                
                # Success message
                st.success(f"✅ **Complaint Submitted Successfully!**")
                st.balloons()
                
                # Show complaint details
                st.markdown(f"""
                ### 📋 Complaint Details
                
                **Tracking ID:** `{complaint.get('complaint_id', 'N/A')}`
                
                - **Issue:** {form['issue_type']}
                - **Priority:** {form['priority']}
                - **Department:** {form['department']}
                - **Location:** {form['location'] or f"{form['latitude']:.4f}, {form['longitude']:.4f}"}
                - **Status:** Registered
                
                **Your complaint has been registered and assigned to the {form['department']} department.**
                You'll receive updates on your phone and email.
                """)
                
                # Reset form
                st.session_state.complaint_form = {
                    'citizen_id': '',
                    'citizen_name': '',
                    'phone': '',
                    'email': '',
                    'location': None,
                    'latitude': None,
                    'longitude': None,
                    'issue_type': '',
                    'department': '',
                    'description': '',
                    'priority': 'Medium',
                    'image_path': None,
                    'image_uploaded': False,
                    'submission_method': None,
                    'status': 'submitted'
                }
                
            except Exception as e:
                st.error(f"❌ Error submitting complaint: {str(e)}")

# Footer
st.markdown("---")
st.caption("🏛️ Municipal Services • Smart Complaint Reporting System")
