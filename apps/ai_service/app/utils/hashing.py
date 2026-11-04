import hashlib
from PIL import Image
import io
import imagehash


def generate_sha256(data: bytes) -> str:
    """
    Generate SHA-256 hash of binary data
    
    Args:
        data: Binary data to hash
        
    Returns:
        Hexadecimal string representation of the hash
    """
    return hashlib.sha256(data).hexdigest()


def generate_phash(image_bytes: bytes, hash_size: int = 8) -> str:
    """
    Generate perceptual hash (pHash) of an image
    
    pHash is robust to minor modifications like:
    - Slight scaling
    - Compression artifacts
    - Minor color adjustments
    
    Args:
        image_bytes: Raw image bytes
        hash_size: Size of the hash (default 8 gives 64-bit hash)
        
    Returns:
        Hexadecimal string representation of the perceptual hash
        
    Raises:
        ValueError: If image cannot be processed
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Generate perceptual hash
        phash = imagehash.phash(image, hash_size=hash_size)
        
        return str(phash)
        
    except Exception as e:
        raise ValueError(f"Failed to generate perceptual hash: {str(e)}")


def generate_dhash(image_bytes: bytes, hash_size: int = 8) -> str:
    """
    Generate difference hash (dHash) of an image
    
    dHash is faster than pHash and good for duplicate detection
    
    Args:
        image_bytes: Raw image bytes
        hash_size: Size of the hash
        
    Returns:
        Hexadecimal string representation of the difference hash
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        dhash = imagehash.dhash(image, hash_size=hash_size)
        
        return str(dhash)
        
    except Exception as e:
        raise ValueError(f"Failed to generate difference hash: {str(e)}")


def generate_average_hash(image_bytes: bytes, hash_size: int = 8) -> str:
    """
    Generate average hash (aHash) of an image
    
    aHash is the simplest and fastest perceptual hash
    
    Args:
        image_bytes: Raw image bytes
        hash_size: Size of the hash
        
    Returns:
        Hexadecimal string representation of the average hash
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        ahash = imagehash.average_hash(image, hash_size=hash_size)
        
        return str(ahash)
        
    except Exception as e:
        raise ValueError(f"Failed to generate average hash: {str(e)}")


def compare_hashes(hash1: str, hash2: str) -> int:
    """
    Compare two perceptual hashes and return Hamming distance
    
    Lower distance = more similar images
    Distance of 0 = identical images
    Distance < 10 = very similar images
    Distance < 20 = similar images
    
    Args:
        hash1: First hash string
        hash2: Second hash string
        
    Returns:
        Hamming distance between the hashes
    """
    try:
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)
        
        return h1 - h2
        
    except Exception as e:
        raise ValueError(f"Failed to compare hashes: {str(e)}")


def generate_all_hashes(image_bytes: bytes) -> dict:
    """
    Generate all types of hashes for an image
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        Dictionary containing all hash types
    """
    return {
        "sha256": generate_sha256(image_bytes),
        "phash": generate_phash(image_bytes),
        "dhash": generate_dhash(image_bytes),
        "ahash": generate_average_hash(image_bytes)
    }