"""
Satellite & User Image Cross-Verification Module
Matches satellite AI detections with user-uploaded images for verification
Includes tracking ID and location-based verification logic
"""

import os
import json
from datetime import datetime
from pathlib import Path
import hashlib
from typing import Dict, Any

# Use MySQL instead of SQLite
from mysql_database import MunicipalDatabase


class SatelliteVerifier:
    """
    Cross-verifies satellite detections with user images
    Handles verification status, tracking, and nearby complaint analysis
    """
    
    def __init__(self, config_path="satellite_config.json"):
        """Initialize verifier"""
        self.config = self.load_config(config_path)
        
        # Get shared database instance
        try:
            self.db = MunicipalDatabase()
        except Exception as e:
            print(f"⚠️ Database connection error in verifier: {e}")
            self.db = None
        
        # Create required directories
        img_storage = self.config.get('image_storage', {})
        for key in ['satellite_images_path', 'user_images_path', 'detection_results_path']:
            path = img_storage.get(key)
            if path:
                Path(path).mkdir(exist_ok=True)
    
    def load_config(self, config_path):
        """Load configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'detection_thresholds': {'verification_match_threshold': 0.7},
                'verification_rules': {
                    'check_nearby_complaints': True,
                    'nearby_radius_km': 0.5,
                    'confidence_boost_nearby': 0.15,
                    'accept_unconfirmed': True
                }
            }
    
    def verify_complaint(self, complaint_id, satellite_detection, user_detection, 
                        latitude, longitude):
        """
        Main verification function
        Compares satellite vs user image detections
        Includes nearby complaint checking
        
        Returns verification result with status and tracking info
        """
        
        verification_result = {
            "complaint_id": complaint_id,
            "timestamp": datetime.now().isoformat(),
            "satellite_detection": satellite_detection,
            "user_detection": user_detection,
            "verification_status": "unknown",
            "confidence_score": 0.0,
            "matched_issues": [],
            "unmatched_issues": [],
            "nearby_complaints": [],
            "final_status": "pending",
            "tracking_history": [],
            "recommendation": ""
        }
        
        # Check if both detections exist
        if not satellite_detection or not user_detection:
            verification_result["verification_status"] = "incomplete_data"
            verification_result["final_status"] = "needs_manual_review"
            verification_result["recommendation"] = "Missing satellite or user image detection data"
            return verification_result
        
        # Perform matching
        matched_issues, unmatched_sat, unmatched_user = self._match_issues(
            satellite_detection.get('detected_issues', []),
            user_detection.get('detected_issues', [])
        )
        
        verification_result['matched_issues'] = matched_issues
        verification_result['unmatched_issues'] = {
            'satellite': unmatched_sat,
            'user': unmatched_user
        }
        
        # Calculate confidence
        confidence = self._calculate_verification_confidence(
            matched_issues,
            satellite_detection.get('overall_confidence', 0),
            user_detection.get('overall_confidence', 0)
        )
        
        verification_result['confidence_score'] = round(confidence, 3)
        
        # Determine verification status
        thresholds = self.config.get('detection_thresholds', {})
        match_threshold = thresholds.get('verification_match_threshold', 0.7)
        
        if confidence >= match_threshold:
            verification_result['verification_status'] = "verified"
        elif confidence >= (match_threshold * 0.7):
            verification_result['verification_status'] = "partial_match"
        else:
            verification_result['verification_status'] = "no_match"
        
        # Check nearby complaints
        rules = self.config.get('verification_rules', {})
        if rules.get('check_nearby_complaints', True):
            nearby = self.get_nearby_complaints(
                latitude, 
                longitude, 
                complaint_id,
                radius_km=rules.get('nearby_radius_km', 0.5)
            )
            verification_result['nearby_complaints'] = nearby
            
            # Boost confidence if nearby complaints exist
            if nearby:
                confidence_boost = rules.get('confidence_boost_nearby', 0.15)
                verification_result['confidence_score'] = min(
                    verification_result['confidence_score'] + confidence_boost,
                    1.0
                )
        
        # Determine final status
        if verification_result['verification_status'] == "verified":
            verification_result['final_status'] = "verified_auto"
            verification_result['recommendation'] = "AUTO-APPROVED: Satellite and user image match"
        
        elif verification_result['verification_status'] == "partial_match":
            verification_result['final_status'] = "verified_uncertain"
            if rules.get('accept_unconfirmed', True):
                verification_result['recommendation'] = "ACCEPTED with low confidence - Manual review recommended"
            else:
                verification_result['final_status'] = "needs_manual_review"
                verification_result['recommendation'] = "Requires manual verification"
        
        else:  # no_match
            if nearby and rules.get('accept_unconfirmed', True):
                verification_result['final_status'] = "verified_by_proximity"
                verification_result['recommendation'] = f"ACCEPTED: {len(nearby)} nearby complaints detected at same location"
            else:
                verification_result['final_status'] = "needs_manual_review"
                verification_result['recommendation'] = "Images don't match - Manual department review required"
        
        # Add tracking
        verification_result['tracking_history'] = [
            {
                "timestamp": datetime.now().isoformat(),
                "status": verification_result['final_status'],
                "verifier": "automatic_satellite_system"
            }
        ]
        
        return verification_result
    
    def _match_issues(self, satellite_issues, user_issues):
        """
        Match detected issues from satellite vs user image
        Returns: (matched_issues, unmatched_satellite, unmatched_user)
        """
        matched = []
        unmatched_sat = list(satellite_issues)
        unmatched_user = list(user_issues)
        
        # Issue type mapping for matching
        issue_type_mapping = {
            'garbage_accumulation': ['garbage', 'waste', 'debris'],
            'road_damage': ['pothole', 'crack', 'damage', 'pavement'],
            'water_pooling': ['flooding', 'water', 'leak', 'wet'],
            'vegetation_damage': ['tree', 'vegetation', 'overgrown']
        }
        
        for sat_issue in satellite_issues:
            sat_type = sat_issue.get('type', '')
            sat_confidence = sat_issue.get('confidence', 0)
            
            for user_issue in user_issues:
                user_type = user_issue.get('type', '')
                user_confidence = user_issue.get('confidence', 0)
                
                # Check if issue types match
                if self._issue_types_match(sat_type, user_type, issue_type_mapping):
                    matched.append({
                        'satellite': sat_issue,
                        'user': user_issue,
                        'satellite_confidence': sat_confidence,
                        'user_confidence': user_confidence,
                        'average_confidence': (sat_confidence + user_confidence) / 2
                    })
                    if sat_issue in unmatched_sat:
                        unmatched_sat.remove(sat_issue)
                    if user_issue in unmatched_user:
                        unmatched_user.remove(user_issue)
                    break
        
        return matched, unmatched_sat, unmatched_user
    
    def _issue_types_match(self, sat_type, user_type, mapping):
        """Check if two issue types are related"""
        sat_type_lower = sat_type.lower()
        user_type_lower = user_type.lower()
        
        # Direct match
        if sat_type_lower == user_type_lower:
            return True
        
        # Check mapping
        for issue_category, keywords in mapping.items():
            if sat_type_lower in keywords and user_type_lower in keywords:
                return True
        
        return False
    
    def _calculate_verification_confidence(self, matched_issues, sat_overall, user_overall):
        """
        Calculate verification confidence score (0-1)
        Based on: number of matches, confidence levels, agreement
        """
        if not matched_issues:
            return 0.0
        
        # Confidence from matched issues
        match_confidences = [m['average_confidence'] for m in matched_issues]
        average_match_confidence = sum(match_confidences) / len(match_confidences)
        
        # Confidence from overall scores
        overall_average = (sat_overall + user_overall) / 2
        
        # Weighted calculation
        match_weight = 0.6
        overall_weight = 0.4
        
        final_confidence = (average_match_confidence * match_weight) + (overall_average * overall_weight)
        
        return final_confidence
    
    def get_nearby_complaints(self, latitude, longitude, complaint_id, radius_km=0.5):
        """
        Find complaints within specified radius (MySQL)
        Returns list of nearby complaints
        """
        try:
            if not self.db:
                return []
            
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Approximate: 1 degree = 111 km
            lat_range = radius_km / 111
            long_range = radius_km / 111
            
            cursor.execute("""
                SELECT 
                    complaint_id,
                    latitude,
                    longitude,
                    description,
                    status,
                    satellite_detection_result,
                    verification_status,
                    created_at
                FROM complaints
                WHERE 
                    complaint_id != %s
                    AND latitude BETWEEN %s AND %s
                    AND longitude BETWEEN %s AND %s
                    AND (status = 'Registered' OR status = 'In Progress')
                ORDER BY 
                    ABS(latitude - %s) + ABS(longitude - %s) ASC
                LIMIT 10
            """, (
                complaint_id,
                latitude - lat_range, latitude + lat_range,
                longitude - long_range, longitude + long_range,
                latitude, longitude
            ))
            
            nearby = []
            for row in cursor.fetchall():
                if row.get('latitude') and row.get('longitude'):
                    distance = self._calculate_distance(
                        latitude, longitude,
                        float(row['latitude']), float(row['longitude'])
                    )
                    
                    nearby.append({
                        'complaint_id': row['complaint_id'],
                        'distance_km': round(distance, 3),
                        'description': row.get('description', ''),
                        'status': row.get('status', ''),
                        'satellite_detection': row.get('satellite_detection_result', ''),
                        'verification_status': row.get('verification_status', ''),
                        'created_at': str(row.get('created_at', ''))
                    })
            
            cursor.close()
            conn.close()
            return nearby
            
        except Exception as e:
            print(f"⚠️ Error getting nearby complaints: {e}")
            return []
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate simple distance between two points in km
        Using Haversine formula approximation
        """
        from math import radians, cos, sin, asin, sqrt
        
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        km = 6371 * c
        return km
    
    def update_verification_in_db(self, verification_result):
        """Update database with verification results (MySQL)"""
        try:
            if not self.db:
                return False
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE complaints
                SET 
                    verification_status = %s,
                    verification_confidence = %s,
                    verification_result_json = %s,
                    last_verified_at = %s
                WHERE complaint_id = %s
            """, (
                verification_result['final_status'],
                verification_result['confidence_score'],
                json.dumps(verification_result),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                verification_result['complaint_id']
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
        except Exception as e:
            print(f"⚠️ Error updating verification in DB: {e}")
            return False
    
    def generate_verification_report(self, complaint_id):
        """Generate comprehensive verification report for a complaint (MySQL)"""
        try:
            if not self.db:
                return None
            
            complaint = self.db.get_complaint(complaint_id)
            
            if not complaint:
                return None
            
            # Parse stored verification result
            verification_data = {}
            if complaint.get('verification_result_json'):
                verification_data = json.loads(complaint['verification_result_json'])
            
            report = {
                "complaint_id": complaint_id,
                "date_generated": datetime.now().isoformat(),
                "complaint_details": {
                    "description": complaint.get('description', ''),
                    "location": complaint.get('location', ''),
                    "status": complaint.get('status', ''),
                    "created_at": str(complaint.get('created_at', ''))
                },
                "location_data": {
                    "latitude": complaint.get('latitude'),
                    "longitude": complaint.get('longitude')
                },
                "verification_status": complaint.get('verification_status'),
                "verification_confidence": complaint.get('verification_confidence'),
                "satellite_image_path": complaint.get('satellite_image_path'),
                "user_image_path": complaint.get('user_image_path'),
                "verification_data": verification_data,
                "last_verified": str(complaint.get('last_verified_at', ''))
            }
            
            return report
            
        except Exception as e:
            print(f"⚠️ Error generating report: {e}")
            return None
