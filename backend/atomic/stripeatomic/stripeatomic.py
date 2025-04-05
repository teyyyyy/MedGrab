from flask import Flask, request, jsonify
from flask_cors import CORS
import stripe
import os
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Get Stripe API keys from environment variables
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')


@app.route('/create-payment-link', methods=['POST'])
def create_payment_link():
    try:
        data = request.json
        amount = float(data.get('amount', 0)) * 100  # Convert to cents
        booking_id = data.get('booking_id', str(uuid.uuid4()))
        patient_id = data.get('patient_id', '')
        nurse_id = data.get('nurse_id', '')

        # Create a Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'Healthcare Appointment ({booking_id})',
                        'description': 'Medical appointment booking'
                    },
                    'unit_amount': int(amount),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{request.host_url}payment-success?session_id={{CHECKOUT_SESSION_ID}}&booking_id={booking_id}",
            cancel_url=f"{request.host_url}payment-cancelled?booking_id={booking_id}",
            metadata={
                'booking_id': booking_id,
                'patient_id': patient_id,
                'nurse_id': nurse_id
            }
        )

        return jsonify({
            'success': True,
            'payment_url': checkout_session.url,
            'session_id': checkout_session.id
        })

    except Exception as e:
        print(f"Error creating payment link: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/payment-status/<session_id>', methods=['GET'])
def payment_status(session_id):
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return jsonify({
            'success': True,
            'payment_status': session.payment_status,
            'metadata': session.metadata
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/payment-success', methods=['GET'])
def payment_success():
    """Serve a page that closes itself and sends message to parent"""
    session_id = request.args.get('session_id')
    booking_id = request.args.get('booking_id')

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Successful</title>
        <style>
            body {{ font-family: sans-serif; text-align: center; padding: 40px; background-color: #f0f9ff; }}
            h1 {{ color: #0f766e; }}
            .message {{ margin: 20px 0; color: #374151; }}
            .spinner {{ margin: 20px auto; width: 40px; height: 40px; border: 4px solid #ddd; border-top: 4px solid #0f766e; border-radius: 50%; animation: spin 1s linear infinite; }}
            @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
        </style>
    </head>
    <body>
        <h1>Payment Successful!</h1>
        <p class="message">Your payment has been processed. This window will close automatically.</p>
        <div class="spinner"></div>
        <script>
            // Send message to parent window
            window.opener.postMessage({{
                type: 'PAYMENT_COMPLETED',
                sessionId: '{session_id}',
                bookingId: '{booking_id}',
                status: 'success'
            }}, '*');

            // Close this window after 2 seconds
            setTimeout(function() {{
                window.close();
            }}, 2000);
        </script>
    </body>
    </html>
    """
    return html


@app.route('/payment-cancelled', methods=['GET'])
def payment_cancelled():
    """Serve a page that closes itself and sends cancel message to parent"""
    booking_id = request.args.get('booking_id')

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Cancelled</title>
        <style>
            body {{ font-family: sans-serif; text-align: center; padding: 40px; background-color: #fff1f2; }}
            h1 {{ color: #be123c; }}
            .message {{ margin: 20px 0; color: #374151; }}
            .spinner {{ margin: 20px auto; width: 40px; height: 40px; border: 4px solid #ddd; border-top: 4px solid #be123c; border-radius: 50%; animation: spin 1s linear infinite; }}
            @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
        </style>
    </head>
    <body>
        <h1>Payment Cancelled</h1>
        <p class="message">Your payment was cancelled. This window will close automatically.</p>
        <div class="spinner"></div>
        <script>
            // Send message to parent window
            window.opener.postMessage({{
                type: 'PAYMENT_CANCELLED',
                bookingId: '{booking_id}',
                status: 'cancelled'
            }}, '*');

            // Close this window after 2 seconds
            setTimeout(function() {{
                window.close();
            }}, 2000);
        </script>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5010))
    app.run(host='0.0.0.0', port=port, debug=True)