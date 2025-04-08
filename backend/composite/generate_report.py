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
import json

app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# Service URLs
NURSE_SERVICE_URL = environ.get('NURSE_SERVICE_URL')
BOOKING_SERVICE_URL = environ.get('BOOKING_SERVICE_URL')
REPORT_SERVICE_URL = environ.get('REPORT_SERVICE_URL')

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

def get_nurse_details(nid):
    """Get nurse details from nurse service"""
    try:
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
        response = requests.get(f"{BOOKING_SERVICE_URL}/GetBookingsForNurse/{nid}")
        
        if response.status_code == 200:
            all_bookings = response.json().get('Bookings', [])
            filtered_bookings = []
            
            for booking in all_bookings:
                try:
                    start_time_str = booking.get('fields', {}).get('StartTime', {}).get('timestampValue', '')
                    if not start_time_str:
                        continue
                        
                    start_time = datetime.datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    
                    if start_time.year == year and start_time.month == month:
                        filtered_bookings.append({
                            'booking': booking,
                            'start_time': start_time
                        })
                        
                except (ValueError, TypeError) as e:
                    print(f"Error parsing booking time: {e}")
                    continue
            
            filtered_bookings.sort(key=lambda x: x['start_time'])
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
                total_earned += float(payment) if payment else 0.0
            except (ValueError, TypeError):
                total_earned += 0.0
    return round(total_earned, 2)

def calculate_hours_worked(bookings):
    """Calculate total hours worked from bookings"""
    total_hours = 0.0
    completed_bookings = []
    
    for booking in bookings:
        fields = booking.get('fields', {})
        status = fields.get('Status', {}).get('stringValue', '').lower()
        
        if status == 'completed':
            try:
                start_time_str = fields.get('StartTime', {}).get('timestampValue', '')
                end_time_str = fields.get('EndTime', {}).get('timestampValue', '')
                
                if start_time_str and end_time_str:
                    start_time = datetime.datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    end_time = datetime.datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                    duration = (end_time - start_time).total_seconds() / 3600
                    total_hours += float(duration)
                    
            except (ValueError, TypeError) as e:
                print(f"Error parsing time: {e}")
                continue
    
    return round(total_hours, 2), completed_bookings

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
            "hoursWorked": float(hours_worked) if hours_worked else 0.0,
            "totalBookings": int(total_bookings) if total_bookings else 0
        }
        response = requests.post(REPORT_SERVICE_URL, json=data)
        return response.json() if response.status_code == 200 else None
    except requests.RequestException:
        return None

def format_date(date_str):
    """Format ISO date string to a more readable format (DD-MM-YYYY HH:MM)"""
    if not date_str:
        return "N/A"
    try:
        dt = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%d-%m-%Y %H:%M')
    except (ValueError, TypeError):
        return date_str

def generate_report_content(nid, month_str, bookings, hours_worked, nurse_data):
    """Generate the HTML report content"""
    try:
        year, month = month_str.split('-')
        month_name = datetime.datetime(int(year), int(month), 1).strftime('%B')
        
        total_bookings = len(bookings)
        completed_bookings = sum(1 for b in bookings if b.get('fields', {}).get('Status', {}).get('stringValue', '').lower() == 'completed')
        cancelled_bookings = sum(1 for b in bookings if b.get('fields', {}).get('Status', {}).get('stringValue', '').lower() == 'cancelled')
        
        # Convert all values to float explicitly
        total_earned = float(calculate_earnings(bookings))
        hours_worked = float(hours_worked) if hours_worked else 0.0
        cancellation_rate = (float(cancelled_bookings) / float(total_bookings) * 100) if total_bookings > 0 else 0.0
        avg_session = (float(hours_worked) / float(completed_bookings)) if completed_bookings > 0 else 0.0
        
        credit_score = float(nurse_data.get('creditScore', 100))
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
            
            try:
                if start_time_str:
                    start_time = datetime.datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    start_time = start_time.astimezone(datetime.timezone(datetime.timedelta(hours=8)))
                    date_part = start_time.strftime('%d %B %Y')
                    time_part = start_time.strftime('%H:%M')
                else:
                    date_part = 'N/A'
                    time_part = 'N/A'
            except (ValueError, TypeError):
                date_part = 'Invalid Date'
                time_part = 'Invalid Time'
            
            duration = 0.0
            if start_time_str and end_time_str:
                try:
                    start = datetime.datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    end = datetime.datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                    duration = float((end - start).total_seconds() / 3600)
                except ValueError:
                    pass
            
            reason = fields.get('cancellationReason', {}).get('stringValue', '-') if status == 'cancelled' else '-'
            
            booking_rows.append(
                f'<tr class="{"highlight" if status == "cancelled" else ""}">'
                f'<td>{date_part}</td>'
                f'<td>{time_part}</td>'
                f'<td>{float(duration):.1f} hours</td>'
                f'<td>{status.capitalize()}</td>'
                f'<td>{reason}</td>'
                '</tr>'
            )
        
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
                <h2>Summary for {nurse_data.get("name", "Unknown Nurse")}</h2>
                <p>Report Period: {month_name} {year}</p>
                <p>Total Bookings: {total_bookings}</p>
                <p>Completed Sessions: {completed_bookings}</p>
                <p>Cancelled Sessions: <span class="{"warning" if cancelled_bookings > 2 else ""}">{cancelled_bookings}</span></p>
                <p>Cancellation Rate: <span class="{"warning" if cancellation_rate > 30 else ""}">{float(cancellation_rate):.1f}%</span></p>
                <p>Total Hours Worked: <span class="{"warning" if hours_worked > 60 else ""}">{float(hours_worked):.1f} hours</span></p>
                <p>Total Earnings: ${float(total_earned):.2f}</p>
                <p>Average Session Duration: {float(avg_session):.1f} hours</p>
                <p>Current Credit Score: <span class="{"warning" if credit_score < 40 else "good" if credit_score > 80 else ""}">{float(credit_score)}</span></p>
            </div>
        """
        
        if is_warned:
            html_content += """
            <div class="warning">
                <h3>⚠️ Warning</h3>
                <p>Your credit score is low. Please be careful about cancellations.</p>
            </div>
            """
        
        if is_suspended:
            html_content += f"""
            <div class="warning">
                <h3>🚫 Account Suspension</h3>
                <p>Your account has been suspended for 1 month due to low credit score.</p>
                <p>During this period, you will not be shown in the nurse pool for new bookings.</p>
                <p>Suspension end date: {suspension_end_date}</p>
            </div>
            """
        
        html_content += f"""
            <h2>Detailed Activity</h2>
            {"<p>You have not completed any bookings this month.</p>" if completed_bookings == 0 else ""}
            {"<h3 class='warning'>High Cancellation Rate</h3>" if cancellation_rate > 30 else ""}
            {"<p>You've cancelled " + str(cancelled_bookings) + " bookings this month. This affects your credit score and reliability rating.</p>" if cancelled_bookings > 2 else ""}
            {"<h3 class='warning'>High Workload</h3>" if hours_worked > 60 else ""}
            {"<p>You've worked " + f"{float(hours_worked):.1f}" + " hours this month. Consider taking adequate rest to maintain service quality.</p>" if hours_worked > 60 else ""}
            <h3>Booking Details</h3>
            <table>
                <tr>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Duration</th>
                    <th>Status</th>
                    <th>Reason (if cancelled)</th>
                </tr>
                {''.join(booking_rows)}
            </table>
            </body>
            </html>
        """
        
        return html_content
    except Exception as e:
        print(f"Error generating report content: {e}")
        raise

async def _generate_monthly_report(nid, month):
    print(f"Starting report generation for nurse {nid}, month {month}")
    nurse_data = get_nurse_details(nid)
    if not nurse_data:
        return {"success": False, "message": "Nurse not found"}
    
    try:
        status_response = requests.post(f"{NURSE_SERVICE_URL}/{nid}/check-status")
        if status_response.status_code == 200:
            print(f"Nurse status checked and updated: {status_response.json()}")
            # Refresh nurse data to get updated status
            nurse_data = get_nurse_details(nid)
    except requests.RequestException as e:
        print(f"Error checking nurse status: {e}")
    
    nurse_email = nurse_data.get('email')
    nurse_name = nurse_data.get('name')
    year, month_num = map(int, month.split('-'))
    bookings = get_bookings_for_month(nid, year, month_num)
    
    hours_worked, completed_bookings = calculate_hours_worked(bookings)
    total_earned = calculate_earnings(bookings)
    cancelled_bookings = sum(1 for b in bookings if b.get('fields', {}).get('Status', {}).get('stringValue', '').lower() == 'cancelled')
    total_bookings = len(bookings)
    cancellation_rate = (float(cancelled_bookings) / float(total_bookings) * 100) if total_bookings > 0 else 0.0
    
    report_content = generate_report_content(nid, month, bookings, hours_worked, nurse_data)
    store_result = store_report(nid, month, report_content, hours_worked, total_bookings)
    
    if nurse_email:
        subject = f"Your MedGrab Monthly Report - {datetime.datetime.strptime(month, '%Y-%m').strftime('%B %Y')}"
        pdf_content = generate_pdf_report(report_content) if report_content else None
        
        message = f"""
        <html>
        <body>
            <p>Hi {nurse_name},</p>
            <p>Your monthly activity report for {datetime.datetime.strptime(month, '%Y-%m').strftime('%B %Y')} is attached.</p>
            
            <h3>Quick Summary:</h3>
            <ul>
                <li><strong>Total Hours Worked:</strong> {float(hours_worked):.1f} hours</li>
                <li><strong>Total Earnings:</strong> ${float(total_earned):.2f}</li>
                <li><strong>Cancelled Bookings:</strong> {cancelled_bookings} ({float(cancellation_rate):.1f}% cancellation rate)</li>
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
        "hours": float(hours_worked),
        "earnings": float(total_earned),
        "totalBookings": int(total_bookings),
        "cancellationRate": float(cancellation_rate)
    }

# GraphQL Schema
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

query = QueryType()
mutation = MutationType()

@query.field("ping")
def resolve_ping(*_):
    return "GraphQL Report Service is running!"

@mutation.field("generateReport")
async def resolve_generate_report(_, info, nurseId, month, **kwargs):
    try:
        full_result = await _generate_monthly_report(nurseId, month)
        if not full_result["success"]:
            return full_result

        response = {
            "success": True,
            "message": full_result["message"],
            "month": full_result["month"],
            "nurseId": full_result["nurseId"],
            "cancellationRate": float(full_result.get("cancellationRate", 0)),
            "hours": float(full_result.get("hours", 0)) if kwargs.get("includeHours", True) else None,
            "earnings": float(full_result.get("earnings", 0)) if kwargs.get("includeEarnings", True) else None,
            "totalBookings": int(full_result.get("totalBookings", 0)) if kwargs.get("includeBookings", False) else None
        }

        return response
    except Exception as e:
        return {"success": False, "message": str(e)}

schema = make_executable_schema(type_defs, query, mutation)
graphql_app = GraphQL(schema)

@generate_report_bp.route("/graphql", methods=["GET", "POST"])
async def graphql_handler():
    request_data = request.get_data()
    query_params = {}
    for key, value in request.args.items():
        query_params[key] = value
    
    scope = {
        "type": "http",
        "path": request.path,
        "query_string": request.query_string,
        "headers": [(k.lower().encode('latin1'), v.encode('latin1')) for k, v in request.headers.items()],
        "method": request.method,
        "http_version": "1.1",
        "scheme": request.scheme,
        "client": ("127.0.0.1", 0),
        "server": (request.host.split(':')[0], int(request.host.split(':')[1]) if ':' in request.host else 80),
    }
    
    async def receive():
        return {"type": "http.request", "body": request_data, "more_body": False}
    
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
    
    await graphql_app(scope, receive, send)
    
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