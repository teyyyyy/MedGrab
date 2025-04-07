import requests
import os
from flask import Flask, Blueprint, request, jsonify
from dotenv import load_dotenv
import json
import asyncio
import sys
from pathlib import Path
from flask_cors import CORS

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import from the same directory
from amqp_setup import setup_amqp, send_notification_amqp, close_amqp
import datetime

# Load environment variables
load_dotenv()

# Service URLs - Update these based on deployment
NURSE_SERVICE_URL=os.environ.get('NURSE_ATOMIC_URL', 'http://host.docker.internal:5003/')
BOOKING_SERVICE_URL=os.environ.get('BOOKING_ATOMIC_MAIN_URL', 'https://personal-o6lh6n5u.outsystemscloud.com/MedGrabBookingAtomic/rest/v1/')
API_KEY = os.getenv('BOOKING_API_KEY')

cancel_booking_bp = Blueprint('cancel_booking', __name__)


# Helper functions
def get_booking_details(bid):
    """Get booking details from booking service"""
    try:
        print(f"Getting booking details: {BOOKING_SERVICE_URL}GetBooking/{bid}")
        response = requests.get(f"{BOOKING_SERVICE_URL}GetBooking/{bid}")

        if response.status_code == 200:
            booking_data = response.json()
            print(f"Booking data retrieved")
            return booking_data
        print(f"Booking service returned status code {response.status_code}")
        return None
    except requests.RequestException as e:
        print(f"Error in get_booking_details: {e}")
        return None


def get_all_bookings():
    """Get all bookings"""
    try:
        print(f"Getting all bookings: {BOOKING_SERVICE_URL}GetAllBookings")
        response = requests.get(f"{BOOKING_SERVICE_URL}GetAllBookings")

        if response.status_code == 200:
            bookings_data = response.json()
            print(f"All bookings retrieved")
            return bookings_data.get('Bookings', [])
        print(f"Booking service returned status code {response.status_code}")
        return []
    except requests.RequestException as e:
        print(f"Error in get_all_bookings: {e}")
        return []


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


def cancel_booking_with_reason(bid, reason):
    """Cancel a booking with reason"""

    try:
        # Put API key in the request body along with the reason
        data = {
            "APIKey": API_KEY,
            "Reason": reason
        }

        print(f"Calling Booking Service to cancel: {BOOKING_SERVICE_URL}CancelWithReason/{bid}")
        response = requests.post(
            f"{BOOKING_SERVICE_URL}CancelWithReason/{bid}",
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
        print(f"Getting nurse details: {NURSE_SERVICE_URL}{nid}")
        response = requests.get(f"{NURSE_SERVICE_URL}{nid}")

        if response.status_code == 200:
            nurse_data = response.json()
            print(f"Nurse data retrieved")
            return nurse_data
        print(f"Nurse service returned status code {response.status_code}")
        return None
    except requests.RequestException as e:
        print(f"Error in get_nurse_details: {e}")
        return None


def get_all_nurses():
    """Get all available nurses"""
    try:
        print(f"Getting all nurses: {NURSE_SERVICE_URL}")
        response = requests.get(f"{NURSE_SERVICE_URL}")

        if response.status_code == 200:
            nurses_data = response.json()
            print(f"All nurses retrieved")
            return nurses_data
        print(f"Nurse service returned status code {response.status_code}")
        return []
    except requests.RequestException as e:
        print(f"Error in get_all_nurses: {e}")
        return []


def create_booking_from_cancellation(PID, NID, StartTime, EndTime, Notes, PaymentAmt, CancellationCount):
    """Create a new booking using the cancellation endpoint"""
    try:
        data = {
            "PID": PID,
            "NID": NID,
            "StartTime": StartTime,
            "EndTime": EndTime,
            "APIKey": API_KEY,
            "Notes": Notes,
            "PaymentAmt": PaymentAmt,
            "CancellationCount": CancellationCount
        }

        print(f"Creating booking from cancellation: {BOOKING_SERVICE_URL}CreateBookingFromCancellation")
        response = requests.post(
            f"{BOOKING_SERVICE_URL}CreateBookingFromCancellation",
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


def update_nurse_credit_score(nid, credit_change, reason):
    """Update nurse credit score"""
    try:
        data = {
            "creditChange": credit_change,
            "reason": reason
        }
        print(f"Updating nurse credit score: {NURSE_SERVICE_URL}{nid}/credit")
        response = requests.put(f"{NURSE_SERVICE_URL}{nid}/credit", json=data)

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
        response = requests.put(f"{NURSE_SERVICE_URL}{nid}/credit", json=credit_data)
        if response.status_code == 200:
            return response.json(), True
        return {"error": "Failed to update credit score"}, False
    except requests.RequestException as e:
        return {"error": str(e)}, False


def check_nurse_status(nid):
    """Check and update nurse warning/suspension status"""
    try:
        print(f"Checking nurse status: {NURSE_SERVICE_URL}{nid}/check-status")
        response = requests.post(f"{NURSE_SERVICE_URL}{nid}/check-status")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException as e:
        print(f"Error checking nurse status: {e}")
        return None


def find_eligible_nurse(pid, start_time, end_time, excluded_nurse_id):
    """Find a nurse that hasn't already cancelled this booking"""
    # Get all nurses
    all_nurses = get_all_nurses()
    if not all_nurses:
        return None, "No nurses available"

    # Get all bookings
    all_bookings = get_all_bookings()

    # Filter out the excluded nurse
    available_nurses = [nurse for nurse in all_nurses if nurse.get('NID') != excluded_nurse_id]

    if not available_nurses:
        return None, "No other nurses available"

    # Find nurses who haven't cancelled this patient's booking at this time
    ineligible_nurse_ids = set()

    for booking in all_bookings:
        fields = booking.get('fields', {})
        booking_pid = fields.get('PID', {}).get('stringValue')
        booking_start = fields.get('StartTime', {}).get('timestampValue')
        booking_end = fields.get('EndTime', {}).get('timestampValue')
        booking_status = fields.get('Status', {}).get('stringValue')
        booking_nid = fields.get('NID', {}).get('stringValue')

        # If this is a cancelled booking for the same patient, time window
        if (booking_pid == pid and booking_start == start_time and
                booking_end == end_time and booking_status == "Cancelled"):
            ineligible_nurse_ids.add(booking_nid)

    # Filter out ineligible nurses
    eligible_nurses = [nurse for nurse in available_nurses if nurse.get('NID') not in ineligible_nurse_ids]

    if not eligible_nurses:
        # If no eligible nurses, just return any available nurse
        return available_nurses[0], "No nurse found who hasn't cancelled this booking before"

    # Return a random eligible nurse
    import random
    return random.choice(eligible_nurses), None


# Main function to handle nurse cancellation and reassignment
async def process_nurse_cancellation(bid, nurse_id, reason, reassignment_count=0, max_reassignments=3):
    """
    Process a nurse cancellation and handle reassignment logic

    Parameters:
    - bid: Booking ID
    - nurse_id: ID of the nurse cancelling the booking
    - reason: Cancellation reason
    - reassignment_count: Current count of reassignments
    - max_reassignments: Maximum number of allowed reassignments
    """
    print(f"Processing nurse cancellation for Booking ID: {bid}, Nurse ID: {nurse_id}")
    print(f"Current reassignment count: {reassignment_count}, Max allowed: {max_reassignments}")

    # Get nurse details
    nurse_data = get_nurse_details(nurse_id)
    if not nurse_data:
        return {
            "success": False,
            "message": "Nurse not found"
        }

    # Get booking details
    booking_details = get_booking_details(bid)
    if not booking_details:
        return {
            "success": False,
            "message": "Booking not found"
        }

    # Extract booking data
    booking_data = booking_details.get('Booking', {})
    fields = booking_data.get('fields', {})

    patient_id = fields.get('PID', {}).get('stringValue')
    start_time = fields.get('StartTime', {}).get('timestampValue')
    end_time = fields.get('EndTime', {}).get('timestampValue')
    notes = fields.get('Notes', {}).get('stringValue', '')
    payment_amt = fields.get('PaymentAmt', {}).get('doubleValue', 0)

    # Increment the cancellation count
    cancellation_count = int(fields.get('CancellationCount', {}).get('integerValue', 0)) + 1

    # Determine credit score deduction based on cancellation count
    credit_deduction = -7  # Base deduction

    # Get patient details
    patient_data = get_patient_details(patient_id)
    if not patient_data:
        return {
            "success": False,
            "message": "Patient not found"
        }

    patient = patient_data.get('Patient', {})
    patient_name = patient.get('PatientName', 'Patient')
    patient_email = patient.get('Email', '')
    location = patient.get('Location', 'Unknown')

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
    if cancellation_count >= max_reassignments:
        # If so, permanently cancel the booking and notify patient

        # Notify patient
        await send_notification_to_patient(
            bid,
            patient_id,
            patient_name,
            patient_email,
            nurse_data.get('name'),
            "max_reassignments"
        )

        return {
            "success": True,
            "message": f"Booking permanently cancelled after {max_reassignments} reassignment attempts",
            "creditScoreDeduction": credit_deduction,
            "nurseStatus": status_result,
            "requireNewBooking": True
        }

    # Otherwise, try to find and assign a new nurse
    new_nurse, find_error = find_eligible_nurse(patient_id, start_time, end_time, nurse_id)

    if not new_nurse:
        return {
            "success": False,
            "message": find_error or "Failed to find an eligible nurse",
            "creditScoreDeduction": credit_deduction,
            "nurseStatus": status_result
        }

    # Create a new booking with the new nurse
    new_booking_data = {
        "PID": patient_id,
        "NID": new_nurse.get('NID'),
        "StartTime": start_time,
        "EndTime": end_time,
        "Notes": notes,
        "PaymentAmt": payment_amt,
        "CancellationCount": cancellation_count
    }

    new_booking_result, new_booking_success = create_booking_from_cancellation(**new_booking_data)

    if not new_booking_success:
        return {
            "success": False,
            "message": "Failed to create new booking",
            "creditScoreDeduction": credit_deduction,
            "nurseStatus": status_result
        }

    new_booking_id = new_booking_result.get('BookingId', '')

    # Notify new nurse about assignment
    await send_notification_to_new_nurse(
        new_nurse,
        new_booking_id,
        patient_name,
        start_time,
        end_time,
        location,
        notes
    )

    # Notify patient about reassignment
    await send_notification_to_patient(
        new_booking_id,
        patient_id,
        patient_name,
        patient_email,
        nurse_data.get('name'),
        "reassigned",
        new_nurse.get('name')
    )

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
            "id": new_nurse.get('NID'),
            "name": new_nurse.get('name')
        },
        "newBookingId": new_booking_id,
        "reassignmentCount": cancellation_count
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


async def send_notification_to_new_nurse(nurse_data, booking_id, patient_name, start_time, end_time, location, notes):
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
        <p>You have been assigned to a booking for patient {patient_name}.</p>
        <hr>
        <h3>Booking Details:</h3>
        <ul>
            <li><strong>Booking ID:</strong> {booking_id}</li>
            <li><strong>Patient:</strong> {patient_name}</li>
            <li><strong>Start time:</strong> {start_time}</li>
            <li><strong>End time:</strong> {end_time}</li>
            <li><strong>Location:</strong> {location}</li>
            <li><strong>Notes:</strong> {notes}</li>
        </ul>
        <p>This booking was reassigned to you from another nurse who cancelled.</p>
        <p>Please check your MedGrab app for further details.</p>
        <p>Best regards,<br>MedGrab Team</p>
    </body>
    </html>
    """

    result = await send_notification_amqp(nurse_email, subject, message)
    return result.get('success', False)


async def send_notification_to_patient(booking_id, patient_id, patient_name, patient_email, nurse_name,
                                       notification_type, new_nurse_name=None):
    """Send notification to patient about booking changes"""
    if not patient_email:
        print(f"No email found for patient {patient_id}")
        return False

    subject = "MedGrab Booking Update"

    if notification_type == "max_reassignments":
        message = f"""
        <html>
        <body>
            <h2>Booking Update Required</h2>
            <p>Dear {patient_name},</p>
            <p>Unfortunately, we've had to cancel your booking #{booking_id} after multiple nurse reassignment attempts.</p>
            <p>This booking has been cancelled and reassigned 3 times, which is our maximum limit.</p>
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
            <p>Dear {patient_name},</p>
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
            <p>Dear {patient_name},</p>
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

    CORS(app)  # Enable Cross-Origin Resource Sharing for all routes

    init_app(app)
    app.run(debug=True, host='0.0.0.0', port=5011)