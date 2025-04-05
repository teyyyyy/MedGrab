"""
MedGrab Booking Composite Service
A microservice for handling booking operations between nurses and patients.
"""
from flask import Flask, Blueprint, request, jsonify
from flask_cors import CORS
import httpx
import logging
import os
import asyncio
import random
from typing import Dict, Any, Tuple, Optional, List
from dataclasses import dataclass
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    """Configuration for external service endpoints."""
    MAIN_URL: str
    NURSE_URL: str
    PATIENT_URL: str
    API_KEY: str


@dataclass
class AmqpConfig:
    """Configuration for AMQP messaging."""
    HOST: str
    PORT: int
    EXCHANGE_NAME: str
    EXCHANGE_TYPE: str
    NOTIFICATION_ROUTING_KEY: str
    NOTIFICATION_QUEUE: str


class Config:
    """Application configuration with environment variable support."""

    @staticmethod
    def get_service_config() -> ServiceConfig:
        """Get service configuration from environment variables."""
        return ServiceConfig(
            MAIN_URL=os.environ.get('MAIN_URL', 'https://personal-o6lh6n5u.outsystemscloud.com/MedGrabBookingAtomic/rest/v1/'),
            NURSE_URL=os.environ.get('NURSE_URL', 'http://host.docker.internal:5003/'),
            PATIENT_URL=os.environ.get('PATIENT_URL', 'https://personal-eassd2ao.outsystemscloud.com/PatientAPI/rest/v2/'),
            API_KEY=os.environ.get('API_KEY', 'adf0fe5c19401034c4466875565bc6c62253eae1dd84d46fba4eeda2bd1a0c5549168bfefa2021f03df33e9eab0bbd8527f6586f79bb36e1be37bfabac288374756ae7b54a548be1f607408a479467bde1fce109f94fa8e151f875451483291f5ead011168c835409bfbda1f2c7781f6a94cdc75d2d33d99ee7486edd9e0f70746f7d7979798ffd473362a3968da6c618693a184a296ce344c7a4c725b5db0bf72025d91b1c0e2186621b9cc7c482f72035b5bb12bfbda41e29ae25546e5f1e087d5f097d6680aef95c12c166f369c8a5911373c787baaaf620c06297c3839dd6c51719eaaff31b99df87512172c5140157acaf4439b7c13a0aecde2c5cb9643')
        )

    @staticmethod
    def get_amqp_config() -> AmqpConfig:
        """Get AMQP configuration from environment variables."""
        return AmqpConfig(
            HOST=os.environ.get('AMQP_HOST', 'localhost'),
            PORT=int(os.environ.get('AMQP_PORT', 5672)),
            EXCHANGE_NAME=os.environ.get('EXCHANGE_NAME', 'medgrab_exchange'),
            EXCHANGE_TYPE=os.environ.get('EXCHANGE_TYPE', 'topic'),
            NOTIFICATION_ROUTING_KEY=os.environ.get('NOTIFICATION_ROUTING_KEY', 'notification.email'),
            NOTIFICATION_QUEUE=os.environ.get('NOTIFICATION_QUEUE', 'email_notifications')
        )


# Import here to avoid circular imports
from amqp_setup import send_notification_amqp


class ApiError(Exception):
    """Exception for API errors with status code."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def api_response(success: bool, message: Optional[str] = None, data: Optional[Dict] = None,
                 error: Optional[str] = None, status_code: int = 200) -> Tuple[Dict, int]:
    """Create a standardized API response."""
    response = {'success': success}

    if message:
        response['message'] = message

    if data:
        response.update(data)

    if error:
        response['error'] = error

    return response, status_code


def async_route(f):
    """Decorator to handle async route functions."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


class HttpClient:
    """HTTP client for making requests to external services."""

    @staticmethod
    async def get(url: str) -> Dict:
        """Make a GET request to the specified URL."""
        try:
            logger.info(f"GET request to: {url}")
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            status_code = e.response.status_code
            raise ApiError(f"HTTP error: {e}", status_code)
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise ApiError(f"Request error: {e}")

    @staticmethod
    async def post(url: str, json_data: Dict) -> Dict:
        """Make a POST request to the specified URL."""
        try:
            logger.info(f"POST request to: {url}")
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.post(url, json=json_data, timeout=10.0)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            status_code = e.response.status_code
            raise ApiError(f"HTTP error: {e}", status_code)
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise ApiError(f"Request error: {e}")

    @staticmethod
    async def patch(url: str, json_data: Dict) -> Dict:
        """Make a PATCH request to the specified URL."""
        try:
            logger.info(f"PATCH request to: {url}")
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.patch(url, json=json_data, timeout=10.0)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            status_code = e.response.status_code
            raise ApiError(f"HTTP error: {e}", status_code)
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise ApiError(f"Request error: {e}")


class NotificationService:
    """Service for creating and sending notifications."""

    @staticmethod
    def create_nurse_booking_notification(nurse_name: str, start_time: str, end_time: str,
                                         location: str, notes: str) -> str:
        """Create HTML notification for a new booking to send to a nurse."""
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
    def create_patient_booking_notification(patient_name: str, start_time: str, end_time: str,
                                          nurse_name: str, notes: str) -> str:
        """Create HTML notification for a new booking to send to a patient."""
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

    @staticmethod
    def create_nurse_accepted_notification(nurse_name: str, patient_name: str,
                                         start_time: str, end_time: str,
                                         location: str, notes: str) -> str:
        """Create HTML notification for an accepted booking to send to a nurse."""
        return f"""
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

    @staticmethod
    def create_patient_accepted_notification(patient_name: str, nurse_name: str,
                                           start_time: str, end_time: str, notes: str) -> str:
        """Create HTML notification for an accepted booking to send to a patient."""
        return f"""
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

    @staticmethod
    def create_new_nurse_reassigned_notification(nurse_name: str, patient_name: str,
                                               start_time: str, end_time: str,
                                               location: str, notes: str) -> str:
        """Create HTML notification for a reassigned booking to send to the new nurse."""
        return f"""
        <html>
        <body>
            <p>Hello {nurse_name},</p>
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

    @staticmethod
    def create_patient_reassigned_notification(patient_name: str, nurse_name: str,
                                             start_time: str, end_time: str, notes: str) -> str:
        """Create HTML notification for a reassigned booking to send to the patient."""
        return f"""
        <html>
        <body>
            <p>Hello {patient_name},</p>
            <p>Your booking has been reassigned to a new nurse: {nurse_name}.</p>
            <hr>
            <h3>Updated Booking Details:</h3>
            <ul>
                <li><strong>Nurse:</strong> {nurse_name}</li>
                <li><strong>Start time:</strong> {start_time}</li>
                <li><strong>End time:</strong> {end_time}</li>
                <li><strong>Notes:</strong> {notes}</li>
            </ul>
            <p>Your new nurse will confirm this booking shortly.</p>
            <p>Best Regards,<br>MedGrab Team</p>
        </body>
        </html>
        """


class NurseService:
    """Service for interacting with the Nurse API."""

    def __init__(self, config: ServiceConfig):
        self.base_url = config.NURSE_URL

    async def get_nurse(self, nurse_id: str) -> Dict:
        """Get details for a specific nurse."""
        url = f"{self.base_url}api/nurses/{nurse_id}"
        return await HttpClient.get(url)

    async def get_all_nurses(self) -> List[Dict]:
        """Get all available nurses."""
        url = f"{self.base_url}api/nurses/"  # Added trailing slash
        return await HttpClient.get(url)


class PatientService:
    """Service for interacting with the Patient API."""

    def __init__(self, config: ServiceConfig):
        self.base_url = config.PATIENT_URL

    async def get_patient(self, patient_id: str) -> Dict:
        """Get details for a specific patient."""
        url = f"{self.base_url}GetPatient/{patient_id}"
        response = await HttpClient.get(url)

        patient = response.get('Patient')
        if not patient:
            raise ApiError("Patient data not found in response", 404)

        return {"patient": patient}


class BookingService:
    """Service for interacting with the Booking API."""

    def __init__(self, config: ServiceConfig):
        self.base_url = config.MAIN_URL
        self.api_key = config.API_KEY

    async def create_booking(self, booking_data: Dict) -> Dict:
        """Create a new booking."""
        url = f"{self.base_url}CreateBooking/"

        # Add API key to booking data
        data_with_key = booking_data.copy()
        data_with_key['APIKey'] = self.api_key

        return await HttpClient.post(url, data_with_key)

    async def get_booking(self, booking_id: str) -> Dict:
        """Get details for a specific booking."""
        url = f"{self.base_url}GetBooking/{booking_id}"
        response = await HttpClient.get(url)

        if response.get("StatusCode") != 200:
            raise ApiError(response.get("Message", "Unknown error"), response.get("StatusCode", 500))

        return response

    async def update_booking_status(self, booking_id: str, status: str) -> Dict:
        """Update the status of a booking."""
        url = f"{self.base_url}UpdateBookingStatus/{booking_id}/{status}"
        response = await HttpClient.patch(url, {"APIKey": self.api_key})

        if response.get("StatusCode") != 200:
            raise ApiError(response.get("Message", "Unknown error"), response.get("StatusCode", 500))

        return response

    async def update_booking_nurse(self, booking_id: str, nurse_id: str) -> Dict:
        """Update the nurse assigned to a booking."""
        url = f"{self.base_url}UpdateBookingNurse/{booking_id}/{nurse_id}"
        response = await HttpClient.patch(url, {"APIKey": self.api_key})

        if response.get("StatusCode") != 200:
            raise ApiError(response.get("Message", "Unknown error"), response.get("StatusCode", 500))

        return response

    async def cancel_with_reason(self, booking_id: str, reason: str) -> Dict:
        """Cancel a booking with a reason."""
        url = f"{self.base_url}CancelWithReason/{booking_id}"
        response = await HttpClient.post(url, {"APIKey": self.api_key, "Reason": reason})

        if response.get("StatusCode") != 200:
            raise ApiError(response.get("Message", "Unknown error"), response.get("StatusCode", 500))

        return response


class BookingManager:
    """Manager class for booking operations that coordinates between services."""

    def __init__(self, service_config: ServiceConfig):
        self.nurse_service = NurseService(service_config)
        self.patient_service = PatientService(service_config)
        self.booking_service = BookingService(service_config)

    async def create_new_booking(self, booking_data: Dict) -> Dict:
        """Create a new booking and handle all related operations."""
        # Extract data
        nurse_id = booking_data.get('NID')
        patient_id = booking_data.get('PID')
        start_time = booking_data.get('StartTime')
        end_time = booking_data.get('EndTime')
        notes = booking_data.get('Notes', '')

        # Get nurse and patient details
        nurse = await self.nurse_service.get_nurse(nurse_id)
        patient_data = await self.patient_service.get_patient(patient_id)
        patient = patient_data.get('patient')

        # Create the booking
        booking_result = await self.booking_service.create_booking(booking_data)

        # Create notifications
        nurse_notification = NotificationService.create_nurse_booking_notification(
            nurse.get('name', 'Nurse'),
            start_time,
            end_time,
            patient.get('Location', 'Unknown'),
            notes
        )

        patient_notification = NotificationService.create_patient_booking_notification(
            patient.get('PatientName', 'Patient'),
            start_time,
            end_time,
            nurse.get('name', 'Nurse'),
            notes
        )

        # Send notifications
        await send_notification_amqp(
            nurse.get('email'),
            "New booking for you",
            nurse_notification
        )

        await send_notification_amqp(
            patient.get('Email', ''),
            "Your MedGrab booking confirmation",
            patient_notification
        )

        return {
            'message': 'Booking made successfully',
            'booking_id': booking_result.get('BookingId', '')
        }

    async def accept_booking(self, booking_id: str) -> Dict:
        """Accept a booking and notify relevant parties."""
        # Get booking details
        booking_result = await self.booking_service.get_booking(booking_id)
        booking_data = booking_result.get('Booking', {})

        # Extract nurse and patient IDs
        fields = booking_data.get('fields', {})
        nurse_id = fields.get('NID', {}).get('stringValue')
        patient_id = fields.get('PID', {}).get('stringValue')

        if not nurse_id or not patient_id:
            raise ApiError('Missing nurse or patient ID in booking data', 400)

        # Get nurse and patient details
        nurse = await self.nurse_service.get_nurse(nurse_id)
        patient_data = await self.patient_service.get_patient(patient_id)
        patient = patient_data.get('patient', {})

        # Update booking status
        await self.booking_service.update_booking_status(booking_id, 'Accepted')

        # Create notifications
        start_time = fields.get('StartTime', {}).get('stringValue', '')
        end_time = fields.get('EndTime', {}).get('stringValue', '')
        location = patient.get('Location', 'Unknown')
        notes = fields.get('Notes', {}).get('stringValue', '')

        nurse_name = nurse.get('name', 'Nurse')
        nurse_email = nurse.get('email', '')
        patient_name = patient.get('PatientName', 'Patient')
        patient_email = patient.get('Email', '')

        nurse_notification = NotificationService.create_nurse_accepted_notification(
            nurse_name, patient_name, start_time, end_time, location, notes
        )

        patient_notification = NotificationService.create_patient_accepted_notification(
            patient_name, nurse_name, start_time, end_time, notes
        )

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

        return {'message': 'Booking accepted'}

    async def reject_and_reassign_booking(self, booking_id: str) -> Dict:
        """Reject a booking and reassign it to another nurse."""
        # Get booking details
        booking_result = await self.booking_service.get_booking(booking_id)
        booking_data = booking_result.get('Booking', {})

        # Extract nurse and patient IDs
        fields = booking_data.get('fields', {})
        current_nurse_id = fields.get('NID', {}).get('stringValue')
        patient_id = fields.get('PID', {}).get('stringValue')

        if not current_nurse_id or not patient_id:
            raise ApiError('Missing nurse or patient ID in booking data', 400)

        # Get all nurses and find a new one
        all_nurses = await self.nurse_service.get_all_nurses()
        available_nurses = [nurse for nurse in all_nurses if nurse.get('NID') != current_nurse_id]

        if not available_nurses:
            raise ApiError('No other nurses available for reassignment', 400)

        # Choose a random nurse
        new_nurse = random.choice(available_nurses)
        new_nurse_id = new_nurse.get('NID')

        # Update booking with new nurse
        await self.booking_service.update_booking_nurse(booking_id, new_nurse_id)

        # Get patient details
        patient_data = await self.patient_service.get_patient(patient_id)
        patient = patient_data.get('patient', {})

        # Create notifications
        start_time = fields.get('StartTime', {}).get('stringValue', '')
        end_time = fields.get('EndTime', {}).get('stringValue', '')
        location = patient.get('Location', 'Unknown')
        notes = fields.get('Notes', {}).get('stringValue', '')

        new_nurse_name = new_nurse.get('name', 'Nurse')
        new_nurse_email = new_nurse.get('email', '')
        patient_name = patient.get('PatientName', 'Patient')
        patient_email = patient.get('Email', '')

        new_nurse_notification = NotificationService.create_new_nurse_reassigned_notification(
            new_nurse_name, patient_name, start_time, end_time, location, notes
        )

        patient_notification = NotificationService.create_patient_reassigned_notification(
            patient_name, new_nurse_name, start_time, end_time, notes
        )

        # Send notifications
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
        await self.booking_service.update_booking_status(booking_id, 'Pending')

        return {
            'message': 'Booking rejected and reassigned',
            'new_nurse_id': new_nurse_id
        }

    async def cancel_with_reason_and_reassign(self, booking_id: str, reason: str) -> Dict:
        """Cancel a booking with reason and create a new booking with another nurse."""
        # Get booking details
        booking_result = await self.booking_service.get_booking(booking_id)
        booking_data = booking_result.get('Booking', {})

        # Extract fields
        fields = booking_data.get('fields', {})
        current_nurse_id = fields.get('NID', {}).get('stringValue')
        patient_id = fields.get('PID', {}).get('stringValue')
        start_time = fields.get('StartTime', {}).get('timestampValue', '')
        end_time = fields.get('EndTime', {}).get('timestampValue', '')
        payment_amt = fields.get('PaymentAmt', {}).get('doubleValue', 0)
        notes = fields.get('Notes', {}).get('stringValue', '')

        if not current_nurse_id or not patient_id:
            raise ApiError('Missing nurse or patient ID in booking data', 400)

        # Cancel the current booking with reason
        await self.booking_service.cancel_with_reason(booking_id, reason)

        # Get all nurses and find a new one
        all_nurses = await self.nurse_service.get_all_nurses()
        available_nurses = [nurse for nurse in all_nurses if nurse.get('NID') != current_nurse_id]

        if not available_nurses:
            raise ApiError('No other nurses available for reassignment', 400)

        # Choose a random nurse
        new_nurse = random.choice(available_nurses)
        new_nurse_id = new_nurse.get('NID')

        # Create a new booking with the new nurse
        new_booking_data = {
            'NID': new_nurse_id,
            'PID': patient_id,
            'StartTime': start_time,
            'EndTime': end_time,
            'PaymentAmt': payment_amt,
            'Notes': notes
        }

        new_booking_result = await self.booking_service.create_booking(new_booking_data)
        new_booking_id = new_booking_result.get('BookingId', '')

        # Get patient details
        patient_data = await self.patient_service.get_patient(patient_id)
        patient = patient_data.get('patient', {})

        # Get current nurse details
        current_nurse = await self.nurse_service.get_nurse(current_nurse_id)

        # Create notifications
        new_nurse_name = new_nurse.get('name', 'Nurse')
        new_nurse_email = new_nurse.get('email', '')
        patient_name = patient.get('PatientName', 'Patient')
        patient_email = patient.get('Email', '')
        current_nurse_name = current_nurse.get('name', 'Nurse')
        current_nurse_email = current_nurse.get('email', '')
        location = patient.get('Location', 'Unknown')

        # Notification to the current nurse about cancellation
        current_nurse_notification = f"""
        <html>
        <body>
            <p>Hello {current_nurse_name},</p>
            <p>Your booking with patient {patient_name} has been cancelled with the following reason:</p>
            <p><em>"{reason}"</em></p>
            <hr>
            <h3>Cancelled Booking Details:</h3>
            <ul>
                <li><strong>Patient:</strong> {patient_name}</li>
                <li><strong>Start time:</strong> {start_time}</li>
                <li><strong>End time:</strong> {end_time}</li>
                <li><strong>Location:</strong> {location}</li>
            </ul>
            <p>This cancellation has been recorded in your profile.</p>
            <p>Best Regards,<br>MedGrab Team</p>
        </body>
        </html>
        """

        # Notification to the new nurse
        new_nurse_notification = NotificationService.create_new_nurse_reassigned_notification(
            new_nurse_name, patient_name, start_time, end_time, location, notes
        )

        # Notification to the patient
        patient_notification = f"""
        <html>
        <body>
            <p>Hello {patient_name},</p>
            <p>Your booking with {current_nurse_name} has been cancelled with the following reason:</p>
            <p><em>"{reason}"</em></p>
            <p>However, we have automatically reassigned you to a new nurse: {new_nurse_name}.</p>
            <hr>
            <h3>Updated Booking Details:</h3>
            <ul>
                <li><strong>New Nurse:</strong> {new_nurse_name}</li>
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
        if current_nurse_email:
            await send_notification_amqp(
                current_nurse_email,
                "Booking Cancelled",
                current_nurse_notification
            )

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

        return {
            'message': 'Booking cancelled with reason and reassigned',
            'new_booking_id': new_booking_id,
            'new_nurse_id': new_nurse_id
        }


# Create Flask app and blueprint
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for all routes
booking_bp = Blueprint('booking_composite', __name__, url_prefix='/v1')


# Initialize services
service_config = Config.get_service_config()
booking_manager = BookingManager(service_config)


@booking_bp.route('/MakeBooking', methods=['POST'])
@async_route
async def make_booking():
    """Endpoint to create a new booking and send notification to nurse."""
    try:
        data = request.json
        logger.info(f"Received booking request: {data}")

        # Validate required fields
        required_fields = ['NID', 'PID', 'StartTime', 'EndTime', 'PaymentAmt']
        for field in required_fields:
            if not data.get(field):
                return jsonify(api_response(
                    success=False,
                    error=f'Missing required field: {field}',
                    status_code=400
                ))

        # Process booking
        result = await booking_manager.create_new_booking(data)

        return jsonify(api_response(
            success=True,
            **result
        ))

    except ApiError as e:
        return jsonify(api_response(
            success=False,
            error=e.message,
            status_code=e.status_code
        ))
    except Exception as e:
        logger.error(f"Error in make_booking: {str(e)}")
        return jsonify(api_response(
            success=False,
            error='Internal server error',
            status_code=500
        ))


@booking_bp.route('/AcceptBooking', methods=['POST'])
@async_route
async def accept_booking():
    """Endpoint to accept a booking."""
    try:
        data = request.json
        logger.info(f"Received accept booking request: {data}")

        booking_id = data.get('bid')
        if not booking_id:
            return jsonify(api_response(
                success=False,
                error='Missing booking ID (bid)',
                status_code=400
            ))

        # Process booking acceptance
        result = await booking_manager.accept_booking(booking_id)

        return jsonify(api_response(
            success=True,
            **result
        ))

    except ApiError as e:
        return jsonify(api_response(
            success=False,
            error=e.message,
            status_code=e.status_code
        ))
    except Exception as e:
        logger.error(f"Error in accept_booking: {str(e)}")
        return jsonify(api_response(
            success=False,
            error='Internal server error',
            status_code=500
        ))


@booking_bp.route('/RejectBooking', methods=['POST'])
@async_route
async def reject_booking():
    """Endpoint to reject a booking and reassign it to another nurse."""
    try:
        data = request.json
        logger.info(f"Received reject booking request: {data}")

        booking_id = data.get('bid')
        if not booking_id:
            return jsonify(api_response(
                success=False,
                error='Missing booking ID (bid)',
                status_code=400
            ))

        # Process booking rejection and reassignment
        result = await booking_manager.reject_and_reassign_booking(booking_id)

        return jsonify(api_response(
            success=True,
            **result
        ))

    except ApiError as e:
        return jsonify(api_response(
            success=False,
            error=e.message,
            status_code=e.status_code
        ))
    except Exception as e:
        logger.error(f"Error in reject_booking: {str(e)}")
        return jsonify(api_response(
            success=False,
            error='Internal server error',
            status_code=500
        ))


@booking_bp.route('/CancelWithReason', methods=['POST'])
@async_route
async def cancel_with_reason():
    """Endpoint to cancel a booking with reason and reassign it to another nurse."""
    try:
        data = request.json
        logger.info(f"Received cancel with reason request: {data}")

        booking_id = data.get('bid')
        reason = data.get('reason')

        if not booking_id:
            return jsonify(api_response(
                success=False,
                error='Missing booking ID (bid)',
                status_code=400
            ))

        if not reason:
            return jsonify(api_response(
                success=False,
                error='Missing cancellation reason',
                status_code=400
            ))

        # Process booking cancellation with reason and reassignment
        result = await booking_manager.cancel_with_reason_and_reassign(booking_id, reason)

        return jsonify(api_response(
            success=True,
            **result
        ))

    except ApiError as e:
        return jsonify(api_response(
            success=False,
            error=e.message,
            status_code=e.status_code
        ))
    except Exception as e:
        logger.error(f"Error in cancel_with_reason: {str(e)}")
        return jsonify(api_response(
            success=False,
            error='Internal server error',
            status_code=500
        ))

# Register blueprint
app.register_blueprint(booking_bp)

if __name__ == '__main__':
    # Load the API key from environment variable
    api_key = service_config.API_KEY
    if not api_key:
        logger.warning("API_KEY environment variable not set. Service may not function correctly.")

    # Run the Flask app
    app.run(
        debug=os.environ.get('DEBUG', 'True').lower() == 'true',
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5008))
    )