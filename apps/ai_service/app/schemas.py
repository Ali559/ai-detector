from pydantic import BaseModel, Field, validator
from typing import Optional


class AnalyzeRequest(BaseModel):
    """Request schema for image analysis"""
    image_base64: str = Field(..., description="Base64 encoded image")
    
    @validator('image_base64')
    def validate_base64(cls, v):
        if not v:
            raise ValueError("image_base64 cannot be empty")
        return v


class AnalyzeResponse(BaseModel):
    """Response schema for image analysis"""
    ai_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="AI confidence score (0-1, higher means more likely AI-generated)"
    )
    phash: str = Field(..., description="Perceptual hash of the image")
    embedding: list[float] = Field(
        ..., 
        description="768-dimensional embedding vector"
    )
    is_flagged: bool = Field(
        ..., 
        description="Whether the image is flagged as suspicious"
    )
    inference_time_ms: int = Field(
        ..., 
        description="Inference time in milliseconds"
    )
    sha256: str = Field(..., description="SHA-256 hash of the image")
    error: Optional[str] = Field(None, description="Error message if processing failed")
    
    @validator('embedding')
    def validate_embedding(cls, v):
        if len(v) != 768:
            raise ValueError(f"Embedding must be 768 dimensions, got {len(v)}")
        return v


class HealthResponse(BaseModel):
    """Health check response"""
    model_config = {"protected_namespaces": ()}  # Fix Pydantic warning
    
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether the model is loaded")
    gpu_available: bool = Field(..., description="Whether GPU is available")


class BatchAnalyzeRequest(BaseModel):
    """Request schema for batch analysis"""
    images_base64: list[str] = Field(
        ..., 
        max_items=32,
        description="List of base64 encoded images (max 32)"
    )
    
    @validator('images_base64')
    def validate_batch_size(cls, v):
        if len(v) == 0:
            raise ValueError("At least one image required")
        if len(v) > 32:
            raise ValueError("Maximum 32 images per batch")
        return v