from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'message': 'Backend is working'})

@app.route('/api/sales_data', methods=['GET'])
def get_sales_data():
    try:
        df = pd.read_csv('../Sales data', sep='\t')
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/kpi_data', methods=['GET'])
def get_kpi_data():
    try:
        df = pd.read_csv('../Sales data', sep='\t')
        
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

        current_retail_sales = current_month_data['RETAIL SALES'].sum()
        current_warehouse_sales = current_month_data['WAREHOUSE SALES'].sum()

        previous_retail_sales = previous_month_data['RETAIL SALES'].sum()
        previous_warehouse_sales = previous_month_data['WAREHOUSE SALES'].sum()

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

@app.route('/api/sales_by_item_type', methods=['GET'])
def get_sales_by_item_type():
    try:
        df = pd.read_csv('../Sales data', sep='\t')
        
        # Group by ITEM TYPE and sum all sales columns
        item_type_sales = df.groupby('ITEM TYPE').agg({
            'RETAIL SALES': 'sum',
            'RETAIL TRANSFERS': 'sum', 
            'WAREHOUSE SALES': 'sum'
        }).reset_index()
        
        # Calculate total sales for each item type
        item_type_sales['TOTAL SALES'] = (
            item_type_sales['RETAIL SALES'] + 
            item_type_sales['RETAIL TRANSFERS'] + 
            item_type_sales['WAREHOUSE SALES']
        )
        
        # Sort by total sales for better visualization
        item_type_sales = item_type_sales.sort_values('TOTAL SALES', ascending=False)
        
        sales_by_item_data = {
            'item_types': item_type_sales['ITEM TYPE'].tolist(),
            'retail_sales': item_type_sales['RETAIL SALES'].tolist(),
            'retail_transfers': item_type_sales['RETAIL TRANSFERS'].tolist(),
            'warehouse_sales': item_type_sales['WAREHOUSE SALES'].tolist(),
            'total_sales': item_type_sales['TOTAL SALES'].tolist()
        }
        
        return jsonify(sales_by_item_data)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/sales_transfer_ratio', methods=['GET'])
def get_sales_transfer_ratio():
    try:
        df = pd.read_csv('../Sales data', sep='\t')
        
        # Group by ITEM TYPE and sum relevant columns
        item_type_data = df.groupby('ITEM TYPE').agg({
            'RETAIL SALES': 'sum',
            'RETAIL TRANSFERS': 'sum'
        }).reset_index()
        
        # Calculate Sales Transfer Ratio (RETAIL SALES / RETAIL TRANSFERS)
        # Handle division by zero by setting ratio to 0 when transfers are 0
        item_type_data['SALES_TRANSFER_RATIO'] = item_type_data.apply(
            lambda row: row['RETAIL SALES'] / row['RETAIL TRANSFERS'] 
            if row['RETAIL TRANSFERS'] > 0 else 0, axis=1
        )
        
        # Sort by ratio for better visualization
        item_type_data = item_type_data.sort_values('SALES_TRANSFER_RATIO', ascending=False)
        
        # Create efficiency categories based on ratio
        def get_efficiency_category(ratio):
            if ratio == 0:
                return 'No Transfers'
            elif 0.8 <= ratio <= 1.2:
                return 'Efficient (0.8-1.2)'
            elif ratio > 1.2:
                return 'High Sales/Low Transfers'
            else:
                return 'Low Sales/High Transfers'
        
        item_type_data['EFFICIENCY_CATEGORY'] = item_type_data['SALES_TRANSFER_RATIO'].apply(get_efficiency_category)
        
        transfer_ratio_data = {
            'item_types': item_type_data['ITEM TYPE'].tolist(),
            'retail_sales': item_type_data['RETAIL SALES'].tolist(),
            'retail_transfers': item_type_data['RETAIL TRANSFERS'].tolist(),
            'transfer_ratios': item_type_data['SALES_TRANSFER_RATIO'].tolist(),
            'efficiency_categories': item_type_data['EFFICIENCY_CATEGORY'].tolist()
        }
        
        return jsonify(transfer_ratio_data)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/overall_sales_performance', methods=['GET'])
def get_overall_sales_performance():
    try:
        df = pd.read_csv('../Sales data', sep='\t')
        
        # Calculate total sales across all revenue streams
        total_retail_sales = df['RETAIL SALES'].sum()
        total_retail_transfers = df['RETAIL TRANSFERS'].sum()
        total_warehouse_sales = df['WAREHOUSE SALES'].sum()
        
        # Calculate grand total
        grand_total = total_retail_sales + total_retail_transfers + total_warehouse_sales
        
        # Calculate percentages for each revenue stream
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

@app.route('/api/sales_mix', methods=['GET'])
def get_sales_mix():
    try:
        df = pd.read_csv('../Sales data', sep='\t')
        
        # Calculate retail sales by item type
        sales_by_item = df.groupby('ITEM TYPE')['RETAIL SALES'].sum().reset_index()
        
        # Calculate total retail sales
        total_retail_sales = sales_by_item['RETAIL SALES'].sum()
        
        # Calculate percentage contribution for each item type
        sales_by_item['PERCENTAGE'] = (sales_by_item['RETAIL SALES'] / total_retail_sales * 100)
        
        # Sort by retail sales for better visualization
        sales_by_item = sales_by_item.sort_values('RETAIL SALES', ascending=False)
        
        # Identify top contributors (items with >5% share)
        sales_by_item['CATEGORY'] = sales_by_item['PERCENTAGE'].apply(
            lambda x: 'Major Contributor' if x >= 10 else 
                     'Moderate Contributor' if x >= 5 else 
                     'Minor Contributor'
        )
        
        sales_mix_data = {
            'item_types': sales_by_item['ITEM TYPE'].tolist(),
            'retail_sales': sales_by_item['RETAIL SALES'].tolist(),
            'percentages': sales_by_item['PERCENTAGE'].tolist(),
            'categories': sales_by_item['CATEGORY'].tolist(),
            'total_retail_sales': total_retail_sales,
            'top_contributor': sales_by_item.iloc[0]['ITEM TYPE'] if len(sales_by_item) > 0 else 'N/A',
            'top_percentage': sales_by_item.iloc[0]['PERCENTAGE'] if len(sales_by_item) > 0 else 0
        }
        
        return jsonify(sales_mix_data)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/top_selling_items', methods=['GET'])
def get_top_selling_items():
    try:
        df = pd.read_csv('../Sales data', sep='\t')
        
        # Group by ITEM CODE and sum retail sales, also get item description
        item_sales = df.groupby(['ITEM CODE', 'ITEM DESCRIPTION'])['RETAIL SALES'].sum().reset_index()
        
        # Filter out items with zero sales
        item_sales = item_sales[item_sales['RETAIL SALES'] > 0]
        
        # Sort by retail sales in descending order and get top 10
        top_items = item_sales.sort_values('RETAIL SALES', ascending=False).head(10)
        
        if len(top_items) == 0:
            return jsonify({'error': 'No items with sales data found'})
        
        # Calculate total sales of top 10 items
        top_10_total = float(top_items['RETAIL SALES'].sum())
        
        # Calculate total retail sales for percentage calculation
        total_retail_sales = float(df['RETAIL SALES'].sum())
        
        # Calculate percentage contribution of top 10 items
        top_10_percentage = (top_10_total / total_retail_sales * 100) if total_retail_sales > 0 else 0
        
        # Add ranking and performance tiers
        top_items = top_items.reset_index(drop=True)
        top_items['RANK'] = range(1, len(top_items) + 1)
        
        def get_performance_tier(rank):
            if rank <= 3:
                return 'Star Performer'
            elif rank <= 6:
                return 'Strong Performer'
            else:
                return 'Good Performer'
        
        top_items['PERFORMANCE_TIER'] = top_items['RANK'].apply(get_performance_tier)
        
        # Create display labels combining item code and description (truncated)
        top_items['DISPLAY_LABEL'] = top_items.apply(
            lambda row: f"{row['ITEM CODE']} - {str(row['ITEM DESCRIPTION'])[:25]}..." 
            if len(str(row['ITEM DESCRIPTION'])) > 25 
            else f"{row['ITEM CODE']} - {str(row['ITEM DESCRIPTION'])}", 
            axis=1
        )
        
        # Reverse order for horizontal bar chart (top item at top)
        top_items = top_items.iloc[::-1].reset_index(drop=True)
        
        top_selling_data = {
            'item_codes': [str(x) for x in top_items['ITEM CODE'].tolist()],
            'display_labels': [str(x) for x in top_items['DISPLAY_LABEL'].tolist()],
            'item_descriptions': [str(x) for x in top_items['ITEM DESCRIPTION'].tolist()],
            'retail_sales': [float(x) for x in top_items['RETAIL SALES'].tolist()],
            'ranks': [int(x) for x in top_items['RANK'].tolist()],
            'performance_tiers': [str(x) for x in top_items['PERFORMANCE_TIER'].tolist()],
            'top_10_total': top_10_total,
            'top_10_percentage': float(top_10_percentage),
            'total_retail_sales': total_retail_sales,
            'best_item': str(item_sales.iloc[0]['ITEM CODE']) if len(item_sales) > 0 else 'N/A',
            'best_sales': float(item_sales.iloc[0]['RETAIL SALES']) if len(item_sales) > 0 else 0
        }
        
        return jsonify(top_selling_data)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return jsonify({'error': f'Error processing data: {str(e)}', 'details': error_details})

@app.route('/api/month_over_month_growth', methods=['GET'])
def get_month_over_month_growth():
    try:
        df = pd.read_csv('../Sales data', sep='\t')
        
        # Group by year and month to get monthly sales
        monthly_sales = df.groupby(['YEAR', 'MONTH'])['RETAIL SALES'].sum().reset_index()
        
        # Sort by year and month
        monthly_sales = monthly_sales.sort_values(['YEAR', 'MONTH'])
        
        # Calculate month-over-month growth
        monthly_sales['previous_month_sales'] = monthly_sales['RETAIL SALES'].shift(1)
        monthly_sales['growth_rate'] = ((monthly_sales['RETAIL SALES'] - monthly_sales['previous_month_sales']) / monthly_sales['previous_month_sales'] * 100)
        
        # Create a proper date string for display
        monthly_sales['date'] = monthly_sales['YEAR'].astype(str) + '-' + monthly_sales['MONTH'].astype(str).str.zfill(2)
        
        # Remove the first row (no previous month to compare)
        monthly_sales = monthly_sales.dropna(subset=['growth_rate'])
        
        # Replace infinite values with 0 (in case previous month had 0 sales)
        monthly_sales['growth_rate'] = monthly_sales['growth_rate'].replace([float('inf'), float('-inf')], 0)
        
        if len(monthly_sales) == 0:
            return jsonify({'error': 'Not enough data for month-over-month comparison'})
        
        # Calculate additional metrics
        avg_growth_rate = float(monthly_sales['growth_rate'].mean())
        latest_growth = float(monthly_sales.iloc[-1]['growth_rate'])
        max_growth = float(monthly_sales['growth_rate'].max())
        min_growth = float(monthly_sales['growth_rate'].min())
        
        # Categorize growth trends
        def get_growth_category(growth_rate):
            if growth_rate > 10:
                return 'High Growth'
            elif 5 <= growth_rate <= 10:
                return 'Moderate Growth'
            elif -5 <= growth_rate < 5:
                return 'Stable'
            elif -10 <= growth_rate < -5:
                return 'Moderate Decline'
            else:
                return 'Significant Decline'
        
        monthly_sales['growth_category'] = monthly_sales['growth_rate'].apply(get_growth_category)
        
        # Ensure all numeric values are JSON serializable
        monthly_sales['RETAIL SALES'] = monthly_sales['RETAIL SALES'].astype(float)
        monthly_sales['previous_month_sales'] = monthly_sales['previous_month_sales'].astype(float)
        monthly_sales['growth_rate'] = monthly_sales['growth_rate'].astype(float)
        
        month_over_month_data = {
            'dates': [str(x) for x in monthly_sales['date'].tolist()],
            'years': [int(x) for x in monthly_sales['YEAR'].tolist()],
            'months': [int(x) for x in monthly_sales['MONTH'].tolist()],
            'current_sales': [float(x) for x in monthly_sales['RETAIL SALES'].tolist()],
            'previous_sales': [float(x) for x in monthly_sales['previous_month_sales'].tolist()],
            'growth_rates': [float(x) for x in monthly_sales['growth_rate'].tolist()],
            'growth_categories': [str(x) for x in monthly_sales['growth_category'].tolist()],
            'metrics': {
                'average_growth_rate': avg_growth_rate,
                'latest_growth_rate': latest_growth,
                'max_growth_rate': max_growth,
                'min_growth_rate': min_growth,
                'total_months': len(monthly_sales)
            }
        }
        
        return jsonify(month_over_month_data)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return jsonify({'error': f'Error processing month-over-month data: {str(e)}', 'details': error_details})

@app.route('/api/inventory_turnover_rate', methods=['GET'])
def get_inventory_turnover_rate():
    try:
        df = pd.read_csv('../Sales data', sep='\t')
        
        # Calculate total retail sales and total warehouse sales
        total_retail_sales = float(df['RETAIL SALES'].sum())
        total_warehouse_sales = float(df['WAREHOUSE SALES'].sum())
        
        # Calculate Inventory Turnover Rate (Proxy): Total Retail Sales / Total Warehouse Sales
        if total_warehouse_sales > 0:
            turnover_rate = total_retail_sales / total_warehouse_sales
        else:
            turnover_rate = 0
        
        # Define performance benchmarks
        def get_performance_category(rate):
            if rate >= 5.0:
                return 'Excellent'
            elif rate >= 3.0:
                return 'Good'
            elif rate >= 1.5:
                return 'Average'
            elif rate >= 0.5:
                return 'Poor'
            else:
                return 'Critical'
        
        def get_performance_color(rate):
            if rate >= 5.0:
                return '#4CAF50'  # Green
            elif rate >= 3.0:
                return '#8BC34A'  # Light Green
            elif rate >= 1.5:
                return '#FFC107'  # Amber
            elif rate >= 0.5:
                return '#FF9800'  # Orange
            else:
                return '#F44336'  # Red
        
        performance_category = get_performance_category(turnover_rate)
        performance_color = get_performance_color(turnover_rate)
        
        # Calculate additional metrics by item type for insights
        item_type_turnover = df.groupby('ITEM TYPE').agg({
            'RETAIL SALES': 'sum',
            'WAREHOUSE SALES': 'sum'
        }).reset_index()
        
        item_type_turnover['TURNOVER_RATE'] = item_type_turnover.apply(
            lambda row: row['RETAIL SALES'] / row['WAREHOUSE SALES'] 
            if row['WAREHOUSE SALES'] > 0 else 0, axis=1
        )
        
        item_type_turnover = item_type_turnover.sort_values('TURNOVER_RATE', ascending=False)
        
        # Calculate efficiency metrics
        efficient_categories = len(item_type_turnover[item_type_turnover['TURNOVER_RATE'] >= 3.0])
        total_categories = len(item_type_turnover)
        efficiency_percentage = (efficient_categories / total_categories * 100) if total_categories > 0 else 0
        
        turnover_data = {
            'turnover_rate': float(turnover_rate),
            'total_retail_sales': total_retail_sales,
            'total_warehouse_sales': total_warehouse_sales,
            'performance_category': performance_category,
            'performance_color': performance_color,
            'benchmarks': {
                'excellent': 5.0,
                'good': 3.0,
                'average': 1.5,
                'poor': 0.5
            },
            'item_type_analysis': {
                'item_types': [str(x) for x in item_type_turnover['ITEM TYPE'].tolist()],
                'retail_sales': [float(x) for x in item_type_turnover['RETAIL SALES'].tolist()],
                'warehouse_sales': [float(x) for x in item_type_turnover['WAREHOUSE SALES'].tolist()],
                'turnover_rates': [float(x) for x in item_type_turnover['TURNOVER_RATE'].tolist()]
            },
            'efficiency_metrics': {
                'efficient_categories': efficient_categories,
                'total_categories': total_categories,
                'efficiency_percentage': float(efficiency_percentage),
                'best_performing_category': str(item_type_turnover.iloc[0]['ITEM TYPE']) if len(item_type_turnover) > 0 else 'N/A',
                'best_turnover_rate': float(item_type_turnover.iloc[0]['TURNOVER_RATE']) if len(item_type_turnover) > 0 else 0
            }
        }
        
        return jsonify(turnover_data)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return jsonify({'error': f'Error processing inventory turnover data: {str(e)}', 'details': error_details})

@app.route('/api/sales_per_supplier', methods=['GET'])
def get_sales_per_supplier():
    try:
        df = pd.read_csv('../Sales data', sep='\t')
        
        # Group by supplier and sum retail sales
        supplier_sales = df.groupby('SUPPLIER')['RETAIL SALES'].sum().reset_index()
        
        # Sort by sales in descending order
        supplier_sales = supplier_sales.sort_values('RETAIL SALES', ascending=False)
        
        # Filter out suppliers with zero sales
        supplier_sales = supplier_sales[supplier_sales['RETAIL SALES'] > 0]
        
        if len(supplier_sales) == 0:
            return jsonify({'error': 'No suppliers with sales data found'})
        
        # Calculate total sales for percentage calculation
        total_sales = float(supplier_sales['RETAIL SALES'].sum())
        
        # Calculate percentages and performance metrics
        supplier_sales['PERCENTAGE'] = (supplier_sales['RETAIL SALES'] / total_sales * 100)
        supplier_sales['RANK'] = range(1, len(supplier_sales) + 1)
        
        # Categorize suppliers by performance
        def get_supplier_category(percentage):
            if percentage >= 20:
                return 'Major Partner'
            elif percentage >= 10:
                return 'Key Partner'
            elif percentage >= 5:
                return 'Important Partner'
            elif percentage >= 1:
                return 'Regular Partner'
            else:
                return 'Minor Partner'
        
        def get_supplier_color(percentage):
            if percentage >= 20:
                return '#1976D2'  # Dark Blue
            elif percentage >= 10:
                return '#2196F3'  # Blue
            elif percentage >= 5:
                return '#4CAF50'  # Green
            elif percentage >= 1:
                return '#FF9800'  # Orange
            else:
                return '#9E9E9E'  # Grey
        
        supplier_sales['CATEGORY'] = supplier_sales['PERCENTAGE'].apply(get_supplier_category)
        supplier_sales['COLOR'] = supplier_sales['PERCENTAGE'].apply(get_supplier_color)
        
        # Get top suppliers for insights
        top_5_suppliers = supplier_sales.head(5)
        top_5_contribution = float(top_5_suppliers['RETAIL SALES'].sum())
        top_5_percentage = (top_5_contribution / total_sales * 100) if total_sales > 0 else 0
        
        # Calculate supplier diversity metrics
        major_partners = len(supplier_sales[supplier_sales['PERCENTAGE'] >= 20])
        key_partners = len(supplier_sales[supplier_sales['PERCENTAGE'] >= 10])
        total_suppliers = len(supplier_sales)
        
        # Create labels for treemap (truncate long supplier names)
        supplier_sales['DISPLAY_NAME'] = supplier_sales['SUPPLIER'].apply(
            lambda x: str(x)[:20] + '...' if len(str(x)) > 20 else str(x)
        )
        
        # Prepare treemap data
        treemap_data = []
        for _, row in supplier_sales.iterrows():
            treemap_data.append({
                'supplier': str(row['SUPPLIER']),
                'display_name': str(row['DISPLAY_NAME']),
                'sales': float(row['RETAIL SALES']),
                'percentage': float(row['PERCENTAGE']),
                'rank': int(row['RANK']),
                'category': str(row['CATEGORY']),
                'color': str(row['COLOR'])
            })
        
        sales_per_supplier_data = {
            'suppliers': treemap_data,
            'total_sales': total_sales,
            'total_suppliers': total_suppliers,
            'top_5_metrics': {
                'contribution': top_5_contribution,
                'percentage': float(top_5_percentage),
                'suppliers': [str(x) for x in top_5_suppliers['SUPPLIER'].tolist()]
            },
            'diversity_metrics': {
                'major_partners': major_partners,
                'key_partners': key_partners,
                'total_suppliers': total_suppliers,
                'supplier_concentration': float(top_5_percentage)
            },
            'best_supplier': {
                'name': str(supplier_sales.iloc[0]['SUPPLIER']),
                'sales': float(supplier_sales.iloc[0]['RETAIL SALES']),
                'percentage': float(supplier_sales.iloc[0]['PERCENTAGE'])
            }
        }
        
        return jsonify(sales_per_supplier_data)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return jsonify({'error': f'Error processing sales per supplier data: {str(e)}', 'details': error_details})

if __name__ == '__main__':
    app.run(debug=True)
