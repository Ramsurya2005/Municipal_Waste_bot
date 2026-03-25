"""
Satellite Imagery Analysis Module
Uses Google Earth API & Gemini Vision to detect municipal infrastructure damage
Now enhanced with real-time local satellite image support
"""

import os
import json
import requests
from datetime import datetime
from PIL import Image
import io
from typing import Dict, List, Tuple, Optional
from google import genai

# Import real-time imaging system
try:
    from satellite_realtime_imaging import RealtimeSatelliteImaging, RealtimeImageStream
    REALTIME_IMAGING_AVAILABLE = True
except ImportError:
    REALTIME_IMAGING_AVAILABLE = False
    print("⚠️ Real-time imaging module not available. API-based detection only.")

class SatelliteDetector:
    """Detects municipal problems from real-time satellite imagery"""
    
    def __init__(self, config_path="satellite_config.json"):
        """Initialize with API credentials and real-time imaging"""
        # Load config if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}
        
        self.google_api_key = config.get('google_maps_api_key', os.getenv('GOOGLE_API_KEY', ''))
        self.gemini_api_key = config.get('gemini_api_key', os.getenv('GEMINI_API_KEY', ''))
        
        if self.gemini_api_key:
            self.genai_client = genai.Client(api_key=self.gemini_api_key)
        else:
            self.genai_client = None
        
        # Initialize real-time imaging system
        self.realtime_imaging = None
        self.image_stream = None
        if REALTIME_IMAGING_AVAILABLE:
            try:
                satellite_images_path = config.get('image_storage', {}).get('satellite_images_path', 'satellite images')
                if os.path.exists(satellite_images_path):
                    self.realtime_imaging = RealtimeSatelliteImaging(satellite_images_path)
                    self.image_stream = RealtimeImageStream(self.realtime_imaging)
                    print(f"✅ Real-time imaging system ready with {len(self.realtime_imaging.image_index)} images")
            except Exception as e:
                print(f"⚠️ Real-time imaging initialization failed: {e}")
        
        # Problem categories to detect
        self.detection_categories = {
            'potholes': ['pothole', 'road damage', 'asphalt damage', 'pavement crack'],
            'flooding': ['water accumulation', 'flooding', 'waterlogged', 'inundation'],
            'vegetation': ['overgrown trees', 'dead vegetation', 'fallen trees', 'branch hazard'],
            'infrastructure': ['broken poles', 'damaged infrastructure', 'structural damage'],
            'waste': ['garbage accumulation', 'waste dump', 'debris pile'],
            'drainage': ['drain blockage', 'stagnant water', 'sewage issue'],
            'lighting': ['broken streetlight', 'dark area', 'light damage']
        }
    
    def get_satellite_image(self, latitude: float, longitude: float, 
                           zoom: int = 18, image_size: int = 640) -> Dict:
        """
        Fetch satellite imagery from Google Maps Static API
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            zoom: Map zoom level (18 = street level detail)
            image_size: Image size in pixels
            
        Returns:
            Dict with image URL and metadata
        """
        try:
            # Using Google Maps Static API (free tier: 25k/month)
            # Alternative: Use Mapbox or Sentinel Hub for open data
            
            if not self.google_api_key:
                return {
                    'status': 'error',
                    'message': 'Google API key not configured. Using fallback URL.',
                    'url': self._get_fallback_url(latitude, longitude),
                    'latitude': latitude,
                    'longitude': longitude,
                    'timestamp': datetime.now().isoformat()
                }
            
            url = f"https://maps.googleapis.com/maps/api/staticmap"
            params = {
                'center': f'{latitude},{longitude}',
                'zoom': zoom,
                'size': f'{image_size}x{image_size}',
                'maptype': 'satellite',
                'key': self.google_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return {
                    'status': 'success',
                    'url': response.url,
                    'image_data': response.content,
                    'latitude': latitude,
                    'longitude': longitude,
                    'zoom': zoom,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'API Error: {response.status_code}',
                    'url': self._get_fallback_url(latitude, longitude),
                    'latitude': latitude,
                    'longitude': longitude
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'url': self._get_fallback_url(latitude, longitude),
                'latitude': latitude,
                'longitude': longitude
            }
    
    def _get_fallback_url(self, lat: float, lon: float) -> str:
        """Get Mapbox satellite tile URL (fallback when API key unavailable)"""
        return f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/{lon},{lat},18,0,0/640x640@2x"
    
    def analyze_satellite_image(self, image_data: bytes) -> Dict:
        """
        Use Gemini Vision to analyze satellite image for damage
        
        Args:
            image_data: Raw image bytes from satellite
            
        Returns:
            Detection results with problems found
        """
        try:
            if not image_data:
                return {'status': 'error', 'message': 'No image data provided'}
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Check if Gemini client is available
            if not self.genai_client:
                return {'status': 'error', 'message': 'Gemini API key not configured'}
            
            prompt = """Analyze this SATELLITE IMAGE of an urban/municipal area and detect infrastructure damage or problems.

FOCUS ON DETECTING:
1. POTHOLES/ROAD DAMAGE - Dark spots, cracks, uneven surfaces on roads
2. FLOODING/WATER - Accumulated water, wet areas, waterlogging
3. VEGETATION ISSUES - Overgrown trees, dead vegetation, hazardous branches
4. INFRASTRUCTURE - Broken poles, collapsed structures, visible damage
5. WASTE/DEBRIS - Garbage accumulation, debris piles, illegal dumps
6. DRAINAGE PROBLEMS - Blocked drains, stagnant water, sewage signs
7. LIGHTING - Dark areas requiring street lighting, broken lamp poles

RESPOND IN JSON FORMAT:
{
    "problems_detected": true/false,
    "severity": "critical/high/medium/low",
    "detected_issues": [
        {
            "type": "category name",
            "description": "what was detected",
            "confidence": 0.0-1.0,
            "location": "approximate location in image (e.g., 'center', 'top-left', 'bottom-right')",
            "affected_area_percentage": 0-100
        }
    ],
    "overall_assessment": "brief summary of municipal condition",
    "recommended_action": "what should be done",
    "repair_urgency": "immediate/urgent/moderate/preventive"
}

Be specific and accurate. Only report what you actually see in the satellite image."""
            
            # Convert image to base64 for new API
            import base64
            image_bytes = io.BytesIO()
            image.save(image_bytes, format='PNG')
            image_base64 = base64.b64encode(image_bytes.getvalue()).decode('utf-8')
            
            # Use new API to generate content
            response = self.genai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    {
                        'role': 'user',
                        'parts': [
                            {'text': prompt},
                            {
                                'inline_data': {
                                    'mime_type': 'image/png',
                                    'data': image_base64
                                }
                            }
                        ]
                    }
                ]
            )
            
            # Extract JSON from response
            response_text = response.text
            
            # Extract JSON from response
            response_text = response.text
            
            # Try to parse JSON
            try:
                # Find JSON in response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    analysis = {'raw_response': response_text}
            except json.JSONDecodeError:
                analysis = {'raw_response': response_text}
            
            return {
                'status': 'success',
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Analysis failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def scan_area(self, latitude: float, longitude: float, 
                  zoom: int = 18) -> Dict:
        """
        Complete pipeline: Fetch satellite image + Analyze for damage
        
        Args:
            latitude: Area latitude
            longitude: Area longitude
            zoom: Satellite zoom level
            
        Returns:
            Complete analysis with detected problems
        """
        # Step 1: Get satellite image
        sat_result = self.get_satellite_image(latitude, longitude, zoom)
        
        if sat_result['status'] != 'success' or 'image_data' not in sat_result:
            return {
                'status': 'error',
                'message': 'Could not fetch satellite image',
                'satellite_url': sat_result.get('url', ''),
                'latitude': latitude,
                'longitude': longitude
            }
        
        # Step 2: Analyze image with Gemini
        analysis = self.analyze_satellite_image(sat_result['image_data'])
        
        # Combine results
        return {
            'status': 'success',
            'latitude': latitude,
            'longitude': longitude,
            'satellite_url': sat_result['url'],
            'analysis': analysis.get('analysis', {}),
            'timestamp': datetime.now().isoformat(),
            'zoom': zoom
        }
    
    def scan_multiple_areas(self, locations: List[Tuple[float, float]]) -> List[Dict]:
        """
        Scan multiple areas for damage
        
        Args:
            locations: List of (latitude, longitude) tuples
            
        Returns:
            List of scan results for each location
        """
        results = []
        for lat, lon in locations:
            result = self.scan_area(lat, lon)
            results.append(result)
        return results
    
    def get_problem_report(self, analysis_results: Dict) -> Dict:
        """
        Generate actionable problem report from satellite analysis
        
        Args:
            analysis_results: Raw analysis from Gemini
            
        Returns:
            Formatted problem report
        """
        if 'analysis' not in analysis_results or 'detected_issues' not in analysis_results['analysis']:
            return {
                'has_problems': False,
                'problems': [],
                'report_summary': 'No problems detected'
            }
        
        issues = analysis_results['analysis']['detected_issues']
        
        # Group by category and severity
        problem_report = {
            'has_problems': len(issues) > 0,
            'total_issues': len(issues),
            'problems': issues,
            'severity': analysis_results['analysis'].get('severity', 'unknown'),
            'urgency': analysis_results['analysis'].get('repair_urgency', 'unknown'),
            'location': (analysis_results['latitude'], analysis_results['longitude']),
            'report_timestamp': analysis_results['timestamp']
        }
        
        return problem_report
    
    # ============== REAL-TIME LOCAL IMAGING METHODS ==============
    
    def analyze_local_satellite_image(self, image: Image.Image, 
                                     image_metadata: Optional[Dict] = None) -> Dict:
        """
        Analyze a local satellite image from the satellite images folder
        
        Args:
            image: PIL Image object
            image_metadata: Optional metadata about the image
            
        Returns:
            Detection results
        """
        try:
            if not image:
                return {'status': 'error', 'message': 'No image provided'}
            
            # Convert PIL Image to bytes
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            image_data = img_bytes.read()
            
            # Use existing analysis method with image data
            analysis_result = self.analyze_satellite_image(image_data)
            
            # Enrich with metadata
            if image_metadata:
                analysis_result['image_metadata'] = image_metadata
            
            return analysis_result
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Local image analysis failed: {str(e)}'
            }
    
    def scan_realtime_batch(self, batch_size: int = 5) -> List[Dict]:
        """
        Scan a batch of images from real-time stream
        
        Args:
            batch_size: Number of images to scan
            
        Returns:
            List of analysis results
        """
        if not self.image_stream:
            return []
        
        results = []
        batch = self.image_stream.get_image_batch(batch_size)
        
        for img, metadata, stream_idx in batch:
            analysis = self.analyze_local_satellite_image(img, metadata)
            results.append({
                'stream_index': stream_idx,
                'analysis': analysis,
                'metadata': metadata,
                'timestamp': datetime.now().isoformat()
            })
        
        return results
    
    def get_next_realtime_detection(self) -> Optional[Dict]:
        """
        Get next image from stream and analyze it
        
        Returns:
            Analysis result for next image or None
        """
        if not self.image_stream:
            return None
        
        next_img = self.image_stream.get_next_image()
        if next_img:
            img, metadata, stream_idx = next_img
            analysis = self.analyze_local_satellite_image(img, metadata)
            return {
                'stream_index': stream_idx,
                'analysis': analysis,
                'metadata': metadata,
                'stream_stats': self.image_stream.get_stream_statistics(),
                'timestamp': datetime.now().isoformat()
            }
        
        return None
    
    def get_imaging_statistics(self) -> Dict:
        """Get statistics about available satellite images"""
        if not self.realtime_imaging:
            return {'status': 'no_realtime_imaging'}
        
        return {
            'status': 'ready',
            'imaging_stats': self.realtime_imaging.get_image_statistics(),
            'stream_stats': self.image_stream.get_stream_statistics() if self.image_stream else {}
        }
    
    def scan_specific_local_image(self, image_index: int) -> Optional[Dict]:
        """
        Scan a specific image by index
        
        Args:
            image_index: Index of image in realtime imaging system
            
        Returns:
            Analysis result or None
        """
        if not self.realtime_imaging:
            return None
        
        result = self.realtime_imaging.get_image_by_index(image_index)
        if not result:
            return None
        
        img, metadata = result
        analysis = self.analyze_local_satellite_image(img, metadata)
        
        return {
            'image_index': image_index,
            'analysis': analysis,
            'metadata': metadata,
            'timestamp': datetime.now().isoformat()
        }
    
    def scan_category_images(self, category: str) -> List[Dict]:
        """
        Scan all images of a specific category
        
        Args:
            category: Image category (e.g., 'cat_1')
            
        Returns:
            List of analysis results
        """
        if not self.realtime_imaging:
            return []
        
        images_of_category = self.realtime_imaging.get_images_by_category(category)
        results = []
        
        for image_metadata in images_of_category:
            result = self.realtime_imaging.get_image_by_path(image_metadata['path'])
            if result:
                img, metadata = result
                analysis = self.analyze_local_satellite_image(img, metadata)
                results.append({
                    'analysis': analysis,
                    'metadata': metadata,
                    'timestamp': datetime.now().isoformat()
                })
        
        return results
    
    def stream_continuous_detection(self, duration_seconds: int = 60, 
                                   interval_seconds: float = 2.0) -> List[Dict]:
        """
        Stream continuous detection from realtime images for specified duration
        
        Args:
            duration_seconds: How long to stream (in seconds)
            interval_seconds: Time between image loads
            
        Returns:
            List of all detections during streaming
        """
        import time
        
        if not self.image_stream:
            return []
        
        detections = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            detection = self.get_next_realtime_detection()
            if detection:
                detections.append(detection)
                print(f"📊 Stream detection {len(detections)}: {detection['metadata']['filename']}")
            
            time.sleep(interval_seconds)
        
        return detections
    
    def export_realtime_index(self, output_path: str = "satellite_images_index.json") -> Optional[str]:
        """
        Export realtime imaging index to JSON file
        
        Args:
            output_path: Path to save the index
            
        Returns:
            Path to saved file or None
        """
        if not self.realtime_imaging:
            return None
        
        return self.realtime_imaging.export_index_json(output_path)


# Example usage
if __name__ == "__main__":
    detector = SatelliteDetector()
    
    # Show statistics
    stats = detector.get_imaging_statistics()
    print("📊 Imaging Statistics:", json.dumps(stats, indent=2))
    
    # Example: Scan batch of realtime images
    if detector.realtime_imaging:
        batch_results = detector.scan_realtime_batch(3)
        print(f"\n✅ Scanned {len(batch_results)} images from realtime stream")
        for result in batch_results:
            print(f"   - {result['metadata']['filename']}")
    
    # Example: Scan a specific location (API-based)
    # This would be Mumbai coordinates as example
    result = detector.scan_area(19.0760, 72.8777)
    
    print(json.dumps(result, indent=2))
