from flask import Flask, render_template_string, jsonify
from flask_cors import CORS
import pyodbc
import pandas as pd
import json
import logging
import os

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQL Server connection details - you'll need to update these
SQL_SERVER_CONFIG = {
    'server': 'SRIKIRANREDDY\\SQLEXPRESS',  # Update with your server
    'database': 'master',  # Update with your database name
    'trusted_connection': 'yes',
    'driver': '{ODBC Driver 17 for SQL Server}'
}

def get_sql_connection():
    """Create SQL Server connection"""
    try:
        # For Azure, we might need a different connection string
        if os.getenv('AZURE_SQL_SERVER'):
            # Azure SQL connection
            connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={os.getenv('AZURE_SQL_SERVER')};DATABASE={os.getenv('AZURE_SQL_DATABASE')};UID={os.getenv('AZURE_SQL_USERNAME')};PWD={os.getenv('AZURE_SQL_PASSWORD')}"
        else:
            # Local SQL Server connection
            connection_string = f"DRIVER={{{SQL_SERVER_CONFIG['driver']}}};SERVER={SQL_SERVER_CONFIG['server']};DATABASE={SQL_SERVER_CONFIG['database']};Trusted_Connection={SQL_SERVER_CONFIG['trusted_connection']}"
        
        conn = pyodbc.connect(connection_string)
        logger.info("Successfully connected to SQL Server")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to SQL Server: {str(e)}")
        return None

def get_data_from_sql():
    """Get data from SQL Server"""
    try:
        conn = get_sql_connection()
        if not conn:
            return None
        
        # Query the monthly analysis table (adjust table name as needed)
        query = "SELECT TOP 1000 * FROM [master].[dbo].[step02_monthly_analysis]"
        df = pd.read_sql(query, conn)
        conn.close()
        
        logger.info(f"Successfully loaded {len(df)} records from SQL Server")
        return df
    except Exception as e:
        logger.error(f"Error loading data from SQL Server: {str(e)}")
        return None

def get_sample_data():
    """Generate sample data if SQL connection fails"""
    logger.info("Using sample data for demonstration")
    
    import datetime
    from datetime import timedelta
    
    # Generate sample data that matches your dashboard structure
    sample_data = []
    base_date = datetime.datetime(2024, 1, 1)
    
    for i in range(100):
        sample_data.append({
            'analysis_month': (base_date + timedelta(days=i*30)).strftime('%Y-%m'),
            'symbol': f'STOCK{i%10}',
            'analysis_type': 'monthly',
            'peak_date': (base_date + timedelta(days=i*30)).strftime('%Y-%m-%d'),
            'peak_value': 100 + i * 10,
            'ttl_trd_qnty': 1000 + i * 100,
            'deliv_qty': 500 + i * 50,
            'close_price': 50 + i * 5,
            'turnover_lacs': 10 + i,
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return pd.DataFrame(sample_data)

# Global data variable
df_global = None

def load_data():
    """Load data from SQL Server or use sample data"""
    global df_global
    if df_global is None:
        logger.info("Loading data...")
        df_global = get_data_from_sql()
        if df_global is None:
            logger.warning("SQL Server connection failed, using sample data")
            df_global = get_sample_data()
    return df_global

# HTML Templates
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sales Dashboard - SQL Server Version</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 50px;
        }
        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin-top: 40px;
        }
        .dashboard-card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            text-decoration: none;
            color: inherit;
        }
        .dashboard-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }
        .card-icon {
            font-size: 3em;
            margin-bottom: 20px;
            text-align: center;
        }
        .card-title {
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 15px;
            text-align: center;
        }
        .card-description {
            color: #666;
            text-align: center;
            line-height: 1.6;
        }
        .operational { border-left: 5px solid #4CAF50; }
        .strategic { border-left: 5px solid #2196F3; }
        .status {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-top: 30px;
            text-align: center;
        }
        .status-good { border-left: 5px solid #28a745; }
        .status-warning { border-left: 5px solid #ffc107; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Sales Dashboard</h1>
            <p>SQL Server Data Analytics Platform</p>
        </div>
        
        <div class="status {{ status_class }}">
            <h3>{{ status_title }}</h3>
            <p>{{ status_message }}</p>
        </div>
        
        <div class="dashboard-grid">
            <a href="/operational" class="dashboard-card operational">
                <div class="card-icon">📈</div>
                <div class="card-title">Operational Dashboard</div>
                <div class="card-description">
                    Real-time operational metrics and KPIs for daily business monitoring
                </div>
            </a>
            
            <a href="/strategic" class="dashboard-card strategic">
                <div class="card-icon">🎯</div>
                <div class="card-title">Strategic Dashboard</div>
                <div class="card-description">
                    Strategic insights and long-term performance analytics
                </div>
            </a>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    """Home page with dashboard overview"""
    try:
        df = load_data()
        if df is not None and len(df) > 0:
            status_class = "status-good"
            status_title = "✅ Data Connected Successfully"
            status_message = f"Loaded {len(df):,} records from database. Dashboard is ready!"
        else:
            status_class = "status-warning"
            status_title = "⚠️ Using Sample Data"
            status_message = "Could not connect to SQL Server. Displaying sample data for demonstration."
    except Exception as e:
        status_class = "status-warning"
        status_title = "⚠️ Data Loading Issue"
        status_message = f"Error: {str(e)}"
    
    return render_template_string(HOME_TEMPLATE, 
                                status_class=status_class,
                                status_title=status_title,
                                status_message=status_message)

@app.route('/operational')
def operational():
    """Operational dashboard page"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Operational Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .dashboard-header { text-align: center; margin-bottom: 30px; }
            .charts-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }
            .chart-card { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        </style>
    </head>
    <body>
        <div class="dashboard-header">
            <h1>📈 Operational Dashboard</h1>
            <p>Real-time business metrics and KPIs</p>
        </div>
        <div class="charts-container">
            <div class="chart-card"><div id="chart1"></div></div>
            <div class="chart-card"><div id="chart2"></div></div>
            <div class="chart-card"><div id="chart3"></div></div>
            <div class="chart-card"><div id="chart4"></div></div>
            <div class="chart-card"><div id="chart5"></div></div>
            <div class="chart-card"><div id="chart6"></div></div>
        </div>
        
        <script>
            // Load operational charts
            Promise.all([
                fetch('/api/total_trade_quantity').then(r => r.json()),
                fetch('/api/average_close_price').then(r => r.json()),
                fetch('/api/total_delivery_quantity').then(r => r.json()),
                fetch('/api/total_turnover').then(r => r.json()),
                fetch('/api/average_peak_value').then(r => r.json()),
                fetch('/api/monthly_records_count').then(r => r.json())
            ]).then(data => {
                const charts = ['chart1', 'chart2', 'chart3', 'chart4', 'chart5', 'chart6'];
                data.forEach((chartData, index) => {
                    Plotly.newPlot(charts[index], chartData.data, chartData.layout, {responsive: true});
                });
            });
        </script>
    </body>
    </html>
    """)

@app.route('/strategic')
def strategic():
    """Strategic dashboard page"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Strategic Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .dashboard-header { text-align: center; margin-bottom: 30px; }
            .charts-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }
            .chart-card { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        </style>
    </head>
    <body>
        <div class="dashboard-header">
            <h1>🎯 Strategic Dashboard</h1>
            <p>Strategic insights and performance analytics</p>
        </div>
        <div class="charts-container">
            <div class="chart-card"><div id="chart1"></div></div>
            <div class="chart-card"><div id="chart2"></div></div>
            <div class="chart-card"><div id="chart3"></div></div>
            <div class="chart-card"><div id="chart4"></div></div>
            <div class="chart-card"><div id="chart5"></div></div>
        </div>
        
        <script>
            // Load strategic charts
            Promise.all([
                fetch('/api/peak_value_distribution').then(r => r.json()),
                fetch('/api/delivery_percentage_trend').then(r => r.json()),
                fetch('/api/symbol_performance').then(r => r.json()),
                fetch('/api/monthly_turnover_trend').then(r => r.json()),
                fetch('/api/price_volatility').then(r => r.json())
            ]).then(data => {
                const charts = ['chart1', 'chart2', 'chart3', 'chart4', 'chart5'];
                data.forEach((chartData, index) => {
                    Plotly.newPlot(charts[index], chartData.data, chartData.layout, {responsive: true});
                });
            });
        </script>
    </body>
    </html>
    """)

# API Endpoints for charts
@app.route('/api/total_trade_quantity')
def total_trade_quantity():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        monthly_totals = df.groupby('analysis_month')['ttl_trd_qnty'].sum().sort_index()
        
        return jsonify({
            'data': [{
                'x': list(monthly_totals.index),
                'y': list(monthly_totals.values),
                'type': 'bar',
                'name': 'Total Trade Quantity',
                'marker': {'color': '#1f77b4'}
            }],
            'layout': {
                'title': 'Total Trade Quantity by Month',
                'xaxis': {'title': 'Month'},
                'yaxis': {'title': 'Quantity'},
                'showlegend': False
            }
        })
    except Exception as e:
        logger.error(f"Error in total_trade_quantity: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/average_close_price')
def average_close_price():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        monthly_avg = df.groupby('analysis_month')['close_price'].mean().sort_index()
        
        return jsonify({
            'data': [{
                'x': list(monthly_avg.index),
                'y': list(monthly_avg.values),
                'type': 'bar',
                'name': 'Average Close Price',
                'marker': {'color': '#ff7f0e'}
            }],
            'layout': {
                'title': 'Average Close Price by Month',
                'xaxis': {'title': 'Month'},
                'yaxis': {'title': 'Price'},
                'showlegend': False
            }
        })
    except Exception as e:
        logger.error(f"Error in average_close_price: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/total_delivery_quantity')
def total_delivery_quantity():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        monthly_delivery = df.groupby('analysis_month')['deliv_qty'].sum().sort_index()
        
        return jsonify({
            'data': [{
                'x': list(monthly_delivery.index),
                'y': list(monthly_delivery.values),
                'type': 'bar',
                'name': 'Total Delivery Quantity',
                'marker': {'color': '#2ca02c'}
            }],
            'layout': {
                'title': 'Total Delivery Quantity by Month',
                'xaxis': {'title': 'Month'},
                'yaxis': {'title': 'Quantity'},
                'showlegend': False
            }
        })
    except Exception as e:
        logger.error(f"Error in total_delivery_quantity: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/total_turnover')
def total_turnover():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        monthly_turnover = df.groupby('analysis_month')['turnover_lacs'].sum().sort_index()
        
        return jsonify({
            'data': [{
                'x': list(monthly_turnover.index),
                'y': list(monthly_turnover.values),
                'type': 'bar',
                'name': 'Total Turnover',
                'marker': {'color': '#d62728'}
            }],
            'layout': {
                'title': 'Total Turnover by Month (Lacs)',
                'xaxis': {'title': 'Month'},
                'yaxis': {'title': 'Turnover (Lacs)'},
                'showlegend': False
            }
        })
    except Exception as e:
        logger.error(f"Error in total_turnover: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/average_peak_value')
def average_peak_value():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        monthly_peak = df.groupby('analysis_month')['peak_value'].mean().sort_index()
        
        return jsonify({
            'data': [{
                'x': list(monthly_peak.index),
                'y': list(monthly_peak.values),
                'type': 'bar',
                'name': 'Average Peak Value',
                'marker': {'color': '#9467bd'}
            }],
            'layout': {
                'title': 'Average Peak Value by Month',
                'xaxis': {'title': 'Month'},
                'yaxis': {'title': 'Peak Value'},
                'showlegend': False
            }
        })
    except Exception as e:
        logger.error(f"Error in average_peak_value: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/monthly_records_count')
def monthly_records_count():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        monthly_count = df.groupby('analysis_month').size().sort_index()
        
        return jsonify({
            'data': [{
                'x': list(monthly_count.index),
                'y': list(monthly_count.values),
                'type': 'bar',
                'name': 'Records Count',
                'marker': {'color': '#8c564b'}
            }],
            'layout': {
                'title': 'Monthly Records Count',
                'xaxis': {'title': 'Month'},
                'yaxis': {'title': 'Count'},
                'showlegend': False
            }
        })
    except Exception as e:
        logger.error(f"Error in monthly_records_count: {str(e)}")
        return jsonify({'error': str(e)})

# Strategic Dashboard APIs
@app.route('/api/peak_value_distribution')
def peak_value_distribution():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        return jsonify({
            'data': [{
                'x': df['peak_value'].tolist(),
                'type': 'histogram',
                'name': 'Peak Value Distribution',
                'marker': {'color': '#1f77b4'}
            }],
            'layout': {
                'title': 'Peak Value Distribution',
                'xaxis': {'title': 'Peak Value'},
                'yaxis': {'title': 'Frequency'},
                'showlegend': False
            }
        })
    except Exception as e:
        logger.error(f"Error in peak_value_distribution: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/delivery_percentage_trend')
def delivery_percentage_trend():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        df['delivery_percentage'] = (df['deliv_qty'] / df['ttl_trd_qnty'] * 100).fillna(0)
        monthly_delivery_pct = df.groupby('analysis_month')['delivery_percentage'].mean().sort_index()
        
        return jsonify({
            'data': [{
                'x': list(monthly_delivery_pct.index),
                'y': list(monthly_delivery_pct.values),
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': 'Delivery Percentage',
                'marker': {'color': '#2ca02c'}
            }],
            'layout': {
                'title': 'Delivery Percentage Trend',
                'xaxis': {'title': 'Month'},
                'yaxis': {'title': 'Delivery %'},
                'showlegend': False
            }
        })
    except Exception as e:
        logger.error(f"Error in delivery_percentage_trend: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/symbol_performance')
def symbol_performance():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        top_symbols = df.groupby('symbol')['turnover_lacs'].sum().nlargest(10)
        
        return jsonify({
            'data': [{
                'x': list(top_symbols.values),
                'y': list(top_symbols.index),
                'type': 'bar',
                'orientation': 'h',
                'name': 'Symbol Performance',
                'marker': {'color': '#ff7f0e'}
            }],
            'layout': {
                'title': 'Top 10 Symbols by Turnover',
                'xaxis': {'title': 'Turnover (Lacs)'},
                'yaxis': {'title': 'Symbol'},
                'showlegend': False
            }
        })
    except Exception as e:
        logger.error(f"Error in symbol_performance: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/monthly_turnover_trend')
def monthly_turnover_trend():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        monthly_turnover = df.groupby('analysis_month')['turnover_lacs'].sum().sort_index()
        
        return jsonify({
            'data': [{
                'x': list(monthly_turnover.index),
                'y': list(monthly_turnover.values),
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': 'Monthly Turnover',
                'marker': {'color': '#d62728'}
            }],
            'layout': {
                'title': 'Monthly Turnover Trend',
                'xaxis': {'title': 'Month'},
                'yaxis': {'title': 'Turnover (Lacs)'},
                'showlegend': False
            }
        })
    except Exception as e:
        logger.error(f"Error in monthly_turnover_trend: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/price_volatility')
def price_volatility():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        volatility = df.groupby('analysis_month')['close_price'].std().sort_index()
        
        return jsonify({
            'data': [{
                'x': list(volatility.index),
                'y': list(volatility.values),
                'type': 'bar',
                'name': 'Price Volatility',
                'marker': {'color': '#9467bd'}
            }],
            'layout': {
                'title': 'Price Volatility by Month',
                'xaxis': {'title': 'Month'},
                'yaxis': {'title': 'Standard Deviation'},
                'showlegend': False
            }
        })
    except Exception as e:
        logger.error(f"Error in price_volatility: {str(e)}")
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    logger.info("Starting Sales Dashboard SQL Server Version...")
    app.run(debug=True, host='0.0.0.0', port=5000)
