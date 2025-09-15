from flask import Flask, jsonify
import os
import sys

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "Sales Dashboard - Minimal Test",
        "status": "working",
        "python_version": sys.version,
        "environment": dict(os.environ)
    })

@app.route('/ping')
def ping():
    return jsonify({"status": "alive"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "minimal-test"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"Starting minimal app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)