from flask import Flask, render_template_string, jsonify
from flask_cors import CORS
import pandas as pd
import json
import logging
import os
import sys

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
df_global = None
data_loaded = False
load_errors = []

def log_message(message):
    """Print and store log messages"""
    print(message)
    sys.stdout.flush()
    logger.info(message)

def load_data():
    """Load the sales data from your actual files"""
    global df_global, data_loaded, load_errors
    
    if df_global is not None:
        return df_global
    
    log_message("=== LOADING SALES DATA ===")
    
    # Try to load your actual data files
    possible_paths = [
        'Sales data - Filtered',
        './Sales data - Filtered',
        '/home/site/wwwroot/Sales data - Filtered',
        'Sales data',
        './Sales data',
        '/home/site/wwwroot/Sales data'
    ]
    
    for path in possible_paths:
        try:
            log_message(f"Trying to load: {path}")
            
            # Try reading as CSV with tab separator (your data appears to be tab-separated)
            df = pd.read_csv(path, sep='\t', encoding='utf-8')
            
            if len(df) > 0:
                log_message(f"✅ Successfully loaded {len(df)} records from {path}")
                log_message(f"Columns: {list(df.columns)}")
                log_message(f"Data shape: {df.shape}")
                
                # Store the data
                df_global = df
                data_loaded = True
                return df_global
                
        except Exception as e:
            log_message(f"❌ Failed to load {path}: {str(e)}")
            load_errors.append(f"{path}: {str(e)}")
            continue
    
    # If no data loaded, create sample data
    log_message("⚠️ No data files found, creating sample data")
    df_global = create_sample_data()
    return df_global

def create_sample_data():
    """Create sample data that matches your data structure"""
    log_message("Creating sample data...")
    
    import random
    from datetime import datetime, timedelta
    
    # Create sample data matching your structure
    sample_data = []
    
    suppliers = ['REPUBLIC NATIONAL DISTRIBUTING CO', 'PWSWN INC', 'RELIABLE CHURCHILL LLLP', 'LANTERNA DISTRIBUTORS INC']
    item_types = ['WINE', 'BEER', 'SPIRITS']
    
    for i in range(1000):
        sample_data.append({
            'YEAR': random.choice([2024, 2025]),
            'MONTH': random.randint(1, 12),
            'SUPPLIER': random.choice(suppliers),
            'ITEM CODE': f'10000{i}',
            'ITEM DESCRIPTION': f'Sample Item {i}',
            'ITEM TYPE': random.choice(item_types),
            'RETAIL SALES': round(random.uniform(0, 1000), 2),
            'RETAIL TRANSFERS': round(random.uniform(0, 100), 2),
            'WAREHOUSE SALES': round(random.uniform(0, 500), 2)
        })
    
    return pd.DataFrame(sample_data)

# HTML Templates
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sales Dashboard 2025</title>
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
        .status {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .status-good { border-left: 5px solid #28a745; }
        .status-warning { border-left: 5px solid #ffc107; }
        .status-error { border-left: 5px solid #dc3545; }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
        }
        .dashboard-card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Sales Dashboard</h1>
            <p>Retail Analytics Platform 2024-2025</p>
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
                    Retail sales, transfers, and warehouse metrics
                </div>
            </a>
            
            <a href="/strategic" class="dashboard-card strategic">
                <div class="card-icon">🎯</div>
                <div class="card-title">Strategic Dashboard</div>
                <div class="card-description">
                    Strategic insights and performance trends
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
            status_title = "✅ Data Loaded Successfully"
            status_message = f"Loaded {len(df):,} records. Data from {df['YEAR'].min()}-{df['YEAR'].max()}. Dashboard ready!"
        else:
            status_class = "status-warning"
            status_title = "⚠️ Using Sample Data"
            status_message = "Could not load data files. Displaying sample data for demonstration."
    except Exception as e:
        status_class = "status-error"
        status_title = "❌ Data Loading Error"
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
            <p>Retail Operations Analytics</p>
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
            // Load charts
            Promise.all([
                fetch('/api/monthly_retail_sales').then(r => r.json()),
                fetch('/api/monthly_warehouse_sales').then(r => r.json()),
                fetch('/api/monthly_transfers').then(r => r.json()),
                fetch('/api/item_type_distribution').then(r => r.json()),
                fetch('/api/top_suppliers').then(r => r.json()),
                fetch('/api/monthly_total_volume').then(r => r.json())
            ]).then(data => {
                const charts = ['chart1', 'chart2', 'chart3', 'chart4', 'chart5', 'chart6'];
                data.forEach((chartData, index) => {
                    if (chartData.data) {
                        Plotly.newPlot(charts[index], chartData.data, chartData.layout, {responsive: true});
                    }
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
            <p>Strategic Business Insights</p>
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
                fetch('/api/yearly_sales_trend').then(r => r.json()),
                fetch('/api/supplier_performance').then(r => r.json()),
                fetch('/api/seasonal_analysis').then(r => r.json()),
                fetch('/api/sales_vs_transfers').then(r => r.json()),
                fetch('/api/item_type_trends').then(r => r.json())
            ]).then(data => {
                const charts = ['chart1', 'chart2', 'chart3', 'chart4', 'chart5'];
                data.forEach((chartData, index) => {
                    if (chartData.data) {
                        Plotly.newPlot(charts[index], chartData.data, chartData.layout, {responsive: true});
                    }
                });
            });
        </script>
    </body>
    </html>
    """)

# API Endpoints matching your data structure
@app.route('/api/monthly_retail_sales')
def monthly_retail_sales():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        # Group by year-month and sum retail sales
        df['YEAR_MONTH'] = df['YEAR'].astype(str) + '-' + df['MONTH'].astype(str).str.zfill(2)
        monthly_sales = df.groupby('YEAR_MONTH')['RETAIL SALES'].sum().sort_index()
        
        return jsonify({
            'data': [{
                'x': list(monthly_sales.index),
                'y': list(monthly_sales.values),
                'type': 'bar',
                'name': 'Monthly Retail Sales',
                'marker': {'color': '#1f77b4'}
            }],
            'layout': {
                'title': 'Monthly Retail Sales',
                'xaxis': {'title': 'Month'},
                'yaxis': {'title': 'Sales ($)'},
                'showlegend': False
            }
        })
    except Exception as e:
        log_message(f"Error in monthly_retail_sales: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/monthly_warehouse_sales')
def monthly_warehouse_sales():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        df['YEAR_MONTH'] = df['YEAR'].astype(str) + '-' + df['MONTH'].astype(str).str.zfill(2)
        monthly_warehouse = df.groupby('YEAR_MONTH')['WAREHOUSE SALES'].sum().sort_index()
        
        return jsonify({
            'data': [{
                'x': list(monthly_warehouse.index),
                'y': list(monthly_warehouse.values),
                'type': 'bar',
                'name': 'Monthly Warehouse Sales',
                'marker': {'color': '#ff7f0e'}
            }],
            'layout': {
                'title': 'Monthly Warehouse Sales',
                'xaxis': {'title': 'Month'},
                'yaxis': {'title': 'Sales ($)'},
                'showlegend': False
            }
        })
    except Exception as e:
        log_message(f"Error in monthly_warehouse_sales: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/monthly_transfers')
def monthly_transfers():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        df['YEAR_MONTH'] = df['YEAR'].astype(str) + '-' + df['MONTH'].astype(str).str.zfill(2)
        monthly_transfers = df.groupby('YEAR_MONTH')['RETAIL TRANSFERS'].sum().sort_index()
        
        return jsonify({
            'data': [{
                'x': list(monthly_transfers.index),
                'y': list(monthly_transfers.values),
                'type': 'bar',
                'name': 'Monthly Transfers',
                'marker': {'color': '#2ca02c'}
            }],
            'layout': {
                'title': 'Monthly Retail Transfers',
                'xaxis': {'title': 'Month'},
                'yaxis': {'title': 'Transfers'},
                'showlegend': False
            }
        })
    except Exception as e:
        log_message(f"Error in monthly_transfers: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/item_type_distribution')
def item_type_distribution():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        item_distribution = df.groupby('ITEM TYPE')['RETAIL SALES'].sum()
        
        return jsonify({
            'data': [{
                'labels': list(item_distribution.index),
                'values': list(item_distribution.values),
                'type': 'pie',
                'name': 'Item Type Distribution'
            }],
            'layout': {
                'title': 'Sales by Item Type',
                'showlegend': True
            }
        })
    except Exception as e:
        log_message(f"Error in item_type_distribution: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/top_suppliers')
def top_suppliers():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        top_suppliers = df.groupby('SUPPLIER')['RETAIL SALES'].sum().nlargest(10)
        
        return jsonify({
            'data': [{
                'x': list(top_suppliers.values),
                'y': list(top_suppliers.index),
                'type': 'bar',
                'orientation': 'h',
                'name': 'Top Suppliers',
                'marker': {'color': '#d62728'}
            }],
            'layout': {
                'title': 'Top 10 Suppliers by Sales',
                'xaxis': {'title': 'Sales ($)'},
                'yaxis': {'title': 'Supplier'},
                'showlegend': False
            }
        })
    except Exception as e:
        log_message(f"Error in top_suppliers: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/monthly_total_volume')
def monthly_total_volume():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        df['YEAR_MONTH'] = df['YEAR'].astype(str) + '-' + df['MONTH'].astype(str).str.zfill(2)
        df['TOTAL_VOLUME'] = df['RETAIL SALES'] + df['WAREHOUSE SALES'] + df['RETAIL TRANSFERS']
        monthly_volume = df.groupby('YEAR_MONTH')['TOTAL_VOLUME'].sum().sort_index()
        
        return jsonify({
            'data': [{
                'x': list(monthly_volume.index),
                'y': list(monthly_volume.values),
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': 'Total Volume',
                'marker': {'color': '#9467bd'}
            }],
            'layout': {
                'title': 'Monthly Total Volume Trend',
                'xaxis': {'title': 'Month'},
                'yaxis': {'title': 'Total Volume'},
                'showlegend': False
            }
        })
    except Exception as e:
        log_message(f"Error in monthly_total_volume: {str(e)}")
        return jsonify({'error': str(e)})

# Strategic Dashboard APIs
@app.route('/api/yearly_sales_trend')
def yearly_sales_trend():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        yearly_sales = df.groupby('YEAR')['RETAIL SALES'].sum()
        
        return jsonify({
            'data': [{
                'x': list(yearly_sales.index),
                'y': list(yearly_sales.values),
                'type': 'bar',
                'name': 'Yearly Sales',
                'marker': {'color': '#1f77b4'}
            }],
            'layout': {
                'title': 'Yearly Sales Trend',
                'xaxis': {'title': 'Year'},
                'yaxis': {'title': 'Sales ($)'},
                'showlegend': False
            }
        })
    except Exception as e:
        log_message(f"Error in yearly_sales_trend: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/supplier_performance')
def supplier_performance():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        supplier_perf = df.groupby('SUPPLIER').agg({
            'RETAIL SALES': 'sum',
            'WAREHOUSE SALES': 'sum'
        }).head(10)
        
        return jsonify({
            'data': [
                {
                    'x': list(supplier_perf.index),
                    'y': list(supplier_perf['RETAIL SALES']),
                    'type': 'bar',
                    'name': 'Retail Sales',
                    'marker': {'color': '#1f77b4'}
                },
                {
                    'x': list(supplier_perf.index),
                    'y': list(supplier_perf['WAREHOUSE SALES']),
                    'type': 'bar',
                    'name': 'Warehouse Sales',
                    'marker': {'color': '#ff7f0e'}
                }
            ],
            'layout': {
                'title': 'Supplier Performance Comparison',
                'xaxis': {'title': 'Supplier'},
                'yaxis': {'title': 'Sales ($)'},
                'barmode': 'group'
            }
        })
    except Exception as e:
        log_message(f"Error in supplier_performance: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/seasonal_analysis')
def seasonal_analysis():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        seasonal = df.groupby('MONTH')['RETAIL SALES'].mean()
        
        return jsonify({
            'data': [{
                'x': list(seasonal.index),
                'y': list(seasonal.values),
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': 'Seasonal Pattern',
                'marker': {'color': '#2ca02c'}
            }],
            'layout': {
                'title': 'Seasonal Sales Pattern',
                'xaxis': {'title': 'Month'},
                'yaxis': {'title': 'Average Sales ($)'},
                'showlegend': False
            }
        })
    except Exception as e:
        log_message(f"Error in seasonal_analysis: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/sales_vs_transfers')
def sales_vs_transfers():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        return jsonify({
            'data': [{
                'x': df['RETAIL SALES'].tolist(),
                'y': df['RETAIL TRANSFERS'].tolist(),
                'mode': 'markers',
                'type': 'scatter',
                'name': 'Sales vs Transfers',
                'marker': {'color': '#d62728', 'size': 8}
            }],
            'layout': {
                'title': 'Retail Sales vs Transfers Correlation',
                'xaxis': {'title': 'Retail Sales ($)'},
                'yaxis': {'title': 'Retail Transfers'},
                'showlegend': False
            }
        })
    except Exception as e:
        log_message(f"Error in sales_vs_transfers: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/item_type_trends')
def item_type_trends():
    try:
        df = load_data()
        if df is None or len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        df['YEAR_MONTH'] = df['YEAR'].astype(str) + '-' + df['MONTH'].astype(str).str.zfill(2)
        trends = df.groupby(['YEAR_MONTH', 'ITEM TYPE'])['RETAIL SALES'].sum().unstack(fill_value=0)
        
        data = []
        for item_type in trends.columns:
            data.append({
                'x': list(trends.index),
                'y': list(trends[item_type]),
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': item_type
            })
        
        return jsonify({
            'data': data,
            'layout': {
                'title': 'Item Type Sales Trends',
                'xaxis': {'title': 'Month'},
                'yaxis': {'title': 'Sales ($)'},
                'showlegend': True
            }
        })
    except Exception as e:
        log_message(f"Error in item_type_trends: {str(e)}")
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    log_message("Starting Sales Dashboard...")
    app.run(debug=True, host='0.0.0.0', port=5000)
