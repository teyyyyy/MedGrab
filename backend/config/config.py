import os
from dotenv import load_dotenv
from pathlib import Path

# Explicitly load .env from the config folder
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

class Config:
    """Base configuration class."""

    # Firestore credentials path
    FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")



   
