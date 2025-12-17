import torch
import logging
# from sam2.build_sam import build_sam2
# from sam2.sam2_image_predictor import SAM2ImagePredictor

logger = logging.getLogger(__name__)

class SAM2Wrapper:
    def __init__(self, checkpoint_path: str = "sam2_hiera_tiny.pt", config_path: str = "sam2_hiera_tiny.yaml"):
        self.checkpoint_path = checkpoint_path
        self.config_path = config_path
        self.predictor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def load_model(self):
        if self.predictor is None:
            logger.info("Loading SAM 2 Model...")
            try:
                # Mocking import for dev environment if sam2 not installed
                # In real deployment, these imports should be at top
                from sam2.build_sam import build_sam2
                from sam2.sam2_image_predictor import SAM2ImagePredictor
                
                model = build_sam2(self.config_path, self.checkpoint_path, device=self.device)
                self.predictor = SAM2ImagePredictor(model)
                logger.info("SAM 2 Model Loaded Successfully")
            except ImportError:
                logger.warning("SAM 2 library not found. Running in MOCK mode.")
                self.predictor = "MOCK_PREDICTOR"

    def unload_model(self):
        if self.predictor:
            del self.predictor
            torch.cuda.empty_cache()
            self.predictor = None
            logger.info("SAM 2 Model Unloaded")

    def predict(self, image, box_prompt):
        """
        Generate mask from box prompt
        box_prompt: [x1, y1, x2, y2]
        """
        if self.predictor is None:
            self.load_model()
            
        if self.predictor == "MOCK_PREDICTOR":
            # Return dummy mask
            import numpy as np
            h, w = image.shape[:2]
            mask = np.zeros((h, w), dtype=np.uint8)
            x1, y1, x2, y2 = map(int, box_prompt)
            mask[y1:y2, x1:x2] = 1 # Simple box mask
            return mask

        self.predictor.set_image(image)
        masks, scores, logits = self.predictor.predict(
            box=box_prompt,
            multimask_output=False
        )
        return masks[0]

# Global instance
sam_service = SAM2Wrapper()
