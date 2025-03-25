import os
import json
from dotenv import load_dotenv
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore

# Explicitly load .env from the config folder
env_path = Path(__file__).parent.parent.parent / "config" / ".env"
load_dotenv(dotenv_path=env_path)

def initialise_firestore():
    # Option 1: Use a path to the credentials file
    cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
    
    if cred_path and os.path.exists(cred_path):
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    

db = initialise_firestore()
