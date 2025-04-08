# MedGrab

Place .env in backend folder

Setting up kong:
cd backend
1. Run: chmod +x kong-basic-setup.sh
2. Run: ./kong-basic-setup.sh
Or just run the bat file

To run backend:
cd backend
docker compose up -d --build 

To run frontend:
cd frontend
npm i 
npm run dev

Login credentials:
- Nurse: aoyYvTwaARewJx4AOykh
- Patient: 8b42ukAoAOZdkfW7Ud5X


.env Structure
NURSE_FB_TYPE='service_account'
NURSE_FB_PROJECT_ID=''
NURSE_FB_PRIVATE_KEY_ID=''
NURSE_FB_PRIVATE_KEY='-----BEGIN PRIVATE KEY-----'
NURSE_FB_CLIENT_EMAIL=''
NURSE_FB_CLIENT_ID=''
NURSE_FB_AUTH_URI='https://accounts.google.com/o/oauth2/auth'
NURSE_FB_TOKEN_URI='https://oauth2.googleapis.com/token'
NURSE_FB_AUTH_PROVIDER_X509_CERT_URL='https://www.googleapis.com/oauth2/v1/certs'
NURSE_FB_CLIENT_X509_CERT_URL=''
NURSE_FB_UNIVERSE_DOMAIN='googleapis.com'

REPORT_FB_TYPE='service_account'
REPORT_FB_PROJECT_ID=''
REPORT_FB_PRIVATE_KEY_ID=''
REPORT_FB_PRIVATE_KEY='-----BEGIN PRIVATE KEY-----'
REPORT_FB_CLIENT_EMAIL=''
REPORT_FB_CLIENT_ID=''
REPORT_FB_AUTH_URI='https://accounts.google.com/o/oauth2/auth'
REPORT_FB_TOKEN_URI='https://oauth2.googleapis.com/token'
REPORT_FB_AUTH_PROVIDER_X509_CERT_URL='https://www.googleapis.com/oauth2/v1/certs'
REPORT_FB_CLIENT_X509_CERT_URL=''
REPORT_FB_UNIVERSE_DOMAIN='googleapis.com'

AMQP_HOST='medgrab_rabbitmq'
AMQP_PORT='5672'

BOOKING_ATOMIC_MAIN_URL=''
STRIPE_SERVICE_URL='http://stripe_service:5010/'
BOOKING_NURSE_ATOMIC_URL='http://nurse_service:5003/'
NURSE_ATOMIC_URL='http://nurse_service:5003/api/nurses/'
PATIENT_ATOMIC_URL=''
BOOKING_API_KEY=''

STRIPE_SECRET_KEY=sk_test_
STRIPE_PUBLISHABLE_KEY=pk_test_

export SENDGRID_API_KEY='SG.'
