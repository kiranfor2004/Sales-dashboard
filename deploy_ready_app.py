from flask import Flask, render_template_string, jsonify, request, g
from flask_cors import CORS
import pandas as pd
import os
import json
from datetime import datetime
import traceback
import sys
import logging
from config import CONFIG
from functools import wraps
import time

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=getattr(logging, CONFIG.LOG_LEVEL, logging.INFO),
    format='%(message)s'
)
logger = logging.getLogger("sales_dashboard")

# Global variables to store data
df = None
data_loaded = False
data_info = {}
load_errors = []
_cache = {}
_cache_meta = {}

CACHE_TTL_SECONDS = 60  # simple in-memory cache duration for heavy endpoints

def log_message(message, **extra):
    """Structured log helper printing JSON lines suitable for Azure log stream."""
    log_record = {"msg": message, "ts": datetime.utcnow().isoformat() + 'Z'}
    if extra:
        log_record.update(extra)
    try:
        logger.info(json.dumps(log_record))
    except Exception:
        # Fallback simple print if JSON fails
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
    possible_paths = CONFIG.DATA_FILE_CANDIDATES + [
        # Additional extension variants
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
                # Invalidate caches when new data loaded
                _cache.clear()
                _cache_meta.clear()
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

# -----------------------------
# Caching Decorator
# -----------------------------
def cache_response(ttl: int = CACHE_TTL_SECONDS):
    """Simple in-memory cache for JSON endpoints.

    Key is path + sorted query args. Stores Flask response object.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if request.method != 'GET':
                return func(*args, **kwargs)
            key_parts = [request.path]
            if request.args:
                key_parts.append('&'.join(f"{k}={v}" for k, v in sorted(request.args.items())))
            key = '?'.join(key_parts)
            now = time.time()
            meta = _cache_meta.get(key)
            if meta and (now - meta['ts']) < meta['ttl']:
                cached = _cache.get(key)
                if cached is not None:
                    g.cache_hit = True  # Signal cache hit for logging
                    return cached
            # execute
            g.cache_hit = False  # Signal cache miss for logging
            resp = func(*args, **kwargs)
            _cache[key] = resp
            _cache_meta[key] = {'ts': now, 'ttl': ttl}
            return resp
        return wrapper
    return decorator

# -----------------------------
# Request Logging Middleware
# -----------------------------
@app.before_request
def before_request():
    """Start timing and initialize request context."""
    g.start_time = time.time()
    g.cache_hit = None  # Will be set by cache decorator if applicable

@app.after_request
def after_request(response):
    """Log structured request details after response is ready."""
    if hasattr(g, 'start_time'):
        duration_ms = round((time.time() - g.start_time) * 1000, 2)
        
        # Only log API endpoints and key routes (avoid static assets)
        if request.path.startswith('/api/') or request.path in ['/', '/operational', '/strategic']:
            log_data = {
                "event": "request",
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "user_agent": request.headers.get('User-Agent', '')[:100] if request.headers.get('User-Agent') else None,
                "remote_addr": request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            }
            
            # Add cache information if available
            if g.cache_hit is not None:
                log_data["cache_hit"] = g.cache_hit
                
            # Add query parameters for API calls (excluding sensitive data)
            if request.args and request.path.startswith('/api/'):
                safe_args = {k: v for k, v in request.args.items() if k.lower() not in ['password', 'token', 'key']}
                if safe_args:
                    log_data["query_params"] = safe_args
            
            log_message("Request processed", **log_data)
    
    return response

# Load data on application startup (async to not block Azure startup)
log_message("🚀 Starting Sales Dashboard application...")

# Try to load data, but don't block startup if it takes too long
import threading

def load_data_async():
    """Load data in background thread to not block app startup"""
    global load_success
    try:
        load_success = load_data()
        if load_success:
            log_message("✅ Application ready with sales data!")
        else:
            log_message("⚠️ Application started but no sales data loaded")
    except Exception as e:
        log_message(f"❌ Error loading data: {e}")

# Start data loading in background
data_thread = threading.Thread(target=load_data_async, daemon=True)
data_thread.start()
log_message("📊 Data loading started in background...")

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

###############################
# Application Routes
###############################
@app.route('/robots.txt')
def robots():
    """Simple endpoint that responds immediately for Azure health checks"""
    return "User-agent: *\nDisallow: /api/\n"

@app.route('/ping')
def ping():
    """Immediate health check endpoint"""
    return jsonify({"status": "alive", "timestamp": datetime.now().isoformat()})

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sales Dashboard - Home</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container { 
                max-width: 1000px; 
                margin: 0 auto; 
                padding: 40px; 
                text-align: center;
                color: white;
            }
            .header { 
                margin-bottom: 50px;
            }
            .header h1 { 
                font-size: 3.5em; 
                margin-bottom: 15px;
                font-weight: 300;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .header p { 
                font-size: 1.4em; 
                opacity: 0.9;
                margin-bottom: 10px;
            }
            .status-info {
                font-size: 1.1em;
                opacity: 0.8;
                margin-bottom: 40px;
            }
            .dashboard-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 30px;
                margin: 40px 0;
            }
            .dashboard-card {
                background: rgba(255, 255, 255, 0.95);
                color: #2c3e50;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                text-decoration: none;
                display: block;
            }
            .dashboard-card:hover {
                transform: translateY(-10px);
                box-shadow: 0 20px 40px rgba(0,0,0,0.3);
                text-decoration: none;
                color: #2c3e50;
            }
            .dashboard-card h3 {
                font-size: 1.8em;
                margin-bottom: 15px;
                color: #667eea;
            }
            .dashboard-card p {
                font-size: 1.1em;
                line-height: 1.6;
                margin-bottom: 20px;
            }
            .dashboard-card .icon {
                font-size: 3em;
                margin-bottom: 20px;
            }
            .api-section {
                background: rgba(255, 255, 255, 0.1);
                padding: 30px;
                border-radius: 15px;
                margin-top: 40px;
            }
            .api-section h3 {
                margin-bottom: 20px;
                font-size: 1.5em;
            }
            .api-links {
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                justify-content: center;
            }
            .api-link {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                padding: 10px 20px;
                border-radius: 25px;
                text-decoration: none;
                transition: background 0.3s ease;
                font-size: 0.9em;
            }
            .api-link:hover {
                background: rgba(255, 255, 255, 0.3);
                color: white;
                text-decoration: none;
            }
            .footer {
                margin-top: 50px;
                font-size: 0.9em;
                opacity: 0.7;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Sales Dashboard</h1>
                <p>Advanced Analytics & Business Intelligence Platform</p>
                <div class="status-info">
                    ✅ System Status: <strong>Online</strong> | 
                    📈 Data Records: <strong>""" + str(len(df) if data_loaded and df is not None else 0) + """</strong> | 
                    🕒 Last Updated: <strong>""" + datetime.now().strftime('%Y-%m-%d %H:%M') + """</strong>
                </div>
            </div>
            
            <div class="dashboard-grid">
                <a href="/operational" class="dashboard-card">
                    <div class="icon">⚡</div>
                    <h3>Operational Dashboard</h3>
                    <p>Real-time operational metrics, daily performance indicators, and live business monitoring for immediate insights.</p>
                    <strong>→ View Operational Analytics</strong>
                </a>
                
                <a href="/strategic" class="dashboard-card">
                    <div class="icon">🎯</div>
                    <h3>Strategic Dashboard</h3>
                    <p>Long-term trends, strategic planning insights, partnership analysis, and executive-level business intelligence.</p>
                    <strong>→ View Strategic Analytics</strong>
                </a>
            </div>
            
            <div class="api-section">
                <h3>🔗 API Endpoints</h3>
                <div class="api-links">
                    <a href="/api/health" class="api-link">Health Check</a>
                    <a href="/api/data-info" class="api-link">Data Information</a>
                    <a href="/api/overall_sales_performance" class="api-link">Sales Performance</a>
                    <a href="/dashboard-test" class="api-link">Test Dashboard</a>
                </div>
            </div>
            
            <div class="footer">
                <p>Sales Dashboard v2.0 | Deployed on Azure App Service | Python 3.11</p>
                <p>© 2025 Advanced Business Intelligence Platform</p>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/api/health')
def health():
    cache_stats = {
        "entries": len(_cache),
        "memory_keys": list(_cache.keys())[:5]  # Show first 5 cache keys
    } if CONFIG.FEATURE_FLAGS.ENABLE_STATS else {}
    
    return jsonify({
        "status": "healthy" if data_loaded else "degraded",
        "service": "Sales Dashboard API",
        "data_loaded": data_loaded,
        "record_count": len(df) if data_loaded and df is not None else 0,
        "timestamp": datetime.now().isoformat(),
        "uptime": "Running",
        "version": "2.1",
        "config": {
            "env": CONFIG.ENV,
            "log_level": CONFIG.LOG_LEVEL,
            "features": {
                "refresh": CONFIG.FEATURE_FLAGS.ENABLE_REFRESH,
                "stats": CONFIG.FEATURE_FLAGS.ENABLE_STATS
            }
        },
        "cache_stats": cache_stats
    })

@app.route('/api/refresh-data', methods=['POST'])
def refresh_data():
    if not CONFIG.FEATURE_FLAGS.ENABLE_REFRESH:
        return jsonify({"error": "Refresh disabled"}), 403
    success = load_data()
    return jsonify({
        "refreshed": success,
        "data_loaded": data_loaded,
        "record_count": len(df) if df is not None else 0,
        "cache_cleared": True
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
@cache_response()
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
    try:
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
    except Exception as e:
        return f"""
        <html>
        <body>
        <h1>Dashboard Error</h1>
        <p>Error rendering dashboard: {str(e)}</p>
        <p>Data loaded: {data_loaded}</p>
        <p>Records: {len(df) if data_loaded and df is not None else 0}</p>
        </body>
        </html>
        """

@app.route('/dashboard-test')
def dashboard_test():
    return """
    <html>
    <head><title>Simple Dashboard Test</title></head>
    <body style="font-family: Arial; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
        <h1>🎯 Sales Dashboard - Test View</h1>
        <div style="background: white; color: black; padding: 20px; margin: 20px 0; border-radius: 10px;">
            <h2>System Status</h2>
            <p><strong>Status:</strong> ✅ Working</p>
            <p><strong>Data Loaded:</strong> """ + str(data_loaded) + """</p>
            <p><strong>Records:</strong> """ + str(len(df) if data_loaded and df is not None else 0) + """</p>
            <p><strong>Timestamp:</strong> """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        </div>
        <div style="background: white; color: black; padding: 20px; margin: 20px 0; border-radius: 10px;">
            <h2>📊 Quick Links</h2>
            <a href="/api/health" style="display: block; margin: 10px 0; color: #667eea;">Health Check</a>
            <a href="/api/data-info" style="display: block; margin: 10px 0; color: #667eea;">Data Information</a>
            <a href="/api/overall_sales_performance" style="display: block; margin: 10px 0; color: #667eea;">Sales Performance</a>
        </div>
    </body>
    </html>
    """

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
