from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'message': 'Sales Dashboard API is running!',
        'status': 'success',
        'environment': 'Azure',
        'port': os.environ.get('PORT', 'Not set')
    })

@app.route('/api/test')
def test():
    return jsonify({
        'message': 'API test successful',
        'status': 'working',
        'data_file_check': 'skipped for testing'
    })

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'Application is running'
    })

if __name__ == '__main__':
    # Get port from environment variable for Azure deployment
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask app on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)
