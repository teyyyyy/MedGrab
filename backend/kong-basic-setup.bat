@echo off
REM Full Kong setup script for MedGrab - maps all the bloody endpoints!

REM Wait for Kong to stop being a lazy git
echo Waiting for Kong to wake up...
:WAIT_LOOP
curl -s http://localhost:8001 > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  timeout /t 2 /nobreak > nul
  echo Still waiting for that slow Kong bastard...
  goto WAIT_LOOP
)
echo Kong admin API is finally up, about fuckin' time!

REM --- CREATE SERVICES ---
echo Creating all them services in Kong...

REM Booking Service
curl -s -X POST http://localhost:8001/services ^
  --data "name=booking-service" ^
  --data "url=http://booking_composite:5008"

REM Cancellation Service
curl -s -X POST http://localhost:8001/services ^
  --data "name=cancel-booking-service" ^
  --data "url=http://cancel_booking_service:5011"

REM Report Generation Service
curl -s -X POST http://localhost:8001/services ^
  --data "name=generate-report-service" ^
  --data "url=http://generate_report:5005"

REM Report Storage Service
curl -s -X POST http://localhost:8001/services ^
  --data "name=report-service" ^
  --data "url=http://report_service:5004"

REM Nurse Service
curl -s -X POST http://localhost:8001/services ^
  --data "name=nurse-service" ^
  --data "url=http://nurse_service:5003"

REM Notification Service
curl -s -X POST http://localhost:8001/services ^
  --data "name=notification-service" ^
  --data "url=http://notification_service:5002"

REM Stripe Payment Service
curl -s -X POST http://localhost:8001/services ^
  --data "name=stripe-service" ^
  --data "url=http://stripe_service:5010"

REM --- CREATE ROUTES ---
echo Setting up all them fancy routes...

REM --- BOOKING SERVICE ROUTES ---
echo Sorting out Booking Service routes...
REM Booking v1 routes (this matches all /v1 requests to booking service)
curl -s -X POST http://localhost:8001/services/booking-service/routes ^
  --data "name=booking-v1-route" ^
  --data "paths[]=/v1" ^
  --data "strip_path=false"

REM --- CANCELLATION SERVICE ROUTES ---
echo Setting up Cancellation Service routes...
curl -s -X POST http://localhost:8001/services/cancel-booking-service/routes ^
  --data "name=cancel-booking-route" ^
  --data "paths[]=/api/cancel-booking" ^
  --data "strip_path=false"

REM --- REPORT GENERATION SERVICE ROUTES ---
echo Sorting the Report Generation routes...
curl -s -X POST http://localhost:8001/services/generate-report-service/routes ^
  --data "name=generate-report-graphql-route" ^
  --data "paths[]=/api/generate_report/graphql" ^
  --data "strip_path=false"

REM --- REPORT STORAGE SERVICE ROUTES ---
echo Setting up Report Storage routes...
curl -s -X POST http://localhost:8001/services/report-service/routes ^
  --data "name=reports-route" ^
  --data "paths[]=/api/reports" ^
  --data "strip_path=false"

REM --- NURSE SERVICE ROUTES ---
echo Sorting out them Nurse Service routes...
curl -s -X POST http://localhost:8001/services/nurse-service/routes ^
  --data "name=nurses-route" ^
  --data "paths[]=/api/nurses" ^
  --data "strip_path=false"

REM --- NOTIFICATION SERVICE ROUTES ---
echo Setting up Notification Service routes...
curl -s -X POST http://localhost:8001/services/notification-service/routes ^
  --data "name=notifications-route" ^
  --data "paths[]=/api/notifications" ^
  --data "strip_path=false"

REM --- STRIPE PAYMENT SERVICE ROUTES ---
echo Sorting out Stripe Payment routes...
REM Create payment session
curl -s -X POST http://localhost:8001/services/stripe-service/routes ^
  --data "name=stripe-create-payment-route" ^
  --data "paths[]=/create-payment-session" ^
  --data "strip_path=false"

REM Payment status
curl -s -X POST http://localhost:8001/services/stripe-service/routes ^
  --data "name=stripe-payment-status-route" ^
  --data "paths[]=/payment-status" ^
  --data "strip_path=false"

REM Payment page
curl -s -X POST http://localhost:8001/services/stripe-service/routes ^
  --data "name=stripe-payment-page-route" ^
  --data "paths[]=/payment-page" ^
  --data "strip_path=false"

echo ===== ALL FUCKIN' DONE! =====
echo Yer Kong API Gateway is set up with all the routes, ya jammy git!
echo.
echo Now you can access ALL yer services through Kong at http://localhost:8000
echo Examples:
echo  - http://localhost:8000/api/nurses (Nurse Service)
echo  - http://localhost:8000/v1/MakeBooking (Booking Service)
echo  - http://localhost:8000/api/reports (Report Service)
echo  - http://localhost:8000/create-payment-session (Stripe Payment)