from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
from typing import Optional
import base64

from app.schemas import AnalyzeRequest, AnalyzeResponse, HealthResponse
from app.services.inference import InferenceService
from app.services.image_processing import ImageProcessor
from app.utils.hashing import generate_sha256, generate_phash

# Global inference service instance
inference_service: Optional[InferenceService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, cleanup on shutdown"""
    global inference_service
    print("🚀 Starting AI Microservice...")
    inference_service = InferenceService()
    await inference_service.load_model()
    print("✅ Model loaded successfully")
    yield
    print("🛑 Shutting down AI Microservice...")


app = FastAPI(
    title="AI Deepfake Detection Service",
    description="Stateless GPU worker for AI inference",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for internal communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Node.js service
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        model_loaded=inference_service is not None and inference_service.model_loaded,
        gpu_available=inference_service.device in ["cuda", "mps"] if inference_service else False
    )


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(
    file: Optional[UploadFile] = File(None),
    request: Optional[AnalyzeRequest] = None
):
    """
    Analyze image for deepfake detection
    
    Accepts either:
    - Multipart form data with image file
    - JSON with base64 encoded image
    """
    start_time = time.time()
    
    if inference_service is None or not inference_service.model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Get image bytes
        if file:
            image_bytes = await file.read()
        elif request and request.image_base64:
            try:
                image_bytes = base64.b64decode(request.image_base64)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid base64 encoding: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="No image provided")
        
        # Process image
        processor = ImageProcessor()
        image_tensor = processor.process_image(image_bytes)
        
        # Generate hashes
        sha256_hash = generate_sha256(image_bytes)
        phash = generate_phash(image_bytes)
        
        # Run inference
        result = await inference_service.predict(image_tensor)
        
        # Calculate inference time
        inference_time_ms = int((time.time() - start_time) * 1000)
        
        return AnalyzeResponse(
            ai_score=result["ai_score"],
            phash=phash,
            embedding=result["embedding"],
            is_flagged=result["is_flagged"],
            inference_time_ms=inference_time_ms,
            sha256=sha256_hash
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/analyze/batch", response_model=list[AnalyzeResponse])
async def analyze_batch(files: list[UploadFile] = File(...)):
    """
    Batch process multiple images
    
    Useful for processing video frames
    """
    if inference_service is None or not inference_service.model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if len(files) > 32:
        raise HTTPException(status_code=400, detail="Maximum 32 images per batch")
    
    results = []
    for file in files:
        try:
            start_time = time.time()
            image_bytes = await file.read()
            
            processor = ImageProcessor()
            image_tensor = processor.process_image(image_bytes)
            
            sha256_hash = generate_sha256(image_bytes)
            phash = generate_phash(image_bytes)
            
            result = await inference_service.predict(image_tensor)
            inference_time_ms = int((time.time() - start_time) * 1000)
            
            results.append(AnalyzeResponse(
                ai_score=result["ai_score"],
                phash=phash,
                embedding=result["embedding"],
                is_flagged=result["is_flagged"],
                inference_time_ms=inference_time_ms,
                sha256=sha256_hash
            ))
        except Exception as e:
            # Continue processing other images even if one fails
            results.append(AnalyzeResponse(
                ai_score=0.0,
                phash="",
                embedding=[0.0] * 768,
                is_flagged=False,
                inference_time_ms=0,
                sha256="",
                error=str(e)
            ))
    
    return results


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)