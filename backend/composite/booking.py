from flask import Flask, Blueprint, request, jsonify
from flask_cors import CORS
import requests
import logging
import os
from typing import Dict, Any, Tuple
import asyncio

from amqp_setup import send_notification_amqp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Configuration using environment variables with defaults for development
class Config:
    """Configuration class for the application."""
    MAIN_URL = os.environ.get('MAIN_URL', 'https://personal-o6lh6n5u.outsystemscloud.com/MedGrabBookingAtomic/rest/v1/')
    NURSE_URL = os.environ.get('NURSE_URL', 'http://host.docker.internal:5003/')
    PATIENT_URL = os.environ.get('PATIENT_URL', 'https://personal-eassd2ao.outsystemscloud.com/PatientAPI/rest/v2/')
    API_KEY = os.environ.get('API_KEY', 'adf0fe5c19401034c4466875565bc6c62253eae1dd84d46fba4eeda2bd1a0c5549168bfefa2021f03df33e9eab0bbd8527f6586f79bb36e1be37bfabac288374756ae7b54a548be1f607408a479467bde1fce109f94fa8e151f875451483291f5ead011168c835409bfbda1f2c7781f6a94cdc75d2d33d99ee7486edd9e0f70746f7d7979798ffd473362a3968da6c618693a184a296ce344c7a4c725b5db0bf72025d91b1c0e2186621b9cc7c482f72035b5bb12bfbda41e29ae25546e5f1e087d5f097d6680aef95c12c166f369c8a5911373c787baaaf620c06297c3839dd6c51719eaaff31b99df87512172c5140157acaf4439b7c13a0aecde2c5cb9643')

    # AMQP Configuration
    AMQP_HOST = os.environ.get('AMQP_HOST', 'localhost')
    AMQP_PORT = int(os.environ.get('AMQP_PORT', 5672))
    EXCHANGE_NAME = os.environ.get('EXCHANGE_NAME', 'medgrab_exchange')
    EXCHANGE_TYPE = os.environ.get('EXCHANGE_TYPE', 'topic')
    NOTIFICATION_ROUTING_KEY = os.environ.get('NOTIFICATION_ROUTING_KEY', 'notification.email')
    NOTIFICATION_QUEUE = os.environ.get('NOTIFICATION_QUEUE', 'email_notifications')


# Create Flask app and blueprint
app = Flask(__name__)
CORS(app)
booking_composite_bp = Blueprint('booking_composite', __name__)


class BookingService:
    """Service class for handling booking operations."""

    @staticmethod
    async def get_nurse_details(nurse_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Get nurse details from the Nurse service.

        Args:
            nurse_id: ID of the nurse

        Returns:
            Tuple containing nurse data and status code
        """
        try:
            url = f"{Config.NURSE_URL}api/nurses/{nurse_id}"
            logger.info(f"Fetching nurse details from: {url}")

            response = requests.get(url)
            response.raise_for_status()
            return response.json(), 200
        except requests.RequestException as e:
            logger.error(f"Error fetching nurse details: {str(e)}")
            return {"error": "Failed to fetch nurse details"}, 500

    @staticmethod
    async def get_patient_details(patient_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Get patient details from the Patient service.

        Args:
            patient_id: ID of the patient

        Returns:
            Tuple containing patient data and status code
        """
        try:
            url = f"{Config.PATIENT_URL}GetPatient/{patient_id}"
            logger.info(f"Fetching patient details from: {url}")

            response = requests.get(url)
            response.raise_for_status()

            response_json = response.json()
            patient = response_json.get('Patient')

            if not patient:
                return {"error": "Patient data not found in response"}, 404

            return {"patient": patient}, 200
        except requests.RequestException as e:
            logger.error(f"Error fetching patient details: {str(e)}")
            return {"error": "Failed to fetch patient details"}, 500

    @staticmethod
    async def create_booking(booking_data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        Create a new booking using the Booking service.

        Args:
            booking_data: Data for the new booking

        Returns:
            Tuple containing response data and status code
        """
        try:
            url = f"{Config.MAIN_URL}CreateBooking/"
            logger.info(f"Creating booking at: {url}")

            # Add API key to booking data
            booking_data['APIKey'] = Config.API_KEY

            response = requests.post(url, json=booking_data)
            response.raise_for_status()

            return response.json(), 200
        except requests.RequestException as e:
            logger.error(f"Error creating booking: {str(e)}")
            return {"error": "Failed to create booking"}, 500

    @staticmethod
    async def get_booking(booking_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Get booking details from the Booking service.

        Args:
            booking_id: ID of the booking

        Returns:
            Tuple containing booking data and status code
        """
        try:
            url = f"{Config.MAIN_URL}GetBooking/{booking_id}"
            logger.info(f"Fetching booking details from: {url}")

            response = requests.get(url)
            response_json = response.json()

            if response_json.get("StatusCode") != 200:
                return {"error": response_json.get("Message", "Unknown error")}, response_json.get("StatusCode", 500)

            return response_json, 200
        except requests.RequestException as e:
            logger.error(f"Error fetching booking details: {str(e)}")
            return {"error": "Failed to fetch booking details"}, 500

    @staticmethod
    async def update_booking_status(booking_id: str, status: str) -> Tuple[Dict[str, Any], int]:
        """
        Update booking status in the Booking service.

        Args:
            booking_id: ID of the booking
            status: New status for the booking

        Returns:
            Tuple containing response data and status code
        """
        try:
            url = f"{Config.MAIN_URL}UpdateBookingStatus/{booking_id}/{status}"
            logger.info(f"Updating booking status at: {url}")

            response = requests.patch(url, json={"APIKey": Config.API_KEY})
            response_json = response.json()

            if response_json.get("StatusCode") != 200:
                return {"error": response_json.get("Message", "Unknown error")}, response_json.get("StatusCode", 500)

            return response_json, 200
        except requests.RequestException as e:
            logger.error(f"Error updating booking status: {str(e)}")
            return {"error": "Failed to update booking status"}, 500

    @staticmethod
    def create_notification_message(nurse_name: str, start_time: str, end_time: str, location: str, notes: str) -> str:
        """
        Create HTML notification message for email.

        Args:
            nurse_name: Name of the nurse
            start_time: Booking start time
            end_time: Booking end time
            location: Patient location
            notes: Additional booking notes

        Returns:
            HTML formatted message
        """
        return f"""
        <html>
        <body>
            <p>Hi {nurse_name},</p>
            <p>There is a new booking for you.</p>
            <hr>
            <h3>Summary:</h3>
            <ul>
                <li><strong>Start time:</strong> {start_time}</li>
                <li><strong>End time:</strong> {end_time}</li>
                <li><strong>Location:</strong> {location}</li>
                <li><strong>Notes:</strong> {notes}</li>
            </ul>

            <p><strong>Please respond to the request within 24 hours:</strong></p>

            <p>Thank you for your service.</p>
            <p>Best Regards,<br>MedGrab Team</p>
        </body>
        </html>
        """


@booking_composite_bp.route('/MakeBooking', methods=['POST'])
async def make_booking():
    """
    Endpoint to create a new booking and send notification to nurse.

    Expected request body:
    {
        "NID": "nurse_id",
        "PID": "patient_id",
        "StartTime": "start_time",
        "EndTime": "end_time",
        "Notes": "booking_notes",
        "PaymentAmt": amount
    }

    Returns:
        JSON response with success status and message
    """
    try:
        data = request.json
        logger.info(f"Received booking request: {data}")

        # Validate required fields
        required_fields = ['NID', 'PID', 'StartTime', 'EndTime', 'PaymentAmt']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Extract booking data
        nurse_id = data.get('NID')
        patient_id = data.get('PID')
        start_time = data.get('StartTime')
        end_time = data.get('EndTime')
        notes = data.get('Notes', '')
        payment_amt = data.get('PaymentAmt')

        # Create booking data
        booking_data = {
            'NID': nurse_id,
            'PID': patient_id,
            'StartTime': start_time,
            'EndTime': end_time,
            'Notes': notes,
            'PaymentAmt': payment_amt
        }

        # Get nurse details
        nurse_result, nurse_status = await BookingService.get_nurse_details(nurse_id)
        if nurse_status != 200:
            return jsonify({
                'success': False,
                'error': 'No nurse with that NID found'
            }), 400

        # Get patient details
        patient_result, patient_status = await BookingService.get_patient_details(patient_id)
        if patient_status != 200:
            return jsonify({
                'success': False,
                'error': 'No patient with that PID found'
            }), 400

        patient = patient_result.get('patient')

        # Create booking
        booking_result, booking_status = await BookingService.create_booking(booking_data)
        if booking_status != 200:
            return jsonify({
                'success': False,
                'error': 'Failed to create booking'
            }), booking_status

        # Send notification to nurse
        notification_message = BookingService.create_notification_message(
            nurse_result.get('name', 'Nurse'),
            start_time,
            end_time,
            patient.get('Location', 'Unknown'),
            notes
        )

        await send_notification_amqp(
            nurse_result.get('email'),
            "New booking for you",
            notification_message
        )

        return jsonify({
            'success': True,
            'message': 'Booking made successfully',
            'booking_id': booking_result.get('BookingId', '')
        })

    except Exception as e:
        logger.error(f"Error in make_booking: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@booking_composite_bp.route('/AcceptBooking', methods=['POST'])
async def accept_booking():
    """
    Endpoint to accept a booking.

    Expected request body:
    {
        "bid": "booking_id"
    }

    Returns:
        JSON response with success status and message
    """
    try:
        data = request.json
        logger.info(f"Received accept booking request: {data}")

        booking_id = data.get('bid')
        if not booking_id:
            return jsonify({
                'success': False,
                'error': 'Missing booking ID (bid)'
            }), 400

        # Get booking details
        booking_result, booking_status = await BookingService.get_booking(booking_id)
        if booking_status != 200:
            return jsonify({
                'success': False,
                'error': booking_result.get('error', 'Failed to fetch booking')
            }), booking_status

        # Update booking status
        update_result, update_status = await BookingService.update_booking_status(booking_id, 'Accepted')
        if update_status != 200:
            return jsonify({
                'success': False,
                'error': update_result.get('error', 'Failed to update booking status')
            }), update_status

        return jsonify({
            'success': True,
            'message': 'Booking accepted'
        })

    except Exception as e:
        logger.error(f"Error in accept_booking: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


# Register blueprint
app.register_blueprint(booking_composite_bp, url_prefix='/v1')

if __name__ == '__main__':
    # Load the API key from environment variable
    if not Config.API_KEY:
        logger.warning("API_KEY environment variable not set. Service may not function correctly.")

    # Run the Flask app
    app.run(debug=os.environ.get('DEBUG', 'True').lower() == 'true',
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5008)))