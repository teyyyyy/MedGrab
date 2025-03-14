import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    """Base configuration class."""
    
    # Firestore
    FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")

   
