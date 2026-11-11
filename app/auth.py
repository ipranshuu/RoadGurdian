from fastapi import Header, HTTPException
from app.config import settings

def require_api_key(x_api_key: str = Header(...)):
    """Every request must include header 'X-API-Key' or it gets rejected.
    Hackathon-grade auth — post-hackathon you'd use per-device tokens."""
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
