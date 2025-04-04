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

            logger.info(f"Getting booking details from: {response_json}")

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

    @staticmethod
    def create_patient_notification_message(patient_name: str, start_time: str, end_time: str, nurse_name: str,
                                            notes: str) -> str:
        """
        Create HTML notification message for patient email.

        Args:
            patient_name: Name of the patient
            start_time: Booking start time
            end_time: Booking end time
            nurse_name: Name of the nurse
            notes: Additional booking notes

        Returns:
            HTML formatted message
        """
        return f"""
        <html>
        <body>
            <p>Dear {patient_name},</p>
            <p>Your booking with MedGrab has been successfully created.</p>
            <hr>
            <h3>Booking Details:</h3>
            <ul>
                <li><strong>Nurse:</strong> {nurse_name}</li>
                <li><strong>Start time:</strong> {start_time}</li>
                <li><strong>End time:</strong> {end_time}</li>
                <li><strong>Notes:</strong> {notes}</li>
            </ul>

            <p>Your nurse will confirm this booking shortly. You'll receive another notification once confirmed.</p>
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

        logger.info(f"Getting nurse")
        # Get nurse details
        nurse_result, nurse_status = await BookingService.get_nurse_details(nurse_id)
        if nurse_status != 200:
            return jsonify({
                'success': False,
                'error': 'No nurse with that NID found'
            }), 400

        logger.info(f"Getting patient")
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

        # Get patient details - we already have this from above
        patient_name = patient.get('PatientName', 'Patient')

        # Create notification for patient
        patient_notification_message = BookingService.create_patient_notification_message(
            patient_name,
            start_time,
            end_time,
            nurse_result.get('name', 'Nurse'),
            notes
        )

        # Send notification to patient
        await send_notification_amqp(
            patient.get('Email', ''),
            "Your MedGrab booking confirmation",
            patient_notification_message
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

        logger.info(f"Getting booking")
        # Get booking details
        booking_result, booking_status = await BookingService.get_booking(booking_id)
        if booking_status != 200:
            return jsonify({
                'success': False,
                'error': booking_result.get('error', 'Failed to fetch booking')
            }), booking_status


        # Extract nurse and patient IDs from booking
        booking_data = booking_result.get('Booking', {})
        nurse_id = booking_data.get('fields').get('NID').get('stringValue')
        patient_id = booking_data.get('fields').get('PID').get('stringValue')
        logger.info(f"Booking data: {booking_data}")

        if not nurse_id or not patient_id:
            return jsonify({
                'success': False,
                'error': 'Missing nurse or patient ID in booking data'
            }), 400

        logger.info(f"Getting nurse")
        # Get nurse details
        nurse_result, nurse_status = await BookingService.get_nurse_details(nurse_id)
        if nurse_status != 200:
            return jsonify({
                'success': False,
                'error': 'Failed to fetch nurse details'
            }), nurse_status

        logger.info(f"Getting patient")
        # Get patient details
        patient_result, patient_status = await BookingService.get_patient_details(patient_id)
        if patient_status != 200:
            return jsonify({
                'success': False,
                'error': 'Failed to fetch patient details'
            }), patient_status

        nurse_email = nurse_result.get('email', '')
        nurse_name = nurse_result.get('name', 'Nurse')

        patient = patient_result.get('patient', {})
        patient_email = patient.get('Email', '')
        patient_name = patient.get('PatientName', 'Patient')

        # Update booking status
        update_result, update_status = await BookingService.update_booking_status(booking_id, 'Accepted')
        if update_status != 200:
            return jsonify({
                'success': False,
                'error': update_result.get('error', 'Failed to update booking status')
            }), update_status

        # Create and send notifications to nurse and patient
        start_time = booking_data.get('StartTime', '')
        end_time = booking_data.get('EndTime', '')
        location = patient.get('Location', 'Unknown')
        notes = booking_data.get('Notes', '')

        # Notification for nurse
        nurse_notification = f"""
        <html>
        <body>
            <p>Hello {nurse_name},</p>
            <p>You have accepted the booking for patient {patient_name}.</p>
            <hr>
            <h3>Booking Details:</h3>
            <ul>
                <li><strong>Start time:</strong> {start_time}</li>
                <li><strong>End time:</strong> {end_time}</li>
                <li><strong>Location:</strong> {location}</li>
                <li><strong>Notes:</strong> {notes}</li>
            </ul>
            <p>Thank you for your service.</p>
            <p>Best Regards,<br>MedGrab Team</p>
        </body>
        </html>
        """

        # Notification for patient
        patient_notification = f"""
        <html>
        <body>
            <p>Hello {patient_name},</p>
            <p>Good news! Your booking has been accepted by {nurse_name}.</p>
            <hr>
            <h3>Booking Details:</h3>
            <ul>
                <li><strong>Nurse:</strong> {nurse_name}</li>
                <li><strong>Start time:</strong> {start_time}</li>
                <li><strong>End time:</strong> {end_time}</li>
                <li><strong>Notes:</strong> {notes}</li>
            </ul>
            <p>Please be available at the scheduled time.</p>
            <p>Best Regards,<br>MedGrab Team</p>
        </body>
        </html>
        """

        # Send notifications
        if nurse_email:
            await send_notification_amqp(
                nurse_email,
                "Booking Accepted",
                nurse_notification
            )

        if patient_email:
            await send_notification_amqp(
                patient_email,
                "Your booking has been accepted",
                patient_notification
            )

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


@booking_composite_bp.route('/RejectBooking', methods=['POST'])
async def reject_booking():
    """
    Endpoint to reject a booking and reassign it to another nurse.

    Expected request body:
    {
        "bid": "booking_id"
    }

    Returns:
        JSON response with success status and message
    """
    try:
        data = request.json
        logger.info(f"Received reject booking request: {data}")

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

        # Extract nurse and patient IDs from booking
        booking_data = booking_result.get('Booking', {})
        current_nurse_id = booking_data.get('fields').get('NID').get('stringValue')
        patient_id = booking_data.get('fields').get('PID').get('stringValue')
        logger.info(f"Booking data: {booking_data}")

        if not current_nurse_id or not patient_id:
            return jsonify({
                'success': False,
                'error': 'Missing nurse or patient ID in booking data'
            }), 400

        # Get all nurses
        try:
            all_nurses_url = f"{Config.NURSE_URL}api/nurses"
            logger.info(f"Fetching all nurses from: {all_nurses_url}")

            all_nurses_response = requests.get(all_nurses_url)
            all_nurses_response.raise_for_status()
            all_nurses = all_nurses_response.json()

            # Filter out the current nurse
            available_nurses = [nurse for nurse in all_nurses if nurse.get('_id') != current_nurse_id]

            if not available_nurses:
                return jsonify({
                    'success': False,
                    'error': 'No other nurses available for reassignment'
                }), 400

            # Choose a random nurse from the available nurses
            import random
            new_nurse = random.choice(available_nurses)
            new_nurse_id = new_nurse.get('_id')

        except requests.RequestException as e:
            logger.error(f"Error fetching nurses: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Failed to fetch available nurses'
            }), 500

        # Update booking with new nurse
        try:
            update_nurse_url = f"{Config.MAIN_URL}UpdateBookingNurse/{booking_id}/{new_nurse_id}"
            logger.info(f"Updating booking nurse at: {update_nurse_url}")

            update_nurse_response = requests.patch(update_nurse_url, json={"APIKey": Config.API_KEY})
            update_nurse_response.raise_for_status()

            update_nurse_result = update_nurse_response.json()

            if update_nurse_result.get("StatusCode") != 200:
                return jsonify({
                    'success': False,
                    'error': update_nurse_result.get("Message", "Failed to update booking nurse")
                }), update_nurse_result.get("StatusCode", 500)

        except requests.RequestException as e:
            logger.error(f"Error updating booking nurse: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Failed to update booking nurse'
            }), 500

        # Get patient details
        patient_result, patient_status = await BookingService.get_patient_details(patient_id)
        if patient_status != 200:
            return jsonify({
                'success': False,
                'error': 'Failed to fetch patient details'
            }), patient_status

        # Get current nurse details
        current_nurse_result, current_nurse_status = await BookingService.get_nurse_details(current_nurse_id)

        patient = patient_result.get('patient', {})
        patient_email = patient.get('Email', '')
        patient_name = patient.get('PatientName', 'Patient')

        # Create and send notifications
        start_time = booking_data.get('fields').get('StartTime', {}).get('stringValue', '')
        end_time = booking_data.get('fields').get('EndTime', {}).get('stringValue', '')
        location = patient.get('Location', 'Unknown')
        notes = booking_data.get('fields').get('Notes', {}).get('stringValue', '')

        # Notification for new nurse
        new_nurse_notification = f"""
        <html>
        <body>
            <p>Hello {new_nurse.get('name', 'Nurse')},</p>
            <p>A booking has been reassigned to you.</p>
            <hr>
            <h3>Booking Details:</h3>
            <ul>
                <li><strong>Patient:</strong> {patient_name}</li>
                <li><strong>Start time:</strong> {start_time}</li>
                <li><strong>End time:</strong> {end_time}</li>
                <li><strong>Location:</strong> {location}</li>
                <li><strong>Notes:</strong> {notes}</li>
            </ul>
            <p><strong>Please respond to the request within 24 hours.</strong></p>
            <p>Best Regards,<br>MedGrab Team</p>
        </body>
        </html>
        """

        # Notification for patient
        patient_notification = f"""
        <html>
        <body>
            <p>Hello {patient_name},</p>
            <p>Your booking has been reassigned to a new nurse: {new_nurse.get('name', 'Nurse')}.</p>
            <hr>
            <h3>Updated Booking Details:</h3>
            <ul>
                <li><strong>Nurse:</strong> {new_nurse.get('name', 'Nurse')}</li>
                <li><strong>Start time:</strong> {start_time}</li>
                <li><strong>End time:</strong> {end_time}</li>
                <li><strong>Notes:</strong> {notes}</li>
            </ul>
            <p>Your new nurse will confirm this booking shortly.</p>
            <p>Best Regards,<br>MedGrab Team</p>
        </body>
        </html>
        """

        # Send notifications
        new_nurse_email = new_nurse.get('email', '')
        if new_nurse_email:
            await send_notification_amqp(
                new_nurse_email,
                "New booking assigned to you",
                new_nurse_notification
            )

        if patient_email:
            await send_notification_amqp(
                patient_email,
                "Your booking has been reassigned",
                patient_notification
            )

        # Update booking status to "Pending" for the new nurse
        await BookingService.update_booking_status(booking_id, 'Pending')

        return jsonify({
            'success': True,
            'message': 'Booking rejected and reassigned',
            'new_nurse_id': new_nurse_id
        })

    except Exception as e:
        logger.error(f"Error in reject_booking: {str(e)}")
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