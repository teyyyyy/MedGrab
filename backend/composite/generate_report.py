from flask import Flask, request, jsonify, Blueprint
from ariadne import ObjectType, QueryType, MutationType, gql, make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
import requests
import datetime
import os
from dotenv import load_dotenv
from rabbitmq.amqp_setup import setup_amqp, send_notification_amqp, close_amqp


# Load environment variables
load_dotenv()

# Service URLs - Update these based on your deployment
NURSE_SERVICE_URL='http://127.0.0.1:5003/api/nurses'
BOOKING_SERVICE_URL='https://personal-o6lh6n5u.outsystemscloud.com/MedGrabBookingAtomic/rest/v1'
NOTIFICATION_SERVICE_URL='http://127.0.0.1:5002/api/notifications/send-email'
REPORT_SERVICE_URL='http://127.0.0.1:5004/api/reports'


generate_report_bp = Blueprint('generate_report', __name__)

# Define GraphQL schema
type_defs = gql("""
    type Query {
        nurseMonthlyReport(nid: String!, month: String!): MonthlyReport
        listNurseReports(nid: String!): [ReportSummary]
    }
    
    type Mutation {
        generateMonthlyReport(nid: String!, month: String!): ReportResult
        checkCreditScore(nid: String!): CreditScoreResult
    }
    
    type MonthlyReport {
        nid: String!
        month: String!
        totalBookings: Int!
        completedBookings: Int!
        cancelledBookings: Int!
        cancellationRate: Float!
        totalHoursWorked: Float!
        averageSessionDuration: Float!
        creditScore: Int!
        isWarned: Boolean!
        isSuspended: Boolean!
        suspensionEndDate: String
        reportLink: String
    }
    
    type ReportSummary {
        rid: String!
        month: String!
        reportLink: String!
    }
    
    type ReportResult {
        success: Boolean!
        reportId: String
        reportLink: String
        message: String!
    }
    
    type CreditScoreResult {
        success: Boolean!
        nid: String!
        creditScore: Int!
        isWarned: Boolean!
        isSuspended: Boolean!
        suspensionEndDate: String
        message: String!
    }
""")

# Initialize types
query = QueryType()
mutation = MutationType()

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
    
nurse_id_mapping = {
    "4mZMSorpJygyYqgKEbCd": 123,  # Example mapping
    # Add more mappings as needed
}

def get_bookings_for_month(nid, year, month):
    """Get all bookings for a nurse in a specific month"""
    try:
        # Map the nurse ID to an integer
        if nid not in nurse_id_mapping:
            raise ValueError(f"Nurse ID {nid} not found in mapping")
        
        mapped_nid = nurse_id_mapping[nid]
        
        # Format dates for filter
        start_date = f"{year}-{month:02d}-01T00:00+08:00"
        if month == 12:
            end_date = f"{year+1}-01-01T00:00+08:00"
        else:
            end_date = f"{year}-{month+1:02d}-01T00:00+08:00"
        
        print(f"Calling Booking Service at: {BOOKING_SERVICE_URL}/GetBookingsForNurse/{mapped_nid}")
        response = requests.get(
            f"{BOOKING_SERVICE_URL}/GetBookingsForNurse/{mapped_nid}",
            params={"startAfter": start_date, "endBefore": end_date}
        )
        print(f"Response from Booking Service: {response.text}")  # Debug print
        
        if response.status_code == 200:
            # Parse the response JSON
            response_data = response.json()
            print(f"Parsed Booking Service Response: {response_data}")  # Debug print
            
            # Extract the 'Bookings' array
            bookings = response_data.get('Bookings', [])
            print(f"Extracted Bookings: {bookings}")  # Debug print
            return bookings
        
        print(f"Booking service returned status code {response.status_code}")
        return []
    except requests.RequestException as e:
        print(f"Error in get_bookings_for_month: {e}")
        return []

# def get_bookings_for_month(nid, year, month):
#     """Get all bookings for a nurse in a specific month"""
#     try:
#         # Format dates for filter
#         start_date = f"{year}-{month:02d}-01T00:00+08:00"
#         if month == 12:
#             end_date = f"{year+1}-01-01T00:00+08:00"
#         else:
#             end_date = f"{year}-{month+1:02d}-01T00:00+08:00"
#         print(f"Calling Booking Service at: {BOOKING_SERVICE_URL}/GetBookingsForNurse/{nid}")
#         response = requests.get(
#             f"{BOOKING_SERVICE_URL}/GetBookingsForNurse/{nid}",
#             params={"startAfter": start_date, "endBefore": end_date}
#         )
#         if response.status_code == 200:
#             return response.json()
#         print(f"Booking service returned status code {response.status_code}")
#         return []
#     except requests.RequestException as e:
#         print(f"Error in get_bookings_for_month: {e}")
#         return []

def calculate_hours_worked(bookings):
    """Calculate total hours worked from bookings"""
    total_hours = 0
    completed_bookings = []
    
    for booking in bookings:
        # Access the nested 'fields' structure
        fields = booking.get('fields', {})
        status = fields.get('Status', {}).get('stringValue', '').lower()
        
        if status == 'completed':
            completed_bookings.append(booking)
            
            # Parse start and end times
            try:
                start_time_str = fields.get('StartTime', {}).get('timestampValue', '')
                end_time_str = fields.get('EndTime', {}).get('timestampValue', '')
                
                if start_time_str and end_time_str:
                    # Convert timestamps to datetime objects
                    start_time = datetime.datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    end_time = datetime.datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                    
                    # Calculate duration in hours
                    duration = (end_time - start_time).total_seconds() / 3600
                    total_hours += duration
            except (ValueError, TypeError) as e:
                print(f"Error parsing time: {e}")
                pass
    
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

def store_report(nid, report_month, report_content, report_link):
    """Store report in the database"""
    try:
        data = {
            "NID": nid,
            "reportMonth": report_month,
            "reportContent": report_content,
            "reportLink": report_link
        }
        response = requests.post(REPORT_SERVICE_URL, json=data)
        return response.json() if response.status_code == 200 else None
    except requests.RequestException:
        return None

def get_stored_report(nid, month):
    """Get stored report from the report service"""
    try:
        response = requests.get(f"{REPORT_SERVICE_URL}/{nid}/{month}")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
        return None

def list_nurse_reports(nid):
    """List all reports for a nurse"""
    try:
        response = requests.get(f"{REPORT_SERVICE_URL}/{nid}")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.RequestException:
        return []

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
    is_warned = credit_score <= 30
    is_suspended = credit_score <= 20
    
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #2c3e50; }}
            .summary {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
            .warning {{ color: #e74c3c; }}
            .good {{ color: #27ae60; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
            .highlight {{ background-color: #f1c40f; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>Monthly Activity Report - {month_name} {year}</h1>
        <div class="summary">
            <h2>Summary for {nurse_data.get('name', 'Unknown Nurse')}</h2>
            <p>Report Period: {month_name} {year}</p>
            <p>Total Bookings: {total_bookings}</p>
            <p>Completed Sessions: {completed_bookings}</p>
            <p>Cancelled Sessions: <span class="{'warning' if cancelled_bookings > 2 else ''}">
                {cancelled_bookings}</span></p>
            <p>Cancellation Rate: <span class="{'warning' if cancellation_rate > 30 else ''}">
                {cancellation_rate:.1f}%</span></p>
            <p>Total Hours Worked: <span class="{'warning' if hours_worked > 60 else ''}">
                {hours_worked:.1f} hours</span></p>
            <p>Average Session Duration: {avg_session:.1f} hours</p>
            <p>Current Credit Score: <span class="{'warning' if credit_score < 40 else 'good' if credit_score > 80 else ''}">
                {credit_score}</span></p>
        </div>
        
        {'''<div class="warning">
            <h3>⚠️ Warning</h3>
            <p>Your credit score is low. Please be careful about cancellations.</p>
        </div>''' if is_warned else ''}
        
        {'''<div class="warning">
            <h3>🚫 Account Suspension</h3>
            <p>Your account has been suspended for 2 weeks due to low credit score.</p>
            <p>During this period, you will not be shown in the nurse pool for new bookings.</p>
        </div>''' if is_suspended else ''}
        
        <h2>Detailed Activity</h2>
        
        {'<p>You have not completed any bookings this month.</p>' if completed_bookings == 0 else ''}
        
        {'<h3 class="warning">High Cancellation Rate</h3>' if cancellation_rate > 30 else ''}
        {'<p>You\'ve cancelled {cancelled_bookings} bookings this month. This affects your credit score and reliability rating.</p>' if cancelled_bookings > 2 else ''}
        
        {'<h3 class="warning">High Workload</h3>' if hours_worked > 60 else ''}
        {'<p>You\'ve worked {hours_worked:.1f} hours this month. Consider taking adequate rest to maintain service quality.</p>' if hours_worked > 60 else ''}
        
        <h3>Booking Details</h3>
        <table>
            <tr>
                <th>Date</th>
                <th>Time</th>
                <th>Duration</th>
                <th>Status</th>
                <th>Reason (if cancelled)</th>
            </tr>
            {''.join([f"""
            <tr class="{'highlight' if b.get('fields', {}).get('Status', {}).get('stringValue', '').lower() == 'cancelled' else ''}">
                <td>{b.get('fields', {}).get('StartTime', {}).get('timestampValue', '').split('T')[0] if b.get('fields', {}).get('StartTime', {}).get('timestampValue') else 'N/A'}</td>
                <td>{b.get('fields', {}).get('StartTime', {}).get('timestampValue', '').split('T')[1].split('.')[0] if b.get('fields', {}).get('StartTime', {}).get('timestampValue') else 'N/A'}</td>
                <td>{(datetime.datetime.fromisoformat(b.get('fields', {}).get('EndTime', {}).get('timestampValue', '').replace('Z', '+00:00')) - 
                     datetime.datetime.fromisoformat(b.get('fields', {}).get('StartTime', {}).get('timestampValue', '').replace('Z', '+00:00'))).total_seconds() / 3600:.1f} hours</td>
                <td>{b.get('fields', {}).get('Status', {}).get('stringValue', 'Unknown')}</td>
                <td>{b.get('fields', {}).get('cancellationReason', {}).get('stringValue', '-') if b.get('fields', {}).get('Status', {}).get('stringValue', '').lower() == 'cancelled' else '-'}</td>
            </tr>
            """ for b in bookings])}
        </table>
    </body>
    </html>
    """
    
    return html_content

# Define query resolvers
@query.field("nurseMonthlyReport")
async def resolve_nurse_monthly_report(_, info, nid, month):
    # First check if report already exists
    existing_report = get_stored_report(nid, month)
    if existing_report:
        # Return the existing report data
        nurse_data = get_nurse_details(nid)
        is_suspended, suspension_end = check_suspension_status(nid)
        
        year, month_num = month.split('-')
        bookings = get_bookings_for_month(nid, int(year), int(month_num))
        hours_worked, completed = calculate_hours_worked(bookings)
        
        return {
            "nid": nid,
            "month": month,
            "totalBookings": len(bookings),
            "completedBookings": len(completed),
            "cancelledBookings": sum(1 for b in bookings if b.get('Status') == 'Cancelled'),
            "cancellationRate": (sum(1 for b in bookings if b.get('Status') == 'Cancelled') / len(bookings) * 100) if len(bookings) > 0 else 0,
            "totalHoursWorked": hours_worked,
            "averageSessionDuration": hours_worked / len(completed) if len(completed) > 0 else 0,
            "creditScore": nurse_data.get('creditScore', 100) if nurse_data else 0,
            "isWarned": nurse_data.get('creditScore', 100) <= 30 if nurse_data else False,
            "isSuspended": is_suspended,
            "suspensionEndDate": suspension_end,
            "reportLink": existing_report.get('reportLink')
        }
    
    # Otherwise, generate a new report
    result = await _generate_monthly_report(nid, month)
    
    if not result.get('success'):
        return None
    
    # Get report data
    year, month_num = month.split('-')
    nurse_data = get_nurse_details(nid)
    bookings = get_bookings_for_month(nid, int(year), int(month_num))
    hours_worked, completed = calculate_hours_worked(bookings)
    is_suspended, suspension_end = check_suspension_status(nid)
    
    return {
        "nid": nid,
        "month": month,
        "totalBookings": len(bookings),
        "completedBookings": len(completed),
        "cancelledBookings": sum(1 for b in bookings if b.get('Status') == 'Cancelled'),
        "cancellationRate": (sum(1 for b in bookings if b.get('Status') == 'Cancelled') / len(bookings) * 100) if len(bookings) > 0 else 0,
        "totalHoursWorked": hours_worked,
        "averageSessionDuration": hours_worked / len(completed) if len(completed) > 0 else 0,
        "creditScore": nurse_data.get('creditScore', 100) if nurse_data else 0,
        "isWarned": nurse_data.get('creditScore', 100) <= 30 if nurse_data else False, 
        "isSuspended": is_suspended,
        "suspensionEndDate": suspension_end,
        "reportLink": result.get('reportLink')
    }

@query.field("listNurseReports")
def resolve_list_nurse_reports(_, info, nid):
    reports = list_nurse_reports(nid)
    
    result = []
    for report in reports:
        result.append({
            "rid": report.get('RID'),
            "month": report.get('reportMonth'),
            "reportLink": report.get('reportLink')
        })
    
    return result

# Define mutation resolvers
@mutation.field("generateMonthlyReport")
async def resolve_generate_monthly_report(_, info, nid, month):
    return await _generate_monthly_report(nid, month)

async def send_consolidated_notification_amqp(nurse_email, nurse_name, report_link, hours_worked, cancelled_bookings, cancellation_rate, credit_score):
    """Send a single, consolidated email with all relevant details via AMQP."""
    subject = f"Your MedGrab Monthly Report - {datetime.datetime.now().strftime('%B %Y')}"
    
    message = f"""
    <html>
    <body>
        <p>Hi {nurse_name},</p>
        <p>Your monthly activity report is now available. <a href='{report_link}'>View your report here</a>.</p>
        <hr>
        <h3>Summary:</h3>
        <ul>
            <li><strong>Total Hours Worked:</strong> {hours_worked:.1f} hours</li>
            <li><strong>Cancelled Bookings:</strong> {cancelled_bookings} ({cancellation_rate:.1f}% cancellation rate)</li>
            <li><strong>Current Credit Score:</strong> {credit_score}</li>
        </ul>
        
        {'<p style="color:red;"><strong>⚠️ High Workload Warning:</strong> You have worked over 60 hours this month. Please take care of your well-being.</p>' if hours_worked > 60 else ''}
        {'<p style="color:red;"><strong>⚠️ High Cancellation Rate:</strong> Your cancellation rate exceeds 30%. This affects your reliability score.</p>' if cancellation_rate > 30 else ''}
        {'<p style="color:red;"><strong>🚫 Account Suspension Notice:</strong> Your credit score is critically low, and your account may be suspended.</p>' if credit_score <= 20 else ''}
        
        <p>Thank you for your service.</p>
        <p>Best Regards,<br>MedGrab Team</p>
    </body>
    </html>
    """
    
    await send_notification_amqp(nurse_email, subject, message)

# Modify _generate_monthly_report to use this function
async def _generate_monthly_report(nid, month):
    nurse_data = get_nurse_details(nid)
    if not nurse_data:
        return {"success": False, "message": "Nurse not found"}
    
    nurse_email = nurse_data.get('email')
    nurse_name = nurse_data.get('name')
    year, month_num = map(int, month.split('-'))
    bookings = get_bookings_for_month(nid, year, month_num)
    hours_worked, _ = calculate_hours_worked(bookings)
    cancelled_bookings = sum(1 for b in bookings if b.get('Status') == 'Cancelled')
    cancellation_rate = (cancelled_bookings / len(bookings) * 100) if bookings else 0
    credit_score = nurse_data.get('creditScore', 100)
    
    report_content = generate_report_content(nid, month, bookings, hours_worked, nurse_data)
    report_link = f"/reports/{nid}/{month}.html"
    store_result = store_report(nid, month, report_content, report_link)
    
    if nurse_email:
        # Use AMQP to send notification asynchronously
        await send_consolidated_notification_amqp(
            nurse_email, 
            nurse_name, 
            report_link, 
            hours_worked, 
            cancelled_bookings, 
            cancellation_rate, 
            credit_score
        )
    
    return {"success": True, "reportLink": report_link, "message": "Report generated and email queued for delivery."}

@mutation.field("checkCreditScore")
async def resolve_check_credit_score(_, info, nid):
    # Get nurse details
    nurse_data = get_nurse_details(nid)
    if not nurse_data:
        return {
            "success": False,
            "nid": nid,
            "creditScore": 0,
            "isWarned": False,
            "isSuspended": False,
            "message": "Nurse not found"
        }
    
    credit_score = nurse_data.get('creditScore', 100)
    nurse_email = nurse_data.get('email')
    nurse_name = nurse_data.get('name')
    
    is_warned = credit_score <= 30
    is_suspended = credit_score <= 20
    suspension_end_date = None
    
    # Check if already suspended
    current_suspension, end_date = check_suspension_status(nid)
    if current_suspension:
        return {
            "success": True,
            "nid": nid,
            "creditScore": credit_score,
            "isWarned": True,
            "isSuspended": True,
            "suspensionEndDate": end_date,
            "message": "Nurse is already suspended"
        }
    
    # Handle warning
    if is_warned and not is_suspended and nurse_email:
        await send_notification_amqp(
            nurse_email,
            "Credit Score Warning",
            f"Hi {nurse_name}, your credit score has dropped to {credit_score}. " +
            "Please be careful about cancellations to avoid suspension."
        )
    
    # Handle suspension
    if is_suspended and nurse_email:
        # Credit score reached suspension threshold
        # The update_credit_score function in nurse.py will handle the suspension creation
        score_update = update_credit_score(nid, 0, "System suspension check")
        
        if score_update and score_update.get('suspended'):
            suspension_end_date = score_update.get('suspensionEndDate')
            
            await send_notification_amqp(
                nurse_email,
                "Account Suspension Notice",
                f"Hi {nurse_name}, due to your credit score falling below the critical threshold, " +
                f"your account has been suspended until {suspension_end_date}. " +
                "During this period, you will not be shown in the nurse pool for new bookings."
            )
    
    return {
        "success": True,
        "nid": nid,
        "creditScore": credit_score,
        "isWarned": is_warned,
        "isSuspended": is_suspended,
        "suspensionEndDate": suspension_end_date,
        "message": "Credit score checked successfully"
    }

# Create executable schema
schema = make_executable_schema(type_defs, query, mutation)

# Create GraphQL application
graphql_app = GraphQL(
    schema,
    debug=True,
)

@generate_report_bp.route("/graphql", methods=["GET", "POST"])
async def graphql_handler():
    return await graphql_app.handle_request(request)

@generate_report_bp.route("/generate/<nid>/<month>", methods=["POST"])
async def generate_report_rest(nid, month):
    try:
        result = await _generate_monthly_report(nid, month)
        return jsonify(result)
    except Exception as e:
        print(f"Error in generate_report_rest: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@generate_report_bp.route("/nurses/<nid>/check-credit", methods=["POST"])
async def check_credit_rest(nid):
    result = await resolve_check_credit_score(None, None, nid)
    return jsonify(result)

