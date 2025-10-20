import torch
import torch.nn as nn
from torchvision import models
from typing import Tuple
import numpy as np


class DeepfakeDetector(nn.Module):
    """
    Deepfake detection model based on EfficientNet
    
    Uses pretrained EfficientNet-B0 as backbone with custom classification head
    Outputs both classification logits and embeddings
    """
    
    def __init__(self, embedding_dim: int = 768, pretrained: bool = True):
        """
        Initialize the model
        
        Args:
            embedding_dim: Dimension of the embedding vector
            pretrained: Whether to use pretrained weights
        """
        super(DeepfakeDetector, self).__init__()
        
        # Load pretrained EfficientNet-B0 with new syntax
        from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights
        
        if pretrained:
            weights = EfficientNet_B0_Weights.IMAGENET1K_V1
        else:
            weights = None
            
        self.backbone = efficientnet_b0(weights=weights)
        
        # Get the number of features from the last layer
        num_features = self.backbone.classifier[1].in_features
        
        # Remove the original classifier
        self.backbone.classifier = nn.Identity()
        
        # Create embedding layer
        self.embedding_layer = nn.Sequential(
            nn.Linear(num_features, embedding_dim),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        
        # Create classification head
        self.classifier = nn.Sequential(
            nn.Linear(embedding_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 1),
            nn.Sigmoid()  # Output probability
        )
        
        self.embedding_dim = embedding_dim
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass
        
        Args:
            x: Input tensor of shape (batch_size, 3, 224, 224)
            
        Returns:
            Tuple of (classification_output, embedding)
        """
        # Extract features from backbone
        features = self.backbone(x)
        
        # Generate embedding
        embedding = self.embedding_layer(features)
        
        # Generate classification output
        output = self.classifier(embedding)
        
        return output, embedding
    
    def predict(self, x: torch.Tensor) -> dict:
        """
        Make prediction with additional metadata
        
        Args:
            x: Input tensor
            
        Returns:
            Dictionary with prediction results
        """
        with torch.no_grad():
            output, embedding = self.forward(x)
            
            # Get probability score
            probability = output.squeeze().cpu().item()
            
            # Get embedding as numpy array
            embedding_np = embedding.squeeze().cpu().numpy()
            
            # Determine if flagged (threshold at 0.7)
            is_flagged = probability > 0.7
            
            return {
                "ai_score": float(probability),
                "embedding": embedding_np.tolist(),
                "is_flagged": bool(is_flagged)
            }


class CLIPBasedDetector(nn.Module):
    """
    Alternative detector using CLIP embeddings
    
    CLIP provides excellent zero-shot capabilities and semantic understanding
    """
    
    def __init__(self, embedding_dim: int = 768):
        super(CLIPBasedDetector, self).__init__()
        
        # Note: In production, you would load CLIP from transformers
        # For now, we'll use a placeholder architecture
        
        self.feature_extractor = nn.Sequential(
            nn.Conv2d(3, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(128, 256, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        
        self.embedding_layer = nn.Linear(256, embedding_dim)
        self.classifier = nn.Sequential(
            nn.Linear(embedding_dim, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        features = self.feature_extractor(x)
        features = features.view(features.size(0), -1)
        embedding = self.embedding_layer(features)
        output = self.classifier(embedding)
        return output, embedding


def load_pretrained_detector(
    model_path: str = None, 
    device: str = "cuda"
) -> DeepfakeDetector:
    """
    Load pretrained deepfake detector
    
    Args:
        model_path: Path to pretrained weights (optional)
        device: Device to load model on
        
    Returns:
        Loaded model
    """
    model = DeepfakeDetector(embedding_dim=768, pretrained=True)
    
    if model_path:
        try:
            state_dict = torch.load(model_path, map_location=device)
            model.load_state_dict(state_dict)
            print(f"✅ Loaded pretrained weights from {model_path}")
        except Exception as e:
            print(f"⚠️  Could not load weights from {model_path}: {e}")
            print("📦 Using ImageNet pretrained backbone only")
    
    model = model.to(device)
    model.eval()
    
    return model