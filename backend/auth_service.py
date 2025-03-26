from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory user store (temporary)
DUMMY_USERS = {}

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if email in DUMMY_USERS:
        return jsonify({'error': 'User already exists'}), 400

    # Get additional fields
    name = data.get("name")
    phone = data.get("phone")
    medical_record = data.get("medicalRecord")
    location = data.get("location")

    # Store everything (simulate user profile)
    DUMMY_USERS[email] = {
        "password": password,
        "name": name,
        "phone": phone,
        "medical_record": medical_record,
        "location": location
    }

    print(f"✅ New user signed up: {email}")
    print(f"Details: Name={name}, Phone={phone}, MedicalRecord={medical_record}, Location={location}")

    return jsonify({'message': 'Signup successful', 'uid': email})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if email in DUMMY_USERS and DUMMY_USERS[email]["password"] == password:
        return jsonify({'message': 'Login successful', 'uid': email})

    return jsonify({'error': 'Invalid credentials'}), 401

if __name__ == '__main__':
    app.run(port=5001, debug=True)
