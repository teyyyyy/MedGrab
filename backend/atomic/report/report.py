from flask import Flask
from flask import Blueprint, request, jsonify
from flask_cors import CORS
from atomic.report.firestore import db

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
    report_link = data.get('reportLink')
    
    if not all([nid, report_month, report_content, report_link]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    # Generate report ID
    report_ref = db.collection('reports').document()
    
    report_data = {
        'RID': report_ref.id,
        'NID': nid,
        'reportMonth': report_month,
        'reportContent': report_content, #Is this needed???
        'reportLink': report_link,
    }
    
    report_ref.set(report_data)
    
    return jsonify({
        'success': True,
        'reportId': report_ref.id,
        'reportLink': report_link
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
            'reportLink': report_data.get('reportLink')
        })
    
    return jsonify(results)

# Register the blueprint with the URL prefix
app.register_blueprint(report_bp, url_prefix='/api/reports')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5004) 
