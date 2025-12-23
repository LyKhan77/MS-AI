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
from typing import List, Dict, Tuple, Optional
from config import Config


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
        self.all_defect_prompts = {
            'scratch': 'linear scratch mark on metal surface',
            'dent': 'dent or deformation on metal sheet',
            'rust': 'rust spot or corrosion on metal',
            'hole': 'hole or perforation in metal',
            'coating_bubble': 'paint bubble or coating defect',
            'oil_stain': 'oil or grease stain on metal',
            'discoloration': 'color irregularity or uneven tint',
            'pitting': 'small pits or indentations on surface',
            'edge_burr': 'rough or sharp edge burr',
            'warping': 'warped or bent metal deformation'
        }
        self.defect_prompts = self.all_defect_prompts.copy()
        
        # Size thresholds for severity classification (pixels²)
        self.severity_thresholds = {
            'minor': 100,      # < 100 px²
            'moderate': 500,   # 100-500 px²
            'critical': 9999999  # > 500 px²
        }
        
        # Confidence threshold
        self.confidence_threshold = 0.5

        # Cache for segmented images
        self.segmented_cache = {}

        # Temporary mask storage for segment_image_only
        self._current_masks = {}

        print(f"[DefectAnalyzer] Initialized on device: {self.device}")
    
    def load_model(self):
        """Load SAM-3 model from HuggingFace Transformers - called on first use to save memory"""
        if self.model is not None:
            return  # Already loaded
        
        try:
            print(f"[DefectAnalyzer] Loading SAM-3 from HuggingFace Transformers...")
            
            # Import SAM-3 for TEXT PROMPTS (based on reference project)
            # Reference uses Sam3Model + Sam3Processor for text prompt support
            from transformers import Sam3Processor, Sam3Model
            
            # SAM-3 model ID
            model_id = "facebook/sam3"
            
            print(f"[DefectAnalyzer] Loading model: {model_id} (Text Prompt Mode)")
            
            # Load processor and model for TEXT prompts
            self.processor = Sam3Processor.from_pretrained(model_id)
            self.model = Sam3Model.from_pretrained(model_id)
            
            # Move to GPU if available
            self.model.to(self.device)
            self.model.eval()
            
            print("[DefectAnalyzer] SAM-3 (Text Prompt Mode) loaded successfully!")
            print(f"[DefectAnalyzer] Model on device: {next(self.model.parameters()).device}")
            
        except Exception as e:
            error_msg = f"[DefectAnalyzer] CRITICAL: Failed to load SAM-3 model: {e}"
            print(error_msg)
            print("[DefectAnalyzer] Please ensure:")
            print("  1. You are logged in to HuggingFace: run 'huggingface-cli login' or './hf_login.sh'")
            print("  2. You have access to the 'facebook/sam3' model")
            print("  3. Required dependencies are installed: transformers, torch")
            import traceback
            traceback.print_exc()
            # Don't fallback to mock - raise error
            raise RuntimeError(f"SAM-3 model loading failed. Defect analysis cannot proceed. {e}")

    
    def analyze_session_captures(self, session_id: int, captures_dir: str, defect_types: list = None) -> Dict:
        """
        Analyze all captured images from a session for defects

        Args:
            session_id: Session ID
            captures_dir: Directory containing captured images
            defect_types: Optional list of defect type IDs to detect (defaults to all)

        Returns:
            results: {
                'total_images': int,
                'defects_found': int,
                'defects': [...]
            }
        """
        # Load model if not already loaded
        self.load_model()

        # Filter defect prompts based on selection
        if defect_types:
            self.defect_prompts = {k: v for k, v in self.all_defect_prompts.items() if k in defect_types}
            print(f"[DefectAnalyzer] Filtering to {len(self.defect_prompts)} defect types: {list(self.defect_prompts.keys())}")
        else:
            self.defect_prompts = self.all_defect_prompts.copy()

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

            # Generate segmented image with masks overlaid
            if defects:
                self._save_segmented_image(image, defects, session_id, img_file)

        results['processing_time'] = time.time() - start_time

        print(f"[DefectAnalyzer] Analysis complete! Found {results['defects_found']} defects in {results['processing_time']:.1f}s")

        return results

    def segment_image_only(
        self,
        session_id: int,
        image_path: str,
        defect_types: list = None
    ) -> Dict:
        """
        Segment image using SAM-3 and save overlay without cropping

        Args:
            session_id: Session ID
            image_path: Path to image file
            defect_types: Optional list of defect types to detect

        Returns:
            results: {
                'image_filename': str,
                'segmented_path': str,
                'defects_detected': int,
                'defects': [...]
            }
        """
        # Load model if not already loaded
        self.load_model()

        # Filter defect prompts based on selection
        if defect_types:
            self.defect_prompts = {k: v for k, v in self.all_defect_prompts.items() if k in defect_types}
            print(f"[DefectAnalyzer] Filtering to {len(self.defect_prompts)} defect types: {list(self.defect_prompts.keys())}")
        else:
            self.defect_prompts = self.all_defect_prompts.copy()

        # Load image
        if not os.path.exists(image_path):
            print(f"[DefectAnalyzer] Image not found: {image_path}")
            return None

        image = cv2.imread(image_path)
        if image is None:
            print(f"[DefectAnalyzer] Failed to load image: {image_path}")
            return None

        image_filename = os.path.basename(image_path)

        # Analyze image for defects (without cropping)
        defects = self._analyze_image_no_crop(image, image_filename, session_id)

        # Store masks for segmented image
        mask_data = {}
        for defect_type, mask in self._current_masks.items():
            mask_data[defect_type] = mask

        # Generate segmented image with masks overlaid
        if defects or mask_data:
            segmented_path = self._save_segmented_image(
                image, defects, session_id, image_filename, mask_data
            )
        else:
            segmented_path = None

        # Clear current masks
        self._current_masks = {}

        return {
            'image_filename': image_filename,
            'segmented_path': segmented_path,
            'defects_detected': len(defects),
            'defects': defects
        }

    def _analyze_image_no_crop(self, image: np.ndarray, img_filename: str, session_id: int) -> List[Dict]:
        """
        Analyze a single image for defects without generating crops

        Args:
            image: Image as numpy array (BGR from cv2)
            img_filename: Filename of the image
            session_id: Session ID

        Returns:
            defects: List of detected defects
        """
        defects = []
        self._current_masks = {}

        # Ensure model is loaded
        if self.model is None:
            raise RuntimeError("SAM-3 model not loaded. Cannot perform defect analysis.")

        # Preprocess image for SAM-3
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Import PIL for HuggingFace processing
        from PIL import Image as PILImage
        pil_image = PILImage.fromarray(image_rgb)

        orig_h, orig_w = image.shape[:2]

        # Detect defects with each text prompt
        for defect_type, prompt in self.defect_prompts.items():
            try:
                # Prepare inputs with text prompt
                inputs = self.processor(
                    text=[prompt],
                    images=pil_image,
                    return_tensors="pt"
                ).to(self.device)

                # Run inference
                with torch.no_grad():
                    outputs = self.model(**inputs)

                # Post-process using processor's instance segmentation method
                results = self.processor.post_process_instance_segmentation(
                    outputs,
                    threshold=self.confidence_threshold,
                    mask_threshold=0.5,
                    target_sizes=[[orig_h, orig_w]]
                )[0]

                # Extract masks and store for segmented image
                if 'masks' in results and len(results['masks']) > 0:
                    # Combine all masks for this defect type
                    combined_mask = np.zeros((orig_h, orig_w), dtype=np.uint8)

                    for mask in results['masks']:
                        # Convert mask to numpy
                        if isinstance(mask, torch.Tensor):
                            mask_np = mask.cpu().numpy()
                        else:
                            mask_np = np.array(mask)

                        # Normalize to uint8 0-255
                        if mask_np.dtype == bool:
                            mask_uint8 = (mask_np.astype(np.uint8)) * 255
                        elif mask_np.max() <= 1.0:
                            mask_uint8 = (mask_np * 255).astype(np.uint8)
                        else:
                            mask_uint8 = mask_np.astype(np.uint8)

                        # Add to combined mask
                        combined_mask = cv2.bitwise_or(combined_mask, mask_uint8)

                    # Store combined mask
                    self._current_masks[defect_type] = combined_mask

                    # Get confidence score
                    score = self.confidence_threshold
                    if hasattr(outputs, 'iou_scores') and len(outputs.iou_scores) > 0:
                        score = float(outputs.iou_scores.max())

                    # Calculate bounding box from combined mask
                    coords = np.argwhere(combined_mask > 0)
                    if len(coords) > 0:
                        y_coords, x_coords = coords[:, 0], coords[:, 1]
                        x_min, x_max = int(x_coords.min()), int(x_coords.max())
                        y_min, y_max = int(y_coords.min()), int(y_coords.max())
                        bbox = [x_min, y_min, x_max - x_min, y_max - y_min]

                        # Calculate area
                        area_pixels = int(combined_mask.sum() / 255)

                        # Determine severity
                        severity = self._calculate_severity(area_pixels)

                        defects.append({
                            'image_filename': img_filename,
                            'defect_type': defect_type,
                            'severity': severity,
                            'bbox': bbox,
                            'area_pixels': area_pixels,
                            'confidence': float(score),
                            'crop_filename': None,
                            'cropped': False,
                            'timestamp': datetime.now().isoformat()
                        })

            except Exception as e:
                print(f"[DefectAnalyzer] Error detecting {defect_type}: {e}")
                import traceback
                traceback.print_exc()
                continue

        return defects
    
    def _analyze_image(self, image: np.ndarray, img_filename: str, session_id: int) -> List[Dict]:
        """
        Analyze a single image for defects using SAM-3 from HuggingFace
        
        Args:
            image: Image as numpy array (BGR from cv2)
            img_filename: Filename of the image
            session_id: Session ID
            
        Returns:
            defects: List of detected defects
        """
        defects = []
        
        # Ensure model is loaded
        if self.model is None:
            raise RuntimeError("SAM-3 model not loaded. Cannot perform defect analysis.")
        
        # Preprocess image for SAM-3
        # Convert BGR (OpenCV) to RGB (SAM expects RGB)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Import PIL for HuggingFace processing
        from PIL import Image as PILImage
        pil_image = PILImage.fromarray(image_rgb)
        
        orig_h, orig_w = image.shape[:2]
        
        # Detect defects with each text prompt
        for defect_type, prompt in self.defect_prompts.items():
            try:
                # Prepare inputs with text prompt (based on reference project line 513-517)
                inputs = self.processor(
                    text=[prompt],  # Text prompt for zero-shot
                    images=pil_image,
                    return_tensors="pt"
                ).to(self.device)
                
                # Run inference
                with torch.no_grad():
                    outputs = self.model(**inputs)
                
                # Post-process using processor's instance segmentation method
                # (based on reference project line 567-572)
                results = self.processor.post_process_instance_segmentation(
                    outputs,
                    threshold=self.confidence_threshold,
                    mask_threshold=0.5,
                    target_sizes=[[orig_h, orig_w]]
                )[0]
                
                # Extract masks from results
                if 'masks' in results and len(results['masks']) > 0:
                    for mask in results['masks']:
                        # Convert mask to numpy (based on reference line 597-610)
                        if isinstance(mask, torch.Tensor):
                            mask_np = mask.cpu().numpy()
                        else:
                            mask_np = np.array(mask)
                        
                        # Normalize to uint8 0-255
                        if mask_np.dtype == bool:
                            mask_uint8 = (mask_np.astype(np.uint8)) * 255
                        elif mask_np.max() <= 1.0:
                            mask_uint8 = (mask_np * 255).astype(np.uint8)
                        else:
                            mask_uint8 = mask_np.astype(np.uint8)
                        
                        # Get confidence score from IoU if available
                        score = self.confidence_threshold  # Default
                        if hasattr(outputs, 'iou_scores') and len(outputs.iou_scores) > 0:
                            score = float(outputs.iou_scores.max())
                        
                        # Process defect mask
                        defect = self._process_defect_mask(
                            image, mask_uint8, score, defect_type,
                            img_filename, session_id
                        )
                        if defect is not None:
                            defects.append(defect)
                        
            except Exception as e:
                print(f"[DefectAnalyzer] Error detecting {defect_type}: {e}")
                import traceback
                traceback.print_exc()
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
            'cropped': crop_filename is not None,
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
        defect_type: str,
        with_mask: bool = True
    ) -> str:
        """
        Save cropped defect region as transparent PNG

        Args:
            image: Source image
            mask: Segmentation mask
            bbox: Bounding box [x, y, w, h]
            session_id: Session ID
            img_filename: Original image filename
            defect_type: Defect type identifier
            with_mask: If True, apply mask for transparency; if False, crop only

        Returns:
            crop_filename: Filename of saved PNG
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

        # Create defects directory
        defects_dir = f"data/sessions/{session_id}/defects"
        os.makedirs(defects_dir, exist_ok=True)

        # Generate filename
        base_name = os.path.splitext(img_filename)[0]
        timestamp = int(time.time() * 1000)  # milliseconds
        crop_filename = f"{defect_type}_{base_name}_{timestamp}.png"
        crop_path = os.path.join(defects_dir, crop_filename)

        # Create BGRA image with alpha channel
        crop_bgra = cv2.cvtColor(crop, cv2.COLOR_BGR2BGRA)

        if with_mask and mask is not None:
            # Crop mask
            mask_crop = mask[y:y+h, x:x+w]

            # Resize mask if needed
            if mask_crop.shape[:2] != crop_bgra.shape[:2]:
                mask_crop = cv2.resize(mask_crop, (crop_bgra.shape[1], crop_bgra.shape[0]))

            # Set alpha channel based on mask
            # Pixels inside mask get alpha=255, outside get alpha=0
            alpha = (mask_crop > 0).astype(np.uint8) * 255
            crop_bgra[:, :, 3] = alpha
        else:
            # No transparency - fully opaque
            crop_bgra[:, :, 3] = 255

        # Save as PNG with alpha channel
        cv2.imwrite(crop_path, crop_bgra)

        return crop_filename

    def _save_segmented_image(
        self,
        image: np.ndarray,
        defects: List[Dict],
        session_id: int,
        image_filename: str,
        mask_data: Optional[Dict[str, np.ndarray]] = None
    ) -> str:
        """
        Overlay all segmentation masks on original image with defect-type colors

        Args:
            image: Original image as numpy array
            defects: List of defects with bbox and type information
            session_id: Session ID
            image_filename: Original image filename
            mask_data: Optional pre-computed masks per defect type {type: mask_array}

        Returns:
            segmented_image_path: Path to saved segmented image
        """
        # Create overlay image copy
        overlay = np.zeros_like(image, dtype=np.float32)

        # Use defect-type colors from Config
        defect_colors = Config.DEFECT_COLORS

        # Apply masks for each defect
        for defect in defects:
            defect_type = defect['defect_type']
            bbox = defect['bbox']
            x, y, w, h = bbox

            # Get color for this defect type
            color = defect_colors.get(defect_type, [255, 255, 255])

            # If mask_data is provided, use actual masks
            if mask_data and defect_type in mask_data:
                mask = mask_data[defect_type]
                # Resize mask to match image if needed
                if mask.shape[:2] != image.shape[:2]:
                    mask = cv2.resize(mask, (image.shape[1], image.shape[0]))

                # Apply mask overlay with defect color
                for c in range(3):
                    overlay[:, :, c] += (mask / 255.0) * color[c]
            else:
                # Fallback: use bounding box rectangle
                cv2.rectangle(overlay, (x, y), (x + w, y + h), color, 2)

        # Clip overlay values to valid range
        overlay = np.clip(overlay, 0, 255).astype(np.uint8)

        # Blend overlay with original image (50% overlay, 50% original)
        result = cv2.addWeighted(image, 0.5, overlay, 0.5, 0)

        # Save to segmented subdirectory
        segmented_dir = f"data/sessions/{session_id}/segmented"
        os.makedirs(segmented_dir, exist_ok=True)

        segmented_filename = f"segmented_{image_filename}"
        segmented_path = os.path.join(segmented_dir, segmented_filename)
        cv2.imwrite(segmented_path, result)

        # Cache the path
        if session_id not in self.segmented_cache:
            self.segmented_cache[session_id] = {}
        self.segmented_cache[session_id][image_filename] = segmented_path

        return segmented_path

    def get_session_segmented_images(self, session_id: int) -> Dict[str, str]:
        """
        Get cached segmented image paths for a session

        Args:
            session_id: Session ID

        Returns:
            Dict mapping filename -> segmented image path
        """
        if session_id in self.segmented_cache:
            return self.segmented_cache[session_id]

        # Load from filesystem if not in cache
        segmented_dir = f"data/sessions/{session_id}/segmented"
        if not os.path.exists(segmented_dir):
            return {}

        files = [f for f in os.listdir(segmented_dir)
                  if f.startswith('segmented_')]

        self.segmented_cache[session_id] = {
            f.replace('segmented_', ''): os.path.join(segmented_dir, f)
            for f in files
        }
        return self.segmented_cache[session_id]

    def generate_segmented_for_image(
        self,
        session_id: int,
        image_filename: str,
        defects: List[Dict]
    ):
        """
        Generate segmented image for a specific image with its defects

        Args:
            session_id: Session ID
            image_filename: Image filename
            defects: List of defects for this image
        """
        if not defects:
            print(f"[DefectAnalyzer] No defects to generate segmented image for: {image_filename}")
            return

        captures_dir = f"data/sessions/{session_id}/captures"
        img_path = os.path.join(captures_dir, image_filename)
        image = cv2.imread(img_path)

        if image is None:
            print(f"[DefectAnalyzer] Failed to load image: {img_path}")
            return

        self._save_segmented_image(image, defects, session_id, image_filename)
        print(f"[DefectAnalyzer] Generated segmented image: {image_filename}")

    def crop_and_store_defects(
        self,
        session_id: int,
        image_filename: str,
        defects: List[Dict],
        mask_data: Optional[Dict[str, np.ndarray]] = None
    ) -> List[str]:
        """
        Generate and store cropped PNGs for defects

        Args:
            session_id: Session ID
            image_filename: Original image filename
            defects: List of defect dictionaries
            mask_data: Optional pre-computed masks per defect type

        Returns:
            crop_filenames: List of generated crop filenames
        """
        # Load original image
        captures_dir = f"data/sessions/{session_id}/captures"
        img_path = os.path.join(captures_dir, image_filename)
        image = cv2.imread(img_path)

        if image is None:
            print(f"[DefectAnalyzer] Failed to load image: {img_path}")
            return []

        crop_filenames = []

        for defect in defects:
            # Check if already cropped
            if defect.get('cropped', False):
                if defect.get('crop_filename'):
                    crop_filenames.append(defect['crop_filename'])
                continue

            defect_type = defect['defect_type']
            bbox = defect['bbox']

            # Get mask for this defect type if available
            mask = None
            if mask_data and defect_type in mask_data:
                mask = mask_data[defect_type]

            # Generate crop filename
            base_name = os.path.splitext(image_filename)[0]
            timestamp = int(time.time() * 1000) + len(crop_filenames)
            crop_filename = f"{defect_type}_{base_name}_{timestamp}.png"

            # Generate crop
            generated_filename = self._save_defect_crop(
                image, mask, bbox, session_id, image_filename, defect_type, with_mask=True
            )

            # Update defect entry
            defect['crop_filename'] = generated_filename
            defect['cropped'] = True

            crop_filenames.append(generated_filename)

        print(f"[DefectAnalyzer] Generated {len(crop_filenames)} cropped PNGs for {image_filename}")
        return crop_filenames


# Global instance (lazy loaded)
_defect_analyzer = None

def get_defect_analyzer():
    """Get or create global DefectAnalyzer instance"""
    global _defect_analyzer
    if _defect_analyzer is None:
        _defect_analyzer = DefectAnalyzer()
    return _defect_analyzer
