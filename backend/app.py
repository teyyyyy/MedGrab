from flask import Flask
import os
from composite.generate_report import generate_report_bp

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
            <li><a href="/api/generate-report/graphql">/api/generate-report/graphql</a> - Report Generation GraphQL</li>
        </ul>
        """
    
    # Import and register blueprints (ONLY COMPOSITE NEEDED)
    # # Nurse
    # from atomic.nurse.nurse import nurse_bp
    # app.register_blueprint(nurse_bp, url_prefix='/api/nurses')

    # GENERATE REPORT (SCENARIO 3)
    app.register_blueprint(generate_report_bp, url_prefix='/api/generate-report')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)