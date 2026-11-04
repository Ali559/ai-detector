import pytest
from fastapi.testclient import TestClient
from app.main import app
import base64
import io
from PIL import Image


client = TestClient(app)


def create_test_image() -> bytes:
    """Create a simple test image"""
    img = Image.new('RGB', (224, 224), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    return img_bytes.getvalue()


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data
    assert "gpu_available" in data


def test_analyze_with_file():
    """Test analyze endpoint with file upload"""
    test_image = create_test_image()
    
    response = client.post(
        "/analyze",
        files={"file": ("test.jpg", test_image, "image/jpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "ai_score" in data
    assert "phash" in data
    assert "embedding" in data
    assert "is_flagged" in data
    assert "inference_time_ms" in data
    assert "sha256" in data
    
    # Check data types and ranges
    assert 0.0 <= data["ai_score"] <= 1.0
    assert isinstance(data["phash"], str)
    assert isinstance(data["embedding"], list)
    assert len(data["embedding"]) == 768
    assert isinstance(data["is_flagged"], bool)
    assert data["inference_time_ms"] > 0


def test_analyze_with_base64():
    """Test analyze endpoint with base64 encoded image"""
    test_image = create_test_image()
    image_b64 = base64.b64encode(test_image).decode('utf-8')
    
    response = client.post(
        "/analyze",
        json={"image_base64": image_b64}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "ai_score" in data
    assert len(data["embedding"]) == 768


def test_analyze_without_image():
    """Test analyze endpoint without providing an image"""
    response = client.post("/analyze")
    assert response.status_code == 400
    assert "No image provided" in response.json()["detail"]


def test_analyze_with_invalid_base64():
    """Test analyze endpoint with invalid base64"""
    response = client.post(
        "/analyze",
        json={"image_base64": "invalid_base64!!!"}
    )
    assert response.status_code == 400
    assert "Invalid base64" in response.json()["detail"]


def test_batch_analyze():
    """Test batch analyze endpoint"""
    test_image = create_test_image()
    
    files = [
        ("files", ("test1.jpg", test_image, "image/jpeg")),
        ("files", ("test2.jpg", test_image, "image/jpeg")),
    ]
    
    response = client.post("/analyze/batch", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) == 2
    
    for item in data:
        assert "ai_score" in item
        assert "embedding" in item
        assert len(item["embedding"]) == 768


def test_batch_analyze_too_many():
    """Test batch endpoint with too many images"""
    test_image = create_test_image()
    
    # Create 33 files (exceeds limit of 32)
    files = [
        ("files", (f"test{i}.jpg", test_image, "image/jpeg"))
        for i in range(33)
    ]
    
    response = client.post("/analyze/batch", files=files)
    assert response.status_code == 400
    assert "Maximum 32 images" in response.json()["detail"]


def test_embedding_consistency():
    """Test that same image produces same embedding"""
    test_image = create_test_image()
    
    # Analyze same image twice
    response1 = client.post(
        "/analyze",
        files={"file": ("test.jpg", test_image, "image/jpeg")}
    )
    response2 = client.post(
        "/analyze",
        files={"file": ("test.jpg", test_image, "image/jpeg")}
    )
    
    data1 = response1.json()
    data2 = response2.json()
    
    # SHA256 should be identical
    assert data1["sha256"] == data2["sha256"]
    
    # pHash should be identical for same image
    assert data1["phash"] == data2["phash"]
    
    # Embeddings should be very similar (allowing for float precision)
    embedding1 = data1["embedding"]
    embedding2 = data2["embedding"]
    
    # Calculate cosine similarity (should be close to 1.0)
    import numpy as np
    e1 = np.array(embedding1)
    e2 = np.array(embedding2)
    similarity = np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2))
    
    assert similarity > 0.99  # Very similar


@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test handling concurrent requests"""
    import asyncio
    
    test_image = create_test_image()
    
    async def make_request():
        return client.post(
            "/analyze",
            files={"file": ("test.jpg", test_image, "image/jpeg")}
        )
    
    # Make 5 concurrent requests
    responses = await asyncio.gather(*[make_request() for _ in range(5)])
    
    # All should succeed
    for response in responses:
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])