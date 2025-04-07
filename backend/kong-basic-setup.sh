#!/bin/bash
# Full Kong setup script for MedGrab - maps all the bloody endpoints!

# Wait for Kong to stop being a lazy git
echo "Waiting for Kong to wake up..."
until curl -s http://localhost:8001 > /dev/null; do
  sleep 2
  echo "Still waiting for that slow Kong bastard..."
done
echo "Kong admin API is finally up, about fuckin' time!"

# --- CREATE SERVICES ---
echo "Creating all them services in Kong..."

# Booking Service
curl -s -X POST http://localhost:8001/services \
  --data "name=booking-service" \
  --data "url=http://booking_composite:5008"

# Cancellation Service
curl -s -X POST http://localhost:8001/services \
  --data "name=cancel-booking-service" \
  --data "url=http://cancel_booking_service:5011"

# Report Generation Service
curl -s -X POST http://localhost:8001/services \
  --data "name=generate-report-service" \
  --data "url=http://generate_report:5005"

# Report Storage Service
curl -s -X POST http://localhost:8001/services \
  --data "name=report-service" \
  --data "url=http://report_service:5004"

# Nurse Service
curl -s -X POST http://localhost:8001/services \
  --data "name=nurse-service" \
  --data "url=http://nurse_service:5003"

# Notification Service
curl -s -X POST http://localhost:8001/services \
  --data "name=notification-service" \
  --data "url=http://notification_service:5002"

# Stripe Payment Service
curl -s -X POST http://localhost:8001/services \
  --data "name=stripe-service" \
  --data "url=http://stripe_service:5010"

# --- CREATE ROUTES ---
echo "Setting up all them fancy routes..."

# --- BOOKING SERVICE ROUTES ---
echo "Sorting out Booking Service routes..."
# Booking v1 routes (this matches all /v1 requests to booking service)
curl -s -X POST http://localhost:8001/services/booking-service/routes \
  --data "name=booking-v1-route" \
  --data "paths[]=/v1" \
  --data "strip_path=false"

# --- CANCELLATION SERVICE ROUTES ---
echo "Setting up Cancellation Service routes..."
curl -s -X POST http://localhost:8001/services/cancel-booking-service/routes \
  --data "name=cancel-booking-route" \
  --data "paths[]=/api/cancel-booking" \
  --data "strip_path=false"

# --- REPORT GENERATION SERVICE ROUTES ---
echo "Sorting the Report Generation routes..."
curl -s -X POST http://localhost:8001/services/generate-report-service/routes \
  --data "name=generate-report-graphql-route" \
  --data "paths[]=/api/generate_report/graphql" \
  --data "strip_path=false"

# --- REPORT STORAGE SERVICE ROUTES ---
echo "Setting up Report Storage routes..."
curl -s -X POST http://localhost:8001/services/report-service/routes \
  --data "name=reports-route" \
  --data "paths[]=/api/reports" \
  --data "strip_path=false"

# --- NURSE SERVICE ROUTES ---
echo "Sorting out them Nurse Service routes..."
curl -s -X POST http://localhost:8001/services/nurse-service/routes \
  --data "name=nurses-route" \
  --data "paths[]=/api/nurses" \
  --data "strip_path=false"

# --- NOTIFICATION SERVICE ROUTES ---
echo "Setting up Notification Service routes..."
curl -s -X POST http://localhost:8001/services/notification-service/routes \
  --data "name=notifications-route" \
  --data "paths[]=/api/notifications" \
  --data "strip_path=false"

# --- STRIPE PAYMENT SERVICE ROUTES ---
echo "Sorting out Stripe Payment routes..."
# Create payment session
curl -s -X POST http://localhost:8001/services/stripe-service/routes \
  --data "name=stripe-create-payment-route" \
  --data "paths[]=/create-payment-session" \
  --data "strip_path=false"

# Payment status
curl -s -X POST http://localhost:8001/services/stripe-service/routes \
  --data "name=stripe-payment-status-route" \
  --data "paths[]=/payment-status" \
  --data "strip_path=false"

# Payment page
curl -s -X POST http://localhost:8001/services/stripe-service/routes \
  --data "name=stripe-payment-page-route" \
  --data "paths[]=/payment-page" \
  --data "strip_path=false"

echo "===== ALL FUCKIN' DONE! ====="
echo "Yer Kong API Gateway is set up with all the routes, ya jammy git!"
echo ""
echo "Now you can access ALL yer services through Kong at http://localhost:8000"
echo "Examples:"
echo " - http://localhost:8000/api/nurses (Nurse Service)"
echo " - http://localhost:8000/v1/MakeBooking (Booking Service)"
echo " - http://localhost:8000/api/reports (Report Service)"
echo " - http://localhost:8000/create-payment-session (Stripe Payment)"