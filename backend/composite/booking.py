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
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

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
    COMPLETION_CREDIT_BONUS: int  # Added configurable credit bonus for completion


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
            API_KEY=os.environ.get('BOOKING_API_KEY', ''),
            COMPLETION_CREDIT_BONUS=int(os.environ.get('COMPLETION_CREDIT_BONUS', 2))  # Default to +2 points
        )

    @staticmethod
    def get_amqp_config() -> AmqpConfig:
        """Get AMQP configuration from environment variables."""
        return AmqpConfig(
            HOST=os.environ.get('AMQP_HOST', 'host.docker.internal'),
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

    @staticmethod
    async def put(url: str, json_data: Dict) -> Dict:
        """Make a PUT request to the specified URL."""
        try:
            logger.info(f"PUT request to: {url}")
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.put(url, json=json_data, timeout=10.0)
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

            <p>Best Regards,<br>MedGrab Team</p>
        </body>
        </html>
        """

    @staticmethod
    def create_nurse_booking_completed_notification(nurse_name: str, patient_name: str,
                                                  start_time: str, end_time: str,
                                                  location: str, notes: str, credit_bonus: int) -> str:
        """Create HTML notification for a completed booking to send to the nurse."""
        return f"""
        <html>
        <body>
            <p>Oi {nurse_name}!</p>
            <p>Your booking has been marked as completed. Good job!</p>
            <hr>
            <h3>Completed Booking Details:</h3>
            <ul>
                <li><strong>Patient:</strong> {patient_name}</li>
                <li><strong>Start time:</strong> {start_time}</li>
                <li><strong>End time:</strong> {end_time}</li>
                <li><strong>Location:</strong> {location}</li>
                <li><strong>Notes:</strong> {notes}</li>
            </ul>
            <p><strong>Good news!</strong> You've received a +{credit_bonus} credit score bonus for completing this booking.</p>
            <p>Thanks for your hard work.</p>
            <p>Best Regards,<br>MedGrab Team</p>
        </body>
        </html>
        """

    @staticmethod
    def create_patient_booking_completed_notification(patient_name: str, nurse_name: str,
                                                    start_time: str, end_time: str, notes: str) -> str:
        """Create HTML notification for a completed booking to send to the patient."""
        return f"""
        <html>
        <body>
            <p>Hello {patient_name},</p>
            <p>Your booking with {nurse_name} has been marked as completed.</p>
            <hr>
            <h3>Completed Booking Details:</h3>
            <ul>
                <li><strong>Nurse:</strong> {nurse_name}</li>
                <li><strong>Start time:</strong> {start_time}</li>
                <li><strong>End time:</strong> {end_time}</li>
                <li><strong>Notes:</strong> {notes}</li>
            </ul>
            <p>We hope your experience was satisfactory. If you have a moment, please consider leaving feedback on our app.</p>
            <p>Best Regards,<br>MedGrab Team</p>
        </body>
        </html>
        """


class NurseService:
    """Service for interacting with the Nurse API."""

    def __init__(self, config: ServiceConfig):
        self.base_url = config.NURSE_URL
        self.completion_credit_bonus = config.COMPLETION_CREDIT_BONUS

    async def get_nurse(self, nurse_id: str) -> Dict:
        """Get details for a specific nurse."""
        url = f"{self.base_url}api/nurses/{nurse_id}"
        return await HttpClient.get(url)

    async def get_all_nurses(self) -> List[Dict]:
        """Get all available nurses."""
        url = f"{self.base_url}api/nurses/"  # Added trailing slash
        return await HttpClient.get(url)

    async def update_nurse_credit_score(self, nurse_id: str, credit_change: int, reason: str) -> Dict:
        """Update nurse credit score."""
        url = f"{self.base_url}api/nurses/{nurse_id}/credit"
        data = {
            "creditChange": credit_change,
            "reason": reason
        }
        logger.info(f"Updating nurse credit score: {url}")
        return await HttpClient.put(url, data)


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

    async def get_all_pending_bookings(self) -> List[Dict]:
        """Get all pending bookings."""
        url = f"{self.base_url}GetBookingsByStatus/Pending"
        response = await HttpClient.get(url)

        if response.get("StatusCode") != 200:
            raise ApiError(response.get("Message", "Unknown error"), response.get("StatusCode", 500))

        return response.get("Bookings", [])

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


class BookingManager:
    """Manager class for booking operations that coordinates between services."""

    def __init__(self, service_config: ServiceConfig):
        self.nurse_service = NurseService(service_config)
        self.patient_service = PatientService(service_config)
        self.booking_service = BookingService(service_config)
        self.completion_credit_bonus = service_config.COMPLETION_CREDIT_BONUS

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

    async def complete_booking(self, booking_id: str) -> Dict:
        """Manually complete a booking, increase nurse credit score, and send notifications."""
        try:
            # Get booking details
            booking_result = await self.booking_service.get_booking(booking_id)
            booking_data = booking_result.get('Booking', {})

            # Extract fields
            fields = booking_data.get('fields', {})
            nurse_id = fields.get('NID', {}).get('stringValue')
            patient_id = fields.get('PID', {}).get('stringValue')
            start_time = fields.get('StartTime', {}).get('timestampValue', '')
            end_time = fields.get('EndTime', {}).get('timestampValue', '')
            notes = fields.get('Notes', {}).get('stringValue', '')

            if not nurse_id or not patient_id:
                raise ApiError('Missing nurse or patient ID in booking data', 400)

            # Update booking status to completed
            await self.booking_service.update_booking_status(booking_id, "Completed")

            # Increase nurse credit score
            credit_update_result = await self.nurse_service.update_nurse_credit_score(
                nurse_id,
                self.completion_credit_bonus,
                f"Booking completion bonus: Booking ID {booking_id}"
            )

            logger.info(f"Updated nurse {nurse_id} credit score: +{self.completion_credit_bonus} points")

            # Get nurse and patient details
            nurse = await self.nurse_service.get_nurse(nurse_id)
            patient_data = await self.patient_service.get_patient(patient_id)
            patient = patient_data.get('patient', {})

            # Send completion notifications
            await self._send_completion_notifications(
                nurse.get('name', 'Nurse'),
                nurse.get('email', ''),
                patient.get('PatientName', 'Patient'),
                patient.get('Email', ''),
                patient.get('Location', 'Unknown'),
                start_time,
                end_time,
                notes
            )

            return {
                'message': 'Booking completed successfully',
                'booking_id': booking_id,
                'credit_bonus': self.completion_credit_bonus,
                'new_credit_score': credit_update_result.get('creditScore')
            }

        except ApiError as e:
            logger.error(f"API error in complete_booking: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in complete_booking: {str(e)}")
            raise ApiError(f"Failed to complete booking: {str(e)}")

    async def _send_completion_notifications(self, nurse_name: str, nurse_email: str,
                                           patient_name: str, patient_email: str,
                                           location: str, start_time: str, end_time: str,
                                           notes: str):
        """Send completion notifications to nurse and patient."""
        # Create notifications
        nurse_notification = NotificationService.create_nurse_booking_completed_notification(
            nurse_name, patient_name, start_time, end_time, location, notes, self.completion_credit_bonus
        )

        patient_notification = NotificationService.create_patient_booking_completed_notification(
            patient_name, nurse_name, start_time, end_time, notes
        )

        # Send notifications
        if nurse_email:
            await send_notification_amqp(
                nurse_email,
                "Booking Completed",
                nurse_notification
            )

        if patient_email:
            await send_notification_amqp(
                patient_email,
                "Your booking has been completed",
                patient_notification
            )

    async def check_completed_bookings(self):
        """Check for pending bookings that have passed their end time and mark them as completed."""
        try:
            logger.info("Running scheduled task to check for completed bookings")

            # Get all pending bookings
            pending_bookings = await self.booking_service.get_all_pending_bookings()

            # Get current time
            current_time = datetime.now()
            completed_count = 0

            for booking in pending_bookings:
                # Extract booking data
                booking_id = booking.get('id')
                fields = booking.get('fields', {})

                # Extract necessary fields
                nurse_id = fields.get('NID', {}).get('stringValue')
                patient_id = fields.get('PID', {}).get('stringValue')
                start_time = fields.get('StartTime', {}).get('timestampValue', '')
                end_time_str = fields.get('EndTime', {}).get('timestampValue', '')
                notes = fields.get('Notes', {}).get('stringValue', '')

                if not end_time_str:
                    logger.warning(f"Booking {booking_id} missing end time")
                    continue

                # Parse end time (assuming ISO format)
                try:
                    end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))

                    # Check if end time has passed
                    if current_time > end_time:
                        logger.info(f"Marking booking {booking_id} as completed (end time: {end_time_str})")

                        # Update booking status to completed
                        await self.booking_service.update_booking_status(booking_id, "Completed")

                        # Increase nurse credit score
                        try:
                            await self.nurse_service.update_nurse_credit_score(
                                nurse_id,
                                self.completion_credit_bonus,
                                f"Automatic booking completion bonus: Booking ID {booking_id}"
                            )
                            logger.info(f"Updated nurse {nurse_id} credit score: +{self.completion_credit_bonus} points")
                        except Exception as credit_error:
                            logger.error(f"Error updating credit score for booking {booking_id}: {credit_error}")
                            # Continue processing even if credit update fails

                        # Get nurse and patient details for notifications
                        try:
                            nurse = await self.nurse_service.get_nurse(nurse_id)
                            patient_data = await self.patient_service.get_patient(patient_id)
                            patient = patient_data.get('patient', {})

                            # Send completion notifications
                            await self._send_completion_notifications(
                                nurse.get('name', 'Nurse'),
                                nurse.get('email', ''),
                                patient.get('PatientName', 'Patient'),
                                patient.get('Email', ''),
                                patient.get('Location', 'Unknown'),
                                start_time,
                                end_time_str,
                                notes
                            )
                        except Exception as notify_error:
                            logger.error(f"Error sending completion notifications for booking {booking_id}: {notify_error}")
                            # Continue processing other bookings even if notification fails

                        completed_count += 1
                except (ValueError, TypeError) as e:
                    logger.error(f"Error parsing end time for booking {booking_id}: {e}")
                    continue

            logger.info(f"Completed {completed_count} bookings")
            return completed_count

        except Exception as e:
            logger.error(f"Error in check_completed_bookings: {str(e)}")
            return 0


# Create Flask app and blueprint
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for all routes
booking_bp = Blueprint('booking_composite', __name__, url_prefix='/v1')


# Initialize services and scheduler
service_config = Config.get_service_config()
booking_manager = BookingManager(service_config)
scheduler = BackgroundScheduler()


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


@booking_bp.route('/ManualCheckCompletedBookings', methods=['POST'])
@async_route
async def manual_check_completed_bookings():
    """Endpoint to manually trigger the check for completed bookings."""
    try:
        completed_count = await booking_manager.check_completed_bookings()

        return jsonify(api_response(
            success=True,
            message=f'Successfully checked and updated {completed_count} completed bookings'
        ))
    except Exception as e:
        logger.error(f"Error in manual_check_completed_bookings: {str(e)}")
        return jsonify(api_response(
            success=False,
            error='Internal server error',
            status_code=500
        ))


@booking_bp.route('/CompleteBooking/<booking_id>', methods=['POST'])
@async_route
async def complete_booking(booking_id: str):
    """Endpoint to manually complete a specific booking."""
    try:
        if not booking_id:
            return jsonify(api_response(
                success=False,
                error='Missing booking ID',
                status_code=400
            ))

        result = await booking_manager.complete_booking(booking_id)

        return jsonify(api_response(
            success=True,
            message=f'Successfully completed booking {booking_id}',
            **result
        ))
    except ApiError as e:
        return jsonify(api_response(
            success=False,
            error=e.message,
            status_code=e.status_code
        ))
    except Exception as e:
        logger.error(f"Error in complete_booking endpoint: {str(e)}")
        return jsonify(api_response(
            success=False,
            error='Internal server error',
            status_code=500
        ))


# Function to run the scheduler task
def run_check_completed_bookings():
    asyncio.run(booking_manager.check_completed_bookings())


# Register blueprint
app.register_blueprint(booking_bp)

if __name__ == '__main__':
    # Load the API key from environment variable
    api_key = service_config.API_KEY
    if not api_key:
        logger.warning("API_KEY environment variable not set. Service may not function correctly.")

    # Set up the scheduler to run every 5 minutes
    scheduler.add_job(run_check_completed_bookings, 'interval', minutes=5)
    scheduler.start()
    logger.info("Started scheduler to check for completed bookings every 5 minutes")

    try:
        # Run the Flask app
        app.run(
            debug=os.environ.get('DEBUG', 'True').lower() == 'true',
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5008))
        )
    except (KeyboardInterrupt, SystemExit):
        # Shut down the scheduler when exiting
        scheduler.shutdown()