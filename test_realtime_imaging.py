"""
Test and demonstration script for Real-Time Satellite Imaging System
Tests the integration of local satellite images with the detection system
"""

import json
from pathlib import Path
from satellite_realtime_imaging import RealtimeSatelliteImaging, RealtimeImageStream
from satellite_detector import SatelliteDetector

def demonstrate_realtime_imaging():
    """Demonstrate real-time imaging capabilities"""
    
    print("=" * 80)
    print("🛰️ REAL-TIME SATELLITE IMAGING SYSTEM - DEMONSTRATION")
    print("=" * 80)
    
    # Check if satellite images folder exists
    satellite_path = Path("satellite images")
    if not satellite_path.exists():
        print(f"❌ Error: 'satellite images' folder not found")
        print(f"   Expected location: {satellite_path.absolute()}")
        return
    
    print(f"✅ Found satellite images folder: {satellite_path.absolute()}\n")
    
    # Initialize real-time imaging system
    print("📚 Initializing Real-Time Imaging System...")
    try:
        imaging = RealtimeSatelliteImaging("satellite images")
    except Exception as e:
        print(f"❌ Failed to initialize imaging system: {e}")
        return
    
    # Get statistics
    print("\n📊 IMAGE STATISTICS")
    print("-" * 80)
    stats = imaging.get_image_statistics()
    print(f"Total Images: {stats['total_images']}")
    print(f"Total Size: {stats['total_size_mb']} MB")
    print(f"Categories: {json.dumps(stats['categories'], indent=2)}")
    
    # Show first few images
    print("\n🖼️ SAMPLE IMAGES")
    print("-" * 80)
    for i in range(min(3, len(imaging.image_index))):
        img_meta = imaging.image_index[i]
        print(f"Image {i+1}:")
        print(f"  - Filename: {img_meta['filename']}")
        print(f"  - Path: {img_meta['path']}")
        print(f"  - Category: {img_meta['category']}")
        print(f"  - Size: {img_meta['width']}x{img_meta['height']}")
        print(f"  - Format: {img_meta.get('format', 'Unknown')}")
        print()
    
    # Test streaming
    print("\n▶️ STREAMING TEST")
    print("-" * 80)
    stream = RealtimeImageStream(imaging)
    print(f"Stream initialized")
    print(f"Stream statistics: {stream.get_stream_statistics()}")
    
    # Get a few images from stream
    print(f"\nGetting 3 images from stream...")
    for i in range(3):
        result = stream.get_next_image()
        if result:
            img, metadata, idx = result
            print(f"  Stream image {i+1}: {metadata['filename']}")
    
    print(f"Updated stream stats: {stream.get_stream_statistics()}\n")
    
    # Initialize detector with real-time imaging
    print("🤖 INITIALIZING SATELLITE DETECTOR WITH REAL-TIME IMAGING")
    print("-" * 80)
    detector = SatelliteDetector()
    
    if detector.realtime_imaging:
        print(f"✅ Real-time imaging system ready")
        print(f"✅ {len(detector.realtime_imaging.image_index)} images available")
    else:
        print(f"⚠️ Real-time imaging system not initialized")
        return
    
    # Get imaging statistics through detector
    print("\n📊 DETECTOR IMAGING STATISTICS")
    print("-" * 80)
    det_stats = detector.get_imaging_statistics()
    print(json.dumps(det_stats, indent=2))
    
    # Demonstrate batch scanning
    print("\n📦 BATCH SCANNING TEST (3 images)")
    print("-" * 80)
    print("Note: Actual analysis requires Gemini API key configured")
    print("Demonstrating the scanning workflow...\n")
    
    batch_results = detector.scan_realtime_batch(3)
    print(f"✅ Batch scan completed for {len(batch_results)} images")
    
    for result in batch_results:
        print(f"\nImage: {result['metadata']['filename']}")
        print(f"  - Stream Index: {result['stream_index']}")
        print(f"  - Size: {result['metadata']['width']}x{result['metadata']['height']}")
        print(f"  - Analysis Status: {result['analysis'].get('status', 'Unknown')}")
        if result['analysis'].get('status') == 'error':
            print(f"  - Error: {result['analysis'].get('message', 'Unknown error')}")
    
    # Export index
    print("\n📥 EXPORTING IMAGE INDEX")
    print("-" * 80)
    export_path = detector.export_realtime_index()
    if export_path:
        print(f"✅ Index exported to: {export_path}")
        print(f"   File size: {Path(export_path).stat().st_size / 1024:.2f} KB")
    
    # Test category scanning
    print("\n🔍 TESTING CATEGORY-BASED SCANNING")
    print("-" * 80)
    categories = stats['categories']
    if categories:
        first_category = list(categories.keys())[0]
        print(f"Scanning category: {first_category}")
        print(f"Note: Actual analysis requires Gemini API key configured")
        
        category_images = imaging.get_images_by_category(first_category)
        print(f"Found {len(category_images)} images in {first_category}")
        
        if category_images:
            print(f"Sample images from {first_category}:")
            for img_meta in category_images[:3]:
                print(f"  - {img_meta['filename']}")
    
    print("\n" + "=" * 80)
    print("✅ REAL-TIME IMAGING SYSTEM DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\n🚀 NEXT STEPS:")
    print("1. Ensure Gemini API key is configured in satellite_config.json")
    print("2. Run the Streamlit app: streamlit run app.py")
    print("3. Navigate to '04_satellite_scan' page")
    print("4. Use 'Real-Time Stream' tab to analyze satellite images")
    print("5. Choose between Batch Processing, Continuous Stream, or Specific Image modes")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    demonstrate_realtime_imaging()
