#!/usr/bin/env python3
"""
Azure App Service startup script for Sales Dashboard
"""
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the Flask app
if __name__ == "__main__":
    from deploy_ready_app import app
    
    # Get port from environment variable (Azure sets this)
    port = int(os.environ.get('PORT', 8000))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=False)