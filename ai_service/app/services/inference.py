import torch
import asyncio
from typing import Dict, Optional
import os

from app.models.deepfake_detector import DeepfakeDetector, load_pretrained_detector


class InferenceService:
    """
    Handles AI model inference
    
    Manages model loading, GPU optimization, and prediction
    """
    
    def __init__(
        self, 
        model_path: Optional[str] = None,
        embedding_dim: int = 768,
        threshold: float = 0.7
    ):
        """
        Initialize inference service
        
        Args:
            model_path: Path to pretrained model weights
            embedding_dim: Dimension of embedding vectors
            threshold: Threshold for flagging images (0-1)
        """
        self.model_path = model_path or os.getenv("MODEL_PATH")
        self.embedding_dim = embedding_dim
        self.threshold = threshold
        self.model = None
        
        # Auto-detect best available device
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"  # Apple Silicon GPU
        else:
            self.device = "cpu"
        
        self.model_loaded = False
        
        print(f"🔧 Inference service initialized on device: {self.device}")
    
    async def load_model(self):
        """Load the model asynchronously"""
        try:
            # Run model loading in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, 
                self._load_model_sync
            )
            self.model_loaded = True
            print(f"✅ Model loaded successfully on {self.device}")
            
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            raise
    
    def _load_model_sync(self) -> DeepfakeDetector:
        """Synchronous model loading"""
        model = load_pretrained_detector(
            model_path=self.model_path,
            device=self.device
        )
        
        # Optimize for inference
        # Note: MPS (Apple Silicon) doesn't support FP16 yet, only CUDA does
        if self.device == "cuda":
            model = model.half()  # Use FP16 for faster inference on GPU
            print("⚡ Using FP16 for CUDA inference")
        elif self.device == "mps":
            print("⚡ Using Apple Silicon GPU (MPS backend)")
        
        return model
    
    async def predict(self, image_tensor: torch.Tensor) -> Dict:
        """
        Run inference on image tensor
        
        Args:
            image_tensor: Preprocessed image tensor
            
        Returns:
            Dictionary with prediction results
        """
        if not self.model_loaded:
            raise RuntimeError("Model not loaded")
        
        try:
            # Move tensor to device
            image_tensor = image_tensor.to(self.device)
            
            # Convert to FP16 only if using CUDA (MPS doesn't support it yet)
            if self.device == "cuda":
                image_tensor = image_tensor.half()
            
            # Run inference in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._predict_sync,
                image_tensor
            )
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Inference failed: {str(e)}")
    
    def _predict_sync(self, image_tensor: torch.Tensor) -> Dict:
        """Synchronous prediction"""
        with torch.no_grad():
            output, embedding = self.model(image_tensor)
            
            # Get probability score
            ai_score = output.squeeze().cpu().float().item()
            
            # Get embedding as list
            embedding_list = embedding.squeeze().cpu().float().numpy().tolist()
            
            # Ensure embedding is exactly 768 dimensions
            if len(embedding_list) != 768:
                # Pad or truncate if necessary
                if len(embedding_list) < 768:
                    embedding_list.extend([0.0] * (768 - len(embedding_list)))
                else:
                    embedding_list = embedding_list[:768]
            
            # Determine if flagged
            is_flagged = ai_score > self.threshold
            
            return {
                "ai_score": float(ai_score),
                "embedding": embedding_list,
                "is_flagged": bool(is_flagged)
            }
    
    def update_threshold(self, new_threshold: float):
        """Update the flagging threshold"""
        if 0.0 <= new_threshold <= 1.0:
            self.threshold = new_threshold
            print(f"📊 Threshold updated to {new_threshold}")
        else:
            raise ValueError("Threshold must be between 0 and 1")
    
    async def batch_predict(
        self, 
        image_tensors: list[torch.Tensor]
    ) -> list[Dict]:
        """
        Run batch inference on multiple images
        
        Args:
            image_tensors: List of preprocessed image tensors
            
        Returns:
            List of prediction results
        """
        results = []
        
        # Process in batches of 8 for efficiency
        batch_size = 8
        for i in range(0, len(image_tensors), batch_size):
            batch = image_tensors[i:i + batch_size]
            
            # Stack tensors into single batch
            batch_tensor = torch.cat(batch, dim=0)
            
            # Run prediction
            result = await self.predict(batch_tensor)
            results.append(result)
        
        return results
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model"""
        if not self.model_loaded:
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            "device": self.device,
            "embedding_dim": self.embedding_dim,
            "threshold": self.threshold,
            "model_params": sum(p.numel() for p in self.model.parameters()),
            "fp16_enabled": self.device == "cuda",
            "mps_enabled": self.device == "mps"
        }