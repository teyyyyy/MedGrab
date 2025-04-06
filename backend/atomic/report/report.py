from flask import Flask
from flask import Blueprint, request, jsonify
from flask_cors import CORS

# Initialise databse
import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv


def initialise_firestore():
    # Load environment variables from .env.two file
    load_dotenv('.env')

    # Create a credential dictionary from environment variables
    cred_dict = {
        "type": os.getenv("REPORT_FB_TYPE", "service_account"),
        "project_id": os.getenv("REPORT_FB_PROJECT_ID"),
        "private_key_id": os.getenv("REPORT_FB_PRIVATE_KEY_ID"),
        "private_key": os.getenv("REPORT_FB_PRIVATE_KEY").replace('\\n', '\n') if os.getenv(
            "REPORT_FB_PRIVATE_KEY") else None,
        "client_email": os.getenv("REPORT_FB_CLIENT_EMAIL"),
        "client_id": os.getenv("REPORT_FB_CLIENT_ID"),
        "auth_uri": os.getenv("REPORT_FB_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
        "token_uri": os.getenv("REPORT_FB_TOKEN_URI", "https://oauth2.googleapis.com/token"),
        "auth_provider_x509_cert_url": os.getenv("REPORT_FB_AUTH_PROVIDER_X509_CERT_URL",
                                                 "https://www.googleapis.com/oauth2/v1/certs"),
        "client_x509_cert_url": os.getenv("REPORT_FB_CLIENT_X509_CERT_URL"),
        "universe_domain": os.getenv("REPORT_FB_UNIVERSE_DOMAIN", "googleapis.com")
    }

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    else:
        # If an app exists, initialize with a name
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, name='report_app')

    return firestore.client()


db = initialise_firestore()

report_bp = Blueprint('report', __name__)

app = Flask(__name__)
CORS(app)


# Store a report
@report_bp.route('/', methods=['POST'])
def store_report():
    data = request.json

    nid = data.get('NID')
    report_month = data.get('reportMonth')  # YYYY-MM
    report_content = data.get('reportContent')
    hours_worked = data.get('hoursWorked')
    total_bookings = data.get('totalBookings')

    if not all([nid, report_month, report_content]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    # Generate report ID
    report_ref = db.collection('reports').document()

    report_data = {
        'RID': report_ref.id,
        'NID': nid,
        'reportMonth': report_month,
        'reportContent': report_content,
        'hoursWorked': hours_worked,
        'totalBookings': total_bookings
    }

    report_ref.set(report_data)

    return jsonify({
        'success': True,
        'reportId': report_ref.id
    })


# Retrieve a report based on month
@report_bp.route('/<nid>/<time_period>', methods=['GET'])
def fetch_report(nid, time_period):
    reports_ref = db.collection('reports')
    query = reports_ref.where('NID', '==', nid).where('reportMonth', '==', time_period).limit(1)

    results = query.stream()

    for doc in results:
        report_data = doc.to_dict()
        return jsonify(report_data)

    return jsonify({'error': 'Report not found'}), 404


# List all reports for a specific nurse
@report_bp.route('/<nid>', methods=['GET'])
def list_reports(nid):
    reports_ref = db.collection('reports')
    query = reports_ref.where('NID', '==', nid)

    results = []
    for doc in query.stream():
        report_data = doc.to_dict()
        # Return only essential data for listing
        results.append({
            'RID': report_data.get('RID'),
            'reportMonth': report_data.get('reportMonth'),
            'reportLink': report_data.get('reportLink'),
            'hoursWorked': report_data.get('hoursWorked'),
            'totalBookings': report_data.get('totalBookings')
        })

    return jsonify(results)


# Register the blueprint with the URL prefix
app.register_blueprint(report_bp, url_prefix='/api/reports')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5004)