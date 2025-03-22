from flask import Flask
import os

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def home():
        return """
        <h1>MedGrab API</h1>
        <p>Available endpoints:</p>
        <ul>
            <li><a href="/api/nurses/">/api/nurses/</a> - Nurse service</li>
            <li><a href="/api/reports/">/api/reports/</a> - Report service</li>
        </ul>
        """
    
    # Import and register blueprints
    # Report
    from atomic.report.report import report_bp
    app.register_blueprint(report_bp, url_prefix='/api/reports')

    # Nurse
    from atomic.nurse.nurse import nurse_bp
    app.register_blueprint(nurse_bp, url_prefix='/api/nurses')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)