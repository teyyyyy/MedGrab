from flask import Flask
from flask import Blueprint, request, jsonify
from flask_cors import CORS

# Initialise databse
import os
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


report_bp = Blueprint('report', __name__)

app = Flask(__name__)
CORS(app)

# Store a report
@report_bp.route('/', methods=['POST'])
def store_report():
    data = request.json
    
    nid = data.get('NID')
    report_month = data.get('reportMonth') #YYYY-MM
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
