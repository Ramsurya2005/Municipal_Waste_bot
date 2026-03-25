"""
Satellite System Integration Module
Connects complaint submission with satellite verification
Handles complete flow from complaint creation to verification
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
import re
from typing import Dict, Tuple

# Use MySQL instead of SQLite
from mysql_database import MunicipalDatabase


class SatelliteIntegration:
    """
    Main integration layer
    - Fetches satellite images when complaint submitted
    - Verifies user images against satellite data
    - Tracks all processes with unique IDs
    - Generates comprehensive reports
    """
    
    def __init__(self, config_path="satellite_config.json"):
        """Initialize integration"""
        self.config = self.load_config(config_path)
        
        from satellite_detector import SatelliteDetector
        from satellite_verifier import SatelliteVerifier
        
        self.detector = SatelliteDetector(config_path)
        self.verifier = SatelliteVerifier(config_path=config_path)
        
        # Get shared database instance
        try:
            self.db = MunicipalDatabase()
        except Exception as e:
            print(f"⚠️ Database connection error: {e}")
            self.db = None
        
        # Create directories
        for path in self.config.get('image_storage', {}).values():
            if isinstance(path, str):
                Path(path).mkdir(exist_ok=True, parents=True)
        
        print("✅ Satellite Integration initialized")
    
    def load_config(self, config_path):
        """Load configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Config file not found: {config_path}")
            return {}
    
    def process_new_complaint(self, complaint_data: Dict) -> Tuple[str, Dict]:
        """
        Process newly submitted complaint
        1. Extract location
        2. Download satellite image
        3. Run AI detection
        4. Store in database
        
        Returns: (process_tracking_id, result)
        """
        
        # Generate process tracking ID
        process_id = self._generate_process_id('SAT', complaint_data['complaint_id'])
        timestamp = datetime.now().isoformat()
        
        process_log = {
            'process_id': process_id,
            'complaint_id': complaint_data['complaint_id'],
            'timestamp': timestamp,
            'steps': [],
            'status': 'processing'
        }
        
        try:
            # Step 1: Extract location
            step1 = self._extract_location(complaint_data)
            process_log['steps'].append(step1)
            
            if not step1['success']:
                process_log['status'] = 'failed'
                return process_id, process_log
            
            latitude = step1['latitude']
            longitude = step1['longitude']
            
            # Step 2: Download satellite image
            step2 = self._download_satellite_image(
                complaint_data['complaint_id'],
                latitude,
                longitude
            )
            process_log['steps'].append(step2)
            
            if not step2['success']:
                process_log['status'] = 'partial'
                return process_id, process_log
            
            satellite_image_path = step2['image_path']
            
            # Step 3: Run AI detection on satellite image
            step3 = self._run_satellite_detection(
                complaint_data['complaint_id'],
                satellite_image_path
            )
            process_log['steps'].append(step3)
            
            satellite_detection = step3.get('detection_result', {})
            
            # Step 4: Store initial data in database
            step4 = self._store_complaint_satellite_data(
                complaint_data['complaint_id'],
                latitude,
                longitude,
                satellite_image_path,
                satellite_detection
            )
            process_log['steps'].append(step4)
            
            # Step 5: Log process
            step5 = self._log_process(process_id, process_log)
            process_log['steps'].append(step5)
            
            process_log['status'] = 'completed'
            
            return process_id, process_log
            
        except Exception as e:
            process_log['status'] = 'error'
            process_log['error'] = str(e)
            return process_id, process_log
    
    def process_user_image(self, complaint_id: str, image_path: str) -> Tuple[str, Dict]:
        """
        Process user-uploaded image
        1. Save image to user_images folder
        2. Run AI detection
        3. Cross-verify with satellite detection
        4. Update complaint status
        
        Returns: (process_tracking_id, result)
        """
        
        process_id = self._generate_process_id('USR', complaint_id)
        timestamp = datetime.now().isoformat()
        
        process_log = {
            'process_id': process_id,
            'complaint_id': complaint_id,
            'timestamp': timestamp,
            'steps': [],
            'status': 'processing'
        }
        
        try:
            # Step 1: Save user image
            step1 = self._save_user_image(complaint_id, image_path)
            process_log['steps'].append(step1)
            
            if not step1['success']:
                process_log['status'] = 'failed'
                return process_id, process_log
            
            saved_image_path = step1['saved_path']
            
            # Step 2: Run AI detection on user image
            step2 = self._run_user_image_detection(complaint_id, saved_image_path)
            process_log['steps'].append(step2)
            
            user_detection = step2.get('detection_result', {})
            
            # Step 3: Get satellite detection from database
            step3 = self._retrieve_satellite_detection(complaint_id)
            process_log['steps'].append(step3)
            
            satellite_detection = step3.get('detection_result', {})
            
            # Step 4: Get location from database
            step4 = self._get_complaint_location(complaint_id)
            process_log['steps'].append(step4)
            
            if not step4['success']:
                process_log['status'] = 'failed'
                return process_id, process_log
            
            latitude = step4['latitude']
            longitude = step4['longitude']
            
            # Step 5: Cross-verify
            step5 = self._cross_verify(
                complaint_id,
                satellite_detection,
                user_detection,
                latitude,
                longitude
            )
            process_log['steps'].append(step5)
            
            verification_result = step5.get('verification_result', {})
            
            # Step 6: Update complaint
            step6 = self._update_complaint_with_verification(
                complaint_id,
                saved_image_path,
                user_detection,
                verification_result
            )
            process_log['steps'].append(step6)
            
            # Step 7: Log process
            step7 = self._log_process(process_id, process_log)
            process_log['steps'].append(step7)
            
            process_log['status'] = 'completed'
            process_log['verification_result'] = verification_result
            
            return process_id, process_log
            
        except Exception as e:
            process_log['status'] = 'error'
            process_log['error'] = str(e)
            return process_id, process_log
    
    # ==================== Step Functions ====================
    
    def _extract_location(self, complaint_data):
        """Extract location from complaint"""
        step = {
            'step': 'extract_location',
            'timestamp': datetime.now().isoformat(),
            'success': False
        }
        
        try:
            latitude = complaint_data.get('latitude')
            longitude = complaint_data.get('longitude')
            
            if latitude is None or longitude is None:
                # Try to extract from location string
                location_str = complaint_data.get('location', '')
                result = self._parse_location_string(location_str)
                if result:
                    latitude, longitude = result
            
            if latitude is not None and longitude is not None:
                step['success'] = True
                step['latitude'] = float(latitude)
                step['longitude'] = float(longitude)
                step['message'] = f"Location extracted: ({latitude}, {longitude})"
            else:
                step['message'] = "Could not extract location coordinates"
        
        except Exception as e:
            step['message'] = f"Error: {str(e)}"
        
        return step
    
    def _parse_location_string(self, location_str):
        """
        Try to parse coordinates from location string
        Format: "lat,lon" or with degrees symbol
        """
        try:
            location_str = location_str.strip().replace('°', '').replace(',', ', ')
            pattern = r'(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)'
            matches = re.findall(pattern, location_str)
            if matches:
                lat, lon = matches[0]
                return float(lat), float(lon)
        except:
            pass
        return None
    
    def _download_satellite_image(self, complaint_id, latitude, longitude):
        """Download satellite image from Google Maps API"""
        step = {
            'step': 'download_satellite_image',
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'complaint_id': complaint_id
        }
        
        try:
            api_key = self.config.get('google_maps_api_key', '')
            
            if not api_key or api_key == 'YOUR_GOOGLE_MAPS_API_KEY_HERE':
                step['message'] = "Google Maps API key not configured"
                return step
            
            url = (
                f"https://maps.googleapis.com/maps/api/staticmap"
                f"?center={latitude},{longitude}"
                f"&zoom=19"
                f"&size=640x640"
                f"&maptype=satellite"
                f"&key={api_key}"
            )
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                step['message'] = f"API error: {response.status_code}"
                return step
            
            # Save image
            sat_folder = self.config.get('image_storage', {}).get('satellite_images_path', 'satellite_images')
            Path(sat_folder).mkdir(exist_ok=True, parents=True)
            image_path = os.path.join(
                sat_folder,
                f"{complaint_id}_{latitude}_{longitude}.png"
            )
            
            with open(image_path, 'wb') as f:
                f.write(response.content)
            
            step['success'] = True
            step['image_path'] = image_path
            step['message'] = f"Satellite image downloaded: {image_path}"
            
        except Exception as e:
            step['message'] = f"Error: {str(e)}"
        
        return step
    
    def _run_satellite_detection(self, complaint_id, image_path):
        """Run AI detection on satellite image"""
        step = {
            'step': 'satellite_detection',
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'complaint_id': complaint_id
        }
        
        try:
            detection_result = self.detector.detect_issues(image_path, complaint_id)
            
            step['success'] = True
            step['detection_result'] = detection_result
            step['confidence'] = detection_result.get('overall_confidence', 0)
            step['issues_detected'] = len(detection_result.get('detected_issues', []))
            step['message'] = f"Detection completed. Confidence: {step['confidence']}"
            
        except Exception as e:
            step['message'] = f"Error: {str(e)}"
        
        return step
    
    def _save_user_image(self, complaint_id, image_path):
        """Save user-uploaded image"""
        step = {
            'step': 'save_user_image',
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'complaint_id': complaint_id
        }
        
        try:
            if not os.path.exists(image_path):
                step['message'] = f"Source image not found: {image_path}"
                return step
            
            user_folder = self.config.get('image_storage', {}).get('user_images_path', 'user_images')
            Path(user_folder).mkdir(exist_ok=True, parents=True)
            saved_path = os.path.join(
                user_folder,
                f"{complaint_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            
            import shutil
            shutil.copy2(image_path, saved_path)
            
            step['success'] = True
            step['saved_path'] = saved_path
            step['message'] = f"User image saved: {saved_path}"
            
        except Exception as e:
            step['message'] = f"Error: {str(e)}"
        
        return step
    
    def _run_user_image_detection(self, complaint_id, image_path):
        """Run AI detection on user image"""
        step = {
            'step': 'user_image_detection',
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'complaint_id': complaint_id
        }
        
        try:
            detection_result = self.detector.detect_issues(image_path, complaint_id)
            
            step['success'] = True
            step['detection_result'] = detection_result
            step['confidence'] = detection_result.get('overall_confidence', 0)
            step['issues_detected'] = len(detection_result.get('detected_issues', []))
            step['message'] = f"User image analyzed. Confidence: {step['confidence']}"
            
        except Exception as e:
            step['message'] = f"Error: {str(e)}"
        
        return step
    
    def _retrieve_satellite_detection(self, complaint_id):
        """Retrieve stored satellite detection from database (MySQL)"""
        step = {
            'step': 'retrieve_satellite_detection',
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'complaint_id': complaint_id
        }
        
        try:
            if not self.db:
                step['message'] = "Database not available"
                return step
            
            complaint = self.db.get_complaint(complaint_id)
            
            if complaint and complaint.get('satellite_detection_result'):
                detection_result = json.loads(complaint['satellite_detection_result'])
                step['success'] = True
                step['detection_result'] = detection_result
                step['message'] = "Satellite detection retrieved from database"
            else:
                step['message'] = "No satellite detection data found"
            
        except Exception as e:
            step['message'] = f"Error: {str(e)}"
        
        return step
    
    def _get_complaint_location(self, complaint_id):
        """Get complaint location from database (MySQL)"""
        step = {
            'step': 'get_complaint_location',
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'complaint_id': complaint_id
        }
        
        try:
            if not self.db:
                step['message'] = "Database not available"
                return step
            
            complaint = self.db.get_complaint(complaint_id)
            
            if complaint and complaint.get('latitude') and complaint.get('longitude'):
                step['success'] = True
                step['latitude'] = float(complaint['latitude'])
                step['longitude'] = float(complaint['longitude'])
                step['message'] = f"Location retrieved: ({complaint['latitude']}, {complaint['longitude']})"
            else:
                step['message'] = "No location data found in database"
            
        except Exception as e:
            step['message'] = f"Error: {str(e)}"
        
        return step
    
    def _cross_verify(self, complaint_id, satellite_detection, user_detection, latitude, longitude):
        """Cross-verify satellite vs user image"""
        step = {
            'step': 'cross_verification',
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'complaint_id': complaint_id
        }
        
        try:
            verification_result = self.verifier.verify_complaint(
                complaint_id,
                satellite_detection,
                user_detection,
                latitude,
                longitude
            )
            
            step['success'] = True
            step['verification_result'] = verification_result
            step['status'] = verification_result.get('final_status', 'unknown')
            step['confidence'] = verification_result.get('confidence_score', 0)
            step['message'] = f"Verification completed. Status: {step['status']}"
            
        except Exception as e:
            step['message'] = f"Error: {str(e)}"
        
        return step
    
    def _store_complaint_satellite_data(self, complaint_id, latitude, longitude, 
                                        satellite_image_path, satellite_detection):
        """Store initial satellite data in database (MySQL)"""
        step = {
            'step': 'store_satellite_data',
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'complaint_id': complaint_id
        }
        
        try:
            if not self.db:
                step['message'] = "Database not available"
                return step
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE complaints
                SET 
                    latitude = %s,
                    longitude = %s,
                    satellite_image_path = %s,
                    satellite_detection_result = %s,
                    last_checked_date = %s
                WHERE complaint_id = %s
            """, (
                latitude,
                longitude,
                satellite_image_path,
                json.dumps(satellite_detection),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                complaint_id
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            step['success'] = True
            step['message'] = "Satellite data stored in database"
            
        except Exception as e:
            step['message'] = f"Error: {str(e)}"
        
        return step
    
    def _update_complaint_with_verification(self, complaint_id, user_image_path, 
                                           user_detection, verification_result):
        """Update complaint with user image and verification (MySQL)"""
        step = {
            'step': 'update_complaint_verification',
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'complaint_id': complaint_id
        }
        
        try:
            if not self.db:
                step['message'] = "Database not available"
                return step
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE complaints
                SET 
                    user_image_path = %s,
                    user_detection_result = %s,
                    verification_status = %s,
                    verification_confidence = %s,
                    verification_result_json = %s,
                    last_verified_at = %s
                WHERE complaint_id = %s
            """, (
                user_image_path,
                json.dumps(user_detection),
                verification_result.get('final_status', 'unknown'),
                verification_result.get('confidence_score', 0),
                json.dumps(verification_result),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                complaint_id
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            step['success'] = True
            step['verification_status'] = verification_result.get('final_status', 'unknown')
            step['message'] = "Complaint updated with verification results"
            
        except Exception as e:
            step['message'] = f"Error: {str(e)}"
        
        return step
    
    def _log_process(self, process_id, process_log):
        """Log entire process to file"""
        step = {
            'step': 'log_process',
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'process_id': process_id
        }
        
        try:
            log_folder = self.config.get('image_storage', {}).get('detection_results_path', 'detection_results')
            Path(log_folder).mkdir(exist_ok=True, parents=True)
            log_file = os.path.join(log_folder, f"{process_id}_process.json")
            
            with open(log_file, 'w') as f:
                json.dump(process_log, f, indent=2)
            
            step['success'] = True
            step['log_file'] = log_file
            step['message'] = f"Process logged: {log_file}"
            
        except Exception as e:
            step['message'] = f"Error: {str(e)}"
        
        return step
    
    def _generate_process_id(self, prefix, complaint_id):
        """Generate unique process ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{prefix}_{complaint_id}_{timestamp}"
    
    # ==================== Helper Functions ====================
    
    def get_process_report(self, process_id):
        """Get detailed report of a process"""
        log_folder = self.config.get('image_storage', {}).get('detection_results_path', 'detection_results')
        log_file = os.path.join(log_folder, f"{process_id}_process.json")
        
        try:
            with open(log_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'status': 'error', 'message': 'Process log not found'}
    
    def get_complaint_verification_summary(self, complaint_id):
        """Get complete verification summary for complaint (MySQL)"""
        try:
            if not self.db:
                return {'error': 'Database not available'}
            
            complaint = self.db.get_complaint(complaint_id)
            
            if not complaint:
                return None
            
            verification_data = {}
            if complaint.get('verification_result_json'):
                verification_data = json.loads(complaint['verification_result_json'])
            
            return {
                'complaint_id': complaint['complaint_id'],
                'description': complaint.get('description'),
                'location': {'lat': complaint.get('latitude'), 'lon': complaint.get('longitude')},
                'status': complaint.get('status'),
                'verification_status': complaint.get('verification_status'),
                'verification_confidence': complaint.get('verification_confidence'),
                'satellite_image': complaint.get('satellite_image_path'),
                'user_image': complaint.get('user_image_path'),
                'verification_details': verification_data,
                'created_at': str(complaint.get('created_at', '')),
                'verified_at': str(complaint.get('last_verified_at', ''))
            }
            
        except Exception as e:
            return {'error': str(e)}
