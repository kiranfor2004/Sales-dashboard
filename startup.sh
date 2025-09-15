#!/bin/bash

# Azure App Service startup script for Sales Dashboard
# This ensures the Flask application starts correctly

echo "=== Sales Dashboard Startup Script ==="
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"
echo "Files in directory:"
ls -la

# Install dependencies if not already installed
echo "Installing dependencies..."
pip install -r requirements.txt

# Start the Flask application
echo "Starting Sales Dashboard application..."
exec gunicorn --bind=0.0.0.0:${PORT:-8000} --timeout 600 --workers 1 --worker-class sync deploy_ready_app:app