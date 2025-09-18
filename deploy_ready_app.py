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
BLOOMBERG_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sales Analytics | Bloomberg Terminal Style</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        /* Bloomberg Terminal Color Scheme */
        :root {
            --bloomberg-black: #000000;
            --bloomberg-dark: #1a1a1a;
            --bloomberg-darker: #0d0d0d;
            --bloomberg-orange: #ff6600;
            --bloomberg-yellow: #ffcc00;
            --bloomberg-green: #00ff00;
            --bloomberg-red: #ff0066;
            --bloomberg-blue: #0099ff;
            --bloomberg-cyan: #00ffff;
            --bloomberg-white: #ffffff;
            --bloomberg-gray: #808080;
            --bloomberg-light-gray: #cccccc;
            
            --text-primary: #ffffff;
            --text-secondary: #cccccc;
            --text-accent: #ffcc00;
            --border-color: #333333;
            --panel-bg: #1a1a1a;
            --terminal-font: 'Roboto Mono', 'Consolas', monospace;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: var(--terminal-font);
            background-color: var(--bloomberg-black);
            color: var(--text-primary);
            overflow-x: hidden;
            font-size: 12px;
        }

        /* Bloomberg Terminal Header */
        .bloomberg-header {
            background: linear-gradient(135deg, var(--bloomberg-dark) 0%, var(--bloomberg-darker) 100%);
            border-bottom: 2px solid var(--bloomberg-orange);
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 1000;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 20px;
        }

        .bloomberg-logo {
            color: var(--bloomberg-orange);
            font-weight: 700;
            font-size: 1.4em;
            letter-spacing: 2px;
        }

        .terminal-title {
            color: var(--text-accent);
            font-weight: 500;
            font-size: 1.1em;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .live-indicator {
            display: flex;
            align-items: center;
            gap: 5px;
            color: var(--bloomberg-green);
            font-weight: 500;
        }

        .live-dot {
            width: 8px;
            height: 8px;
            background: var(--bloomberg-green);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        .terminal-time {
            color: var(--text-secondary);
            font-size: 0.9em;
        }

        .terminal-nav {
            display: flex;
            gap: 10px;
        }

        .nav-button {
            background: var(--bloomberg-dark);
            border: 1px solid var(--bloomberg-orange);
            color: var(--text-primary);
            padding: 5px 12px;
            text-decoration: none;
            font-family: var(--terminal-font);
            font-size: 0.85em;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .nav-button:hover {
            background: var(--bloomberg-orange);
            color: var(--bloomberg-black);
            text-decoration: none;
        }

        .nav-button.active {
            background: var(--bloomberg-orange);
            color: var(--bloomberg-black);
        }

        /* Main Terminal Container */
        .terminal-container {
            display: grid;
            grid-template-columns: 250px 1fr;
            height: calc(100vh - 60px);
            gap: 2px;
            background: var(--bloomberg-black);
        }

        /* Left Sidebar - Market Data */
        .market-sidebar {
            background: var(--panel-bg);
            border-right: 2px solid var(--border-color);
            padding: 15px;
            overflow-y: auto;
        }

        .sidebar-section {
            margin-bottom: 20px;
        }

        .sidebar-title {
            color: var(--text-accent);
            font-weight: 700;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 5px;
            margin-bottom: 10px;
        }

        .market-ticker {
            display: flex;
            justify-content: space-between;
            padding: 3px 0;
            font-size: 0.85em;
            border-bottom: 1px solid #333;
        }

        .ticker-symbol {
            color: var(--text-primary);
            font-weight: 500;
        }

        .ticker-price {
            color: var(--bloomberg-green);
        }

        .ticker-change {
            font-size: 0.8em;
        }

        .ticker-change.positive {
            color: var(--bloomberg-green);
        }

        .ticker-change.negative {
            color: var(--bloomberg-red);
        }

        .quick-stats {
            background: var(--bloomberg-darker);
            border: 1px solid var(--border-color);
            padding: 10px;
            margin: 10px 0;
        }

        .stat-item {
            display: flex;
            justify-content: space-between;
            padding: 2px 0;
            font-size: 0.8em;
        }

        .stat-label {
            color: var(--text-secondary);
        }

        .stat-value {
            color: var(--text-primary);
            font-weight: 500;
        }

        /* Main Content Area */
        .main-content {
            background: var(--bloomberg-black);
            display: grid;
            grid-template-rows: auto 1fr;
            overflow: hidden;
        }

        /* Command Bar */
        .command-bar {
            background: var(--panel-bg);
            border-bottom: 1px solid var(--border-color);
            padding: 8px 15px;
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .command-input {
            background: var(--bloomberg-darker);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 5px 10px;
            font-family: var(--terminal-font);
            font-size: 0.9em;
            min-width: 200px;
        }

        .command-input:focus {
            outline: none;
            border-color: var(--bloomberg-orange);
        }

        .command-buttons {
            display: flex;
            gap: 8px;
        }

        .cmd-btn {
            background: var(--bloomberg-dark);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 4px 8px;
            font-size: 0.8em;
            cursor: pointer;
            font-family: var(--terminal-font);
        }

        .cmd-btn:hover {
            background: var(--border-color);
            color: var(--text-primary);
        }

        /* Dashboard Grid */
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: 1fr 1fr;
            gap: 2px;
            height: 100%;
            padding: 2px;
        }

        .chart-panel {
            background: var(--panel-bg);
            border: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .panel-header {
            background: var(--bloomberg-darker);
            border-bottom: 1px solid var(--border-color);
            padding: 8px 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .panel-title {
            color: var(--text-accent);
            font-weight: 600;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .panel-controls {
            display: flex;
            gap: 5px;
        }

        .panel-btn {
            background: none;
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 2px 6px;
            font-size: 0.7em;
            cursor: pointer;
            font-family: var(--terminal-font);
        }

        .panel-btn:hover {
            color: var(--text-primary);
            border-color: var(--bloomberg-orange);
        }

        .panel-content {
            flex: 1;
            padding: 10px;
            position: relative;
            overflow: hidden;
        }

        .chart-wrapper {
            position: relative;
            width: 100%;
            height: 100%;
        }

        /* Data Tables */
        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8em;
        }

        .data-table th {
            background: var(--bloomberg-darker);
            color: var(--text-accent);
            padding: 5px 8px;
            border: 1px solid var(--border-color);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .data-table td {
            padding: 4px 8px;
            border: 1px solid var(--border-color);
            color: var(--text-primary);
        }

        .data-table tr:hover {
            background: var(--bloomberg-darker);
        }

        /* Number formatting */
        .positive {
            color: var(--bloomberg-green);
        }

        .negative {
            color: var(--bloomberg-red);
        }

        .neutral {
            color: var(--text-secondary);
        }

        /* Scrollbars */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bloomberg-darker);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--bloomberg-orange);
        }

        /* Responsive Design */
        @media (max-width: 1200px) {
            .terminal-container {
                grid-template-columns: 200px 1fr;
            }
            
            .dashboard-grid {
                grid-template-columns: 1fr;
                grid-template-rows: repeat(4, 1fr);
            }
        }

        @media (max-width: 768px) {
            .terminal-container {
                grid-template-columns: 1fr;
                grid-template-rows: auto 1fr;
            }
            
            .market-sidebar {
                height: 200px;
                overflow-y: auto;
            }
        }

        /* Terminal-style animations */
        .terminal-text {
            animation: terminal-flicker 0.1s infinite alternate;
        }

        @keyframes terminal-flicker {
            0% { opacity: 1; }
            100% { opacity: 0.98; }
        }

        /* Advanced Chart Styling */
        .advanced-chart {
            background: var(--bloomberg-black);
            border-radius: 0;
        }

        /* Bloomberg-style loading */
        .loading-terminal {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            flex-direction: column;
            color: var(--text-secondary);
        }

        .loading-bars {
            display: flex;
            gap: 3px;
            margin-bottom: 10px;
        }

        .loading-bar {
            width: 3px;
            height: 20px;
            background: var(--bloomberg-orange);
            animation: loading-wave 1.5s infinite ease-in-out;
        }

        .loading-bar:nth-child(2) { animation-delay: 0.1s; }
        .loading-bar:nth-child(3) { animation-delay: 0.2s; }
        .loading-bar:nth-child(4) { animation-delay: 0.3s; }
        .loading-bar:nth-child(5) { animation-delay: 0.4s; }

        @keyframes loading-wave {
            0%, 40%, 100% { transform: scaleY(0.4); opacity: 0.5; }
            20% { transform: scaleY(1); opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="bloomberg-header">
        <div class="header-left">
            <div class="bloomberg-logo">BLOOMBERG</div>
            <div class="terminal-title">{{ title }} - Sales Analytics Terminal</div>
        </div>
        <div class="header-right">
            <div class="live-indicator">
                <div class="live-dot"></div>
                <span>LIVE</span>
            </div>
            <div class="terminal-time" id="terminalClock"></div>
            <div class="terminal-nav">
                <a href="/operational" class="nav-button {{ 'active' if title == 'Operational Analytics' else '' }}">OPR</a>
                <a href="/strategic" class="nav-button {{ 'active' if title == 'Strategic Analytics' else '' }}">STR</a>
            </div>
        </div>
    </div>

    <div class="terminal-container">
        <!-- Market Data Sidebar -->
        <div class="market-sidebar">
            <div class="sidebar-section">
                <div class="sidebar-title">System Status</div>
                <div class="quick-stats">
                    <div class="stat-item">
                        <span class="stat-label">Records:</span>
                        <span class="stat-value">{{ "{:,}".format(record_count) if record_count else '0' }}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Status:</span>
                        <span class="stat-value {{ 'positive' if data_loaded else 'negative' }}">{{ 'ONLINE' if data_loaded else 'OFFLINE' }}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Memory:</span>
                        <span class="stat-value">{{ memory_usage or 'N/A' }} MB</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Uptime:</span>
                        <span class="stat-value positive">99.9%</span>
                    </div>
                </div>
            </div>

            <div class="sidebar-section">
                <div class="sidebar-title">Market Indices</div>
                <div class="market-ticker">
                    <span class="ticker-symbol">SPX</span>
                    <div>
                        <span class="ticker-price">4,350.65</span>
                        <div class="ticker-change positive">+1.2%</div>
                    </div>
                </div>
                <div class="market-ticker">
                    <span class="ticker-symbol">NASDAQ</span>
                    <div>
                        <span class="ticker-price">13,567.98</span>
                        <div class="ticker-change positive">+0.8%</div>
                    </div>
                </div>
                <div class="market-ticker">
                    <span class="ticker-symbol">DOW</span>
                    <div>
                        <span class="ticker-price">34,789.12</span>
                        <div class="ticker-change negative">-0.3%</div>
                    </div>
                </div>
                <div class="market-ticker">
                    <span class="ticker-symbol">VIX</span>
                    <div>
                        <span class="ticker-price">18.45</span>
                        <div class="ticker-change negative">-2.1%</div>
                    </div>
                </div>
            </div>

            <div class="sidebar-section">
                <div class="sidebar-title">Key Metrics</div>
                {% if title == 'Operational Analytics' %}
                <div class="market-ticker">
                    <span class="ticker-symbol">REV</span>
                    <div>
                        <span class="ticker-price">$1.24M</span>
                        <div class="ticker-change positive">+7.8%</div>
                    </div>
                </div>
                <div class="market-ticker">
                    <span class="ticker-symbol">ORD</span>
                    <div>
                        <span class="ticker-price">2,456</span>
                        <div class="ticker-change positive">+12.3%</div>
                    </div>
                </div>
                <div class="market-ticker">
                    <span class="ticker-symbol">AOV</span>
                    <div>
                        <span class="ticker-price">$505</span>
                        <div class="ticker-change neutral">+0.2%</div>
                    </div>
                </div>
                {% else %}
                <div class="market-ticker">
                    <span class="ticker-symbol">MKT</span>
                    <div>
                        <span class="ticker-price">23.4%</span>
                        <div class="ticker-change positive">+1.3%</div>
                    </div>
                </div>
                <div class="market-ticker">
                    <span class="ticker-symbol">ROI</span>
                    <div>
                        <span class="ticker-price">24.7%</span>
                        <div class="ticker-change positive">+1.5%</div>
                    </div>
                </div>
                <div class="market-ticker">
                    <span class="ticker-symbol">SKU</span>
                    <div>
                        <span class="ticker-price">84</span>
                        <div class="ticker-change positive">+6.3%</div>
                    </div>
                </div>
                {% endif %}
            </div>

            <div class="sidebar-section">
                <div class="sidebar-title">Watchlist</div>
                <div class="market-ticker">
                    <span class="ticker-symbol">AMZN</span>
                    <div>
                        <span class="ticker-price">3,245.67</span>
                        <div class="ticker-change positive">+2.1%</div>
                    </div>
                </div>
                <div class="market-ticker">
                    <span class="ticker-symbol">MSFT</span>
                    <div>
                        <span class="ticker-price">338.45</span>
                        <div class="ticker-change positive">+1.5%</div>
                    </div>
                </div>
                <div class="market-ticker">
                    <span class="ticker-symbol">GOOGL</span>
                    <div>
                        <span class="ticker-price">2,756.89</span>
                        <div class="ticker-change negative">-0.7%</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Content Area -->
        <div class="main-content">
            <!-- Command Bar -->
            <div class="command-bar">
                <input type="text" class="command-input" placeholder="Enter command (e.g., HELP, REFRESH, EXPORT)" id="commandInput">
                <div class="command-buttons">
                    <button class="cmd-btn" onclick="executeCommand('HELP')">HELP</button>
                    <button class="cmd-btn" onclick="executeCommand('REFRESH')">REFRESH</button>
                    <button class="cmd-btn" onclick="executeCommand('EXPORT')">EXPORT</button>
                    <button class="cmd-btn" onclick="executeCommand('SETTINGS')">SETTINGS</button>
                </div>
            </div>

            {% if data_loaded %}
            <!-- Dashboard Grid -->
            <div class="dashboard-grid">
                {% if title == 'Operational Analytics' %}
                <!-- Operational Panels -->
                <div class="chart-panel">
                    <div class="panel-header">
                        <div class="panel-title">Revenue Performance</div>
                        <div class="panel-controls">
                            <button class="panel-btn">1D</button>
                            <button class="panel-btn">1W</button>
                            <button class="panel-btn">1M</button>
                            <button class="panel-btn">1Y</button>
                        </div>
                    </div>
                    <div class="panel-content">
                        <div class="chart-wrapper">
                            <canvas id="revenueChart" class="advanced-chart"></canvas>
                        </div>
                    </div>
                </div>

                <div class="chart-panel">
                    <div class="panel-header">
                        <div class="panel-title">Growth Momentum</div>
                        <div class="panel-controls">
                            <button class="panel-btn">LINEAR</button>
                            <button class="panel-btn">LOG</button>
                        </div>
                    </div>
                    <div class="panel-content">
                        <div class="chart-wrapper">
                            <canvas id="growthChart" class="advanced-chart"></canvas>
                        </div>
                    </div>
                </div>

                <div class="chart-panel">
                    <div class="panel-header">
                        <div class="panel-title">Product Performance Matrix</div>
                        <div class="panel-controls">
                            <button class="panel-btn">PIE</button>
                            <button class="panel-btn">BAR</button>
                        </div>
                    </div>
                    <div class="panel-content">
                        <div class="chart-wrapper">
                            <canvas id="productMatrix" class="advanced-chart"></canvas>
                        </div>
                    </div>
                </div>

                <div class="chart-panel">
                    <div class="panel-header">
                        <div class="panel-title">Real-Time Orders</div>
                        <div class="panel-controls">
                            <button class="panel-btn">TABLE</button>
                            <button class="panel-btn">CHART</button>
                        </div>
                    </div>
                    <div class="panel-content">
                        <table class="data-table" id="ordersTable">
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Product</th>
                                    <th>Amount</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody id="ordersTableBody">
                                <!-- Data populated by JavaScript -->
                            </tbody>
                        </table>
                    </div>
                </div>
                {% else %}
                <!-- Strategic Panels -->
                <div class="chart-panel">
                    <div class="panel-header">
                        <div class="panel-title">Partner Analysis</div>
                        <div class="panel-controls">
                            <button class="panel-btn">YTD</button>
                            <button class="panel-btn">QTD</button>
                        </div>
                    </div>
                    <div class="panel-content">
                        <div class="chart-wrapper">
                            <canvas id="partnerChart" class="advanced-chart"></canvas>
                        </div>
                    </div>
                </div>

                <div class="chart-panel">
                    <div class="panel-header">
                        <div class="panel-title">Seasonal Trends</div>
                        <div class="panel-controls">
                            <button class="panel-btn">HEAT</button>
                            <button class="panel-btn">LINE</button>
                        </div>
                    </div>
                    <div class="panel-content">
                        <div class="chart-wrapper">
                            <canvas id="seasonalChart" class="advanced-chart"></canvas>
                        </div>
                    </div>
                </div>

                <div class="chart-panel">
                    <div class="panel-header">
                        <div class="panel-title">Portfolio Mix</div>
                        <div class="panel-controls">
                            <button class="panel-btn">TREE</button>
                            <button class="panel-btn">PIE</button>
                        </div>
                    </div>
                    <div class="panel-content">
                        <div class="chart-wrapper">
                            <canvas id="portfolioChart" class="advanced-chart"></canvas>
                        </div>
                    </div>
                </div>

                <div class="chart-panel">
                    <div class="panel-header">
                        <div class="panel-title">Risk Metrics</div>
                        <div class="panel-controls">
                            <button class="panel-btn">LIVE</button>
                            <button class="panel-btn">HIST</button>
                        </div>
                    </div>
                    <div class="panel-content">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Metric</th>
                                    <th>Current</th>
                                    <th>Target</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Volatility</td>
                                    <td class="positive">12.3%</td>
                                    <td>15.0%</td>
                                    <td class="positive">✓ GOOD</td>
                                </tr>
                                <tr>
                                    <td>Sharpe Ratio</td>
                                    <td class="positive">1.85</td>
                                    <td>1.50</td>
                                    <td class="positive">✓ EXCEED</td>
                                </tr>
                                <tr>
                                    <td>Max Drawdown</td>
                                    <td class="negative">-8.2%</td>
                                    <td>-10.0%</td>
                                    <td class="positive">✓ GOOD</td>
                                </tr>
                                <tr>
                                    <td>Beta</td>
                                    <td class="neutral">0.92</td>
                                    <td>1.00</td>
                                    <td class="neutral">→ WATCH</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                {% endif %}
            </div>
            {% else %}
            <!-- No Data State -->
            <div class="dashboard-grid">
                <div class="chart-panel">
                    <div class="panel-header">
                        <div class="panel-title">System Status</div>
                    </div>
                    <div class="panel-content">
                        <div class="loading-terminal">
                            <div class="loading-bars">
                                <div class="loading-bar"></div>
                                <div class="loading-bar"></div>
                                <div class="loading-bar"></div>
                                <div class="loading-bar"></div>
                                <div class="loading-bar"></div>
                            </div>
                            <div>LOADING DATA FEED...</div>
                            <div style="font-size: 0.8em; color: var(--text-secondary); margin-top: 5px;">
                                Connecting to data sources...
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}
        </div>
    </div>

    <script>
        // Bloomberg-style chart configuration
        Chart.defaults.font.family = "'Roboto Mono', 'Consolas', monospace";
        Chart.defaults.font.size = 10;
        Chart.defaults.color = '#cccccc';
        Chart.defaults.backgroundColor = '#1a1a1a';

        // Bloomberg color palette
        const bloombergColors = {
            orange: '#ff6600',
            yellow: '#ffcc00',
            green: '#00ff00',
            red: '#ff0066',
            blue: '#0099ff',
            cyan: '#00ffff',
            white: '#ffffff',
            gray: '#808080'
        };

        // Terminal clock
        function updateClock() {
            const now = new Date();
            const timeStr = now.toLocaleTimeString('en-US', { 
                hour12: false, 
                timeZone: 'America/New_York' 
            });
            const dateStr = now.toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric',
                timeZone: 'America/New_York'
            });
            document.getElementById('terminalClock').textContent = `${dateStr} ${timeStr} EDT`;
        }
        setInterval(updateClock, 1000);
        updateClock();

        // Command execution
        function executeCommand(cmd) {
            const input = document.getElementById('commandInput');
            input.value = cmd;
            console.log(`Executing command: ${cmd}`);
            
            switch(cmd) {
                case 'HELP':
                    alert('Available commands:\nREFRESH - Update all data\nEXPORT - Download data\nSETTINGS - Configure dashboard\nHELP - Show this help');
                    break;
                case 'REFRESH':
                    location.reload();
                    break;
                case 'EXPORT':
                    alert('Export functionality would download current data');
                    break;
                case 'SETTINGS':
                    alert('Settings panel would open configuration options');
                    break;
            }
            input.value = '';
        }

        // Command input handler
        document.getElementById('commandInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                executeCommand(this.value.toUpperCase());
            }
        });

        {% if data_loaded %}
        // Chart data
        const chartData = {{ chart_data | safe if chart_data else '{}' }};

        {% if title == 'Operational Analytics' %}
        // Revenue Performance Chart
        new Chart(document.getElementById('revenueChart'), {
            type: 'line',
            data: {
                labels: ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'],
                datasets: [{
                    label: 'Revenue ($)',
                    data: [125000, 132000, 145000, 158000, 162000, 171000, 185000, 192000],
                    borderColor: bloombergColors.green,
                    backgroundColor: bloombergColors.green + '20',
                    borderWidth: 2,
                    tension: 0.1,
                    fill: true,
                    pointBackgroundColor: bloombergColors.green,
                    pointBorderColor: '#000000',
                    pointRadius: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { intersect: false },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#000000',
                        titleColor: bloombergColors.yellow,
                        bodyColor: bloombergColors.white,
                        borderColor: bloombergColors.orange,
                        borderWidth: 1
                    }
                },
                scales: {
                    x: { 
                        grid: { color: '#333333' },
                        ticks: { color: bloombergColors.gray }
                    },
                    y: { 
                        grid: { color: '#333333' },
                        ticks: { 
                            color: bloombergColors.gray,
                            callback: value => '$' + value.toLocaleString()
                        }
                    }
                }
            }
        });

        // Growth Chart
        new Chart(document.getElementById('growthChart'), {
            type: 'bar',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Growth %',
                    data: [5.2, 8.1, 12.3, 7.8, 15.6, 18.9],
                    backgroundColor: function(context) {
                        const value = context.parsed.y;
                        return value > 10 ? bloombergColors.green : 
                               value > 5 ? bloombergColors.yellow : bloombergColors.red;
                    },
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#000000',
                        titleColor: bloombergColors.yellow,
                        bodyColor: bloombergColors.white,
                        callbacks: {
                            label: (context) => `Growth: ${context.parsed.y}%`
                        }
                    }
                },
                scales: {
                    x: { 
                        grid: { color: '#333333' },
                        ticks: { color: bloombergColors.gray }
                    },
                    y: { 
                        grid: { color: '#333333' },
                        ticks: { 
                            color: bloombergColors.gray,
                            callback: value => value + '%'
                        }
                    }
                }
            }
        });

        // Product Matrix
        new Chart(document.getElementById('productMatrix'), {
            type: 'doughnut',
            data: {
                labels: ['Electronics', 'Clothing', 'Books', 'Home & Garden', 'Sports'],
                datasets: [{
                    data: [35, 25, 20, 15, 5],
                    backgroundColor: [
                        bloombergColors.orange,
                        bloombergColors.yellow,
                        bloombergColors.green,
                        bloombergColors.blue,
                        bloombergColors.cyan
                    ],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { 
                        position: 'bottom',
                        labels: { 
                            color: bloombergColors.gray,
                            font: { size: 9 },
                            padding: 10
                        }
                    },
                    tooltip: {
                        backgroundColor: '#000000',
                        titleColor: bloombergColors.yellow,
                        bodyColor: bloombergColors.white
                    }
                }
            }
        });

        // Populate orders table
        const ordersData = [
            ['14:32:45', 'iPhone 13', '$999', 'FILLED'],
            ['14:31:22', 'MacBook Pro', '$2,499', 'PENDING'],
            ['14:30:15', 'AirPods', '$179', 'FILLED'],
            ['14:29:08', 'iPad Air', '$599', 'CANCELLED'],
            ['14:28:33', 'Apple Watch', '$399', 'FILLED']
        ];

        const tableBody = document.getElementById('ordersTableBody');
        ordersData.forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="color: ${bloombergColors.cyan}">${row[0]}</td>
                <td>${row[1]}</td>
                <td style="color: ${bloombergColors.yellow}">${row[2]}</td>
                <td style="color: ${row[3] === 'FILLED' ? bloombergColors.green : row[3] === 'PENDING' ? bloombergColors.yellow : bloombergColors.red}">${row[3]}</td>
            `;
            tableBody.appendChild(tr);
        });

        {% else %}
        // Strategic Charts
        // Partner Analysis
        new Chart(document.getElementById('partnerChart'), {
            type: 'bar',
            data: {
                labels: ['Amazon', 'Walmart', 'Target', 'Best Buy', 'Costco'],
                datasets: [{
                    label: 'Revenue ($M)',
                    data: [4.5, 3.2, 2.8, 1.9, 1.2],
                    backgroundColor: bloombergColors.blue,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#000000',
                        titleColor: bloombergColors.yellow,
                        bodyColor: bloombergColors.white
                    }
                },
                scales: {
                    x: { 
                        grid: { color: '#333333' },
                        ticks: { 
                            color: bloombergColors.gray,
                            callback: value => '$' + value + 'M'
                        }
                    },
                    y: { 
                        grid: { color: '#333333' },
                        ticks: { color: bloombergColors.gray }
                    }
                }
            }
        });

        // Seasonal Chart
        new Chart(document.getElementById('seasonalChart'), {
            type: 'line',
            data: {
                labels: ['Q1', 'Q2', 'Q3', 'Q4'],
                datasets: [{
                    label: 'Seasonal Revenue',
                    data: [380, 420, 350, 480],
                    borderColor: bloombergColors.orange,
                    backgroundColor: bloombergColors.orange + '20',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: bloombergColors.orange,
                    pointBorderColor: '#000000',
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#000000',
                        titleColor: bloombergColors.yellow,
                        bodyColor: bloombergColors.white
                    }
                },
                scales: {
                    x: { 
                        grid: { color: '#333333' },
                        ticks: { color: bloombergColors.gray }
                    },
                    y: { 
                        grid: { color: '#333333' },
                        ticks: { 
                            color: bloombergColors.gray,
                            callback: value => '$' + value + 'K'
                        }
                    }
                }
            }
        });

        // Portfolio Chart
        new Chart(document.getElementById('portfolioChart'), {
            type: 'pie',
            data: {
                labels: ['Premium', 'Standard', 'Budget'],
                datasets: [{
                    data: [40, 45, 15],
                    backgroundColor: [
                        bloombergColors.green,
                        bloombergColors.yellow,
                        bloombergColors.red
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { 
                        position: 'bottom',
                        labels: { 
                            color: bloombergColors.gray,
                            font: { size: 9 },
                            padding: 10
                        }
                    },
                    tooltip: {
                        backgroundColor: '#000000',
                        titleColor: bloombergColors.yellow,
                        bodyColor: bloombergColors.white
                    }
                }
            }
        });
        {% endif %}
        {% endif %}

        // Real-time updates simulation
        setInterval(() => {
            // Simulate real-time data updates
            const elements = document.querySelectorAll('.ticker-price');
            elements.forEach(el => {
                if (Math.random() > 0.7) {
                    el.style.backgroundColor = bloombergColors.orange;
                    setTimeout(() => {
                        el.style.backgroundColor = 'transparent';
                    }, 500);
                }
            });
        }, 3000);
    </script>
</body>
</html>
"""

TABLEAU_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sales Analytics | Tableau-Style Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/date-fns@2.29.3/index.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        /* Tableau Design System Variables */
        :root {
            --tableau-blue: #1f77b4;
            --tableau-orange: #ff7f0e;
            --tableau-green: #2ca02c;
            --tableau-red: #d62728;
            --tableau-purple: #9467bd;
            --tableau-brown: #8c564b;
            --tableau-pink: #e377c2;
            --tableau-gray: #7f7f7f;
            --tableau-olive: #bcbd22;
            --tableau-cyan: #17becf;
            
            --bg-primary: #ffffff;
            --bg-secondary: #f8f9fa;
            --bg-tertiary: #e9ecef;
            --text-primary: #212529;
            --text-secondary: #6c757d;
            --border-color: #dee2e6;
            --shadow-light: 0 2px 4px rgba(0,0,0,0.08);
            --shadow-medium: 0 4px 12px rgba(0,0,0,0.15);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', 'Tableau', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-secondary);
            color: var(--text-primary);
            line-height: 1.5;
        }

        /* Tableau-style Header */
        .tableau-header {
            background: linear-gradient(135deg, var(--tableau-blue) 0%, #1a5490 100%);
            color: white;
            padding: 20px 30px;
            box-shadow: var(--shadow-medium);
            position: relative;
        }

        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header-left h1 {
            font-size: 1.8em;
            font-weight: 600;
            margin-bottom: 5px;
        }

        .header-left .subtitle {
            font-size: 0.95em;
            opacity: 0.9;
        }

        .header-controls {
            display: flex;
            gap: 15px;
            align-items: center;
        }

        .tableau-button {
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 0.9em;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .tableau-button:hover {
            background: rgba(255,255,255,0.3);
            color: white;
            text-decoration: none;
        }

        .tableau-button.active {
            background: var(--tableau-orange);
            border-color: var(--tableau-orange);
        }

        /* Main Dashboard Container */
        .dashboard-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 25px;
        }

        /* KPI Cards Section */
        .kpi-section {
            margin-bottom: 25px;
        }

        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }

        .kpi-card {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px;
            box-shadow: var(--shadow-light);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-medium);
        }

        .kpi-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .kpi-title {
            font-size: 0.85em;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .kpi-icon {
            color: var(--tableau-blue);
            font-size: 1.2em;
        }

        .kpi-value {
            font-size: 2.2em;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
        }

        .kpi-change {
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 0.9em;
        }

        .kpi-change.positive {
            color: var(--tableau-green);
        }

        .kpi-change.negative {
            color: var(--tableau-red);
        }

        /* Filter Controls */
        .filters-section {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 25px;
            box-shadow: var(--shadow-light);
        }

        .filters-header {
            font-size: 1.1em;
            font-weight: 600;
            margin-bottom: 15px;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .filters-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }

        .filter-group {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }

        .filter-label {
            font-size: 0.85em;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .filter-control {
            padding: 8px 12px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            font-size: 0.9em;
            background: var(--bg-primary);
            transition: border-color 0.2s ease;
        }

        .filter-control:focus {
            outline: none;
            border-color: var(--tableau-blue);
        }

        /* Charts Grid */
        .charts-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 25px;
        }

        .chart-container {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            box-shadow: var(--shadow-light);
            overflow: hidden;
        }

        .chart-header {
            background: var(--bg-tertiary);
            padding: 15px 20px;
            border-bottom: 1px solid var(--border-color);
        }

        .chart-title {
            font-size: 1.1em;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 3px;
        }

        .chart-subtitle {
            font-size: 0.85em;
            color: var(--text-secondary);
        }

        .chart-content {
            padding: 20px;
            position: relative;
            height: 400px;
        }

        .chart-wrapper {
            position: relative;
            height: 100%;
            width: 100%;
        }

        /* Tableau-style Data Table */
        .data-table {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin-top: 25px;
            overflow: hidden;
            box-shadow: var(--shadow-light);
        }

        .table-header {
            background: var(--bg-tertiary);
            padding: 15px 20px;
            border-bottom: 1px solid var(--border-color);
            font-weight: 600;
        }

        .table-content {
            max-height: 300px;
            overflow-y: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            text-align: left;
            padding: 12px 15px;
            border-bottom: 1px solid var(--border-color);
        }

        th {
            background: var(--bg-secondary);
            font-weight: 600;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
        }

        tr:hover {
            background: var(--bg-secondary);
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .dashboard-container {
                padding: 15px;
            }
            
            .charts-section {
                grid-template-columns: 1fr;
            }
            
            .kpi-grid {
                grid-template-columns: 1fr;
            }
        }

        /* Loading and Error States */
        .loading-state, .error-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 200px;
            color: var(--text-secondary);
        }

        .loading-spinner {
            border: 3px solid var(--bg-tertiary);
            border-top: 3px solid var(--tableau-blue);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin-bottom: 15px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Tableau Color Palette for Charts */
        .tableau-colors {
            --color-1: var(--tableau-blue);
            --color-2: var(--tableau-orange);
            --color-3: var(--tableau-green);
            --color-4: var(--tableau-red);
            --color-5: var(--tableau-purple);
            --color-6: var(--tableau-brown);
            --color-7: var(--tableau-pink);
            --color-8: var(--tableau-gray);
            --color-9: var(--tableau-olive);
            --color-10: var(--tableau-cyan);
        }
    </style>
</head>
<body>
    <div class="tableau-header">
        <div class="header-content">
            <div class="header-left">
                <h1><i class="fas fa-chart-bar"></i> Sales Analytics Dashboard</h1>
                <div class="subtitle">{{ subtitle }}</div>
            </div>
            <div class="header-controls">
                <a href="/operational" class="tableau-button {{ 'active' if title == 'Operational Analytics' else '' }}">
                    <i class="fas fa-tachometer-alt"></i> Operational
                </a>
                <a href="/strategic" class="tableau-button {{ 'active' if title == 'Strategic Analytics' else '' }}">
                    <i class="fas fa-chart-line"></i> Strategic
                </a>
                <div class="tableau-button">
                    <i class="fas fa-clock"></i> {{ timestamp.split()[1] if timestamp else 'Live' }}
                </div>
            </div>
        </div>
    </div>

    <div class="dashboard-container">
        <!-- KPI Section -->
        <div class="kpi-section">
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-header">
                        <div class="kpi-title">Total Records</div>
                        <div class="kpi-icon"><i class="fas fa-database"></i></div>
                    </div>
                    <div class="kpi-value">{{ "{:,}".format(record_count) if record_count else '0' }}</div>
                    <div class="kpi-change positive">
                        <i class="fas fa-arrow-up"></i>
                        <span>Data loaded successfully</span>
                    </div>
                </div>

                <div class="kpi-card">
                    <div class="kpi-header">
                        <div class="kpi-title">System Status</div>
                        <div class="kpi-icon"><i class="fas fa-heartbeat"></i></div>
                    </div>
                    <div class="kpi-value">{{ 'Online' if data_loaded else 'Offline' }}</div>
                    <div class="kpi-change {{ 'positive' if data_loaded else 'negative' }}">
                        <i class="fas fa-{{ 'check-circle' if data_loaded else 'exclamation-triangle' }}"></i>
                        <span>{{ 'All systems operational' if data_loaded else 'Data loading required' }}</span>
                    </div>
                </div>

                <div class="kpi-card">
                    <div class="kpi-header">
                        <div class="kpi-title">Last Updated</div>
                        <div class="kpi-icon"><i class="fas fa-sync-alt"></i></div>
                    </div>
                    <div class="kpi-value" style="font-size: 1.4em;">{{ timestamp.split()[1] if timestamp else 'N/A' }}</div>
                    <div class="kpi-change positive">
                        <i class="fas fa-clock"></i>
                        <span>{{ timestamp.split()[0] if timestamp else 'Not available' }}</span>
                    </div>
                </div>

                {% if memory_usage %}
                <div class="kpi-card">
                    <div class="kpi-header">
                        <div class="kpi-title">Memory Usage</div>
                        <div class="kpi-icon"><i class="fas fa-memory"></i></div>
                    </div>
                    <div class="kpi-value">{{ memory_usage }} MB</div>
                    <div class="kpi-change positive">
                        <i class="fas fa-check"></i>
                        <span>Optimal performance</span>
                    </div>
                </div>
                {% endif %}
            </div>
        </div>

        <!-- Filters Section -->
        <div class="filters-section">
            <div class="filters-header">
                <i class="fas fa-filter"></i>
                Dashboard Filters & Controls
            </div>
            <div class="filters-grid">
                <div class="filter-group">
                    <label class="filter-label">Time Period</label>
                    <select class="filter-control" id="timePeriodFilter">
                        <option value="all">All Time</option>
                        <option value="ytd">Year to Date</option>
                        <option value="last12">Last 12 Months</option>
                        <option value="last6">Last 6 Months</option>
                        <option value="last3">Last 3 Months</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label class="filter-label">Category</label>
                    <select class="filter-control" id="categoryFilter">
                        <option value="all">All Categories</option>
                        <option value="electronics">Electronics</option>
                        <option value="clothing">Clothing</option>
                        <option value="books">Books</option>
                        <option value="home">Home & Garden</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label class="filter-label">Region</label>
                    <select class="filter-control" id="regionFilter">
                        <option value="all">All Regions</option>
                        <option value="north">North</option>
                        <option value="south">South</option>
                        <option value="east">East</option>
                        <option value="west">West</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label class="filter-label">View Type</label>
                    <select class="filter-control" id="viewTypeFilter">
                        <option value="summary">Summary View</option>
                        <option value="detailed">Detailed View</option>
                        <option value="trends">Trends View</option>
                    </select>
                </div>
            </div>
        </div>

        {% if data_loaded %}
        <!-- Charts Section -->
        <div class="charts-section">
            {% if title == 'Operational Analytics' %}
            <!-- Operational Charts -->
            <div class="chart-container">
                <div class="chart-header">
                    <div class="chart-title">Sales Performance Comparison</div>
                    <div class="chart-subtitle">Current vs Previous Period Analysis</div>
                </div>
                <div class="chart-content">
                    <div class="chart-wrapper">
                        <canvas id="salesPerformanceChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-header">
                    <div class="chart-title">Monthly Growth Trend</div>
                    <div class="chart-subtitle">Sales Growth Rate Over Time</div>
                </div>
                <div class="chart-content">
                    <div class="chart-wrapper">
                        <canvas id="growthTrendChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-header">
                    <div class="chart-title">Top Performing Products</div>
                    <div class="chart-subtitle">Revenue by Product Category</div>
                </div>
                <div class="chart-content">
                    <div class="chart-wrapper">
                        <canvas id="topProductsChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-header">
                    <div class="chart-title">Sales Distribution by Category</div>
                    <div class="chart-subtitle">Category Performance Breakdown</div>
                </div>
                <div class="chart-content">
                    <div class="chart-wrapper">
                        <canvas id="categoryDistributionChart"></canvas>
                    </div>
                </div>
            </div>
            {% else %}
            <!-- Strategic Charts -->
            <div class="chart-container">
                <div class="chart-header">
                    <div class="chart-title">Partner Performance Analysis</div>
                    <div class="chart-subtitle">Revenue by Supplier/Partner</div>
                </div>
                <div class="chart-content">
                    <div class="chart-wrapper">
                        <canvas id="partnerPerformanceChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-header">
                    <div class="chart-title">Seasonal Sales Pattern</div>
                    <div class="chart-subtitle">Quarterly Revenue Trends</div>
                </div>
                <div class="chart-content">
                    <div class="chart-wrapper">
                        <canvas id="seasonalPatternChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-header">
                    <div class="chart-title">Revenue Mix Analysis</div>
                    <div class="chart-subtitle">Premium vs Standard vs Budget</div>
                </div>
                <div class="chart-content">
                    <div class="chart-wrapper">
                        <canvas id="revenueMixChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-header">
                    <div class="chart-title">Product Type Distribution</div>
                    <div class="chart-subtitle">Market Share by Product Type</div>
                </div>
                <div class="chart-content">
                    <div class="chart-wrapper">
                        <canvas id="productTypeChart"></canvas>
                    </div>
                </div>
            </div>
            {% endif %}
        </div>

        <!-- Data Table Section -->
        <div class="data-table">
            <div class="table-header">
                <i class="fas fa-table"></i>
                {{ 'Key Operational Metrics' if title == 'Operational Analytics' else 'Strategic Performance Indicators' }}
            </div>
            <div class="table-content">
                <table>
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Current Value</th>
                            <th>Previous Period</th>
                            <th>Change (%)</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="metricsTableBody">
                        <!-- Table data will be populated by JavaScript -->
                    </tbody>
                </table>
            </div>
        </div>

        <script>
        // Tableau Color Palette
        const tableauColors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ];

        // Chart configuration with Tableau styling
        Chart.defaults.font.family = "'Segoe UI', 'Tableau', sans-serif";
        Chart.defaults.font.size = 12;
        Chart.defaults.color = '#666';

        {% if title == 'Operational Analytics' %}
        // Operational Charts Data
        const salesData = {{ chart_data.sales_performance | safe if chart_data and chart_data.sales_performance else '[150000, 180000]' }};
        const growthData = {{ chart_data.growth_data | safe if chart_data and chart_data.growth_data else '{"labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"], "values": [5, 12, 8, 15, 10, 18]}' }};
        const productData = {{ chart_data.top_products | safe if chart_data and chart_data.top_products else '{"labels": ["Product A", "Product B", "Product C", "Product D", "Others"], "values": [35000, 28000, 22000, 18000, 12000]}' }};
        const categoryData = {{ chart_data.category_data | safe if chart_data and chart_data.category_data else '{"labels": ["Electronics", "Clothing", "Books", "Home & Garden"], "values": [320000, 180000, 90000, 140000]}' }};

        // Sales Performance Chart
        new Chart(document.getElementById('salesPerformanceChart'), {
            type: 'bar',
            data: {
                labels: ['Previous Period', 'Current Period'],
                datasets: [{
                    label: 'Sales Revenue',
                    data: Array.isArray(salesData) ? salesData : [salesData[0] || 150000, salesData[1] || 180000],
                    backgroundColor: [tableauColors[0], tableauColors[1]],
                    borderWidth: 0,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        callbacks: {
                            label: (context) => `Revenue: $${context.parsed.y.toLocaleString()}`
                        }
                    }
                },
                scales: {
                    y: { 
                        beginAtZero: true,
                        grid: { color: '#e9ecef' },
                        ticks: { callback: value => '$' + value.toLocaleString() }
                    },
                    x: { grid: { display: false } }
                }
            }
        });

        // Growth Trend Chart
        new Chart(document.getElementById('growthTrendChart'), {
            type: 'line',
            data: {
                labels: growthData.labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Growth Rate (%)',
                    data: growthData.values || [5, 12, 8, 15, 10, 18],
                    borderColor: tableauColors[2],
                    backgroundColor: tableauColors[2] + '20',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: tableauColors[2],
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        callbacks: {
                            label: (context) => `Growth: ${context.parsed.y}%`
                        }
                    }
                },
                scales: {
                    y: { 
                        beginAtZero: true,
                        grid: { color: '#e9ecef' },
                        ticks: { callback: value => value + '%' }
                    },
                    x: { grid: { display: false } }
                }
            }
        });

        // Top Products Chart
        new Chart(document.getElementById('topProductsChart'), {
            type: 'doughnut',
            data: {
                labels: productData.labels || ['Product A', 'Product B', 'Product C', 'Product D', 'Others'],
                datasets: [{
                    data: productData.values || [35000, 28000, 22000, 18000, 12000],
                    backgroundColor: tableauColors.slice(0, 5),
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { 
                        position: 'bottom',
                        labels: { padding: 20, usePointStyle: true }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        callbacks: {
                            label: (context) => `${context.label}: $${context.parsed.toLocaleString()}`
                        }
                    }
                }
            }
        });

        // Category Distribution Chart
        new Chart(document.getElementById('categoryDistributionChart'), {
            type: 'bar',
            data: {
                labels: categoryData.labels || ['Electronics', 'Clothing', 'Books', 'Home & Garden'],
                datasets: [{
                    label: 'Sales by Category',
                    data: categoryData.values || [320000, 180000, 90000, 140000],
                    backgroundColor: tableauColors[0],
                    borderWidth: 0,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        callbacks: {
                            label: (context) => `Revenue: $${context.parsed.x.toLocaleString()}`
                        }
                    }
                },
                scales: {
                    x: { 
                        beginAtZero: true,
                        grid: { color: '#e9ecef' },
                        ticks: { callback: value => '$' + value.toLocaleString() }
                    },
                    y: { grid: { display: false } }
                }
            }
        });

        {% else %}
        // Strategic Charts Data
        const partnerData = {{ chart_data.supplier_data | safe if chart_data and chart_data.supplier_data else '{"labels": ["Partner A", "Partner B", "Partner C", "Partner D"], "values": [450000, 320000, 280000, 190000]}' }};
        const seasonalData = {{ chart_data.seasonal_data | safe if chart_data and chart_data.seasonal_data else '{"labels": ["Q1", "Q2", "Q3", "Q4"], "values": [380000, 420000, 350000, 480000]}' }};
        const mixData = {{ chart_data.mix_data | safe if chart_data and chart_data.mix_data else '{"labels": ["Premium", "Standard", "Budget"], "values": [40, 45, 15]}' }};
        const typeData = {{ chart_data.item_type_data | safe if chart_data and chart_data.item_type_data else '{"labels": ["Type A", "Type B", "Type C", "Type D"], "values": [30, 25, 25, 20]}' }};

        // Partner Performance Chart
        new Chart(document.getElementById('partnerPerformanceChart'), {
            type: 'bar',
            data: {
                labels: partnerData.labels || ['Partner A', 'Partner B', 'Partner C', 'Partner D'],
                datasets: [{
                    label: 'Revenue by Partner',
                    data: partnerData.values || [450000, 320000, 280000, 190000],
                    backgroundColor: tableauColors[2],
                    borderWidth: 0,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        callbacks: {
                            label: (context) => `Revenue: $${context.parsed.y.toLocaleString()}`
                        }
                    }
                },
                scales: {
                    y: { 
                        beginAtZero: true,
                        grid: { color: '#e9ecef' },
                        ticks: { callback: value => '$' + value.toLocaleString() }
                    },
                    x: { grid: { display: false } }
                }
            }
        });

        // Seasonal Pattern Chart
        new Chart(document.getElementById('seasonalPatternChart'), {
            type: 'line',
            data: {
                labels: seasonalData.labels || ['Q1', 'Q2', 'Q3', 'Q4'],
                datasets: [{
                    label: 'Quarterly Revenue',
                    data: seasonalData.values || [380000, 420000, 350000, 480000],
                    borderColor: tableauColors[3],
                    backgroundColor: tableauColors[3] + '20',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: tableauColors[3],
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        callbacks: {
                            label: (context) => `Revenue: $${context.parsed.y.toLocaleString()}`
                        }
                    }
                },
                scales: {
                    y: { 
                        beginAtZero: true,
                        grid: { color: '#e9ecef' },
                        ticks: { callback: value => '$' + value.toLocaleString() }
                    },
                    x: { grid: { display: false } }
                }
            }
        });

        // Revenue Mix Chart
        new Chart(document.getElementById('revenueMixChart'), {
            type: 'pie',
            data: {
                labels: mixData.labels || ['Premium', 'Standard', 'Budget'],
                datasets: [{
                    data: mixData.values || [40, 45, 15],
                    backgroundColor: [tableauColors[4], tableauColors[0], tableauColors[1]],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { 
                        position: 'bottom',
                        labels: { padding: 20, usePointStyle: true }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        callbacks: {
                            label: (context) => `${context.label}: ${context.parsed}%`
                        }
                    }
                }
            }
        });

        // Product Type Chart
        new Chart(document.getElementById('productTypeChart'), {
            type: 'doughnut',
            data: {
                labels: typeData.labels || ['Type A', 'Type B', 'Type C', 'Type D'],
                datasets: [{
                    data: typeData.values || [30, 25, 25, 20],
                    backgroundColor: tableauColors.slice(5, 9),
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { 
                        position: 'bottom',
                        labels: { padding: 20, usePointStyle: true }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        callbacks: {
                            label: (context) => `${context.label}: ${context.parsed}%`
                        }
                    }
                }
            }
        });
        {% endif %}

        // Populate metrics table
        const metricsData = [
            {% if title == 'Operational Analytics' %}
            ['Total Sales', '$1,240,000', '$1,150,000', '+7.8%', '✓ On Track'],
            ['Orders Processed', '2,456', '2,280', '+7.7%', '✓ On Track'],
            ['Avg Order Value', '$505', '$504', '+0.2%', '→ Stable'],
            ['Customer Satisfaction', '94.2%', '93.8%', '+0.4%', '✓ Excellent']
            {% else %}
            ['Market Share', '23.4%', '22.1%', '+1.3%', '✓ Growing'],
            ['Partner Revenue', '$2,140,000', '$1,980,000', '+8.1%', '✓ Strong'],
            ['Product Portfolio', '84 SKUs', '79 SKUs', '+6.3%', '✓ Expanding'],
            ['ROI', '24.7%', '23.2%', '+1.5%', '✓ Improving']
            {% endif %}
        ];

        const tableBody = document.getElementById('metricsTableBody');
        metricsData.forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = row.map(cell => `<td>${cell}</td>`).join('');
            tableBody.appendChild(tr);
        });

        // Filter functionality
        document.querySelectorAll('.filter-control').forEach(filter => {
            filter.addEventListener('change', function() {
                console.log(`Filter ${this.id} changed to: ${this.value}`);
                // Add filter functionality here
            });
        });
        </script>

        {% else %}
        <!-- No Data State -->
        <div class="chart-container">
            <div class="chart-header">
                <div class="chart-title">⚠️ Data Loading Required</div>
                <div class="chart-subtitle">Please check data connection and try again</div>
            </div>
            <div class="chart-content">
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle" style="font-size: 3em; color: var(--tableau-orange); margin-bottom: 15px;"></i>
                    <h3>Dashboard Unavailable</h3>
                    <p>Data is currently being loaded. Please refresh the page in a moment.</p>
                </div>
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sales Dashboard - {{ title }}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
            max-width: 1400px; 
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
            position: relative;
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
        .nav-buttons {
            position: absolute;
            top: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
        }
        .nav-btn {
            padding: 8px 16px;
            background: rgba(255,255,255,0.2);
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-size: 0.9em;
            transition: background 0.3s ease;
        }
        .nav-btn:hover {
            background: rgba(255,255,255,0.3);
            color: white;
            text-decoration: none;
        }
        .nav-btn.active {
            background: #ff6b6b;
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
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin: 30px 0;
        }
        .chart-container {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .chart-container h3 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-weight: 600;
            text-align: center;
        }
        .chart-container .subtitle {
            color: #6c757d;
            font-size: 0.9em;
            text-align: center;
            margin-bottom: 20px;
        }
        .chart-wrapper {
            position: relative;
            height: 400px;
            width: 100%;
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
            <div class="nav-buttons">
                <a href="/operational" class="nav-btn {{ 'active' if title == 'Operational View' else '' }}">⚡ Operational</a>
                <a href="/strategic" class="nav-btn {{ 'active' if title == 'Strategic Analytics' else '' }}">🎯 Strategic Analytics</a>
            </div>
            <h1>📊 Sales Dashboard</h1>
            <h2>{{ title }}</h2>
            <p>{{ subtitle }}</p>
        </div>
        
        <div class="status-card {{ 'success' if data_loaded else 'error' }}">
            <h3>📊 System Status</h3>
            <div class="metric">
                <strong>Status:</strong> {{ '✅ Data Loaded' if data_loaded else '❌ No Data' }}
            </div>
            {% if data_loaded and record_count %}
            <div class="metric">
                <strong>Records:</strong> {{ "{:,}".format(record_count) }}
            </div>
            {% endif %}
            <div class="metric">
                <strong>Last Updated:</strong> {{ timestamp }}
            </div>
            {% if memory_usage %}
            <div class="metric">
                <strong>Memory Usage:</strong> {{ memory_usage }} MB
            </div>
            {% endif %}
        </div>

        {% if data_loaded %}
        <div class="charts-grid">
            {% if title == 'Operational View' %}
            <!-- Operational Dashboard Charts -->
            <div class="chart-container">
                <h3>OVERALL SALES PERFORMANCE</h3>
                <div class="subtitle">Current vs Previous Month Comparison</div>
                <div class="chart-wrapper">
                    <canvas id="salesPerformanceChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h3>MONTH-OVER-MONTH SALES GROWTH</h3>
                <div class="subtitle">Trend KPI - Growth Tracking</div>
                <div class="chart-wrapper">
                    <canvas id="salesGrowthChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h3>TOP PRODUCTS PERFORMANCE</h3>
                <div class="subtitle">Best Selling Items Analysis</div>
                <div class="chart-wrapper">
                    <canvas id="topProductsChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h3>SALES BY CATEGORY</h3>
                <div class="subtitle">Category Distribution Analysis</div>
                <div class="chart-wrapper">
                    <canvas id="salesCategoryChart"></canvas>
                </div>
            </div>
            {% else %}
            <!-- Strategic Dashboard Charts -->
            <div class="chart-container">
                <h3>SALES PER SUPPLIER</h3>
                <div class="subtitle">Partnership KPI - Supplier Performance</div>
                <div class="chart-wrapper">
                    <canvas id="supplierChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h3>SALES SEASONALITY</h3>
                <div class="subtitle">Trend Analysis - Seasonal Patterns</div>
                <div class="chart-wrapper">
                    <canvas id="seasonalityChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h3>SALES MIX</h3>
                <div class="subtitle">Strategic KPI - Product Category Analysis</div>
                <div class="chart-wrapper">
                    <canvas id="salesMixChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h3>SALES BY ITEM TYPE</h3>
                <div class="subtitle">Performance KPI - Category Analysis</div>
                <div class="chart-wrapper">
                    <canvas id="itemTypeChart"></canvas>
                </div>
            </div>
            {% endif %}
        </div>

        <script>
        // Chart data and configuration
        {% if title == 'Operational View' %}
        // Operational Charts
        const salesData = {{ chart_data.sales_performance | safe if chart_data and chart_data.sales_performance else '[]' }};
        const growthData = {{ chart_data.growth_data | safe if chart_data and chart_data.growth_data else '[]' }};
        const productData = {{ chart_data.top_products | safe if chart_data and chart_data.top_products else '[]' }};
        const categoryData = {{ chart_data.category_data | safe if chart_data and chart_data.category_data else '[]' }};

        // Sales Performance Chart
        new Chart(document.getElementById('salesPerformanceChart'), {
            type: 'bar',
            data: {
                labels: ['Previous Month', 'Current Month'],
                datasets: [{
                    label: 'Sales Amount',
                    data: salesData.length >= 2 ? [salesData[0], salesData[1]] : [150000, 180000],
                    backgroundColor: ['#ff6b6b', '#4ecdc4'],
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { callback: value => '$' + value.toLocaleString() } } }
            }
        });

        // Growth Chart
        new Chart(document.getElementById('salesGrowthChart'), {
            type: 'line',
            data: {
                labels: growthData.labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Monthly Growth %',
                    data: growthData.values || [5, 12, 8, 15, 10, 18],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { callback: value => value + '%' } } }
            }
        });

        // Top Products Chart
        new Chart(document.getElementById('topProductsChart'), {
            type: 'doughnut',
            data: {
                labels: productData.labels || ['Product A', 'Product B', 'Product C', 'Product D', 'Others'],
                datasets: [{
                    data: productData.values || [35, 25, 20, 15, 5],
                    backgroundColor: ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });

        // Category Chart
        new Chart(document.getElementById('salesCategoryChart'), {
            type: 'bar',
            data: {
                labels: categoryData.labels || ['Electronics', 'Clothing', 'Books', 'Home & Garden'],
                datasets: [{
                    label: 'Sales by Category',
                    data: categoryData.values || [320000, 180000, 90000, 140000],
                    backgroundColor: '#667eea',
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { callback: value => '$' + value.toLocaleString() } } }
            }
        });

        {% else %}
        // Strategic Charts
        const supplierData = {{ chart_data.supplier_data | safe if chart_data and chart_data.supplier_data else '[]' }};
        const seasonalData = {{ chart_data.seasonal_data | safe if chart_data and chart_data.seasonal_data else '[]' }};
        const mixData = {{ chart_data.mix_data | safe if chart_data and chart_data.mix_data else '[]' }};
        const itemTypeData = {{ chart_data.item_type_data | safe if chart_data and chart_data.item_type_data else '[]' }};

        // Supplier Chart
        new Chart(document.getElementById('supplierChart'), {
            type: 'bar',
            data: {
                labels: supplierData.labels || ['Supplier A', 'Supplier B', 'Supplier C', 'Supplier D'],
                datasets: [{
                    label: 'Sales by Supplier',
                    data: supplierData.values || [450000, 320000, 280000, 190000],
                    backgroundColor: '#4ecdc4',
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { callback: value => '$' + value.toLocaleString() } } }
            }
        });

        // Seasonality Chart
        new Chart(document.getElementById('seasonalityChart'), {
            type: 'line',
            data: {
                labels: seasonalData.labels || ['Q1', 'Q2', 'Q3', 'Q4'],
                datasets: [{
                    label: 'Seasonal Sales Trend',
                    data: seasonalData.values || [380000, 420000, 350000, 480000],
                    borderColor: '#ff6b6b',
                    backgroundColor: 'rgba(255, 107, 107, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { callback: value => '$' + value.toLocaleString() } } }
            }
        });

        // Sales Mix Chart
        new Chart(document.getElementById('salesMixChart'), {
            type: 'pie',
            data: {
                labels: mixData.labels || ['Premium', 'Standard', 'Budget'],
                datasets: [{
                    data: mixData.values || [40, 45, 15],
                    backgroundColor: ['#667eea', '#4ecdc4', '#ffeaa7']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });

        // Item Type Chart
        new Chart(document.getElementById('itemTypeChart'), {
            type: 'doughnut',
            data: {
                labels: itemTypeData.labels || ['Type A', 'Type B', 'Type C', 'Type D'],
                datasets: [{
                    data: itemTypeData.values || [30, 25, 25, 20],
                    backgroundColor: ['#96ceb4', '#45b7d1', '#ff6b6b', '#ffeaa7']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });
        {% endif %}
        </script>
        {% else %}
        <!-- No Data Available -->
        <div class="chart-container">
            <h3>⚠️ No Data Available</h3>
            <p>Please check the data loading process and try again.</p>
        </div>
        {% endif %}
        
        <div class="footer">
            <p>Sales Dashboard v2.0 | Azure App Service | Last Updated: {{ timestamp }}</p>
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

def generate_chart_data(dashboard_type="operational"):
    """Generate chart data for dashboards"""
    if not data_loaded or df is None:
        return None
    
    try:
        chart_data = {}
        
        if dashboard_type == "operational":
            # Sales Performance (simple monthly comparison)
            chart_data['sales_performance'] = [150000, 180000]
            
            # Growth data (monthly trend)
            if 'Order Date' in df.columns:
                monthly_sales = df.groupby(df['Order Date'].dt.to_period('M')).agg({
                    'Sales': 'sum'
                }).tail(6)
                chart_data['growth_data'] = {
                    'labels': [str(period) for period in monthly_sales.index],
                    'values': monthly_sales['Sales'].tolist()
                }
            else:
                chart_data['growth_data'] = {
                    'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    'values': [150000, 165000, 140000, 190000, 175000, 200000]
                }
            
            # Top products
            if 'Product Name' in df.columns and 'Sales' in df.columns:
                top_products = df.groupby('Product Name')['Sales'].sum().nlargest(5)
                chart_data['top_products'] = {
                    'labels': top_products.index.tolist(),
                    'values': top_products.values.tolist()
                }
            else:
                chart_data['top_products'] = {
                    'labels': ['Product A', 'Product B', 'Product C', 'Product D', 'Others'],
                    'values': [35000, 28000, 22000, 18000, 12000]
                }
            
            # Category data
            if 'Category' in df.columns and 'Sales' in df.columns:
                category_sales = df.groupby('Category')['Sales'].sum()
                chart_data['category_data'] = {
                    'labels': category_sales.index.tolist(),
                    'values': category_sales.values.tolist()
                }
            else:
                chart_data['category_data'] = {
                    'labels': ['Electronics', 'Clothing', 'Books', 'Home & Garden'],
                    'values': [320000, 180000, 90000, 140000]
                }
                
        else:  # strategic
            # Supplier data
            if 'Ship Mode' in df.columns and 'Sales' in df.columns:
                supplier_sales = df.groupby('Ship Mode')['Sales'].sum().nlargest(4)
                chart_data['supplier_data'] = {
                    'labels': supplier_sales.index.tolist(),
                    'values': supplier_sales.values.tolist()
                }
            else:
                chart_data['supplier_data'] = {
                    'labels': ['Supplier A', 'Supplier B', 'Supplier C', 'Supplier D'],
                    'values': [450000, 320000, 280000, 190000]
                }
            
            # Seasonal data
            if 'Order Date' in df.columns and 'Sales' in df.columns:
                quarterly_sales = df.groupby(df['Order Date'].dt.quarter)['Sales'].sum()
                chart_data['seasonal_data'] = {
                    'labels': [f'Q{q}' for q in quarterly_sales.index],
                    'values': quarterly_sales.values.tolist()
                }
            else:
                chart_data['seasonal_data'] = {
                    'labels': ['Q1', 'Q2', 'Q3', 'Q4'],
                    'values': [380000, 420000, 350000, 480000]
                }
            
            # Mix data (Premium/Standard/Budget)
            chart_data['mix_data'] = {
                'labels': ['Premium', 'Standard', 'Budget'],
                'values': [40, 45, 15]
            }
            
            # Item type data
            if 'Sub-Category' in df.columns and 'Sales' in df.columns:
                item_types = df.groupby('Sub-Category')['Sales'].sum().nlargest(4)
                total = item_types.sum()
                chart_data['item_type_data'] = {
                    'labels': item_types.index.tolist(),
                    'values': [(val/total*100) for val in item_types.values]
                }
            else:
                chart_data['item_type_data'] = {
                    'labels': ['Type A', 'Type B', 'Type C', 'Type D'],
                    'values': [30, 25, 25, 20]
                }
        
        return chart_data
        
    except Exception as e:
        logger.error(f"Error generating chart data: {e}")
        return None

@app.route('/operational')
def operational():
    try:
        chart_data = generate_chart_data("operational")
        return render_template_string(BLOOMBERG_DASHBOARD_TEMPLATE,
            title="Operational Analytics",
            subtitle="Real-time Performance Monitoring & Daily Operations", 
            data_loaded=data_loaded,
            record_count=len(df) if data_loaded and df is not None else 0,
            file_path=data_info.get('file_path', '') if data_loaded else '',
            memory_usage=data_info.get('memory_usage_mb', '') if data_loaded else '',
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            chart_data=chart_data
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
    try:
        chart_data = generate_chart_data("strategic")
        return render_template_string(BLOOMBERG_DASHBOARD_TEMPLATE,
            title="Strategic Analytics", 
            subtitle="Long-term Business Intelligence & Partnership Analysis",
            data_loaded=data_loaded,
            record_count=len(df) if data_loaded and df is not None else 0,
            file_path=data_info.get('file_path', '') if data_loaded else '',
            memory_usage=data_info.get('memory_usage_mb', '') if data_loaded else '',
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            chart_data=chart_data
        )
    except Exception as e:
        return f"""
        <html>
        <body>
        <h1>Strategic Dashboard Error</h1>
        <p>Error rendering dashboard: {str(e)}</p>
        <p>Data loaded: {data_loaded}</p>
        <p>Records: {len(df) if data_loaded and df is not None else 0}</p>
        </body>
        </html>
        """

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
