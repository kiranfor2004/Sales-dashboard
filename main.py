import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Try to import the full app first, fallback to minimal test
try:
    from app_stable import app
    print("Using full app_stable.py")
except Exception as e:
    print(f"Error loading app_stable.py: {e}")
    print("Loading minimal test app...")
    
    # Import minimal test app
    import importlib.util
    spec = importlib.util.spec_from_file_location("app_minimal_test", os.path.join(os.path.dirname(__file__), "app_minimal_test.py"))
    minimal_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(minimal_module)
    app = minimal_module.app

if __name__ == "__main__":
    # Get port from environment variable for Azure deployment
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting application on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)
