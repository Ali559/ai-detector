from PIL import Image
import io
import torch
import torchvision.transforms as transforms
from typing import Union


class ImageProcessor:
    """Handles image loading, preprocessing, and validation"""
    
    def __init__(self, target_size: tuple = (224, 224)):
        """
        Initialize image processor
        
        Args:
            target_size: Target image size (height, width)
        """
        self.target_size = target_size
        
        # Standard ImageNet normalization
        self.transform = transforms.Compose([
            transforms.Resize(target_size),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
    
    def load_image_from_bytes(self, image_bytes: bytes) -> Image.Image:
        """
        Load image from bytes
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            PIL Image object
            
        Raises:
            ValueError: If image cannot be loaded or is corrupt
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Verify image is valid
            image.verify()
            
            # Reopen after verify (verify closes the file)
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
            
        except Exception as e:
            raise ValueError(f"Failed to load image: {str(e)}")
    
    def preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """
        Preprocess image for model inference
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed image tensor
        """
        try:
            # Apply transforms
            tensor = self.transform(image)
            
            # Add batch dimension
            tensor = tensor.unsqueeze(0)
            
            return tensor
            
        except Exception as e:
            raise ValueError(f"Failed to preprocess image: {str(e)}")
    
    def process_image(self, image_bytes: bytes) -> torch.Tensor:
        """
        Complete pipeline: load and preprocess image
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Preprocessed image tensor ready for inference
        """
        image = self.load_image_from_bytes(image_bytes)
        return self.preprocess_image(image)
    
    def validate_image_size(self, image: Image.Image, max_size_mb: float = 10.0) -> bool:
        """
        Validate image size
        
        Args:
            image: PIL Image object
            max_size_mb: Maximum allowed size in MB
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        width, height = image.size
        
        # Check dimensions
        if width > 4096 or height > 4096:
            raise ValueError(f"Image dimensions too large: {width}x{height}")
        
        if width < 32 or height < 32:
            raise ValueError(f"Image dimensions too small: {width}x{height}")
        
        return True
    
    def get_image_info(self, image_bytes: bytes) -> dict:
        """
        Get image metadata
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Dictionary with image information
        """
        try:
            image = self.load_image_from_bytes(image_bytes)
            
            return {
                "width": image.size[0],
                "height": image.size[1],
                "mode": image.mode,
                "format": image.format,
                "size_bytes": len(image_bytes)
            }
        except Exception as e:
            raise ValueError(f"Failed to get image info: {str(e)}")