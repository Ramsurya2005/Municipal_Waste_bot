"""
Real-time Satellite Imaging System
Loads and serves satellite images from local storage for live detection and analysis
"""

import os
import json
from pathlib import Path
from PIL import Image
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import hashlib


class RealtimeSatelliteImaging:
    """Manages real-time satellite image loading and serving from local storage"""
    
    def __init__(self, base_path: str = "satellite images"):
        """
        Initialize real-time imaging system
        
        Args:
            base_path: Path to satellite images folder
        """
        self.base_path = Path(base_path)
        self.images_cache = {}
        self.image_metadata = {}
        self.image_index = []
        
        # Ensure paths exist
        if not self.base_path.exists():
            raise ValueError(f"Satellite images folder not found: {base_path}")
        
        self._load_images_index()
        print(f"✅ Real-time Imaging initialized: {len(self.image_index)} images found")
    
    def _load_images_index(self):
        """Index all available satellite images"""
        self.image_index = []
        supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
        
        for root, dirs, files in os.walk(self.base_path):
            for file in sorted(files):
                if file.lower().endswith(supported_formats):
                    full_path = Path(root) / file
                    relative_path = full_path.relative_to(self.base_path)
                    
                    # Extract metadata
                    metadata = self._extract_metadata(file, str(relative_path), full_path)
                    self.image_index.append(metadata)
                    self.image_metadata[str(full_path)] = metadata
        
        print(f"📊 Indexed {len(self.image_index)} satellite images")
    
    def _extract_metadata(self, filename: str, relative_path: str, 
                         full_path: Path) -> Dict:
        """Extract metadata from image filename and properties"""
        try:
            # Try to open image and get dimensions
            img = Image.open(full_path)
            width, height = img.size
            file_size = os.path.getsize(full_path) / (1024 * 1024)  # MB
            
            # Extract category from filename if available (e.g., cat_1.jpg)
            category = "unknown"
            if "_" in filename:
                parts = filename.split("_")
                if parts[0].startswith("cat"):
                    category = parts[0]
            
            # Generate image hash for verification
            img_hash = self._get_file_hash(full_path)
            
            return {
                'filename': filename,
                'path': str(relative_path),
                'full_path': str(full_path),
                'category': category,
                'width': width,
                'height': height,
                'file_size_mb': round(file_size, 2),
                'format': img.format,
                'hash': img_hash,
                'indexed_at': datetime.now().isoformat(),
                'source': 'local'
            }
        except Exception as e:
            print(f"⚠️ Error processing {filename}: {e}")
            return {
                'filename': filename,
                'path': str(relative_path),
                'full_path': str(full_path),
                'category': 'unknown',
                'error': str(e),
                'source': 'local'
            }
    
    @staticmethod
    def _get_file_hash(filepath: Path, algorithm: str = 'md5') -> str:
        """Generate hash of image file"""
        hash_obj = hashlib.md5() if algorithm == 'md5' else hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    
    def get_image_by_index(self, index: int) -> Optional[Tuple[Image.Image, Dict]]:
        """
        Get image by index
        
        Returns:
            Tuple of (PIL Image, metadata) or None if index invalid
        """
        if index < 0 or index >= len(self.image_index):
            return None
        
        metadata = self.image_index[index]
        full_path = metadata['full_path']
        
        try:
            img = Image.open(full_path)
            return img, metadata
        except Exception as e:
            print(f"❌ Error loading image: {e}")
            return None
    
    def get_image_by_path(self, relative_path: str) -> Optional[Tuple[Image.Image, Dict]]:
        """Get image by relative path"""
        full_path = self.base_path / relative_path
        
        try:
            img = Image.open(full_path)
            metadata = self.image_metadata.get(str(full_path), {})
            return img, metadata
        except Exception as e:
            print(f"❌ Error loading image: {e}")
            return None
    
    def get_images_by_category(self, category: str) -> List[Dict]:
        """Get all images for a specific category"""
        return [img for img in self.image_index if img.get('category') == category]
    
    def get_random_images(self, count: int = 5) -> List[Tuple[Image.Image, Dict]]:
        """Get random images for streaming/detection"""
        import random
        selected_indices = random.sample(range(len(self.image_index)), 
                                        min(count, len(self.image_index)))
        
        images = []
        for idx in selected_indices:
            result = self.get_image_by_index(idx)
            if result:
                images.append(result)
        
        return images
    
    def get_all_metadata(self) -> List[Dict]:
        """Get metadata for all images"""
        return self.image_index
    
    def get_images_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Filter images by indexed date range (ISO format)"""
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        return [img for img in self.image_index 
                if start <= datetime.fromisoformat(img.get('indexed_at', '')) <= end]
    
    def convert_to_numpy(self, image: Image.Image) -> np.ndarray:
        """Convert PIL Image to numpy array"""
        return np.array(image)
    
    def get_image_statistics(self) -> Dict:
        """Get statistics about available images"""
        total_size = sum([img.get('file_size_mb', 0) for img in self.image_index])
        categories = {}
        
        for img in self.image_index:
            cat = img.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            'total_images': len(self.image_index),
            'total_size_mb': round(total_size, 2),
            'categories': categories,
            'indexed_at': datetime.now().isoformat(),
            'base_path': str(self.base_path)
        }
    
    def reload_index(self):
        """Reload image index (for detecting new images)"""
        self.image_index = []
        self.image_metadata = {}
        self._load_images_index()
        print("🔄 Image index reloaded")
    
    def export_index_json(self, output_path: str = "satellite_images_index.json"):
        """Export image index to JSON for quick access"""
        index_data = {
            'generated_at': datetime.now().isoformat(),
            'total_images': len(self.image_index),
            'images': self.image_index,
            'statistics': self.get_image_statistics()
        }
        
        with open(output_path, 'w') as f:
            json.dump(index_data, f, indent=2)
        
        print(f"✅ Index exported to {output_path}")
        return output_path


class RealtimeImageStream:
    """Stream satellite images for continuous monitoring and detection"""
    
    def __init__(self, imaging_system: RealtimeSatelliteImaging):
        """Initialize image stream"""
        self.imaging = imaging_system
        self.stream_history = []
        self.current_index = 0
    
    def get_next_image(self) -> Optional[Tuple[Image.Image, Dict, int]]:
        """
        Get next image in stream
        
        Returns:
            Tuple of (image, metadata, stream_index)
        """
        if self.current_index >= len(self.imaging.image_index):
            self.current_index = 0
        
        result = self.imaging.get_image_by_index(self.current_index)
        
        if result:
            img, metadata = result
            index = self.current_index
            self.current_index += 1
            
            stream_entry = {
                'stream_index': index,
                'timestamp': datetime.now().isoformat(),
                'image_metadata': metadata
            }
            self.stream_history.append(stream_entry)
            
            return img, metadata, index
        
        return None
    
    def get_image_batch(self, batch_size: int = 5) -> List[Tuple[Image.Image, Dict, int]]:
        """Get batch of images for parallel processing"""
        batch = []
        for _ in range(batch_size):
            result = self.get_next_image()
            if result:
                batch.append(result)
            else:
                break
        
        return batch
    
    def reset_stream(self):
        """Reset stream to beginning"""
        self.current_index = 0
        print("🔄 Image stream reset")
    
    def get_stream_statistics(self) -> Dict:
        """Get streaming statistics"""
        return {
            'current_position': self.current_index,
            'total_images': len(self.imaging.image_index),
            'stream_entries': len(self.stream_history),
            'progress_percent': (self.current_index / len(self.imaging.image_index) * 100) 
                               if self.imaging.image_index else 0
        }


# Example usage
if __name__ == "__main__":
    # Initialize real-time imaging
    imaging = RealtimeSatelliteImaging("satellite images")
    
    # Get statistics
    stats = imaging.get_image_statistics()
    print(f"\n📊 Image Statistics:")
    print(json.dumps(stats, indent=2))
    
    # Get first image
    result = imaging.get_image_by_index(0)
    if result:
        img, metadata = result
        print(f"\n🖼️ First image: {metadata['filename']}")
        print(f"   Size: {metadata['width']}x{metadata['height']}")
        print(f"   Format: {metadata['format']}")
    
    # Initialize streaming
    stream = RealtimeImageStream(imaging)
    print(f"\n▶️ Stream started: {stream.get_stream_statistics()}")
    
    # Get batch
    batch = stream.get_image_batch(3)
    print(f"📦 Batch loaded: {len(batch)} images")
    
    # Export index
    imaging.export_index_json()
