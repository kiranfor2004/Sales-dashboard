from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# Load data once at startup
print("Loading sales data...")
try:
    df = pd.read_csv('../Sales data', sep='\t')
    print(f"Data loaded successfully! Shape: {df.shape}")
except Exception as e:
    print(f"Error loading data: {e}")
    df = None

@app.route('/api/test')
def test():
    return jsonify({'message': 'Server is working', 'data_loaded': df is not None})

@app.route('/api/kpi_data')
def get_kpi_data():
    if df is None:
        return jsonify({'error': 'Data not loaded'})
    
    try:
        latest_year = df['YEAR'].max()
        latest_month = df[df['YEAR'] == latest_year]['MONTH'].max()

        if latest_month == 1:
            previous_month = 12
            previous_year = latest_year - 1
        else:
            previous_month = latest_month - 1
            previous_year = latest_year

        current_month_data = df[(df['YEAR'] == latest_year) & (df['MONTH'] == latest_month)]
        previous_month_data = df[(df['YEAR'] == previous_year) & (df['MONTH'] == previous_month)]

        current_retail_sales = float(current_month_data['RETAIL SALES'].sum())
        current_warehouse_sales = float(current_month_data['WAREHOUSE SALES'].sum())

        previous_retail_sales = float(previous_month_data['RETAIL SALES'].sum())
        previous_warehouse_sales = float(previous_month_data['WAREHOUSE SALES'].sum())

        kpi_data = {
            'labels': ['Retail Sales', 'Warehouse Sales'],
            'current_month': {
                'name': f'{latest_year}-{latest_month:02d}',
                'values': [current_retail_sales, current_warehouse_sales]
            },
            'previous_month': {
                'name': f'{previous_year}-{previous_month:02d}',
                'values': [previous_retail_sales, previous_warehouse_sales]
            }
        }
        return jsonify(kpi_data)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/overall_sales_performance')
def get_overall_sales_performance():
    if df is None:
        return jsonify({'error': 'Data not loaded'})
    
    try:
        total_retail_sales = float(df['RETAIL SALES'].sum())
        total_retail_transfers = float(df['RETAIL TRANSFERS'].sum())
        total_warehouse_sales = float(df['WAREHOUSE SALES'].sum())
        
        grand_total = total_retail_sales + total_retail_transfers + total_warehouse_sales
        
        retail_percentage = (total_retail_sales / grand_total * 100) if grand_total > 0 else 0
        transfers_percentage = (total_retail_transfers / grand_total * 100) if grand_total > 0 else 0
        warehouse_percentage = (total_warehouse_sales / grand_total * 100) if grand_total > 0 else 0
        
        overall_performance_data = {
            'revenue_streams': ['Retail Sales', 'Retail Transfers', 'Warehouse Sales'],
            'total_amounts': [total_retail_sales, total_retail_transfers, total_warehouse_sales],
            'percentages': [retail_percentage, transfers_percentage, warehouse_percentage],
            'grand_total': grand_total,
            'summary': {
                'total_retail_sales': total_retail_sales,
                'total_retail_transfers': total_retail_transfers,
                'total_warehouse_sales': total_warehouse_sales,
                'grand_total': grand_total
            }
        }
        
        return jsonify(overall_performance_data)
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000)
