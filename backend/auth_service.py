from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate("firebase_config.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)

def verify_token(id_token):
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token['uid']
    except:
        return None

@app.route('/signup', methods=['POST'])
def signup():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    uid = verify_token(token)
    if not uid:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    print(f"User {uid} signed up with: {data}")
    return jsonify({'message': 'Signup successful', 'uid': uid})

@app.route('/login', methods=['POST'])
def login():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    uid = verify_token(token)
    if not uid:
        return jsonify({'error': 'Unauthorized'}), 401

    return jsonify({'message': 'Login successful', 'uid': uid})

if __name__ == '__main__':
    app.run(port=5001, debug=True) 
