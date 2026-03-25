"""
Satellite Problem Detection Page
Autonomous municipal damage detection from real-time satellite imagery
Now with support for streaming local satellite images
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import json
from satellite_detector import SatelliteDetector
from datetime import datetime
import pandas as pd
import time

# Initialize detector
if 'satellite_detector' not in st.session_state:
    st.session_state.satellite_detector = SatelliteDetector()

def render_satellite_detection_page():
    """Main satellite detection interface"""
    
    st.markdown("""
        <style>
        .satellite-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
        }
        .problem-card {
            border-left: 4px solid #ff5252;
            padding: 1rem;
            margin: 0.5rem 0;
            background: #fff3e0;
            border-radius: 5px;
        }
        .severity-critical { color: #d32f2f; font-weight: bold; }
        .severity-high { color: #f57c00; font-weight: bold; }
        .severity-medium { color: #fbc02d; font-weight: bold; }
        .severity-low { color: #388e3c; font-weight: bold; }
        .realtime-badge {
            background: linear-gradient(135deg, #ff6b6b, #ff5252);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: bold;
            display: inline-block;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="satellite-header">
        <h1>🛰️ Satellite Problem Detection</h1>
        <p>AI-powered autonomous detection of municipal infrastructure damage from real-time satellite imagery</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different scanning modes
    tab1, tab2, tab3 = st.tabs([
        "📍 Location-Based Scan",
        "▶️ Real-Time Stream",
        "📊 Batch Processing"
    ])
    
    # TAB 1: Location-Based Scanning
    with tab1:
        # Create two columns for input
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📍 Select Location to Scan")
            
            # Input method selection
            input_method = st.radio(
                "Choose input method:",
                ["📌 Map Click", "🔍 Coordinates", "📝 Address Search"],
                horizontal=True
            )
            
            if input_method == "📌 Map Click":
                st.info("Click on the map below to select a location")
                m = folium.Map(
                    location=[20.5937, 78.9629],  # India center
                    zoom_start=5,
                    tiles="OpenStreetMap"
                )
                map_data = st_folium(m, width=700, height=500)
                
                if map_data and 'last_clicked' in map_data and map_data['last_clicked']:
                    latitude = map_data['last_clicked']['lat']
                    longitude = map_data['last_clicked']['lng']
                else:
                    latitude = None
                    longitude = None
            
            elif input_method == "🔍 Coordinates":
                col_lat, col_lon = st.columns(2)
                with col_lat:
                    latitude = st.number_input("Latitude", value=20.5937, format="%.4f")
                with col_lon:
                    longitude = st.number_input("Longitude", value=78.9629, format="%.4f")
            
            else:  # Address Search
                address = st.text_input("Enter address or location name", "Mumbai, India")
                st.caption("(Coordinates will be used in production with geocoding API)")
                latitude = 19.0760
                longitude = 72.8777  # Mumbai default
        
        with col2:
            st.subheader("⚙️ Scan Settings")
            zoom_level = st.slider("Satellite Zoom Level", 15, 20, 18)
            auto_compare = st.checkbox("Compare with citizen reports", value=True)
            st.caption(f"Zoom: {zoom_level} (18 = street detail)")
        
        # Scan button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            scan_button = st.button("🔍 Scan Area Now", use_container_width=True)
        
        # Show recent scans
        st.markdown("---")
        st.subheader("📊 Recent Scans")
        
        if 'scan_history' not in st.session_state:
            st.session_state.scan_history = []
        
        # Perform scan if button clicked
        if scan_button and latitude and longitude:
            with st.spinner("🛰️ Fetching satellite imagery..."):
                result = st.session_state.satellite_detector.scan_area(
                    latitude, longitude, zoom=zoom_level
                )
                
                # Store in history
                st.session_state.scan_history.insert(0, {
                    'timestamp': datetime.now(),
                    'location': (latitude, longitude),
                    'result': result
                })
            
            # Display results
            if result['status'] == 'success':
                st.success("✅ Satellite scan completed!")
                
                # Show satellite image
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("🛰️ Satellite Image")
                    if 'satellite_url' in result:
                        st.markdown(f"📸 [View full resolution]({result['satellite_url']})")
                        # Display satellite image thumbnail
                        try:
                            from PIL import Image
                            import requests
                            import io
                            img_response = requests.get(result['satellite_url'], timeout=5)
                            if img_response.status_code == 200:
                                img = Image.open(io.BytesIO(img_response.content))
                                st.image(img, caption="Satellite view", use_container_width=True)
                        except:
                            st.warning("Could not load image preview")
                
                with col2:
                    st.subheader("📍 Location Details")
                    st.metric("Latitude", f"{latitude:.4f}")
                    st.metric("Longitude", f"{longitude:.4f}")
                    st.metric("Zoom Level", f"{zoom_level}x")
                
                # Show analysis results
                st.markdown("---")
                st.subheader("🤖 AI Analysis Results")
                
                if 'analysis' in result:
                    analysis = result['analysis']
                    
                    if 'analysis' in analysis:
                        ai_analysis = analysis['analysis']
                        
                        # Severity indicator
                        severity = ai_analysis.get('severity', 'unknown').upper()
                        severity_class = f"severity-{ai_analysis.get('severity', 'low')}"
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("🚨 Severity", severity)
                        with col2:
                            st.metric("⏱️ Urgency", ai_analysis.get('repair_urgency', 'Unknown').upper())
                        with col3:
                            issues_found = len(ai_analysis.get('detected_issues', []))
                            st.metric("🔍 Issues Found", issues_found)
                        
                        # Detailed issues
                        if ai_analysis.get('problems_detected'):
                            st.markdown("**🚨 Detected Problems:**")
                            
                            issues = ai_analysis.get('detected_issues', [])
                            if isinstance(issues, list) and len(issues) > 0:
                                for i, issue in enumerate(issues, 1):
                                    with st.expander(f"Issue #{i}: {issue.get('type', 'Unknown').title()}"):
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.write(f"**Type:** {issue.get('type', 'Unknown')}")
                                            st.write(f"**Confidence:** {issue.get('confidence', 0):.1%}")
                                            st.write(f"**Location:** {issue.get('location', 'Unknown')}")
                                        with col2:
                                            st.write(f"**Description:** {issue.get('description', 'N/A')}")
                                            st.write(f"**Affected Area:** {issue.get('affected_area_percentage', 0)}%")
                            else:
                                st.info("Analysis details available in raw response")
                        else:
                            st.success("✅ No significant problems detected in this area")
                        
                        # Overall assessment
                        st.markdown("**📋 Overall Assessment:**")
                        st.info(ai_analysis.get('overall_assessment', 'Assessment pending'))
                        
                        # Recommended action
                        st.markdown("**🎯 Recommended Action:**")
                        st.warning(ai_analysis.get('recommended_action', 'No action recommended'))
                
                # Store as complaint if issues found
                if 'analysis' in result and result['analysis'].get('analysis', {}).get('problems_detected'):
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📝 Create Complaint from Detection"):
                            # This would integrate with the main complaint system
                            st.success("Automatic complaint created! Routing to appropriate department...")
                            st.caption(f"Tracking ID: AS-{datetime.now().strftime('%Y%m%d')}-{result['longitude']:.0f}")
                    with col2:
                        if st.button("📊 Compare with Citizen Reports"):
                            st.info("Comparing with reported issues in this area...")
            
            else:
                st.error(f"❌ Scan failed: {result.get('message', 'Unknown error')}")
                st.info("💡 **Tip:** Ensure you have configured Google API key in .env file for real satellite imagery")
                st.info("We can still use free satellite tiers like Mapbox or Sentinel Hub")
        
        # Show scan history
        if st.session_state.scan_history:
            st.markdown("---")
            st.subheader("📜 Scan History")
            
            history_data = []
            for scan in st.session_state.scan_history[:5]:  # Show last 5 scans
                result = scan['result']
                if result['status'] == 'success':
                    analysis = result['analysis'].get('analysis', {})
                    history_data.append({
                        'Time': scan['timestamp'].strftime("%H:%M:%S"),
                        'Location': f"{scan['location'][0]:.4f}, {scan['location'][1]:.4f}",
                        'Severity': analysis.get('severity', 'unknown').upper(),
                        'Issues': len(analysis.get('detected_issues', []))
                    })
            
            if history_data:
                df = pd.DataFrame(history_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
    
    # TAB 2: Real-Time Streaming
    with tab2:
        st.markdown("""
        <div style="background-color: rgba(255, 107, 107, 0.1); padding: 20px; border-radius: 10px; border-left: 4px solid #ff6b6b;">
        <h3>▶️ Real-Time Satellite Image Streaming & Detection</h3>
        <p>Stream satellite images from local storage and analyze them in real-time for autonomous damage detection.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Check if real-time imaging is available
        detector = st.session_state.satellite_detector
        if not detector.realtime_imaging:
            st.error("❌ Real-time imaging system not available")
            st.info("Ensure satellite images folder exists in the project root")
        else:
            # Get imaging statistics
            stats = detector.get_imaging_statistics()
            if stats.get('status') == 'ready':
                imaging_stats = stats['imaging_stats']
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📸 Total Images", imaging_stats['total_images'])
                with col2:
                    st.metric("💾 Total Size", f"{imaging_stats['total_size_mb']} MB")
                with col3:
                    st.metric("📂 Categories", len(imaging_stats['categories']))
                with col4:
                    st.metric("Progress", f"{stats['stream_stats'].get('progress_percent', 0):.0f}%")
                
                st.markdown("---")
                
                # Streaming options
                streaming_mode = st.radio(
                    "Choose streaming mode:",
                    ["📦 Batch Processing", "⏱️ Continuous Stream", "🎯 Specific Image"],
                    horizontal=True
                )
                
                if streaming_mode == "📦 Batch Processing":
                    batch_size = st.slider("Batch Size", 1, 20, 5)
                    st.markdown(f"**Processing {batch_size} images...**")
                    
                    if st.button("▶️ Start Batch Analysis"):
                        progress_bar = st.progress(0)
                        results_container = st.container()
                        
                        batch_results = detector.scan_realtime_batch(batch_size)
                        
                        if batch_results:
                            st.success(f"✅ Processed {len(batch_results)} images")
                            
                            # Display results
                            for idx, result in enumerate(batch_results):
                                progress = (idx + 1) / len(batch_results)
                                progress_bar.progress(progress)
                                
                                with st.expander(f"Image {result['stream_index'] + 1}: {result['metadata'].get('filename', 'Unknown')}"):
                                    col1, col2 = st.columns([1, 2])
                                    
                                    with col1:
                                        st.write("**Image Info:**")
                                        st.write(f"Format: {result['metadata'].get('format', 'Unknown')}")
                                        st.write(f"Size: {result['metadata'].get('width', 0)}x{result['metadata'].get('height', 0)}")
                                        st.write(f"File Size: {result['metadata'].get('file_size_mb', 0):.2f} MB")
                                    
                                    with col2:
                                        st.write("**Analysis Result:**")
                                        analysis = result['analysis']
                                        if analysis.get('status') == 'success':
                                            st.success("✅ Analysis complete")
                                            if 'analysis' in analysis:
                                                ai_result = analysis['analysis']
                                                st.write(f"Severity: **{ai_result.get('severity', 'Unknown')}**")
                                                st.write(f"Issues Found: **{len(ai_result.get('detected_issues', []))}**")
                                        else:
                                            st.error(f"Analysis failed: {analysis.get('message', 'Unknown error')}")
                
                elif streaming_mode == "⏱️ Continuous Stream":
                    duration = st.slider("Stream Duration (seconds)", 5, 120, 30)
                    interval = st.slider("Image Interval (seconds)", 0.5, 5.0, 2.0)
                    
                    if st.button("▶️ Start Continuous Stream"):
                        st.info("🔴 Streaming in progress... Press 'Stop' to halt")
                        progress_bar = st.progress(0)
                        stream_results_placeholder = st.empty()
                        
                        stream_results = []
                        
                        # Manual streaming loop
                        start_time = time.time()
                        while time.time() - start_time < duration:
                            detection = detector.get_next_realtime_detection()
                            if detection:
                                stream_results.append(detection)
                                
                                # Update progress
                                elapsed = time.time() - start_time
                                progress = min(elapsed / duration, 1.0)
                                progress_bar.progress(progress)
                                
                                # Display streaming stats
                                with stream_results_placeholder.container():
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("📊 Processed", len(stream_results))
                                    with col2:
                                        st.metric("⏱️ Elapsed", f"{elapsed:.1f}s")
                                    with col3:
                                        st.metric("📸 Current", detection['metadata'].get('filename', 'Unknown'))
                            
                            time.sleep(interval)
                        
                        st.success(f"✅ Stream completed! Analyzed {len(stream_results)} images")
                        st.info(f"Total detections: {len([r for r in stream_results if r['analysis'].get('status') == 'success'])}")
                
                else:  # Specific Image
                    image_index = st.number_input("Image Index", min_value=0, max_value=imaging_stats['total_images'] - 1)
                    
                    if st.button("🔍 Analyze Image"):
                        with st.spinner("Analyzing image..."):
                            result = detector.scan_specific_local_image(image_index)
                            
                            if result:
                                col1, col2 = st.columns([1, 1])
                                
                                with col1:
                                    st.subheader("📸 Image Details")
                                    metadata = result['metadata']
                                    st.write(f"**Filename:** {metadata.get('filename')}")
                                    st.write(f"**Size:** {metadata.get('width')}x{metadata.get('height')}")
                                    st.write(f"**Format:** {metadata.get('format')}")
                                    st.write(f"**Category:** {metadata.get('category')}")
                                
                                with col2:
                                    st.subheader("🤖 Analysis Results")
                                    analysis = result['analysis']
                                    if analysis.get('status') == 'success':
                                        if 'analysis' in analysis:
                                            ai_result = analysis['analysis']
                                            st.metric("Severity", ai_result.get('severity', 'Unknown').upper())
                                            st.metric("Issues Found", len(ai_result.get('detected_issues', [])))
    
    # TAB 3: Batch Processing
    with tab3:
        st.subheader("📊 Batch Processing & Statistics")
        
        detector = st.session_state.satellite_detector
        if not detector.realtime_imaging:
            st.error("❌ Real-time imaging system not available")
        else:
            # Category-based batch processing
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Process by Category:**")
                categories = detector.realtime_imaging.get_image_statistics()['categories']
                selected_category = st.selectbox("Select category", list(categories.keys()))
                
                if st.button(f"🔍 Scan All {selected_category} Images"):
                    st.info(f"Scanning {categories[selected_category]} images from {selected_category}...")
                    
                    with st.spinner("Processing..."):
                        category_results = detector.scan_category_images(selected_category)
                    
                    st.success(f"✅ Processed {len(category_results)} images from {selected_category}")
            
            with col2:
                st.write("**Export Index:**")
                if st.button("📥 Export Image Index"):
                    with st.spinner("Exporting..."):
                        export_path = detector.export_realtime_index()
                        if export_path:
                            st.success(f"✅ Index exported to {export_path}")
                            st.caption("Use this JSON file for quick access to all satellite images")


if __name__ == "__main__":
    render_satellite_detection_page()
    """Main satellite detection interface"""
    
    st.markdown("""
        <style>
        .satellite-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
        }
        .problem-card {
            border-left: 4px solid #ff5252;
            padding: 1rem;
            margin: 0.5rem 0;
            background: #fff3e0;
            border-radius: 5px;
        }
        .severity-critical { color: #d32f2f; font-weight: bold; }
        .severity-high { color: #f57c00; font-weight: bold; }
        .severity-medium { color: #fbc02d; font-weight: bold; }
        .severity-low { color: #388e3c; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="satellite-header">
        <h1>🛰️ Satellite Problem Detection</h1>
        <p>AI-powered autonomous detection of municipal infrastructure damage from real-time satellite imagery</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Create two columns for input
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📍 Select Location to Scan")
        
        # Input method selection
        input_method = st.radio(
            "Choose input method:",
            ["📌 Map Click", "🔍 Coordinates", "📝 Address Search"],
            horizontal=True
        )
        
        if input_method == "📌 Map Click":
            st.info("Click on the map below to select a location")
            m = folium.Map(
                location=[20.5937, 78.9629],  # India center
                zoom_start=5,
                tiles="OpenStreetMap"
            )
            map_data = st_folium(m, width=700, height=500)
            
            if map_data and 'last_clicked' in map_data and map_data['last_clicked']:
                latitude = map_data['last_clicked']['lat']
                longitude = map_data['last_clicked']['lng']
            else:
                latitude = None
                longitude = None
        
        elif input_method == "🔍 Coordinates":
            col_lat, col_lon = st.columns(2)
            with col_lat:
                latitude = st.number_input("Latitude", value=20.5937, format="%.4f")
            with col_lon:
                longitude = st.number_input("Longitude", value=78.9629, format="%.4f")
        
        else:  # Address Search
            address = st.text_input("Enter address or location name", "Mumbai, India")
            st.caption("(Coordinates will be used in production with geocoding API)")
            latitude = 19.0760
            longitude = 72.8777  # Mumbai default
    
    with col2:
        st.subheader("⚙️ Scan Settings")
        zoom_level = st.slider("Satellite Zoom Level", 15, 20, 18)
        auto_compare = st.checkbox("Compare with citizen reports", value=True)
        st.caption(f"Zoom: {zoom_level} (18 = street detail)")
    
    # Scan button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        scan_button = st.button("🔍 Scan Area Now", use_container_width=True)
    
    # Show recent scans
    st.markdown("---")
    st.subheader("📊 Recent Scans")
    
    if 'scan_history' not in st.session_state:
        st.session_state.scan_history = []
    
    # Perform scan if button clicked
    if scan_button and latitude and longitude:
        with st.spinner("🛰️ Fetching satellite imagery..."):
            result = st.session_state.satellite_detector.scan_area(
                latitude, longitude, zoom=zoom_level
            )
            
            # Store in history
            st.session_state.scan_history.insert(0, {
                'timestamp': datetime.now(),
                'location': (latitude, longitude),
                'result': result
            })
        
        # Display results
        if result['status'] == 'success':
            st.success("✅ Satellite scan completed!")
            
            # Show satellite image
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("🛰️ Satellite Image")
                if 'satellite_url' in result:
                    st.markdown(f"📸 [View full resolution]({result['satellite_url']})")
                    # Display satellite image thumbnail
                    try:
                        from PIL import Image
                        import requests
                        import io
                        img_response = requests.get(result['satellite_url'], timeout=5)
                        if img_response.status_code == 200:
                            img = Image.open(io.BytesIO(img_response.content))
                            st.image(img, caption="Satellite view", use_container_width=True)
                    except:
                        st.warning("Could not load image preview")
            
            with col2:
                st.subheader("📍 Location Details")
                st.metric("Latitude", f"{latitude:.4f}")
                st.metric("Longitude", f"{longitude:.4f}")
                st.metric("Zoom Level", f"{zoom_level}x")
            
            # Show analysis results
            st.markdown("---")
            st.subheader("🤖 AI Analysis Results")
            
            if 'analysis' in result:
                analysis = result['analysis']
                
                if 'analysis' in analysis:
                    ai_analysis = analysis['analysis']
                    
                    # Severity indicator
                    severity = ai_analysis.get('severity', 'unknown').upper()
                    severity_class = f"severity-{ai_analysis.get('severity', 'low')}"
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("🚨 Severity", severity)
                    with col2:
                        st.metric("⏱️ Urgency", ai_analysis.get('repair_urgency', 'Unknown').upper())
                    with col3:
                        issues_found = len(ai_analysis.get('detected_issues', []))
                        st.metric("🔍 Issues Found", issues_found)
                    
                    # Detailed issues
                    if ai_analysis.get('problems_detected'):
                        st.markdown("**🚨 Detected Problems:**")
                        
                        issues = ai_analysis.get('detected_issues', [])
                        if isinstance(issues, list) and len(issues) > 0:
                            for i, issue in enumerate(issues, 1):
                                with st.expander(f"Issue #{i}: {issue.get('type', 'Unknown').title()}"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**Type:** {issue.get('type', 'Unknown')}")
                                        st.write(f"**Confidence:** {issue.get('confidence', 0):.1%}")
                                        st.write(f"**Location:** {issue.get('location', 'Unknown')}")
                                    with col2:
                                        st.write(f"**Description:** {issue.get('description', 'N/A')}")
                                        st.write(f"**Affected Area:** {issue.get('affected_area_percentage', 0)}%")
                        else:
                            st.info("Analysis details available in raw response")
                    else:
                        st.success("✅ No significant problems detected in this area")
                    
                    # Overall assessment
                    st.markdown("**📋 Overall Assessment:**")
                    st.info(ai_analysis.get('overall_assessment', 'Assessment pending'))
                    
                    # Recommended action
                    st.markdown("**🎯 Recommended Action:**")
                    st.warning(ai_analysis.get('recommended_action', 'No action recommended'))
            
            # Store as complaint if issues found
            if 'analysis' in result and result['analysis'].get('analysis', {}).get('problems_detected'):
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📝 Create Complaint from Detection"):
                        # This would integrate with the main complaint system
                        st.success("Automatic complaint created! Routing to appropriate department...")
                        st.caption(f"Tracking ID: AS-{datetime.now().strftime('%Y%m%d')}-{result['longitude']:.0f}")
                with col2:
                    if st.button("📊 Compare with Citizen Reports"):
                        st.info("Comparing with reported issues in this area...")
        
        else:
            st.error(f"❌ Scan failed: {result.get('message', 'Unknown error')}")
            st.info("💡 **Tip:** Ensure you have configured Google API key in .env file for real satellite imagery")
            st.info("We can still use free satellite tiers like Mapbox or Sentinel Hub")
    
    # Show scan history
    if st.session_state.scan_history:
        st.markdown("---")
        st.subheader("📜 Scan History")
        
        history_data = []
        for scan in st.session_state.scan_history[:5]:  # Show last 5 scans
            result = scan['result']
            if result['status'] == 'success':
                analysis = result['analysis'].get('analysis', {})
                history_data.append({
                    'Time': scan['timestamp'].strftime("%H:%M:%S"),
                    'Location': f"{scan['location'][0]:.4f}, {scan['location'][1]:.4f}",
                    'Severity': analysis.get('severity', 'unknown').upper(),
                    'Issues': len(analysis.get('detected_issues', []))
                })
        
        if history_data:
            df = pd.DataFrame(history_data)
            st.dataframe(df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    render_satellite_detection_page()
