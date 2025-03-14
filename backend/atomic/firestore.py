import os
import firebase_admin
from firebase_admin import credentials, firestore
from config.config import Config

def initialise_firestore():
    cred_path = Config.FIREBASE_CREDENTIALS  

    if not cred_path or not os.path.exists(cred_path):
        raise FileNotFoundError(f"Firebase credentials file not found: {cred_path}")

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    return firestore.client()


db = initialise_firestore()
