from flask import Flask, request, jsonify, render_template_string, redirect
from flask_cors import CORS
import stripe
import os
import uuid
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Get Stripe API keys from environment variables
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')


@app.route('/create-payment-session', methods=['POST'])
def create_payment_session():
    """
    Create a payment session that will be managed by the booking service.
    This endpoint is called by the booking service, not directly by the frontend.
    """
    try:
        data = request.json
        amount = float(data.get('amount', 0)) * 100  # Convert to cents
        booking_id = data.get('booking_id', str(uuid.uuid4()))
        patient_id = data.get('patient_id', '')
        nurse_id = data.get('nurse_id', '')
        success_callback_url = data.get('success_callback_url', '')
        booking_data = data.get('booking_data', {})

        # Store booking data as a JSON string in the session metadata
        booking_data_str = json.dumps(booking_data) if booking_data else '{}'

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
            success_url=f"{success_callback_url}?session_id={{CHECKOUT_SESSION_ID}}&booking_id={booking_id}",
            cancel_url=f"{success_callback_url}?session_id=cancelled&booking_id={booking_id}",
            metadata={
                'booking_id': booking_id,
                'patient_id': patient_id,
                'nurse_id': nurse_id,
                'booking_data': booking_data_str
            }
        )

        return jsonify({
            'success': True,
            'payment_url': checkout_session.url,
            'session_id': checkout_session.id
        })

    except Exception as e:
        print(f"Error creating payment session: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/payment-status/<session_id>', methods=['GET'])
def payment_status(session_id):
    """
    Check the status of a payment session.
    Used by the booking service to verify payment completion.
    """
    try:
        if session_id == 'cancelled':
            return jsonify({
                'success': False,
                'payment_status': 'cancelled',
                'metadata': {}
            })

        session = stripe.checkout.Session.retrieve(session_id)

        # Parse booking data from metadata
        metadata = session.metadata.copy()

        if 'booking_data' in metadata and metadata['booking_data']:
            try:
                booking_data = json.loads(metadata['booking_data'])
                metadata['booking_data'] = booking_data
            except json.JSONDecodeError:
                metadata['booking_data'] = {}

        return jsonify({
            'success': True,
            'payment_status': session.payment_status,
            'metadata': metadata
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/payment-page/<session_id>', methods=['GET'])
def payment_page(session_id):
    """
    Show a page that embeds Stripe checkout directly.
    This is used by the booking service to display the payment form.
    """
    try:
        if session_id == 'cancelled':
            return render_template_string(PAYMENT_CANCELLED)

        session = stripe.checkout.Session.retrieve(session_id)

        # Render the checkout page with the session ID
        return render_template_string(
            STRIPE_CHECKOUT_PAGE,
            session_id=session_id,
            stripe_publishable_key=os.environ.get('STRIPE_PUBLISHABLE_KEY')
        )
    except Exception as e:
        return render_template_string(
            PAYMENT_ERROR,
            error_message=str(e)
        )


# Templates for payment pages
STRIPE_CHECKOUT_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Complete Your Payment</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://js.stripe.com/v3/"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #f8f9fa;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 600px;
            margin: 2rem auto;
            padding: 2rem;
            background-color: #fff;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .header h1 {
            color: #333;
            font-size: 24px;
            margin-bottom: 0.5rem;
        }
        .header p {
            color: #666;
            font-size: 16px;
        }
        .secure-badge {
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 1rem 0;
            color: #4F566B;
            font-size: 14px;
        }
        .secure-badge svg {
            margin-right: 8px;
        }
        #payment-form {
            margin-top: 2rem;
        }
        .card-element {
            margin-bottom: 1.5rem;
            padding: 10px;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
        }
        .submit-button {
            background-color: #5469d4;
            color: #ffffff;
            border: none;
            padding: 12px 16px;
            border-radius: 4px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: all 0.2s ease;
        }
        .submit-button:hover {
            background-color: #4a5ac4;
        }
        .loading {
            display: none;
            text-align: center;
            margin-top: 1rem;
        }
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(0, 0, 0, 0.1);
            border-radius: 50%;
            border-top-color: #636678;
            animation: spin 1s ease-in-out infinite;
            margin-right: 10px;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .error-message {
            color: #dc3545;
            font-size: 14px;
            margin-top: 1rem;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Complete Your Payment</h1>
            <p>Secure payment processing for your medical appointment</p>
        </div>

        <div class="secure-badge">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
            Secure payment powered by Stripe
        </div>

        <form id="payment-form">
            <div id="card-element" class="card-element">
                <!-- Stripe Card Element will be inserted here -->
            </div>

            <button id="submit-button" class="submit-button">Pay Now</button>

            <div id="loading" class="loading">
                <div class="spinner"></div>
                Processing your payment...
            </div>

            <div id="error-message" class="error-message"></div>
        </form>
    </div>

    <script>
        // Initialize Stripe
        const stripe = Stripe('{{ stripe_publishable_key }}');
        const sessionId = '{{ session_id }}';

        // Create an instance of Elements
        const elements = stripe.elements();

        // Create Card Element
        const cardElement = elements.create('card', {
            style: {
                base: {
                    color: '#32325d',
                    fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
                    fontSmoothing: 'antialiased',
                    fontSize: '16px',
                    '::placeholder': {
                        color: '#aab7c4'
                    }
                },
                invalid: {
                    color: '#fa755a',
                    iconColor: '#fa755a'
                }
            }
        });

        // Mount the Card Element
        cardElement.mount('#card-element');

        // Handle form submission
        const form = document.getElementById('payment-form');
        const submitButton = document.getElementById('submit-button');
        const loadingElement = document.getElementById('loading');
        const errorElement = document.getElementById('error-message');

        form.addEventListener('submit', async (event) => {
            event.preventDefault();

            // Disable the submit button and show loading
            submitButton.disabled = true;
            loadingElement.style.display = 'block';
            errorElement.textContent = '';

            try {
                const { error } = await stripe.confirmCardPayment(sessionId, {
                    payment_method: {
                        card: cardElement,
                    }
                });

                if (error) {
                    // Show error to customer
                    errorElement.textContent = error.message;
                    submitButton.disabled = false;
                    loadingElement.style.display = 'none';
                } else {
                    // Payment succeeded, redirect to success page
                    window.location.href = '/payment-success?session_id=' + sessionId;
                }
            } catch (err) {
                errorElement.textContent = 'An unexpected error occurred. Please try again.';
                submitButton.disabled = false;
                loadingElement.style.display = 'none';
                console.error(err);
            }
        });
    </script>
</body>
</html>
"""

PAYMENT_ERROR = """
<!DOCTYPE html>
<html>
<head>
    <title>Payment Error</title>
    <style>
        body { font-family: sans-serif; text-align: center; padding: 40px; background-color: #fff1f2; }
        h1 { color: #be123c; }
        .message { margin: 20px 0; color: #374151; }
        .button { display: inline-block; background: #3b82f6; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Payment Error</h1>
    <p class="message">{{ error_message }}</p>
    <p><a href="javascript:window.close();" class="button">Close Window</a></p>
    <script>
        // Notify the opener window if it exists
        if (window.opener) {
            window.opener.postMessage({ 
                type: 'PAYMENT_ERROR', 
                success: false, 
                error: '{{ error_message }}'
            }, '*');
        }
    </script>
</body>
</html>
"""

PAYMENT_CANCELLED = """
<!DOCTYPE html>
<html>
<head>
    <title>Payment Cancelled</title>
    <style>
        body { font-family: sans-serif; text-align: center; padding: 40px; background-color: #fff1f2; }
        h1 { color: #be123c; }
        .message { margin: 20px 0; color: #374151; }
        .button { display: inline-block; background: #3b82f6; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Payment Cancelled</h1>
    <p class="message">Your payment was cancelled. You can try again when you're ready.</p>
    <p><a href="javascript:window.close();" class="button">Close Window</a></p>
    <script>
        // Notify the opener window if it exists
        if (window.opener) {
            window.opener.postMessage({ 
                type: 'PAYMENT_CANCELLED', 
                success: false, 
                status: 'cancelled'
            }, '*');
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5010))
    app.run(host='0.0.0.0', port=port, debug=True)