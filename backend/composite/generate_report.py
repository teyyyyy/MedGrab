import requests
import datetime
from os import environ
from dotenv import load_dotenv
from amqp_setup import send_notification_amqp
from flask import Flask, request, Blueprint
from ariadne import QueryType, MutationType, gql, make_executable_schema
from ariadne.asgi import GraphQL
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


# Load environment variables
load_dotenv()

# Service URLs - Update these based on your deployment
NURSE_SERVICE_URL= environ.get('NURSE_SERVICE_URL')
BOOKING_SERVICE_URL= environ.get('BOOKING_SERVICE_URL')
REPORT_SERVICE_URL= environ.get('REPORT_SERVICE_URL')


generate_report_bp = Blueprint('generate_report', __name__)

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
        # Format dates for filter
        start_date = f"{year}-{month:02d}-01T00:00+08:00"
        if month == 12:
            end_date = f"{year+1}-01-01T00:00+08:00"
        else:
            end_date = f"{year}-{month+1:02d}-01T00:00+08:00"
        
        print(f"Calling Booking Service at: {BOOKING_SERVICE_URL}/GetBookingsForNurse/{nid}")
        response = requests.get(
            f"{BOOKING_SERVICE_URL}/GetBookingsForNurse/{nid}",
            params={"startAfter": start_date, "endBefore": end_date}
        )
        
        if response.status_code == 200:
            # Parse the response JSON
            response_data = response.json()
            
            # Extract the 'Bookings' array
            bookings = response_data.get('Bookings', [])
            return bookings
        
        print(f"Booking service returned status code {response.status_code}")
        return []
    except requests.RequestException as e:
        print(f"Error in get_bookings_for_month: {e}")
        return []

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
        
        start_time = fields.get('StartTime', {}).get('timestampValue', '')
        end_time = fields.get('EndTime', {}).get('timestampValue', '')
        
        date_part = start_time.split('T')[0] if start_time else 'N/A'
        time_part = start_time.split('T')[1].split('.')[0] if start_time else 'N/A'
        
        duration = 0.0
        if start_time and end_time:
            try:
                start = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end = datetime.datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                duration = (end - start).total_seconds() / 3600
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
    hours_worked, _ = calculate_hours_worked(bookings)
    cancelled_bookings = sum(1 for b in bookings if b.get('fields', {}).get('Status', {}).get('stringValue', '').lower() == 'cancelled')
    total_bookings = len(bookings) if bookings else 0
    cancellation_rate = (cancelled_bookings / total_bookings * 100) if total_bookings > 0 else 0
    
    # Simplified suspension logic:
    if nurse_data.get('isSuspended', False):
        try:
            response = requests.put(f"{NURSE_SERVICE_URL}/{nid}", json={
                'isSuspended': False,
                'suspensionEndDate': None,
                'creditScore': 50
            })
            if response.status_code == 200:
                nurse_data['isSuspended'] = False
                nurse_data['suspensionEndDate'] = None
                nurse_data['creditScore'] = 50
                print(f"Suspension reset for nurse {nid} during monthly report generation")
        except requests.RequestException as e:
            print(f"Error resetting suspension status: {e}")
    else:
        status_result = check_nurse_status(nid)
        if status_result and status_result.get('success'):
            nurse_data['isWarned'] = status_result.get('isWarned', False)
            nurse_data['isSuspended'] = status_result.get('isSuspended', False)
            nurse_data['suspensionEndDate'] = status_result.get('suspensionEndDate')
    
    report_content = generate_report_content(nid, month, bookings, hours_worked, nurse_data)
    
    store_result = store_report(nid, month, report_content, hours_worked, total_bookings)
    
    if nurse_email:
        subject = f"Your MedGrab Monthly Report - {datetime.datetime.strptime(month, '%Y-%m').strftime('%B %Y')}"
        formatted_suspension_end = format_date(nurse_data.get('suspensionEndDate'))
        
        warning_message = ""
        if nurse_data.get('isWarned', False) and not nurse_data.get('isSuspended', False):
            warning_message = """
            <div style="margin-top: 20px; padding: 10px; background-color: #fff3cd; border-left: 5px solid #ffc107; color: #856404;">
                <h3 style="margin-top: 0;">⚠️ Credit Score Warning</h3>
                <p>Your credit score has dropped to {credit_score}, which is below our warning threshold of 30.</p>
                <p>Please be careful about cancellations to avoid account suspension.</p>
            </div>
            """.format(credit_score=nurse_data.get('creditScore', 0))
            
        suspension_message = ""
        if nurse_data.get('isSuspended', False) and nurse_data.get('suspensionEndDate'):
            suspension_message = """
            <div style="margin-top: 20px; padding: 10px; background-color: #f8d7da; border-left: 5px solid #dc3545; color: #721c24;">
                <h3 style="margin-top: 0;">🚫 Account Suspension Notice</h3>
                <p>Due to your credit score falling below the critical threshold of 20, your account has been suspended until {suspension_end}.</p>
                <p>During this period, you will not be shown in the nurse pool for new bookings.</p>
            </div>
            """.format(suspension_end=formatted_suspension_end)
        
        message = f"""
        <html>
        <body>
            <p>Hi {nurse_name},</p>
            <p>Your monthly activity report is now available.</p>
            <!-- Remove the link and include the actual report content -->
            <div style="margin: 20px 0;">
                {report_content}  <!-- This is the HTML report content -->
            </div>
            <hr>
            <h3>Summary:</h3>
            <ul>
                <li><strong>Total Hours Worked:</strong> {hours_worked:.1f} hours</li>
                <li><strong>Cancelled Bookings:</strong> {cancelled_bookings} ({cancellation_rate:.1f}% cancellation rate)</li>
                <li><strong>Current Credit Score:</strong> {nurse_data.get('creditScore', 100)}</li>
            </ul>
            
            {'<p style="color:red;"><strong>⚠️ High Workload Warning:</strong> You have worked over 60 hours this month. Please take care of your well-being.</p>' if hours_worked > 60 else ''}
            {'<p style="color:red;"><strong>⚠️ High Cancellation Rate:</strong> Your cancellation rate exceeds 30%. This affects your reliability score.</p>' if cancellation_rate > 30 else ''}
            
            {warning_message}
            {suspension_message}
            
            <p>Thank you for your service.</p>
            <p>Best Regards,<br>MedGrab Team</p>
        </body>
        </html>
        """
        
        notification_result = await send_notification_amqp(nurse_email, subject, message)
        print(f"Notification result: {notification_result}")
    
    print(f"Report generation completed successfully")
    return {
        "success": True, 
        "message": "Report generated and email queued for delivery.",
        "month": month,
        "nurseId": nid,
        "hours": hours_worked,
        "totalBookings": total_bookings,
        "cancellationRate": cancellation_rate,
        "isWarned": nurse_data.get('isWarned', False),
        "isSuspended": nurse_data.get('isSuspended', False)
    }

# Define GraphQL schema
type_defs = gql("""
    type Query {
        ping: String!
    }
    
    type Mutation {
        generateReport(nurseId: ID!, month: String!): ReportResult!
    }
    
    type ReportResult {
        success: Boolean!
        message: String!
        reportLink: String
        month: String
        nurseId: ID
        hours: Float
        totalBookings: Int
        cancellationRate: Float
        isWarned: Boolean
        isSuspended: Boolean
    }
""")

# Create resolvers
query = QueryType()
mutation = MutationType()

@query.field("ping")
def resolve_ping(*_):
    return "GraphQL Report Service is running!"

@mutation.field("generateReport")
async def resolve_generate_report(*_, nurseId, month):
    try:
        result = await _generate_monthly_report(nurseId, month)
        return result
    except Exception as e:
        print(f"Error in resolve_generate_report: {e}")
        return {"success": False, "message": str(e)}

# Create executable schema
schema = make_executable_schema(type_defs, query, mutation)

# Create GraphQL app
graphql_app = GraphQL(schema)

# Keep the existing REST endpoint for compatibility if needed
# @generate_report_bp.route("/generate/<nid>/<month>", methods=["POST"])
# async def generate_report_rest(nid, month):
#     try:
#         result = await _generate_monthly_report(nid, month)
#         return jsonify(result)
#     except Exception as e:
#         print(f"Error in generate_report_rest: {e}")
#         return jsonify({"success": False, "message": str(e)}), 500

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
