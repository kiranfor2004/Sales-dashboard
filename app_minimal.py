from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Sales Dashboard - WORKING! 🎉"

@app.route('/ping')
def ping():
    return "PING OK! 🏓"

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "message": "Azure deployment successful!"})

@app.route('/test')
def test():
    return jsonify({
        "status": "success",
        "message": "All systems operational",
        "port": os.environ.get('PORT', 'not set'),
        "app": "minimal test v2"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"🚀 Starting minimal app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)