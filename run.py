from deploy_ready_app import app
import os

if __name__ == "__main__":
    # Azure expects the app to bind to port 8000 (not PORT environment variable)
    port = int(os.environ.get('PORT', 8000))
    print(f"🚀 Starting Sales Dashboard on port {port}")
    
    # Use threaded=True for better performance and to handle Azure health checks
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)