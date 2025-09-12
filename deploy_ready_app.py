from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import pandas as pd
import os
import json
from datetime import datetime
import traceback
import sys

app = Flask(__name__)
CORS(app)

# Global variables to store data
df = None
data_loaded = False
data_info = {}
load_errors = []

def log_message(message):
    """Print and store log messages"""
    print(message)
    sys.stdout.flush()

def load_data():
    """Load the sales data with comprehensive path checking for Azure"""
    global df, data_loaded, data_info, load_errors
    
    log_message("=== SALES DATA LOADING DEBUG ===")
    log_message(f"Current working directory: {os.getcwd()}")
    log_message(f"Script directory: {os.path.dirname(__file__)}")
    
    # List all files in current directory
    try:
        files_in_cwd = os.listdir('.')
        log_message(f"Files in current directory: {files_in_cwd}")
    except Exception as e:
        log_message(f"Error listing current directory: {e}")
    
    # Multiple possible file paths for Azure deployment
    possible_paths = [
        'Sales data - Filtered',
        './Sales data - Filtered', 
        '/home/site/wwwroot/Sales data - Filtered',
        '/home/site/wwwroot/backend/Sales data - Filtered',
        'backend/Sales data - Filtered',
        os.path.join(os.getcwd(), 'Sales data - Filtered'),
        os.path.join(os.path.dirname(__file__), 'Sales data - Filtered'),
        os.path.join(os.path.dirname(__file__), 'backend', 'Sales data - Filtered'),
        # Try with different extensions
        'Sales data - Filtered.csv',
        'Sales data - Filtered.xlsx',
        'Sales data - Filtered.tsv',
        './Sales data - Filtered.csv',
        './Sales data - Filtered.xlsx', 
        './Sales data - Filtered.tsv'
    ]
    
    for path in possible_paths:
        try:
            log_message(f"Trying path: {path}")
            if os.path.exists(path):
                log_message(f"✅ Found data file at: {path}")
                
                # Try different read methods based on file extension
                if path.endswith('.xlsx'):
                    df = pd.read_excel(path)
                elif path.endswith('.csv'):
                    df = pd.read_csv(path)
                elif path.endswith('.tsv'):
                    df = pd.read_csv(path, sep='\t')
                else:
                    # Try TSV first (our original format)
                    try:
                        df = pd.read_csv(path, sep='\t')
                    except:
                        df = pd.read_csv(path)
                
                log_message(f"✅ Data loaded successfully! Shape: {df.shape}")
                log_message(f"✅ Columns: {list(df.columns)}")
                
                # Store comprehensive data info
                data_info = {
                    'file_path': path,
                    'shape': df.shape,
                    'columns': list(df.columns),
                    'memory_usage_mb': round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
                    'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                    'null_counts': df.isnull().sum().to_dict(),
                    'loaded_at': datetime.now().isoformat()
                }
                
                # Sample data for verification
                if len(df) > 0:
                    data_info['sample_records'] = df.head(3).to_dict('records')
                    data_info['record_count'] = len(df)
                
                # Check for date columns and analyze
                date_columns = df.select_dtypes(include=['datetime64']).columns.tolist()
                if date_columns:
                    for col in date_columns:
                        data_info[f'{col}_range'] = {
                            'min': df[col].min().strftime('%Y-%m-%d'),
                            'max': df[col].max().strftime('%Y-%m-%d')
                        }
                
                data_loaded = True
                log_message(f"✅ Data processing complete! Records: {len(df)}")
                return True
                
        except Exception as e:
            error_msg = f"❌ Failed to load from {path}: {str(e)}"
            log_message(error_msg)
            load_errors.append(error_msg)
            continue
    
    log_message("❌ Could not load data from any path")
    log_message("Available paths attempted:")
    for path in possible_paths:
        log_message(f"  - {path}")
    
    return False

# Load data on application startup
log_message("🚀 Starting Sales Dashboard application...")
load_success = load_data()

if load_success:
    log_message("✅ Application ready with sales data!")
else:
    log_message("⚠️ Application started but no sales data loaded")
    log_message("Application will run in demo mode")

# HTML Templates
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sales Dashboard - {{ title }}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            line-height: 1.6; 
            color: #333;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
        }
        .header { 
            background: {{ gradient }}; 
            color: white; 
            padding: 30px; 
            border-radius: 15px; 
            text-align: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .header h1 { 
            font-size: 2.5em; 
            margin-bottom: 10px;
            font-weight: 300;
        }
        .header p { 
            font-size: 1.2em; 
            opacity: 0.9;
        }
        .status-card { 
            background: white;
            margin: 20px 0; 
            padding: 25px; 
            border-radius: 12px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border-left: 5px solid {{ accent_color }};
        }
        .status-card.success { border-left-color: #28a745; }
        .status-card.error { border-left-color: #dc3545; }
        .status-card h3 { 
            color: #2c3e50;
            margin-bottom: 15px;
            font-weight: 600;
        }
        .metric { 
            display: inline-block; 
            margin: 10px 15px 10px 0;
            padding: 8px 15px;
            background: #f8f9fa;
            border-radius: 6px;
            border: 1px solid #e9ecef;
        }
        .metric strong { color: #495057; }
        .api-links { 
            background: white;
            padding: 25px; 
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .api-links h3 { 
            color: #2c3e50;
            margin-bottom: 20px;
            font-weight: 600;
        }
        .api-links ul { 
            list-style: none; 
        }
        .api-links li { 
            margin: 12px 0; 
        }
        .api-links a { 
            color: {{ accent_color }}; 
            text-decoration: none; 
            font-weight: 500;
            padding: 8px 12px;
            border: 2px solid {{ accent_color }};
            border-radius: 6px;
            display: inline-block;
            transition: all 0.3s ease;
        }
        .api-links a:hover { 
            background: {{ accent_color }}; 
            color: white;
            transform: translateY(-2px);
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #6c757d;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Sales Dashboard</h1>
            <h2>{{ title }}</h2>
            <p>{{ subtitle }}</p>
        </div>
        
        <div class="status-card {{ 'success' if data_loaded else 'error' }}">
            <h3>📊 System Status</h3>
            <div class="metric">
                <strong>Status:</strong> {{ '✅ Active' if data_loaded else '❌ No Data' }}
            </div>
            {% if data_loaded and record_count %}
            <div class="metric">
                <strong>Records:</strong> {{ "{:,}".format(record_count) }}
            </div>
            {% endif %}
            {% if file_path %}
            <div class="metric">
                <strong>Data Source:</strong> {{ file_path }}
            </div>
            {% endif %}
            {% if memory_usage %}
            <div class="metric">
                <strong>Memory Usage:</strong> {{ memory_usage }} MB
            </div>
            {% endif %}
        </div>
        
        <div class="api-links">
            <h3>🔗 API Endpoints</h3>
            <ul>
                <li><a href="/api/health" target="_blank">🏥 Health Check</a></li>
                <li><a href="/api/data-info" target="_blank">📋 Data Information</a></li>
                <li><a href="/api/overall_sales_performance" target="_blank">📈 Sales Performance</a></li>
                <li><a href="{{ '/strategic' if title == 'Operational View' else '/operational' }}" target="_blank">
                    🔄 Switch to {{ 'Strategic' if title == 'Operational View' else 'Operational' }} View
                </a></li>
            </ul>
        </div>
        
        <div class="footer">
            <p>Sales Dashboard v2.0 | Deployed on Azure App Service | Last Updated: {{ timestamp }}</p>
        </div>
    </div>
</body>
</html>
"""

# Application Routes
@app.route('/')
def home():
    return jsonify({
        "message": "Sales Dashboard API v2.0",
        "status": "running",
        "data_loaded": data_loaded,
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/api/health",
            "data_info": "/api/data-info", 
            "sales_performance": "/api/overall_sales_performance",
            "operational_dashboard": "/operational",
            "strategic_dashboard": "/strategic"
        },
        "app_info": {
            "python_version": sys.version,
            "flask_app": "deploy_ready_app.py",
            "environment": "Azure App Service"
        }
    })

@app.route('/api/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "Sales Dashboard API",
        "data_loaded": data_loaded,
        "record_count": len(df) if data_loaded and df is not None else 0,
        "timestamp": datetime.now().isoformat(),
        "uptime": "Running",
        "version": "2.0"
    })

@app.route('/api/data-info')
def data_info_endpoint():
    if not data_loaded:
        return jsonify({
            "error": "No data loaded", 
            "data_loaded": False,
            "load_errors": load_errors,
            "timestamp": datetime.now().isoformat()
        })
    
    return jsonify({
        "data_loaded": True,
        "info": data_info,
        "load_errors": load_errors,
        "api_status": "operational",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/overall_sales_performance')
def get_overall_sales_performance():
    if not data_loaded or df is None:
        return jsonify({
            "error": "Sales data not available",
            "data_loaded": False,
            "suggestion": "Check /api/data-info for more details"
        })
    
    try:
        # Analyze available columns to determine data structure
        columns = list(df.columns)
        log_message(f"Available columns: {columns}")
        
        # Try to find sales-related columns
        sales_columns = [col for col in columns if 'sales' in col.lower() or 'revenue' in col.lower() or 'amount' in col.lower()]
        
        if sales_columns:
            # Simple aggregation for demonstration
            result = {
                "success": True,
                "data_structure": {
                    "total_records": len(df),
                    "available_columns": columns,
                    "sales_columns": sales_columns
                },
                "sample_data": df.head(5).to_dict('records'),
                "summary": {
                    "message": "Sales data loaded successfully",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Add basic statistics if numeric columns exist
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_columns:
                result["statistics"] = {}
                for col in numeric_columns[:5]:  # Limit to first 5 numeric columns
                    result["statistics"][col] = {
                        "sum": float(df[col].sum()),
                        "mean": float(df[col].mean()),
                        "min": float(df[col].min()),
                        "max": float(df[col].max())
                    }
            
            return jsonify(result)
        else:
            return jsonify({
                "error": "No sales columns found in data",
                "available_columns": columns,
                "suggestion": "Please check the data structure",
                "sample_data": df.head(3).to_dict('records') if len(df) > 0 else []
            })
            
    except Exception as e:
        return jsonify({
            "error": f"Processing error: {str(e)}",
            "traceback": traceback.format_exc(),
            "success": False,
            "timestamp": datetime.now().isoformat()
        })

@app.route('/operational')
def operational():
    return render_template_string(DASHBOARD_TEMPLATE,
        title="Operational View",
        subtitle="Daily Operations & Performance Metrics", 
        gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        accent_color="#667eea",
        data_loaded=data_loaded,
        record_count=len(df) if data_loaded and df is not None else 0,
        file_path=data_info.get('file_path', '') if data_loaded else '',
        memory_usage=data_info.get('memory_usage_mb', '') if data_loaded else '',
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

@app.route('/strategic')
def strategic():
    return render_template_string(DASHBOARD_TEMPLATE,
        title="Strategic View", 
        subtitle="Long-term Insights & Partnership Analysis",
        gradient="linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        accent_color="#f093fb",
        data_loaded=data_loaded,
        record_count=len(df) if data_loaded and df is not None else 0,
        file_path=data_info.get('file_path', '') if data_loaded else '',
        memory_usage=data_info.get('memory_usage_mb', '') if data_loaded else '',
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "/", "/api/health", "/api/data-info", 
            "/api/overall_sales_performance", "/operational", "/strategic"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "message": str(error),
        "suggestion": "Check /api/health for system status"
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    log_message(f"🚀 Starting Sales Dashboard on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
