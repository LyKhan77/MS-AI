"""
SAM-3 Defect Analyzer for Metal Sheet Quality Control

Post-session batch analysis of captured images to detect:
- Scratches
- Dents  
- Rust
- Holes
- Coating bubbles
"""

import os
import cv2
import numpy as np
import torch
import time
from datetime import datetime
from typing import List, Dict, Tuple


class DefectAnalyzer:
    """
    SAM-3 based defect detection for metal sheets
    Uses zero-shot segmentation with text prompts
    """
    
    def __init__(self, checkpoint_path='models/sam3_vit_h.pth', device='cuda'):
        """
        Initialize SAM-3 model for defect detection
        
        Args:
            checkpoint_path: Path to SAM-3 checkpoint
            device: 'cuda' or 'cpu'
        """
        self.device = device if torch.cuda.is_available() else 'cpu'
        self.checkpoint_path = checkpoint_path
        self.model = None
        self.predictor = None
        
        # Defect prompts for zero-shot detection
        self.defect_prompts = {
            'scratch': 'linear scratch mark on metal surface',
            'dent': 'dent or deformation on metal sheet',
            'rust': 'rust spot or corrosion on metal',
            'hole': 'hole or perforation in metal',
            'coating_bubble': 'paint bubble or coating defect'
        }
        
        # Size thresholds for severity classification (pixels²)
        self.severity_thresholds = {
            'minor': 100,      # < 100 px²
            'moderate': 500,   # 100-500 px²
            'critical': 9999999  # > 500 px²
        }
        
        # Confidence threshold
        self.confidence_threshold = 0.5
        
        print(f"[DefectAnalyzer] Initialized on device: {self.device}")
    
    def load_model(self):
        """Load SAM-3 model - called on first use to save memory"""
        if self.model is not None:
            return  # Already loaded
        
        try:
            # Import SAM-3 modules
            from sam3 import sam3_model_registry, Sam3Predictor
            
            # Load model
            print(f"[DefectAnalyzer] Loading SAM-3 from {self.checkpoint_path}...")
            self.model = sam3_model_registry['vit_h'](checkpoint=self.checkpoint_path)
            self.model.to(self.device)
            self.model.eval()
            
            # Create predictor
            self.predictor = Sam3Predictor(self.model)
            
            print("[DefectAnalyzer] SAM-3 loaded successfully!")
            
        except Exception as e:
            print(f"[DefectAnalyzer] Error loading SAM-3: {e}")
            print("[DefectAnalyzer] Falling back to mock mode for testing")
            self.model = "mock"  # Mock mode for testing
    
    def analyze_session_captures(self, session_id: int, captures_dir: str) -> Dict:
        """
        Analyze all captured images from a session for defects
        
        Args:
            session_id: Session ID
            captures_dir: Directory containing captured images
            
        Returns:
            results: {
                'total_images': int,
                'defects_found': int,
                'defects': [...]
            }
        """
        # Load model if not already loaded
        self.load_model()
        
        results = {
            'total_images': 0,
            'defects_found': 0,
            'defects': [],
            'processing_time': 0
        }
        
        # Check if captures directory exists
        if not os.path.exists(captures_dir):
            print(f"[DefectAnalyzer] Captures directory not found: {captures_dir}")
            return results
        
        # Get all image files
        image_files = [f for f in os.listdir(captures_dir) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        image_files.sort()
        
        results['total_images'] = len(image_files)
        print(f"[DefectAnalyzer] Analyzing {len(image_files)} images from session {session_id}...")
        
        start_time = time.time()
        
        # Process each image
        for idx, img_file in enumerate(image_files):
            print(f"[DefectAnalyzer] Processing {idx+1}/{len(image_files)}: {img_file}")
            
            img_path = os.path.join(captures_dir, img_file)
            image = cv2.imread(img_path)
            
            if image is None:
                print(f"[DefectAnalyzer] Failed to load image: {img_file}")
                continue
            
            # Analyze image for defects
            defects = self._analyze_image(image, img_file, session_id)
            
            results['defects'].extend(defects)
            results['defects_found'] += len(defects)
        
        results['processing_time'] = time.time() - start_time
        
        print(f"[DefectAnalyzer] Analysis complete! Found {results['defects_found']} defects in {results['processing_time']:.1f}s")
        
        return results
    
    def _analyze_image(self, image: np.ndarray, img_filename: str, session_id: int) -> List[Dict]:
        """
        Analyze a single image for defects
        
        Args:
            image: Image as numpy array
            img_filename: Filename of the image
            session_id: Session ID
            
        Returns:
            defects: List of detected defects
        """
        defects = []
        
        # Mock mode for testing
        if self.model == "mock":
            return self._mock_detection(image, img_filename, session_id)
        
        # Set image for SAM-3 predictor
        self.predictor.set_image(image)
        
        # Detect defects with each prompt
        for defect_type, prompt in self.defect_prompts.items():
            try:
                # Run SAM-3 prediction with text prompt
                masks, scores, _ = self.predictor.predict_with_text(
                    text_prompt=prompt,
                    multimask_output=True
                )
                
                # Process each detected mask
                for mask, score in zip(masks, scores):
                    if score > self.confidence_threshold:
                        defect = self._process_defect_mask(
                            image, mask, score, defect_type, 
                            img_filename, session_id
                        )
                        defects.append(defect)
                        
            except Exception as e:
                print(f"[DefectAnalyzer] Error detecting {defect_type}: {e}")
                continue
        
        return defects
    
    def _process_defect_mask(
        self, 
        image: np.ndarray, 
        mask: np.ndarray, 
        score: float,
        defect_type: str,
        img_filename: str,
        session_id: int
    ) -> Dict:
        """
        Process a defect mask and extract information
        
        Returns:
            defect: Dictionary with defect information
        """
        # Calculate bounding box
        coords = np.argwhere(mask > 0)
        if len(coords) == 0:
            # Empty mask
            return None
        
        y_coords, x_coords = coords[:, 0], coords[:, 1]
        x_min, x_max = int(x_coords.min()), int(x_coords.max())
        y_min, y_max = int(y_coords.min()), int(y_coords.max())
        
        bbox = [x_min, y_min, x_max - x_min, y_max - y_min]
        
        # Calculate area
        area_pixels = int(mask.sum())
        
        # Determine severity
        severity = self._calculate_severity(area_pixels)
        
        # Save defect crop
        crop_filename = self._save_defect_crop(
            image, mask, bbox, session_id, img_filename, defect_type
        )
        
        return {
            'image_filename': img_filename,
            'defect_type': defect_type,
            'severity': severity,
            'bbox': bbox,
            'area_pixels': area_pixels,
            'confidence': float(score),
            'crop_filename': crop_filename,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_severity(self, area_pixels: int) -> str:
        """Calculate defect severity based on area"""
        if area_pixels < self.severity_thresholds['minor']:
            return 'minor'
        elif area_pixels < self.severity_thresholds['moderate']:
            return 'moderate'
        else:
            return 'critical'
    
    def _save_defect_crop(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        bbox: List[int],
        session_id: int,
        img_filename: str,
        defect_type: str
    ) -> str:
        """
        Save cropped defect region with mask overlay
        
        Returns:
            crop_filename: Filename of saved crop
        """
        x, y, w, h = bbox
        
        # Ensure bbox is within image bounds
        h_img, w_img = image.shape[:2]
        x = max(0, min(x, w_img - 1))
        y = max(0, min(y, h_img - 1))
        w = min(w, w_img - x)
        h = min(h, h_img - y)
        
        # Crop image
        crop = image[y:y+h, x:x+w].copy()
        
        # Crop mask
        mask_crop = mask[y:y+h, x:x+w]
        
        # Overlay mask (semi-transparent red)
        if crop.shape[0] > 0 and crop.shape[1] > 0:
            crop[mask_crop > 0] = crop[mask_crop > 0] * 0.6 + np.array([0, 0, 255]) * 0.4
        
        # Create defects directory
        defects_dir = f"data/sessions/{session_id}/defects"
        os.makedirs(defects_dir, exist_ok=True)
        
        # Generate filename
        base_name = os.path.splitext(img_filename)[0]
        timestamp = int(time.time() * 1000)  # milliseconds
        crop_filename = f"{defect_type}_{base_name}_{timestamp}.jpg"
        crop_path = os.path.join(defects_dir, crop_filename)
        
        # Save crop
        cv2.imwrite(crop_path, crop)
        
        return crop_filename
    
    def _mock_detection(self, image: np.ndarray, img_filename: str, session_id: int) -> List[Dict]:
        """
        Mock defect detection for testing without SAM-3
        Generates random defects for demonstration
        """
        import random
        
        defects = []
        h, w = image.shape[:2]
        
        # Generate 0-3 random defects per image
        num_defects = random.randint(0, 3)
        
        for i in range(num_defects):
            defect_type = random.choice(list(self.defect_prompts.keys()))
            
            # Random bbox
            x = random.randint(0, w - 100)
            y = random.randint(0, h - 100)
            bbox_w = random.randint(50, 200)
            bbox_h = random.randint(50, 200)
            bbox = [x, y, bbox_w, bbox_h]
            
            area = bbox_w * bbox_h
            severity = self._calculate_severity(area)
            confidence = random.uniform(0.6, 0.95)
            
            # Create simple mask
            mask = np.zeros((h, w), dtype=bool)
            mask[y:y+bbox_h, x:x+bbox_w] = True
            
            # Save crop
            crop_filename = self._save_defect_crop(
                image, mask, bbox, session_id, img_filename, defect_type
            )
            
            defects.append({
                'image_filename': img_filename,
                'defect_type': defect_type,
                'severity': severity,
                'bbox': bbox,
                'area_pixels': area,
                'confidence': confidence,
                'crop_filename': crop_filename,
                'timestamp': datetime.now().isoformat()
            })
        
        return defects


# Global instance (lazy loaded)
_defect_analyzer = None

def get_defect_analyzer():
    """Get or create global DefectAnalyzer instance"""
    global _defect_analyzer
    if _defect_analyzer is None:
        _defect_analyzer = DefectAnalyzer()
    return _defect_analyzer
