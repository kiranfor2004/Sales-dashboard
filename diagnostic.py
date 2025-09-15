#!/usr/bin/env python3
"""
Quick diagnostic script to test if the Sales Dashboard application can start.
Run this to verify all imports work correctly.
"""

import sys
import os

print("=== Sales Dashboard Diagnostic ===")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Files in directory: {os.listdir('.')}")

try:
    print("\n1. Testing Flask import...")
    import flask
    print(f"✅ Flask {flask.__version__} imported successfully")
    
    print("\n2. Testing Flask-CORS import...")
    import flask_cors
    print(f"✅ Flask-CORS imported successfully")
    
    print("\n3. Testing pandas import...")
    import pandas as pd
    print(f"✅ Pandas {pd.__version__} imported successfully")
    
    print("\n4. Testing application import...")
    import deploy_ready_app
    print("✅ Deploy ready app imported successfully")
    
    print("\n5. Testing app instance...")
    app = deploy_ready_app.app
    print(f"✅ Flask app instance: {app}")
    
    print("\n6. Testing basic route...")
    with app.test_client() as client:
        response = client.get('/')
        print(f"✅ Root route responds with status: {response.status_code}")
    
    print("\n🎉 All tests passed! Application should work correctly.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)