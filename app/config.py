from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # SQLite = a database stored as one file. Zero setup. Perfect for hackathons.
    database_url: str = "sqlite:///./pothole.db"
    # The secret key your mobile app must send. Change this before the demo.
    api_key: str = "hackathon-demo-key-123"
    # Two detections closer than this (meters) = same pothole
    dedup_radius_m: float = 25.0
    # "sandbox" = pretend portal for the demo (honest). Never fake a real submission.
    portal_mode: str = "sandbox"

class Config:
        env_file = ".env"

settings = Settings()
