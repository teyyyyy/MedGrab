import firebase_admin
from firebase_admin import credentials, firestore
from config import Config

def initialize_firestore():
    if not firebase_admin._apps:  
        cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS)
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firestore()