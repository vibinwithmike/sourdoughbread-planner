# app.py - Debug Version
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import os

# Create Flask app with explicit template folder
app = Flask(__name__, template_folder='templates')

# Test route that doesn't rely on templates
@app.route('/')
def index():
    try:
        # First, let's see if we can return basic HTML without templates
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sourdough Planner - Debug</title>
        </head>
        <body>
            <h1>🍞 Sourdough Schedule Planner</h1>
            <p>App is working! Template system will be loaded next.</p>
            <p><a href="/health">Health Check</a></p>
            <p><a href="/test">Test Route</a></p>
            <p><a href="/debug">Debug Info</a></p>
        </body>
        </html>
        '''
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/test')
def test_route():
    return "Flask is working! This is a test route."

@app.route('/debug')
def debug():
    import os
    return jsonify({
        'current_directory': os.getcwd(),
        'files_in_root': os.listdir('.'),
        'templates_exists': os.path.exists('templates'),
        'index_exists': os.path.exists('templates/index.html'),
        'flask_working': True,
        'python_version': os.sys.version,
        'port': os.environ.get('PORT', 'Not Set')
    })

# Add a simple API endpoint that works without templates
@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'API Working',
        'app': 'Sourdough Planner',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
