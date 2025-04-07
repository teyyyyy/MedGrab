import requests
import datetime
from os import environ
from dotenv import load_dotenv
from amqp_setup import send_notification_amqp
from flask import Flask, request, Blueprint
from ariadne import QueryType, MutationType, gql, make_executable_schema
from ariadne.asgi import GraphQL
from flask_cors import CORS
from io import BytesIO
from xhtml2pdf import pisa
import base64

app = Flask(__name__)
CORS(app)


# Load environment variables
load_dotenv()

# Service URLs - Update these based on your deployment
NURSE_SERVICE_URL= environ.get('NURSE_SERVICE_URL')
BOOKING_SERVICE_URL= environ.get('BOOKING_SERVICE_URL')
REPORT_SERVICE_URL= environ.get('REPORT_SERVICE_URL')


generate_report_bp = Blueprint('generate_report', __name__)


def generate_pdf_report(html_content):
    """Convert HTML report to PDF"""
    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
    
    if pisa_status.err:
        print("Error generating PDF")
        return None
    
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()

# Helper functions
def get_nurse_details(nid):
    """Get nurse details from nurse service"""
    try:
        print(f"Calling Nurse Service at: {NURSE_SERVICE_URL}/{nid}")
        response = requests.get(f"{NURSE_SERVICE_URL}/{nid}")
        
        if response.status_code == 200:
            return response.json()
        print(f"Nurse service returned status code {response.status_code}")
        return None
    except requests.RequestException as e:
        print(f"Error in get_nurse_details: {e}")
        return None

def get_bookings_for_month(nid, year, month):
    """Get all bookings for a nurse in a specific month"""
    try:
        # First get all bookings for the nurse
        response = requests.get(f"{BOOKING_SERVICE_URL}/GetBookingsForNurse/{nid}")
        
        if response.status_code == 200:
            all_bookings = response.json().get('Bookings', [])
            filtered_bookings = []
            
            # Filter bookings by month locally
            for booking in all_bookings:
                try:
                    # Get the start time from booking fields
                    start_time_str = booking.get('fields', {}).get('StartTime', {}).get('timestampValue', '')
                    if not start_time_str:
                        continue
                        
                    # Parse the timestamp
                    start_time = datetime.datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    
                    # Check if it's in the requested month/year
                    if start_time.year == year and start_time.month == month:
                        # Store both the booking and its datetime for sorting
                        filtered_bookings.append({
                            'booking': booking,
                            'start_time': start_time
                        })
                        
                except (ValueError, TypeError) as e:
                    print(f"Error parsing booking time: {e}")
                    continue
            
            # Sort bookings by start time
            filtered_bookings.sort(key=lambda x: x['start_time'])
            
            print(f"Found {len(filtered_bookings)} bookings for {month}/{year}")
            # Return just the booking objects in sorted order
            return [item['booking'] for item in filtered_bookings]
            
        print(f"Booking service returned status code {response.status_code}")
        return []
    except requests.RequestException as e:
        print(f"Error in get_bookings_for_month: {e}")
        return []

    
def calculate_earnings(bookings):
    """Calculate total earnings from completed bookings"""
    total_earned = 0.0
    for booking in bookings:
        fields = booking.get('fields', {})
        status = fields.get('Status', {}).get('stringValue', '').lower()
        if status == 'completed':
            payment = fields.get('PaymentAmt', {}).get('doubleValue', 0.0)
            try:
                total_earned += float(payment)
            except (ValueError, TypeError):
                pass
    return total_earned

def calculate_hours_worked(bookings):
    """Calculate total hours worked from bookings"""
    total_hours = 0
    completed_bookings = []
    
    print(f"Total bookings received: {len(bookings)}")
    
    for booking in bookings:
        # Access the nested 'fields' structure
        fields = booking.get('fields', {})
        status = fields.get('Status', {}).get('stringValue', '').lower()
        
        print(f"Booking status: {status}")
        
        if status == 'completed':
            completed_bookings.append(booking)
            
            # Parse start and end times
            try:
                start_time_str = fields.get('StartTime', {}).get('timestampValue', '')
                end_time_str = fields.get('EndTime', {}).get('timestampValue', '')
                
                print(f"Start time: {start_time_str}")
                print(f"End time: {end_time_str}")
                
                if start_time_str and end_time_str:
                    # Convert timestamps to datetime objects
                    start_time = datetime.datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    end_time = datetime.datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                    
                    # Calculate duration in hours
                    duration = (end_time - start_time).total_seconds() / 3600
                    total_hours += duration
                    
                    print(f"Duration for this booking: {duration} hours")
            except (ValueError, TypeError) as e:
                print(f"Error parsing time: {e}")
                pass
    
    print(f"Total hours calculated: {total_hours}")
    return total_hours, completed_bookings

def update_credit_score(nid, credit_change, reason):
    """Update nurse credit score"""
    try:
        data = {
            "creditChange": credit_change,
            "reason": reason
        }
        response = requests.put(f"{NURSE_SERVICE_URL}/{nid}/credit", json=data)
        return response.json() if response.status_code == 200 else None
    except requests.RequestException:
        return None

def store_report(nid, report_month, report_content, hours_worked, total_bookings):
    """Store report in the database"""
    try:
        data = {
            "NID": nid,
            "reportMonth": report_month,
            "reportContent": report_content,
            "hoursWorked": hours_worked,
            "totalBookings": total_bookings
        }
        response = requests.post(REPORT_SERVICE_URL, json=data)
        return response.json() if response.status_code == 200 else None
    except requests.RequestException:
        return None

def check_suspension_status(nid):
    """Check if a nurse is currently suspended"""
    try:
        nurse_data = get_nurse_details(nid)
        if not nurse_data:
            return None, None
            
        current_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M+08:00')
        
        # Check suspension status directly from nurse document
        is_suspended = nurse_data.get('isSuspended', False)
        suspension_end_date = nurse_data.get('suspensionEndDate')
        
        # If current time is past the suspension end date, the nurse is no longer suspended
        if is_suspended and suspension_end_date:
            if current_time >= suspension_end_date:
                # Update the nurse's suspension status
                requests.put(f"{NURSE_SERVICE_URL}/{nid}", json={
                    'isSuspended': False,
                    'suspensionEndDate': None
                })
                return False, None
                
            return True, suspension_end_date
            
        return False, None
    except requests.RequestException:
        return False, None

def format_date(date_str):
    """Format ISO date string to a more readable format (DD-MM-YYYY HH:MM)"""
    if not date_str:
        return "N/A"
    try:
        # Parse the ISO date string
        dt = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        # Format it in a more readable way
        return dt.strftime('%d-%m-%Y %H:%M')
    except (ValueError, TypeError):
        return date_str

def generate_report_content(nid, month_str, bookings, hours_worked, nurse_data):
    """Generate the HTML report content"""
    year, month = month_str.split('-')
    month_name = datetime.datetime(int(year), int(month), 1).strftime('%B')
    
    total_bookings = len(bookings)
    completed_bookings = sum(1 for b in bookings if b.get('fields', {}).get('Status', {}).get('stringValue', '').lower() == 'completed')
    cancelled_bookings = sum(1 for b in bookings if b.get('fields', {}).get('Status', {}).get('stringValue', '').lower() == 'cancelled')
    total_earned = calculate_earnings(bookings)
    
    cancellation_rate = (cancelled_bookings / total_bookings * 100) if total_bookings > 0 else 0
    avg_session = hours_worked / completed_bookings if completed_bookings > 0 else 0
    
    credit_score = nurse_data.get('creditScore', 100)
    is_warned = nurse_data.get('isWarned', False)
    is_suspended = nurse_data.get('isSuspended', False)
    suspension_end_date = format_date(nurse_data.get('suspensionEndDate'))
    
    # Generate booking rows
    booking_rows = []
    for b in bookings:
        fields = b.get('fields', {})
        status = fields.get('Status', {}).get('stringValue', 'Unknown').lower()
        
        start_time_str = fields.get('StartTime', {}).get('timestampValue', '')
        end_time_str = fields.get('EndTime', {}).get('timestampValue', '')
        
        # Parse and format the date/time
        try:
            if start_time_str:
                start_time = datetime.datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                # Convert to UTC+8 (Singapore time)
                start_time = start_time.astimezone(datetime.timezone(datetime.timedelta(hours=8)))
                date_part = start_time.strftime('%d %B %Y')  # "05 April 2025"
                time_part = start_time.strftime('%H:%M')      # "00:45"
            else:
                date_part = 'N/A'
                time_part = 'N/A'
        except (ValueError, TypeError):
            date_part = 'Invalid Date'
            time_part = 'Invalid Time'
        
        # Calculate duration
        duration = 0.0
        if start_time_str and end_time_str:
            try:
                start = datetime.datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                end = datetime.datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                duration = (end - start).total_seconds() / 3600  # in hours
            except ValueError:
                pass
        
        reason = fields.get('cancellationReason', {}).get('stringValue', '-') if status == 'cancelled' else '-'
        
        booking_rows.append(
            f'<tr class="{"highlight" if status == "cancelled" else ""}">'
            f'<td>{date_part}</td>'
            f'<td>{time_part}</td>'
            f'<td>{duration:.1f} hours</td>'
            f'<td>{status.capitalize()}</td>'
            f'<td>{reason}</td>'
            '</tr>'
        )
    
    # Build HTML content using string concatenation instead of multi-line f-string
    html_parts = [
        '<html>',
        '<head>',
        '<style>',
        'body { font-family: Arial, sans-serif; margin: 40px; }',
        'h1 { color: #2c3e50; }',
        '.summary { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }',
        '.warning { color: #e74c3c; }',
        '.good { color: #27ae60; }',
        'table { width: 100%; border-collapse: collapse; margin-top: 20px; }',
        'th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }',
        'th { background-color: #f2f2f2; }',
        '.highlight { background-color: #f1c40f; font-weight: bold; }',
        '</style>',
        '</head>',
        '<body>',
        f'<h1>Monthly Activity Report - {month_name} {year}</h1>',
        '<div class="summary">',
        f'<h2>Summary for {nurse_data.get("name", "Unknown Nurse")}</h2>',
        f'<p>Report Period: {month_name} {year}</p>',
        f'<p>Total Bookings: {total_bookings}</p>',
        f'<p>Completed Sessions: {completed_bookings}</p>',
        f'<p>Cancelled Sessions: <span class="{"warning" if cancelled_bookings > 2 else ""}">{cancelled_bookings}</span></p>',
        f'<p>Cancellation Rate: <span class="{"warning" if cancellation_rate > 30 else ""}">{cancellation_rate:.1f}%</span></p>',
        f'<p>Total Hours Worked: <span class="{"warning" if hours_worked > 60 else ""}">{hours_worked:.1f} hours</span></p>',
        f'<p>Total Earnings: ${total_earned:.2f}</p>',  
        f'<p>Average Session Duration: {avg_session:.1f} hours</p>',
        f'<p>Current Credit Score: <span class="{"warning" if credit_score < 40 else "good" if credit_score > 80 else ""}">{credit_score}</span></p>',
        '</div>'
    ]
    
    # Add warning/suspension messages if needed
    if is_warned:
        html_parts.extend([
            '<div class="warning">',
            '<h3>⚠️ Warning</h3>',
            '<p>Your credit score is low. Please be careful about cancellations.</p>',
            '</div>'
        ])
    
    if is_suspended:
        html_parts.extend([
            '<div class="warning">',
            '<h3>🚫 Account Suspension</h3>',
            '<p>Your account has been suspended for 1 month due to low credit score.</p>',
            '<p>During this period, you will not be shown in the nurse pool for new bookings.</p>',
            f'<p>Suspension end date: {suspension_end_date}</p>',
            '</div>'
        ])
    
    # Add activity details
    html_parts.extend([
        '<h2>Detailed Activity</h2>',
        f'{"<p>You have not completed any bookings this month.</p>" if completed_bookings == 0 else ""}',
        f"""{"<h3 class='warning'>High Cancellation Rate</h3>" if cancellation_rate > 30 else ""}""",
        f"""{"<p>You've cancelled " + str(cancelled_bookings) + " bookings this month. This affects your credit score and reliability rating.</p>" if cancelled_bookings > 2 else ""}""",
        f"""{"<h3 class='warning'>High Workload</h3>" if hours_worked > 60 else ""}""",
        f"""{"<p>You've worked " + f"{hours_worked:.1f}" + " hours this month. Consider taking adequate rest to maintain service quality.</p>" if hours_worked > 60 else ""}""",
        '<h3>Booking Details</h3>',
        '<table>',
        '<tr>',
        '<th>Date</th>',
        '<th>Time</th>',
        '<th>Duration</th>',
        '<th>Status</th>',
        '<th>Reason (if cancelled)</th>',
        '</tr>',
        ''.join(booking_rows),
        '</table>',
        '</body>',
        '</html>'
    ])
    
    return '\n'.join(html_parts)

def check_nurse_status(nid):
    """Check and update nurse warning/suspension status"""
    try:
        response = requests.post(f"{NURSE_SERVICE_URL}/{nid}/check-status")
        return response.json() if response.status_code == 200 else None
    except requests.RequestException as e:
        print(f"Error checking nurse status: {e}")
        return None

# Core function to generate a monthly report
async def _generate_monthly_report(nid, month):
    print(f"Starting report generation for nurse {nid}, month {month}")
    nurse_data = get_nurse_details(nid)
    print(f"Nurse data retrieved: {nurse_data is not None}")
    if not nurse_data:
        print(f"Nurse not found with ID: {nid}")
        return {"success": False, "message": "Nurse not found"}
    
    nurse_email = nurse_data.get('email')
    nurse_name = nurse_data.get('name')
    year, month_num = map(int, month.split('-'))
    bookings = get_bookings_for_month(nid, year, month_num)
    print(f"Bookings retrieved: {len(bookings)}")
    
    hours_worked, completed_bookings = calculate_hours_worked(bookings)
    total_earned = calculate_earnings(bookings)
    cancelled_bookings = sum(1 for b in bookings if b.get('fields', {}).get('Status', {}).get('stringValue', '').lower() == 'cancelled')
    total_bookings = len(bookings) if bookings else 0
    cancellation_rate = (cancelled_bookings / total_bookings * 100) if total_bookings > 0 else 0
    
    # Generate report content
    report_content = generate_report_content(nid, month, bookings, hours_worked, nurse_data)
    
    # Store report in database
    store_result = store_report(nid, month, report_content, hours_worked, total_bookings)
    
    if nurse_email:
        subject = f"Your MedGrab Monthly Report - {datetime.datetime.strptime(month, '%Y-%m').strftime('%B %Y')}"
        
        # Generate PDF
        pdf_content = generate_pdf_report(report_content) if report_content else None
        
        # Create email message
        message = f"""
        <html>
        <body>
            <p>Hi {nurse_name},</p>
            <p>Your monthly activity report for {datetime.datetime.strptime(month, '%Y-%m').strftime('%B %Y')} is attached.</p>
            
            <h3>Quick Summary:</h3>
            <ul>
                <li><strong>Total Hours Worked:</strong> {hours_worked:.1f} hours</li>
                <li><strong>Total Earnings:</strong> ${total_earned:.2f}</li>  <!-- NEW LINE -->
                <li><strong>Cancelled Bookings:</strong> {cancelled_bookings} ({cancellation_rate:.1f}% cancellation rate)</li>
                <li><strong>Current Credit Score:</strong> {nurse_data.get('creditScore', 100)}</li>
            </ul>
            
            {'<p style="color:red;"><strong>⚠️ High Workload Warning:</strong> You have worked over 60 hours this month. Please take care of your well-being.</p>' if hours_worked > 60 else ''}
            {'<p style="color:red;"><strong>⚠️ High Cancellation Rate:</strong> Your cancellation rate exceeds 30%. This affects your reliability score.</p>' if cancellation_rate > 30 else ''}
            
            <p>Please find the detailed report attached as a PDF.</p>
            <p>Thank you for your service.</p>
            <p>Best Regards,<br>MedGrab Team</p>
        </body>
        </html>
        """
        
        # Prepare notification data
        notification_data = {
            "to_email": nurse_email,
            "subject": subject,
            "message": message
        }

        if pdf_content:
            notification_data["attachment"] = pdf_content
            notification_data["attachment_name"] = f"MedGrab_Report_{month}.pdf"

        notification_result = await send_notification_amqp(**notification_data)
        print(f"Notification result: {notification_result}")
    
    return {
        "success": True, 
        "message": "Report generated successfully",
        "month": month,
        "nurseId": nid,
        "hours": hours_worked,
        "earnings": total_earned,
        "totalBookings": total_bookings,
        "cancellationRate": cancellation_rate
    }

# Define GraphQL schema
type_defs = gql("""
    type Query {
        ping: String!
    }
    
    type Mutation {
        generateReport(
            nurseId: ID!
            month: String!
            includeHours: Boolean = true
            includeEarnings: Boolean = true
            includeBookings: Boolean = false
        ): ReportResult!
    }
    
    type ReportResult {
        success: Boolean!
        message: String!
        reportLink: String
        month: String
        nurseId: ID
        hours: Float
        earnings: Float
        totalBookings: Int
        cancellationRate: Float
        isWarned: Boolean
        isSuspended: Boolean
        bookings: [Booking]
    }

    type Booking {
        date: String!
        status: String!
        duration: Float!
        payment: Float
    }
""")

# Create resolvers
query = QueryType()
mutation = MutationType()

@query.field("ping")
def resolve_ping(*_):
    return "GraphQL Report Service is running!"

@mutation.field("generateReport")
async def resolve_generate_report(_, info, nurseId, month, **kwargs):
    try:
        # First generate the full report (including email sending)
        full_result = await _generate_monthly_report(nurseId, month)
        if not full_result["success"]:
            return full_result

        # Then filter based on requested fields
        include_hours = kwargs.get("includeHours", True)
        include_earnings = kwargs.get("includeEarnings", True)
        include_bookings = kwargs.get("includeBookings", False)

        response = {
            "success": True,
            "message": full_result["message"],
            "month": full_result["month"],
            "nurseId": full_result["nurseId"],
            "cancellationRate": full_result["cancellationRate"]
        }

        if include_hours:
            response["hours"] = full_result["hours"]
        if include_earnings:
            response["earnings"] = full_result["earnings"]
        if include_bookings:
            # You'll need to modify _generate_monthly_report to return bookings
            response["bookings"] = []  # Add actual bookings data here

        return response

    except Exception as e:
        return {"success": False, "message": str(e)}

# Create executable schema
schema = make_executable_schema(type_defs, query, mutation)

# Create GraphQL app
graphql_app = GraphQL(schema)

# Add the GraphQL endpoint
@generate_report_bp.route("/graphql", methods=["GET", "POST"])
async def graphql_handler():
    # Get the request data
    request_data = request.get_data()
    
    # Get the query parameters
    query_params = {}
    for key, value in request.args.items():
        query_params[key] = value
    
    # Create the ASGI scope
    scope = {
        "type": "http",
        "path": request.path,
        "query_string": request.query_string,
        "headers": [(k.lower().encode('latin1'), v.encode('latin1')) for k, v in request.headers.items()],
        "method": request.method,
        "http_version": "1.1",
        "scheme": request.scheme,
        "client": ("127.0.0.1", 0),  # Placeholder
        "server": (request.host.split(':')[0], int(request.host.split(':')[1]) if ':' in request.host else 80),
    }
    
    # Define receive function that returns the request body
    async def receive():
        return {"type": "http.request", "body": request_data, "more_body": False}
    
    # Define send function to collect response
    response_start = {}
    response_body = []
    
    async def send(message):
        if message["type"] == "http.response.start":
            response_start.update({
                "status": message["status"],
                "headers": message["headers"]
            })
        elif message["type"] == "http.response.body":
            response_body.append(message.get("body", b""))
    
    # Process with GraphQL
    await graphql_app(scope, receive, send)
    
    # Convert to Flask response
    from flask import Response
    headers = {}
    for key, value in response_start.get("headers", []):
        headers[key.decode('latin1')] = value.decode('latin1')
    
    status = response_start.get("status", 200)
    body = b"".join(response_body)
    
    return Response(body, status=status, headers=headers)

app.register_blueprint(generate_report_bp, url_prefix='/api/generate_report')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)  
