import requests
import os
from flask import Flask, Blueprint, request, jsonify
from dotenv import load_dotenv
import json
import asyncio
# To
import sys
import os
from pathlib import Path

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import from the same directory
from amqp_setup import setup_amqp, send_notification_amqp, close_amqp
import datetime

# Load environment variables
load_dotenv()

# Service URLs - Update these based on deployment
NURSE_SERVICE_URL = 'http://host.docker.internal:5003/api/nurses'
BOOKING_SERVICE_URL = 'https://personal-o6lh6n5u.outsystemscloud.com/MedGrabBookingAtomic/rest/v1'
API_KEY = os.getenv('BOOKING_API_KEY')

cancel_booking_bp = Blueprint('cancel_booking', __name__)

# Helper functions
def get_booking_details(bid):
    """Get booking details from booking service"""
    try:
        print(f"Getting booking details: {BOOKING_SERVICE_URL}/GetBooking/{bid}")
        response = requests.get(f"{BOOKING_SERVICE_URL}/GetBooking/{bid}")
        
        if response.status_code == 200:
            booking_data = response.json()
            print(f"Booking data retrieved")
            return booking_data
        print(f"Booking service returned status code {response.status_code}")
        return None
    except requests.RequestException as e:
        print(f"Error in get_booking_details: {e}")
        return None
def get_patient_details(pid):
    """Get patient details from patient service"""
    try:
        response = requests.get(f"https://personal-eassd2ao.outsystemscloud.com/PatientAPI/rest/v2/GetPatient/{pid}")
        if response.status_code == 200:
            return response.json()
        print(f"Patient service returned status code {response.status_code}")
        return None
    except requests.RequestException as e:
        print(f"Error in get_patient_details: {e}")
        return None
def get_cancelled_bookings_for_patient_time(pid, start_time, end_time):
    """Get cancelled bookings for a patient in a specific time slot"""
    try:
        print(f"Getting all bookings for patient: {pid}")
        response = requests.get(f"{BOOKING_SERVICE_URL}/GetBookingsFromUser/{pid}")
        
        if response.status_code != 200:
            print(f"Failed to get patient bookings with status {response.status_code}")
            return []
        
        all_bookings = response.json().get('Bookings', [])
        
        # Filter for cancelled bookings in the same time slot
        cancelled_bookings = []
        for booking in all_bookings:
            fields = booking.get('fields', {})
            booking_status = fields.get('Status', {}).get('stringValue', '')
            booking_start = fields.get('StartTime', {}).get('timestampValue', '')
            booking_end = fields.get('EndTime', {}).get('timestampValue', '')
            
            # Check if booking is cancelled and matches the time slot
            if (booking_status == 'Cancelled' and 
                booking_start == start_time and 
                booking_end == end_time):
                cancelled_bookings.append(booking)
        
        print(f"Found {len(cancelled_bookings)} cancelled bookings matching criteria")
        return cancelled_bookings
    except requests.RequestException as e:
        print(f"Error getting cancelled bookings: {e}")
        return []

def create_booking_from_cancellation(pid, nid, start_time, end_time, notes, payment_amt, cancellation_count):
    """Create a new booking from a cancelled booking"""
    try:
        data = {
            "APIKey": API_KEY,
            "PID": pid,
            "NID": nid,
            "StartTime": start_time,
            "EndTime": end_time,
            "Notes": notes,
            "PaymentAmt": payment_amt,
            "CancellationCount": cancellation_count
        }
        
        print(f"Creating booking from cancellation: {BOOKING_SERVICE_URL}/CreateBookingFromCancellation")
        response = requests.post(
            f"{BOOKING_SERVICE_URL}/CreateBookingFromCancellation", 
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"New booking created successfully: {result}")
            return result, True
        
        print(f"Create booking failed with status code {response.status_code}: {response.text}")
        return {"error": f"Create booking failed: {response.text}"}, False
    except requests.RequestException as e:
        print(f"Error in create_booking_from_cancellation: {e}")
        return {"error": str(e)}, False
def cancel_booking_with_reason(bid, reason):
    """Cancel a booking with reason"""
    
    try:
        # Put API key in the request body along with the reason
        data = {
            "APIKey": API_KEY,  # Note the capitalization
            "Reason": reason    # Note the capitalization
        }

        # # MOCK FOR TESTING - Skip API call for specific test booking ID
        # if bid == "Z4sn7tfV4SFH51tM4Kne":
        #     print(f"MOCK: Cancelling test booking {bid}")
        #     # Update Firebase directly if needed
        #     # ...
        #     return {"StatusCode": 200, "Message": "Booking Cancelled (Mock)"}, True
            
        # # Regular API call logic continues below
        # data = {
        #     "APIKey": API_KEY,
        #     "Reason": reason
        # }
        
        print(f"Calling Booking Service to cancel: {BOOKING_SERVICE_URL}/CancelWithReason/{bid}")
        response = requests.post(
            f"{BOOKING_SERVICE_URL}/CancelWithReason/{bid}", 
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Booking cancelled successfully: {result}")
            return result, True
        
        print(f"Cancel booking failed with status code {response.status_code}: {response.text}")
        return {"error": f"Cancel booking failed: {response.text}"}, False
    except requests.RequestException as e:
        print(f"Error in cancel_booking_with_reason: {e}")
        return {"error": str(e)}, False

def get_nurse_details(nid):
    """Get nurse details from nurse service"""
    try:
        print(f"Getting nurse details: {NURSE_SERVICE_URL}/{nid}")
        response = requests.get(f"{NURSE_SERVICE_URL}/{nid}")
        
        if response.status_code == 200:
            nurse_data = response.json()
            print(f"Nurse data retrieved")
            return nurse_data
        print(f"Nurse service returned status code {response.status_code}")
        return None
    except requests.RequestException as e:
        print(f"Error in get_nurse_details: {e}")
        return None

def assign_new_nurse():
    """Assign a new nurse based on availability"""
    try:
        # Call the nurse service to assign a new nurse
        print(f"Assigning new nurse: {NURSE_SERVICE_URL}/assign")
        response = requests.post(f"{NURSE_SERVICE_URL}/assign", json={})
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"New nurse assigned")
                return result.get('nurse'), True
        
        print(f"Assign new nurse failed")
        return {"error": "Failed to assign a new nurse"}, False
    except requests.RequestException as e:
        print(f"Error in assign_new_nurse: {e}")
        return {"error": str(e)}, False

def update_booking_nurse(bid, nid):
    """Update the nurse assigned to a booking"""
    try:
        data = {
            "APIKey": API_KEY
        }
        print(f"Updating booking nurse: {BOOKING_SERVICE_URL}/UpdateBookingNurse/{bid}/{nid}")
        response = requests.patch(
            f"{BOOKING_SERVICE_URL}/UpdateBookingNurse/{bid}/{nid}", 
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Booking nurse updated")
            return result, True
        print(f"Update booking nurse failed with status {response.status_code}")
        return {"error": f"Update booking nurse failed: {response.text}"}, False
    except requests.RequestException as e:
        print(f"Error in update_booking_nurse: {e}")
        return {"error": str(e)}, False

def update_nurse_credit_score(nid, credit_change, reason):
    """Update nurse credit score"""
    try:
        data = {
            "creditChange": credit_change,
            "reason": reason
        }
        print(f"Updating nurse credit score: {NURSE_SERVICE_URL}/{nid}/credit")
        response = requests.put(f"{NURSE_SERVICE_URL}/{nid}/credit", json=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Credit score updated")
            return result, True
        print(f"Update credit score failed with status {response.status_code}")
        return {"error": f"Update credit score failed: {response.text}"}, False
    except requests.RequestException as e:
        print(f"Error in update_nurse_credit_score: {e}")
        return {"error": str(e)}, False
def increase_nurse_credit_score(nid, booking_id):
    """Increase nurse credit score when booking is accepted"""
    credit_data = {
        "creditChange": 2,  # Add 2 points
        "reason": f"Booking acceptance: {booking_id}"
    }
    try:
        response = requests.put(f"{NURSE_SERVICE_URL}/{nid}/credit", json=credit_data)
        if response.status_code == 200:
            return response.json(), True
        return {"error": "Failed to update credit score"}, False
    except requests.RequestException as e:
        return {"error": str(e)}, False


def check_nurse_status(nid):
    """Check and update nurse warning/suspension status"""
    try:
        print(f"Checking nurse status: {NURSE_SERVICE_URL}/{nid}/check-status")
        response = requests.post(f"{NURSE_SERVICE_URL}/{nid}/check-status")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException as e:
        print(f"Error checking nurse status: {e}")
        return None

# Main function to handle nurse cancellation and reassignment
async def process_nurse_cancellation(bid, nurse_id, reason, reassignment_count=0, max_reassignments=3):
    """Process a nurse cancellation and handle reassignment logic"""
    print(f"Processing nurse cancellation for Booking ID: {bid}, Nurse ID: {nurse_id}")
    print(f"Current reassignment count: {reassignment_count}, Max allowed: {max_reassignments}")
    
    # Get nurse details
    nurse_data = get_nurse_details(nurse_id)
    if not nurse_data:
        return {
            "success": False, 
            "message": "Nurse not found"
        }
    
    # Get booking details to retrieve patient info and time slot
    booking_details = get_booking_details(bid)
    if not booking_details:
        return {
            "success": False,
            "message": "Booking not found"
        }
    
    # Extract booking information
    fields = booking_details.get('fields', {})
    patient_id = fields.get('PatientID', {}).get('stringValue')
    start_time = fields.get('StartTime', {}).get('timestampValue')
    end_time = fields.get('EndTime', {}).get('timestampValue')
    notes = fields.get('Notes', {}).get('stringValue', '')
    payment_amt = fields.get('PaymentAmt', {}).get('doubleValue', 0)
    
    # Determine credit score deduction
    credit_deduction = -7
    
    # Cancel the booking with reason
    cancel_result, cancel_success = cancel_booking_with_reason(bid, reason)
    if not cancel_success:
        return {
            "success": False,
            "message": "Failed to cancel booking"
        }
    
    # Update nurse credit score
    credit_result, credit_success = update_nurse_credit_score(
        nurse_id, 
        credit_deduction, 
        f"Booking cancellation: {reason}"
    )
    
    # Check if nurse needs to be warned or suspended based on new credit score
    status_result = check_nurse_status(nurse_id)
    
    # Send notification to nurse about cancellation and credit score impact
    await send_notification_to_nurse(nurse_data, bid, credit_deduction)
    
    # Check if we've exceeded max reassignments
    if reassignment_count >= max_reassignments:
        # If so, permanently cancel the booking and notify patient
        await send_notification_to_patient(bid, nurse_data.get('name'), "max_reassignments")
        
        return {
            "success": True,
            "message": f"Booking permanently cancelled after {max_reassignments} reassignment attempts",
            "creditScoreDeduction": credit_deduction,
            "nurseStatus": status_result,
            "requireNewBooking": True
        }
    
    # Get all cancelled bookings for this patient/time slot
    cancelled_bookings = get_cancelled_bookings_for_patient_time(patient_id, start_time, end_time)
    
    # Extract nurse IDs who previously cancelled
    excluded_nurse_ids = []
    for booking in cancelled_bookings:
        nurse_id_field = booking.get('fields', {}).get('NID', {}).get('stringValue')
        if nurse_id_field and nurse_id_field not in excluded_nurse_ids:
            excluded_nurse_ids.append(nurse_id_field)
    
    # Add the current cancelling nurse to the exclusion list
    if nurse_id not in excluded_nurse_ids:
        excluded_nurse_ids.append(nurse_id)
    
    # Get all available nurses
    try:
        nurse_response = requests.get(f"{NURSE_SERVICE_URL}/")
        if nurse_response.status_code != 200:
            return {
                "success": False,
                "message": "Failed to get available nurses",
                "creditScoreDeduction": credit_deduction,
                "nurseStatus": status_result
            }
            
        all_nurses = nurse_response.json()
        
        # Filter out nurses who previously cancelled and suspended nurses
        eligible_nurses = [
            nurse for nurse in all_nurses 
            if nurse.get('NID') not in excluded_nurse_ids 
            and not nurse.get('isSuspended', False)
        ]
        
        if not eligible_nurses:
            # If no eligible nurses available, permanently cancel
            await send_notification_to_patient(bid, nurse_data.get('name'), "max_reassignments")
            
            return {
                "success": True,
                "message": "Booking permanently cancelled as no eligible nurses are available",
                "creditScoreDeduction": credit_deduction,
                "nurseStatus": status_result,
                "requireNewBooking": True
            }
        
        # Randomly select a nurse
        import random
        new_nurse = random.choice(eligible_nurses)
        new_nurse_id = new_nurse.get('NID')
        
        # Create a new booking from the cancelled one with incremented cancellation count
        new_booking_result, create_success = create_booking_from_cancellation(
            patient_id, 
            new_nurse_id, 
            start_time, 
            end_time, 
            notes, 
            payment_amt, 
            reassignment_count + 1
        )
        
        if not create_success:
            return {
                "success": False,
                "message": "Failed to create new booking after cancellation",
                "creditScoreDeduction": credit_deduction,
                "nurseStatus": status_result
            }
        
        # Extract new booking ID from result
        new_booking_id = new_booking_result.get('BID')
        
        # Notify new nurse about assignment
        await send_notification_to_new_nurse(new_nurse, new_booking_id)
        
        # Notify patient about reassignment
        await send_notification_to_patient(bid, nurse_data.get('name'), "reassigned", new_nurse.get('name'))
        
        return {
            "success": True,
            "message": "Booking successfully reassigned to new nurse",
            "previousNurse": {
                "id": nurse_id,
                "name": nurse_data.get('name'),
                "creditScoreDeduction": credit_deduction,
                "newCreditScore": credit_result.get('creditScore') if credit_success else None,
                "status": status_result
            },
            "newNurse": {
                "id": new_nurse_id,
                "name": new_nurse.get('name')
            },
            "oldBookingId": bid,
            "newBookingId": new_booking_id,
            "cancellationCount": reassignment_count + 1
        }
        
    except Exception as e:
        print(f"Error during nurse reassignment: {e}")
        return {
            "success": False,
            "message": f"Server error during reassignment: {str(e)}",
            "creditScoreDeduction": credit_deduction,
            "nurseStatus": status_result
        }
# Notification functions
async def send_notification_to_nurse(nurse_data, booking_id, credit_deduction):
    """Send notification to nurse about cancellation and credit score impact"""
    nurse_email = nurse_data.get('email')
    if not nurse_email:
        print("No email found for nurse")
        return False
    
    subject = "MedGrab Booking Cancellation"
    message = f"""
    <html>
    <body>
        <h2>Booking Cancellation Confirmation</h2>
        <p>Dear {nurse_data.get('name')},</p>
        <p>Your cancellation of booking #{booking_id} has been processed.</p>
        <p><strong>Important:</strong> This cancellation has resulted in a credit score change of {credit_deduction} points.</p>
        <p>Your current credit score is now {nurse_data.get('creditScore', 100) + credit_deduction}.</p>
        <ul>
            <li>If your credit score falls below 30, you will receive a warning.</li>
            <li>If your credit score falls below 20 after receiving a warning, your account will be suspended for 30 days.</li>
        </ul>
        <p>Thank you for your understanding.</p>
        <p>Best regards,<br>MedGrab Team</p>
    </body>
    </html>
    """
    
    result = await send_notification_amqp(nurse_email, subject, message)
    return result.get('success', False)

async def send_notification_to_new_nurse(nurse_data, booking_id):
    """Send notification to new nurse about the assignment"""
    nurse_email = nurse_data.get('email')
    if not nurse_email:
        print("No email found for new nurse")
        return False
    
    subject = "MedGrab New Booking Assignment"
    message = f"""
    <html>
    <body>
        <h2>New Booking Assignment</h2>
        <p>Dear {nurse_data.get('name')},</p>
        <p>You have been assigned to booking #{booking_id}.</p>
        <p>Please check your MedGrab app for booking details and to accept or decline this assignment.</p>
        <p>Best regards,<br>MedGrab Team</p>
    </body>
    </html>
    """
    
    result = await send_notification_amqp(nurse_email, subject, message)
    return result.get('success', False)

async def send_notification_to_patient(booking_id, nurse_name, notification_type, new_nurse_name=None):
    """Send notification to patient about booking changes"""
    # Get booking details to find patient ID
    booking_details = get_booking_details(booking_id)
    if not booking_details:
        print(f"Failed to get booking details for ID: {booking_id}")
        return False

    # Extract patient ID from booking data - adjust field names based on actual API response structure
    patient_id = booking_details.get('fields', {}).get('PatientID', {}).get('stringValue')
    if not patient_id:
        print(f"No patient ID found in booking {booking_id}")
        return False
    
    # Get patient details to find email
    patient_details = get_patient_details(patient_id)
    if not patient_details:
        print(f"Failed to get patient details for ID: {patient_id}")
        return False
    
    # Extract email from patient data - adjust field name based on actual API response
    patient_email = patient_details.get('Email')  # Might be 'email' or another field
    if not patient_email:
        print(f"No email found for patient {patient_id}")
        return False
    
    subject = "MedGrab Booking Update"
    
    if notification_type == "max_reassignments":
        message = f"""
        <html>
        <body>
            <h2>Booking Update Required</h2>
            <p>Dear Patient,</p>
            <p>Unfortunately, we've had to cancel your booking #{booking_id} after multiple nurse reassignment attempts.</p>
            <p>Please create a new booking at your convenience. We apologize for the inconvenience.</p>
            <p>Best regards,<br>MedGrab Team</p>
        </body>
        </html>
        """
    elif notification_type == "reassigned":
        message = f"""
        <html>
        <body>
            <h2>Nurse Reassignment Notification</h2>
            <p>Dear Patient,</p>
            <p>Your booking #{booking_id} has been reassigned to a new nurse due to cancellation by {nurse_name}.</p>
            <p>Your new nurse will be {new_nurse_name}. All other booking details remain the same.</p>
            <p>We apologize for any inconvenience.</p>
            <p>Best regards,<br>MedGrab Team</p>
        </body>
        </html>
        """
    else:
        message = f"""
        <html>
        <body>
            <h2>Booking Update</h2>
            <p>Dear Patient,</p>
            <p>There has been an update to your booking #{booking_id}.</p>
            <p>Please check your MedGrab app for details.</p>
            <p>Best regards,<br>MedGrab Team</p>
        </body>
        </html>
        """
    
    result = await send_notification_amqp(patient_email, subject, message)
    return result.get('success', False)

# Endpoint for nurse to cancel a booking
@cancel_booking_bp.route('/nurse-cancel', methods=['POST'])
async def nurse_cancel_endpoint():
    """API endpoint for nurse to cancel a booking"""
    data = request.json
    booking_id = data.get('bookingId')
    nurse_id = data.get('nurseId')
    reason = data.get('reason')
    reassignment_count = data.get('reassignmentCount', 0)
    
    # Validate required fields
    if not all([booking_id, nurse_id, reason]):
        return jsonify({
            "success": False,
            "message": "Missing required fields: bookingId, nurseId, and reason are required"
        }), 400
    
    # Initialize AMQP
    await setup_amqp()
    
    try:
        # Process the cancellation
        result = await process_nurse_cancellation(booking_id, nurse_id, reason, reassignment_count)
        return jsonify(result)
    except Exception as e:
        print(f"Error processing nurse cancellation: {e}")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500
    finally:
        # Close AMQP connection
        await close_amqp()

# Initialize the blueprint
def init_app(app):
    app.register_blueprint(cancel_booking_bp, url_prefix='/api/cancel-booking')

# Run as standalone for testing
if __name__ == '__main__':
    app = Flask(__name__)
    init_app(app)
    app.run(debug=True, host='0.0.0.0', port=5011)