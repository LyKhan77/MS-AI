"""
SAM-3 based metal sheet detection and segmentation module
Handles model loading, inference, and post-processing
"""

import torch
import numpy as np
import cv2
import supervision as sv
from typing import List, Dict, Tuple, Optional, Union
from PIL import Image
import logging
from dataclasses import dataclass
import time
import os

# Import SAM-3 components
try:
    from transformers import Sam3Processor, Sam3Model
except ImportError:
    logger.error("Please install transformers>=4.45.0 with SAM-3 support")
    raise

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """Data class for detection results"""
    masks: np.ndarray  # [N, H, W] binary masks
    boxes: np.ndarray  # [N, 4] bounding boxes (x1, y1, x2, y2)
    scores: np.ndarray  # [N] confidence scores
    count: int  # number of detected objects
    processing_time: float  # inference time in seconds
    dimensions: List[Dict[str, float]]  # [{length: mm, width: mm}, ...]
    quality_status: List[str]  # ["OK" or "NG"] for each detected object


class SAM3Engine:
    """SAM-3 based metal sheet detection engine"""
    
    def __init__(self, 
                 model_name: str = "facebook/sam3",
                 device: Optional[str] = None,
                 confidence_threshold: float = 0.5,
                 mask_threshold: float = 0.5):
        """
        Initialize SAM-3 detection engine
        
        Args:
            model_name: SAM-3 model name or path
            device: Device to run inference on (auto-detect if None)
            confidence_threshold: Minimum confidence for detections
            mask_threshold: Threshold for mask binary conversion
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.mask_threshold = mask_threshold
        
        # Auto-detect device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Using device: {self.device}")
        
        # Model components
        self.model = None
        self.processor = None
        self.model_loaded = False
        
        # Performance optimization
        self.vision_embeds_cache = {}
        self.text_embeds_cache = {}
        
    def load_model(self) -> bool:
        """
        Load SAM-3 model and processor
        
        Returns:
            bool: True if model loaded successfully
        """
        try:
            logger.info(f"Loading SAM-3 model: {self.model_name}")
            
            # Load processor and model
            self.processor = Sam3Processor.from_pretrained(self.model_name)
            self.model = Sam3Model.from_pretrained(self.model_name)
            
            # Move to device
            self.model = self.model.to(self.device)
            
            # Set to evaluation mode
            self.model.eval()
            
            # Optimize for inference
            if self.device == "cuda":
                # Enable CUDA optimizations
                with torch.no_grad():
                    # Warm up the model
                    dummy_input = torch.randn(1, 3, 224, 224).to(self.device)
                    _ = self.model.get_vision_features(pixel_values=dummy_input)
            
            self.model_loaded = True
            logger.info("SAM-3 model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load SAM-3 model: {e}")
            return False
    
    def preprocess_image(self, image: Union[np.ndarray, Image.Image]) -> Image.Image:
        """
        Preprocess input image for SAM-3
        
        Args:
            image: Input image (numpy array or PIL Image)
            
        Returns:
            PIL.Image: Preprocessed image
        """
        if isinstance(image, np.ndarray):
            # Convert BGR to RGB if needed
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            return Image.fromarray(image)
        return image
    
    def detect_sheets(self, 
                     image: Union[np.ndarray, Image.Image],
                     text_prompt: str = "metal sheet",
                     use_cache: bool = True) -> Optional[DetectionResult]:
        """
        Detect metal sheets in image using SAM-3
        
        Args:
            image: Input image
            text_prompt: Text prompt for detection
            use_cache: Whether to use cached embeddings
            
        Returns:
            DetectionResult or None if detection failed
        """
        if not self.model_loaded:
            logger.error("Model not loaded")
            return None
        
        start_time = time.time()
        
        try:
            # Preprocess image
            if isinstance(image, np.ndarray):
                pil_image = self.preprocess_image(image)
            else:
                pil_image = image
            
            # Get image hash for caching
            image_hash = hash(pil_image.tobytes()) if use_cache else None
            
            # Check cache for vision embeddings
            vision_embeds = None
            if use_cache and image_hash in self.vision_embeds_cache:
                vision_embeds = self.vision_embeds_cache[image_hash]
                logger.debug("Using cached vision embeddings")
            
            # Check cache for text embeddings
            text_hash = hash(text_prompt) if use_cache else None
            text_embeds = None
            attention_mask = None
            if use_cache and text_hash in self.text_embeds_cache:
                cached = self.text_embeds_cache[text_hash]
                text_embeds = cached["embeds"]
                attention_mask = cached["mask"]
                logger.debug("Using cached text embeddings")
            
            with torch.no_grad():
                if vision_embeds is None:
                    # Process image and get vision embeddings
                    img_inputs = self.processor(images=pil_image, return_tensors="pt")
                    img_inputs = {k: v.to(self.device) for k, v in img_inputs.items()}
                    vision_embeds = self.model.get_vision_features(
                        pixel_values=img_inputs["pixel_values"]
                    )
                    
                    # Cache vision embeddings
                    if use_cache and image_hash is not None:
                        self.vision_embeds_cache[image_hash] = vision_embeds
                        # Limit cache size
                        if len(self.vision_embeds_cache) > 10:
                            self.vision_embeds_cache.pop(next(iter(self.vision_embeds_cache)))
                
                if text_embeds is None:
                    # Process text and get text embeddings
                    text_inputs = self.processor(text=text_prompt, return_tensors="pt")
                    text_inputs = {k: v.to(self.device) for k, v in text_inputs.items()}
                    text_embeds = self.model.get_text_features(**text_inputs)
                    attention_mask = text_inputs["attention_mask"]
                    
                    # Cache text embeddings
                    if use_cache and text_hash is not None:
                        self.text_embeds_cache[text_hash] = {
                            "embeds": text_embeds,
                            "mask": attention_mask
                        }
                
                # Run inference
                outputs = self.model(
                    vision_embeds=vision_embeds,
                    text_embeds=text_embeds,
                    attention_mask=attention_mask
                )
                
                # Post-process results
                results = self.processor.post_process_instance_segmentation(
                    outputs,
                    threshold=self.confidence_threshold,
                    mask_threshold=self.mask_threshold,
                    target_sizes=[(pil_image.height, pil_image.width)]
                )[0]
                
                # Extract results
                masks = results["masks"].cpu().numpy() if len(results["masks"]) > 0 else np.array([])
                boxes = results["boxes"].cpu().numpy() if len(results["boxes"]) > 0 else np.array([])
                scores = results["scores"].cpu().numpy() if len(results["scores"]) > 0 else np.array([])
                
                # Initialize empty lists for dimensions and quality
                dimensions = []
                quality_status = []
                
                processing_time = time.time() - start_time
                
                detection_result = DetectionResult(
                    masks=masks,
                    boxes=boxes,
                    scores=scores,
                    count=len(masks),
                    processing_time=processing_time,
                    dimensions=dimensions,
                    quality_status=quality_status
                )
                
                logger.info(f"Detected {detection_result.count} metal sheets in {processing_time:.3f}s")
                return detection_result
                
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return None
    
    def calculate_dimensions(self, 
                           detection_result: DetectionResult,
                           pixel_to_mm_ratio: float) -> DetectionResult:
        """
        Calculate real-world dimensions for detected sheets
        
        Args:
            detection_result: Detection results
            pixel_to_mm_ratio: Conversion ratio from pixels to millimeters
            
        Returns:
            DetectionResult with dimensions calculated
        """
        dimensions = []
        
        for i in range(detection_result.count):
            if i < len(detection_result.masks):
                mask = detection_result.masks[i]
                
                # Find contours in mask
                contours, _ = cv2.findContours(
                    mask.astype(np.uint8) * 255,
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE
                )
                
                if contours:
                    # Get largest contour
                    contour = max(contours, key=cv2.contourArea)
                    
                    # Get minimum area rectangle (rotated bounding box)
                    rect = cv2.minAreaRect(contour)
                    (center, (width, height), angle) = rect
                    
                    # Convert to millimeters
                    length_mm = max(width, height) * pixel_to_mm_ratio
                    width_mm = min(width, height) * pixel_to_mm_ratio
                    
                    dimensions.append({
                        "length": length_mm,
                        "width": width_mm,
                        "angle": angle,
                        "center": center
                    })
                else:
                    dimensions.append({
                        "length": 0,
                        "width": 0,
                        "angle": 0,
                        "center": (0, 0)
                    })
        
        detection_result.dimensions = dimensions
        return detection_result
    
    def detect_defects(self, 
                      detection_result: DetectionResult,
                      original_image: np.ndarray,
                      defect_sensitivity: float = 0.1) -> DetectionResult:
        """
        Detect surface defects in metal sheets
        
        Args:
            detection_result: Detection results
            original_image: Original image for defect analysis
            defect_sensitivity: Sensitivity threshold for defect detection
            
        Returns:
            DetectionResult with quality status updated
        """
        quality_status = []
        
        for i in range(detection_result.count):
            if i < len(detection_result.masks):
                mask = detection_result.masks[i]
                
                # Apply mask to original image
                masked_image = cv2.bitwise_and(
                    original_image, 
                    original_image, 
                    mask=mask.astype(np.uint8)
                )
                
                # Convert to grayscale for analysis
                gray = cv2.cvtColor(masked_image, cv2.COLOR_BGR2GRAY)
                
                # Calculate texture features
                # Use Laplacian variance for texture analysis
                laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                
                # Use Sobel gradients for edge detection
                sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
                sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
                edge_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
                
                # Calculate defect score
                edge_density = np.mean(edge_magnitude > 50)  # Threshold for edge pixels
                
                # Simple defect classification based on texture and edges
                defect_score = laplacian_var / 1000 + edge_density
                
                # Determine quality status
                if defect_score > defect_sensitivity:
                    quality_status.append("NG")
                else:
                    quality_status.append("OK")
            else:
                quality_status.append("NG")  # Default to NG if no mask
        
        detection_result.quality_status = quality_status
        return detection_result
    
    def visualize_results(self, 
                         image: np.ndarray,
                         detection_result: DetectionResult,
                         pixel_to_mm_ratio: float = 1.0,
                         show_labels: bool = True) -> np.ndarray:
        """
        Visualize detection results on image
        
        Args:
            image: Original image
            detection_result: Detection results
            pixel_to_mm_ratio: Conversion ratio for dimension display
            show_labels: Whether to show dimension labels
            
        Returns:
            np.ndarray: Image with visualizations overlay
        """
        if detection_result.count == 0:
            return image
        
        # Create copy for visualization
        vis_image = image.copy()
        
        # Color map for different objects
        colors = sv.ColorPalette.default()
        
        for i in range(detection_result.count):
            if i >= len(detection_result.masks):
                continue
            
            mask = detection_result.masks[i]
            color = colors.by_idx(i)
            
            # Determine color based on quality
            if i < len(detection_result.quality_status):
                if detection_result.quality_status[i] == "OK":
                    overlay_color = (0, 255, 0, 128)  # Green with transparency
                else:
                    overlay_color = (0, 0, 255, 128)  # Red with transparency
            else:
                overlay_color = color.as_rgb() + (128,)  # Default color with transparency
            
            # Draw filled mask with transparency
            mask_overlay = np.zeros_like(vis_image)
            mask_overlay[mask > 0] = overlay_color[:3]
            vis_image = cv2.addWeighted(vis_image, 0.7, mask_overlay, 0.3, 0)
            
            # Draw bounding box
            if i < len(detection_result.boxes):
                box = detection_result.boxes[i].astype(int)
                cv2.rectangle(vis_image, (box[0], box[1]), (box[2], box[3]), overlay_color[:3], 2)
                
                # Add dimension text
                if show_labels and i < len(detection_result.dimensions):
                    dim = detection_result.dimensions[i]
                    label = f"L:{dim['length']:.1f}mm W:{dim['width']:.1f}mm"
                    
                    # Position text at top of box
                    text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                    text_x = box[0]
                    text_y = box[1] - 10 if box[1] > 30 else box[1] + text_size[1] + 10
                    
                    # Draw background for text
                    cv2.rectangle(
                        vis_image,
                        (text_x - 5, text_y - text_size[1] - 5),
                        (text_x + text_size[0] + 5, text_y + 5),
                        (255, 255, 255),
                        -1
                    )
                    
                    # Draw text
                    cv2.putText(
                        vis_image,
                        label,
                        (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        overlay_color[:3],
                        2
                    )
        
        # Add count and processing time info
        info_text = f"Count: {detection_result.count} | Time: {detection_result.processing_time:.3f}s"
        cv2.putText(
            vis_image,
            info_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )
        
        return vis_image
    
    def clear_cache(self):
        """Clear embedding caches"""
        self.vision_embeds_cache.clear()
        self.text_embeds_cache.clear()
        logger.info("Cleared embedding caches")
    
    def get_model_info(self) -> dict:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "loaded": self.model_loaded,
            "confidence_threshold": self.confidence_threshold,
            "mask_threshold": self.mask_threshold,
            "vision_cache_size": len(self.vision_embeds_cache),
            "text_cache_size": len(self.text_embeds_cache)
        }
