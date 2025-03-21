from atomic.firestore import db
from flask import Blueprint, request, jsonify
from google.cloud import firestore
import datetime
import random

nurse_bp = Blueprint('nurse', __name__)

# Create a new nurse
@nurse_bp.route('/', methods=['POST'])
def create_nurse():
    data = request.json
    
    name = data.get('name')
    phone_num = data.get('phoneNum')
    available_timing = data.get('availableTiming', [])
    credit_score = data.get('creditScore', 100)  # Default credit score is 100
    
    if not all([name, phone_num]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    # Generate nurse ID
    nurse_ref = db.collection('nurses').document()
    
    nurse_data = {
        'NID': nurse_ref.id,
        'name': name,
        'phoneNum': phone_num,
        'availableTiming': available_timing,
        'creditScore': credit_score,
        'createdAt': firestore.SERVER_TIMESTAMP
    }
    
    # Check if certification data is provided
    cert = data.get('cert')
    if cert:
        issued_date = cert.get('issuedDate')
        expiry_date = cert.get('expiryDate')
        status = cert.get('status', 'Active')
        
        if issued_date and expiry_date:
            nurse_data['cert'] = {
                'issuedDate': issued_date,
                'expiryDate': expiry_date,
                'status': status
            }
    
    nurse_ref.set(nurse_data)
    
    return jsonify({
        'success': True,
        'NID': nurse_ref.id,
        'message': 'Nurse created successfully'
    })

# Get all nurses
@nurse_bp.route('/', methods=['GET'])
def get_all_nurses():
    nurses_ref = db.collection('nurses')
    
    nurses = []
    for doc in nurses_ref.stream():
        nurse_data = doc.to_dict()
        nurses.append(nurse_data)
    
    return jsonify(nurses)

# Retrieve a nurse by ID
@nurse_bp.route('/<nid>', methods=['GET'])
def get_nurse(nid):
    nurse_ref = db.collection('nurses').document(nid)
    nurse = nurse_ref.get()
    
    if not nurse.exists:
        return jsonify({'success': False, 'error': 'Nurse not found'}), 404
    
    nurse_data = nurse.to_dict()
    return jsonify(nurse_data)

# Update nurse details
@nurse_bp.route('/<nid>', methods=['PUT'])
def update_nurse(nid):
    data = request.json
    
    nurse_ref = db.collection('nurses').document(nid)
    nurse = nurse_ref.get()
    
    if not nurse.exists:
        return jsonify({'success': False, 'error': 'Nurse not found'}), 404
    
    # Fields that can be updated
    updateable_fields = ['name', 'phoneNum', 'availableTiming', 'creditScore']
    update_data = {}
    
    for field in updateable_fields:
        if field in data:
            update_data[field] = data[field]
    
    # Handle certificate updates
    if 'cert' in data:
        cert = data['cert']
        if all(key in cert for key in ['issuedDate', 'expiryDate', 'status']):
            update_data['cert'] = cert
    
    # Add update timestamp
    update_data['updatedAt'] = firestore.SERVER_TIMESTAMP
    
    nurse_ref.update(update_data)
    
    return jsonify({
        'success': True,
        'message': 'Nurse updated successfully'
    })

# Update nurse credit score (for Scenario 2)
@nurse_bp.route('/<nid>/credit', methods=['PUT'])
def update_credit_score(nid):
    data = request.json
    
    credit_change = data.get('creditChange')
    reason = data.get('reason')
    
    if credit_change is None:
        return jsonify({'success': False, 'error': 'Credit change amount is required'}), 400
    
    nurse_ref = db.collection('nurses').document(nid)
    nurse = nurse_ref.get()
    
    if not nurse.exists:
        return jsonify({'success': False, 'error': 'Nurse not found'}), 404
    
    nurse_data = nurse.to_dict()
    current_score = nurse_data.get('creditScore', 100)
    new_score = max(0, min(100, current_score + credit_change))  # Keep score between 0-100
    
    # Update credit score
    nurse_ref.update({
        'creditScore': new_score,
        'updatedAt': firestore.SERVER_TIMESTAMP
    })
    
    # Log credit score change
    credit_log_ref = db.collection('creditScoreLogs').document()
    credit_log_ref.set({
        'NID': nid,
        'previousScore': current_score,
        'newScore': new_score,
        'change': credit_change,
        'reason': reason,
        'timestamp': firestore.SERVER_TIMESTAMP
    })
    
    # Check if suspension is needed for low credit score (for Scenario 3)
    suspension_threshold = 30  # First warning
    suspension_critical = 20   # Suspension threshold
    
    if new_score <= suspension_critical:
        # Create a 2-week suspension
        end_date = datetime.datetime.now() + datetime.timedelta(weeks=2)
        end_date_str = end_date.strftime('%Y-%m-%dT%H:%M+08:00')
        
        suspension_ref = db.collection('suspensions').document()
        suspension_ref.set({
            'NID': nid,
            'endDate': end_date_str,
            'reason': 'Credit score dropped below critical threshold',
            'createdAt': firestore.SERVER_TIMESTAMP
        })
        
        return jsonify({
            'success': True,
            'message': 'Credit score updated and nurse suspended',
            'creditScore': new_score,
            'suspended': True,
            'suspensionEndDate': end_date_str
        })
    elif new_score <= suspension_threshold:
        # Just send a warning
        return jsonify({
            'success': True,
            'message': 'Credit score updated. Warning issued to nurse.',
            'creditScore': new_score,
            'warned': True
        })
    
    return jsonify({
        'success': True,
        'message': 'Credit score updated successfully',
        'creditScore': new_score
    })

# Get nurse availability timing
@nurse_bp.route('/<nid>/availability', methods=['GET'])
def get_availability(nid):
    nurse_ref = db.collection('nurses').document(nid)
    nurse = nurse_ref.get()
    
    if not nurse.exists:
        return jsonify({'success': False, 'error': 'Nurse not found'}), 404
    
    nurse_data = nurse.to_dict()
    availability = nurse_data.get('availableTiming', [])
    
    return jsonify({
        'NID': nid,
        'availableTiming': availability
    })

# Update nurse availability
@nurse_bp.route('/<nid>/availability', methods=['PUT'])
def update_availability(nid):
    data = request.json
    
    availability = data.get('availableTiming')
    
    if availability is None:
        return jsonify({'success': False, 'error': 'Available timing is required'}), 400
    
    nurse_ref = db.collection('nurses').document(nid)
    nurse = nurse_ref.get()
    
    if not nurse.exists:
        return jsonify({'success': False, 'error': 'Nurse not found'}), 404
    
    nurse_ref.update({
        'availableTiming': availability,
        'updatedAt': firestore.SERVER_TIMESTAMP
    })
    
    return jsonify({
        'success': True,
        'message': 'Availability timing updated successfully'
    })

# Filter and randomly assign a nurse (for Scenario 1)
@nurse_bp.route('/assign', methods=['POST'])
def assign_nurse():
    data = request.json
    
    # Get filter criteria
    gender = data.get('gender')
    location = data.get('location')
    
    # Start with a base query for nurses
    nurses_ref = db.collection('nurses')
    query = nurses_ref
    
    # Apply filters if provided
    if gender:
        query = query.where('gender', '==', gender)
    if location:
        query = query.where('location', '==', location)
    
    # Get the current date and time to check for suspended nurses
    current_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M+08:00')
    
    # Execute the query
    available_nurses = []
    for doc in query.stream():
        nurse_data = doc.to_dict()
        nid = nurse_data.get('NID')
        
        # Check if nurse is suspended
        is_suspended = False
        suspensions_ref = db.collection('suspensions')
        suspension_query = suspensions_ref.where('NID', '==', nid).where('endDate', '>', current_time)
        
        for _ in suspension_query.stream():
            is_suspended = True
            break
        
        # Only include non-suspended nurses
        if not is_suspended:
            available_nurses.append(nurse_data)
    
    # Check if any nurses are available
    if not available_nurses:
        return jsonify({
            'success': False,
            'error': 'No nurses available with the specified criteria'
        }), 404
    
    # Randomly select a nurse
    selected_nurse = random.choice(available_nurses)
    
    return jsonify({
        'success': True,
        'message': 'Nurse assigned successfully',
        'nurse': selected_nurse
    })

# Get filtered nurses
@nurse_bp.route('/filter', methods=['GET'])
def filter_nurses():
    # Get query parameters for filtering
    gender = request.args.get('gender')
    location = request.args.get('location')
    
    # Start with a base query for nurses
    nurses_ref = db.collection('nurses')
    query = nurses_ref
    
    # Apply filters if provided
    if gender:
        query = query.where('gender', '==', gender)
    if location:
        query = query.where('location', '==', location)
    
    # Get the current date and time to check for suspended nurses
    current_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M+08:00')
    
    # Execute the query
    nurses = []
    for doc in query.stream():
        nurse_data = doc.to_dict()
        nid = nurse_data.get('NID')
        
        # Check if nurse is suspended
        is_suspended = False
        suspensions_ref = db.collection('suspensions')
        suspension_query = suspensions_ref.where('NID', '==', nid).where('endDate', '>', current_time)
        
        for _ in suspension_query.stream():
            is_suspended = True
            break
        
        # Only include non-suspended nurses
        if not is_suspended:
            nurses.append(nurse_data)
    
    return jsonify(nurses)

# Check if a nurse is suspended
@nurse_bp.route('/<nid>/suspension', methods=['GET'])
def check_suspension(nid):
    # Get the current date and time
    current_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M+08:00')
    
    # Check for active suspensions
    suspensions_ref = db.collection('suspensions')
    query = suspensions_ref.where('NID', '==', nid).where('endDate', '>', current_time)
    
    suspension = None
    for doc in query.stream():
        suspension = doc.to_dict()
        break
    
    if suspension:
        return jsonify({
            'suspended': True,
            'endDate': suspension.get('endDate'),
            'reason': suspension.get('reason')
        })
    
    return jsonify({
        'suspended': False
    })

# Get nurse cancel count for a specific month (for Report Generation - Scenario 3)
@nurse_bp.route('/<nid>/cancellations/<year_month>', methods=['GET'])
def get_cancellation_stats(nid, year_month):
    # Parse year and month
    try:
        year, month = year_month.split('-')
        year = int(year)
        month = int(month)
    except ValueError:
        return jsonify({'error': 'Invalid format. Use YYYY-MM'}), 400
    
    # Calculate start and end dates for the month
    start_date = datetime.datetime(year, month, 1)
    if month == 12:
        end_date = datetime.datetime(year + 1, 1, 1)
    else:
        end_date = datetime.datetime(year, month + 1, 1)
    
    # Convert to timestamp strings for Firestore
    start_date_str = start_date.strftime('%Y-%m-%dT%H:%M+08:00')
    end_date_str = end_date.strftime('%Y-%m-%dT%H:%M+08:00')
    
    # Query cancellation logs
    logs_ref = db.collection('creditScoreLogs')
    query = logs_ref.where('NID', '==', nid) \
                    .where('reason', '==', 'Booking cancellation') \
                    .where('timestamp', '>=', start_date_str) \
                    .where('timestamp', '<', end_date_str)
    
    # Count cancellations
    cancellation_count = 0
    for _ in query.stream():
        cancellation_count += 1
    
    return jsonify({
        'NID': nid,
        'yearMonth': year_month,
        'cancellationCount': cancellation_count
    })

# Get nurse work hours for a specific month (for Report Generation - Scenario 3)
@nurse_bp.route('/<nid>/workhours/<year_month>', methods=['GET'])
def get_work_hours(nid, year_month):
    return jsonify({
        'NID': nid,
        'yearMonth': year_month,
        'workHours': 0  # This will be implemented in a composite service
    })