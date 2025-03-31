import os
import json
from dotenv import load_dotenv
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore


def initialise_firestore():

    current_dir = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.join(current_dir, 'credentials.json')
    
    if cred_path and os.path.exists(cred_path):
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    

db = initialise_firestore()
