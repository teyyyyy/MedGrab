from flask import Flask
from flask import Blueprint, request, jsonify
from flask_cors import CORS
import requests
import aio_pika
import json
import amqp_lib
from amqp_setup import send_notification_amqp

AMQP_HOST = 'localhost'
AMQP_PORT = 5672
EXCHANGE_NAME = 'medgrab_exchange'
EXCHANGE_TYPE = 'topic'
NOTIFICATION_ROUTING_KEY = 'notification.email'
NOTIFICATION_QUEUE = 'email_notifications'

amqp_connection = None
amqp_channel = None
exchange = None
booking_composite_bp = Blueprint('booking_composite', __name__)
main_url = 'https://personal-o6lh6n5u.outsystemscloud.com/MedGrabBookingAtomic/rest/v1/'
nurse_url = 'http://host.docker.internal:5003/'
patient_url = 'https://personal-eassd2ao.outsystemscloud.com/PatientAPI/rest/v2/'
apikey = "adf0fe5c19401034c4466875565bc6c62253eae1dd84d46fba4eeda2bd1a0c5549168bfefa2021f03df33e9eab0bbd8527f6586f79bb36e1be37bfabac288374756ae7b54a548be1f607408a479467bde1fce109f94fa8e151f875451483291f5ead011168c835409bfbda1f2c7781f6a94cdc75d2d33d99ee7486edd9e0f70746f7d7979798ffd473362a3968da6c618693a184a296ce344c7a4c725b5db0bf72025d91b1c0e2186621b9cc7c482f72035b5bb12bfbda41e29ae25546e5f1e087d5f097d6680aef95c12c166f369c8a5911373c787baaaf620c06297c3839dd6c51719eaaff31b99df87512172c5140157acaf4439b7c13a0aecde2c5cb9643"

app = Flask(__name__)
CORS(app)

@booking_composite_bp.route('/MakeBooking', methods=['POST'])
async def make_booking():
    data = request.json

    NID = data.get('NID')
    PID = data.get('PID')
    StartTime = data.get('StartTime')
    EndTime = data.get('EndTime')
    Notes = data.get('Notes')
    PaymentAmt = data.get('PaymentAmt')
    newBooking = {
        'NID': NID,
        'PID': PID,
        'StartTime': StartTime,
        'EndTime': EndTime,
        'Notes': Notes,
        'PaymentAmt': PaymentAmt,
        'APIKey': apikey
    }

    if not all([NID, PID, StartTime, EndTime, PaymentAmt]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    # get nurse full details
    response = requests.get(nurse_url+"api/nurses/"+NID)
    if(response.status_code != 200):
        return jsonify({'success': False, 'error': 'No nurse with that NID found'}), 400
    nurse = response.json();

    # get patient full details
    response = requests.get(patient_url+"GetPatient/"+PID)
    if(response.status_code != 200):
        return jsonify({'success': False, 'error': 'No patient with that NID found'}), 400
    responseJson = response.json()
    patient = responseJson.get('Patient')

    print(f"Calling Booking Service at: /CreateBooking/")
    response = requests.post(
        f"{main_url}/CreateBooking/",
        json=newBooking
    )

    message = f"""
            <html>
            <body>
                <p>Hi {nurse.get('name')},</p>
                <p>There is a new booking for you.</p>
                <hr>
                <h3>Summary:</h3>
                <ul>
                    <li><strong>Start time:</strong> {StartTime}</li>
                    <li><strong>End time:</strong> {EndTime}</li>
                    <li><strong>Location:</strong> {patient.get('Location')}</li>
                    <li><strong>Notes:</strong> {Notes}</li>
                </ul>

                <p><strong>Please respond to the request within 24 hours:</strong></p>

                <p>Thank you for your service.</p>
                <p>Best Regards,<br>MedGrab Team</p>
            </body>
            </html>
            """
    print(f"Calling Notification Service")
    not_result = await send_notification_amqp(nurse.get('email'), "New booking for you", message)

    return jsonify({
        'success': True,
        'message': 'Booking made successfully'
    })
@booking_composite_bp.route('/AcceptBooking', methods=['POST'])
def accept_booking():
    data = request.json

    BID = data.get('bid')

    print(f"Calling Booking Service at: /GetBooking/{BID}")
    response = requests.get(
        f"{main_url}/GetBooking/{BID}"
    )

    print(response.json())

    if(response.json()["StatusCode"] != 200):
        return jsonify({'success': False, 'error': response.json()["Message"]})

    print(f"Calling Booking Service at: /UpdateBookingStatus/")
    response = requests.patch(
        f"{main_url}/UpdateBookingStatus/{BID}/Accepted",
        json={
            'APIKey': apikey
        }
    )
    print(response.json())

    if(response.json()["StatusCode"] != 200):
        return jsonify({'success': False, 'error': response.json()["Message"]})

    return jsonify({
        'success': True,
        'message': 'Booking accepted'
    })

app.register_blueprint(booking_composite_bp, url_prefix='/v1')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5008)
