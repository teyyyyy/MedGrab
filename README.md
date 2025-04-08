# MedGrab - Nurse Booking System

MedGrab is a fullstack application for booking medical professionals, connecting patients with nurses through a streamlined digital platform.

## What's This Bloody Thing Do?

- Patients can book appointments with available nurses
- Nurses can manage their schedules and view bookings
- Secure payment processing through Stripe
- Email notifications via SendGrid
- Microservice architecture with Kong API Gateway

## Prerequisites

Before you start arsing about with the code, make sure you've got:

- Docker and Docker Compose
- Node.js (v16 or higher)
- npm or yarn
- Git

## Project Structure

```
medgrab/
├── backend/         # Microservices
│   └── ...
└── frontend/        # Vue frontend application
```

## Getting Started

### Environment Setup

1. Create a `.env` file in the `backend` folder following the structure below
2. Replace the placeholder values with your actual credentials

### Setting Up Kong API Gateway

```bash
cd backend
chmod +x kong-basic-setup.sh
./kong-basic-setup.sh
```

Or if you're on Windows:
```bash
cd backend
kong-basic-setup.bat
```

### Running Backend Services

```bash
cd backend
docker compose up -d --build
```

### Running Frontend

```bash
cd frontend
npm install
npm run dev
```

## Accessing the Application

Once everything is up and running:
- Frontend: http://localhost:5173/
- Backend API: http://localhost:8000/

## Testing Credentials

For development and testing purposes only:
- **Nurse Login**: aoyYvTwaARewJx4AOykh
- **Patient Login**: 8b42ukAoAOZdkfW7Ud5X

⚠️ **IMPORTANT**: Change these credentials in production!

## Environment Variables

Create a `.env` file in the backend directory with the following structure:

```
# Firebase Configuration for Nurse Service
NURSE_FB_TYPE='service_account'
NURSE_FB_PROJECT_ID='your-project-id'
NURSE_FB_PRIVATE_KEY_ID='your-key-id'
NURSE_FB_PRIVATE_KEY='-----BEGIN PRIVATE KEY-----\nyour-private-key-here\n-----END PRIVATE KEY-----\n'
NURSE_FB_CLIENT_EMAIL='your-client-email'
NURSE_FB_CLIENT_ID='your-client-id'
NURSE_FB_AUTH_URI='https://accounts.google.com/o/oauth2/auth'
NURSE_FB_TOKEN_URI='https://oauth2.googleapis.com/token'
NURSE_FB_AUTH_PROVIDER_X509_CERT_URL='https://www.googleapis.com/oauth2/v1/certs'
NURSE_FB_CLIENT_X509_CERT_URL='your-cert-url'
NURSE_FB_UNIVERSE_DOMAIN='googleapis.com'

# Firebase Configuration for Report Service
REPORT_FB_TYPE='service_account'
REPORT_FB_PROJECT_ID='your-project-id'
REPORT_FB_PRIVATE_KEY_ID='your-key-id'
REPORT_FB_PRIVATE_KEY='-----BEGIN PRIVATE KEY-----\nyour-private-key-here\n-----END PRIVATE KEY-----\n'
REPORT_FB_CLIENT_EMAIL='your-client-email'
REPORT_FB_CLIENT_ID='your-client-id'
REPORT_FB_AUTH_URI='https://accounts.google.com/o/oauth2/auth'
REPORT_FB_TOKEN_URI='https://oauth2.googleapis.com/token'
REPORT_FB_AUTH_PROVIDER_X509_CERT_URL='https://www.googleapis.com/oauth2/v1/certs'
REPORT_FB_CLIENT_X509_CERT_URL='your-cert-url'
REPORT_FB_UNIVERSE_DOMAIN='googleapis.com'

# RabbitMQ Configuration
AMQP_HOST='medgrab_rabbitmq'
AMQP_PORT='5672'

# Service URLs
BOOKING_ATOMIC_MAIN_URL='your-booking-url'
STRIPE_SERVICE_URL='http://stripe_service:5010/'
BOOKING_NURSE_ATOMIC_URL='http://nurse_service:5003/'
NURSE_ATOMIC_URL='http://nurse_service:5003/api/nurses/'
PATIENT_ATOMIC_URL='your-patient-url'
BOOKING_API_KEY='your-api-key'

# Stripe Configuration
STRIPE_SECRET_KEY='sk_test_your_key'
STRIPE_PUBLISHABLE_KEY='pk_test_your_key'

# SendGrid
SENDGRID_API_KEY='SG.your_key'
```

## Troubleshooting

### Common Issues
- **Kong not starting**: Check if ports 8000 and 8001 are already in use
- **Connection to RabbitMQ fails**: Ensure RabbitMQ container is running
- **Firebase authentication errors**: Verify your Firebase credentials in .env

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b new-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin new-feature`
5. Submit a pull request

## License

[MIT License](LICENSE)