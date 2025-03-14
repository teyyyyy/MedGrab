from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    
    # Import and register blueprints
    # Report
    from atomic.report.report import report_bp
    app.register_blueprint(report_bp, url_prefix='/api/reports')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)