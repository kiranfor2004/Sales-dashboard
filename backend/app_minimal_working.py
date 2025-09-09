from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# Load data once at startup to improve performance
print("Loading filtered sales data (2024-2025 only)...")
try:
    df = pd.read_csv('../Sales data - Filtered', sep='\t')
    print(f"Filtered data loaded successfully! Shape: {df.shape}")
    print(f"Years included: {sorted(df['YEAR'].unique())}")
except Exception as e:
    print(f"Error loading filtered data: {e}")
    df = pd.DataFrame()  # Empty dataframe as fallback

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'message': 'Backend is working', 'data_loaded': len(df) > 0, 'records': len(df)})

@app.route('/api/kpi_data', methods=['GET'])
def get_kpi_data():
    try:
        if len(df) == 0:
            return jsonify({'error': 'No data available'})
            
        latest_year = df['YEAR'].max()
        latest_month = df[df['YEAR'] == latest_year]['MONTH'].max()

        if latest_month == 1:
            prev_month = 12
            prev_year = latest_year - 1
        else:
            prev_month = latest_month - 1
            prev_year = latest_year

        current_data = df[(df['YEAR'] == latest_year) & (df['MONTH'] == latest_month)]
        previous_data = df[(df['YEAR'] == prev_year) & (df['MONTH'] == prev_month)]

        current_retail = current_data['RETAIL SALES'].sum() if len(current_data) > 0 else 0
        current_warehouse = current_data['WAREHOUSE SALES'].sum() if len(current_data) > 0 else 0
        prev_retail = previous_data['RETAIL SALES'].sum() if len(previous_data) > 0 else 0
        prev_warehouse = previous_data['WAREHOUSE SALES'].sum() if len(previous_data) > 0 else 0

        retail_change = ((current_retail - prev_retail) / prev_retail * 100) if prev_retail > 0 else 0
        warehouse_change = ((current_warehouse - prev_warehouse) / prev_warehouse * 100) if prev_warehouse > 0 else 0

        total_current = current_retail + current_warehouse
        total_previous = prev_retail + prev_warehouse
        total_change = ((total_current - total_previous) / total_previous * 100) if total_previous > 0 else 0

        # Get top supplier
        supplier_sales = df.groupby('SUPPLIER')['RETAIL SALES'].sum().sort_values(ascending=False)
        top_supplier = supplier_sales.index[0] if len(supplier_sales) > 0 else 'N/A'
        
        kpi_data = {
            'current_retail_sales': float(current_retail),
            'current_warehouse_sales': float(current_warehouse),
            'retail_change_percent': float(retail_change),
            'warehouse_change_percent': float(warehouse_change),
            'total_sales_current': float(total_current),
            'total_change_percent': float(total_change),
            'top_supplier': str(top_supplier),
            'total_suppliers': int(df['SUPPLIER'].nunique()),
            'total_items': int(df['ITEM CODE'].nunique()),
            'current_month': f"{latest_year}-{latest_month:02d}"
        }
        
        return jsonify(kpi_data)
    except Exception as e:
        return jsonify({'error': f'Error calculating KPI data: {str(e)}'})

@app.route('/api/sales_performance', methods=['GET'])
def get_sales_performance():
    try:
        if len(df) == 0:
            return jsonify({'error': 'No data available'})

        total_retail = df['RETAIL SALES'].sum()
        total_warehouse = df['WAREHOUSE SALES'].sum()
        total_transfers = df['RETAIL TRANSFERS'].sum()
        
        performance_data = {
            'retail_sales': float(total_retail),
            'warehouse_sales': float(total_warehouse),
            'retail_transfers': float(total_transfers),
            'total_revenue': float(total_retail + total_warehouse + total_transfers),
            'revenue_streams': 3
        }
        
        return jsonify(performance_data)
    except Exception as e:
        return jsonify({'error': f'Error calculating sales performance: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000)
