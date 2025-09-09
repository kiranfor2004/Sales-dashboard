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

@app.route('/api/overall_sales_performance', methods=['GET'])
def get_overall_sales_performance():
    try:
        if len(df) == 0:
            return jsonify({'error': 'No data available'})
        
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

@app.route('/api/sales_mix', methods=['GET'])
def get_sales_mix():
    try:
        if len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        sales_by_item = df.groupby('ITEM TYPE')['RETAIL SALES'].sum().reset_index()
        total_retail_sales = float(sales_by_item['RETAIL SALES'].sum())
        
        sales_by_item['PERCENTAGE'] = (sales_by_item['RETAIL SALES'] / total_retail_sales * 100)
        sales_by_item = sales_by_item.sort_values('RETAIL SALES', ascending=False)
        
        sales_by_item['CATEGORY'] = sales_by_item['PERCENTAGE'].apply(
            lambda x: 'Major Contributor' if x >= 10 else 
                     'Moderate Contributor' if x >= 5 else 
                     'Minor Contributor'
        )
        
        sales_mix_data = {
            'item_types': [str(x) for x in sales_by_item['ITEM TYPE'].tolist()],
            'retail_sales': [float(x) for x in sales_by_item['RETAIL SALES'].tolist()],
            'percentages': [float(x) for x in sales_by_item['PERCENTAGE'].tolist()],
            'categories': [str(x) for x in sales_by_item['CATEGORY'].tolist()],
            'total_retail_sales': total_retail_sales,
            'top_contributor': str(sales_by_item.iloc[0]['ITEM TYPE']) if len(sales_by_item) > 0 else 'N/A',
            'top_percentage': float(sales_by_item.iloc[0]['PERCENTAGE']) if len(sales_by_item) > 0 else 0
        }
        
        return jsonify(sales_mix_data)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/top_selling_items', methods=['GET'])
def get_top_selling_items():
    try:
        if len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        item_sales = df.groupby(['ITEM CODE', 'ITEM DESCRIPTION'])['RETAIL SALES'].sum().reset_index()
        item_sales = item_sales[item_sales['RETAIL SALES'] > 0]
        top_items = item_sales.sort_values('RETAIL SALES', ascending=False).head(10)
        
        if len(top_items) == 0:
            return jsonify({'error': 'No items with sales data found'})
        
        top_10_total = float(top_items['RETAIL SALES'].sum())
        total_retail_sales = float(df['RETAIL SALES'].sum())
        top_10_percentage = (top_10_total / total_retail_sales * 100) if total_retail_sales > 0 else 0
        
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
        
        top_items['DISPLAY_LABEL'] = top_items.apply(
            lambda row: f"{row['ITEM CODE']} - {str(row['ITEM DESCRIPTION'])[:25]}..." 
            if len(str(row['ITEM DESCRIPTION'])) > 25 
            else f"{row['ITEM CODE']} - {str(row['ITEM DESCRIPTION'])}", 
            axis=1
        )
        
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
        return jsonify({'error': f'Error processing data: {str(e)}'})

@app.route('/api/sales_by_item_type', methods=['GET'])
def get_sales_by_item_type():
    try:
        if len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        item_type_sales = df.groupby('ITEM TYPE').agg({
            'RETAIL SALES': 'sum',
            'RETAIL TRANSFERS': 'sum', 
            'WAREHOUSE SALES': 'sum'
        }).reset_index()
        
        item_type_sales['TOTAL SALES'] = (
            item_type_sales['RETAIL SALES'] + 
            item_type_sales['RETAIL TRANSFERS'] + 
            item_type_sales['WAREHOUSE SALES']
        )
        
        item_type_sales = item_type_sales.sort_values('TOTAL SALES', ascending=False)
        
        sales_by_item_data = {
            'item_types': [str(x) for x in item_type_sales['ITEM TYPE'].tolist()],
            'retail_sales': [float(x) for x in item_type_sales['RETAIL SALES'].tolist()],
            'retail_transfers': [float(x) for x in item_type_sales['RETAIL TRANSFERS'].tolist()],
            'warehouse_sales': [float(x) for x in item_type_sales['WAREHOUSE SALES'].tolist()],
            'total_sales': [float(x) for x in item_type_sales['TOTAL SALES'].tolist()]
        }
        
        return jsonify(sales_by_item_data)
    except Exception as e:
        return jsonify({'error': str(e)})

# Sales Transfer Ratio - Efficiency KPI
@app.route('/api/sales_transfer_ratio', methods=['GET'])
def get_sales_transfer_ratio():
    try:
        if len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        # Calculate total retail sales and retail transfers
        total_retail_sales = float(df['RETAIL SALES'].sum())
        total_retail_transfers = float(df['RETAIL TRANSFERS'].sum())
        
        # Calculate transfer ratio (transfers as % of total retail activity)
        total_retail_activity = total_retail_sales + total_retail_transfers
        transfer_ratio = (total_retail_transfers / total_retail_activity * 100) if total_retail_activity > 0 else 0
        
        # Monthly breakdown
        monthly_data = df.groupby(['YEAR', 'MONTH']).agg({
            'RETAIL SALES': 'sum',
            'RETAIL TRANSFERS': 'sum'
        }).reset_index()
        
        monthly_data['TOTAL_ACTIVITY'] = monthly_data['RETAIL SALES'] + monthly_data['RETAIL TRANSFERS']
        monthly_data['TRANSFER_RATIO'] = (monthly_data['RETAIL TRANSFERS'] / monthly_data['TOTAL_ACTIVITY'] * 100).fillna(0)
        monthly_data['PERIOD'] = monthly_data['YEAR'].astype(str) + '-' + monthly_data['MONTH'].astype(str).str.zfill(2)
        
        # Sort by year and month
        monthly_data = monthly_data.sort_values(['YEAR', 'MONTH'])
        
        # Efficiency categories
        def get_efficiency_level(ratio):
            if ratio >= 25:
                return 'High Efficiency'
            elif ratio >= 15:
                return 'Moderate Efficiency'
            elif ratio >= 5:
                return 'Low Efficiency'
            else:
                return 'Very Low Efficiency'
        
        monthly_data['EFFICIENCY_LEVEL'] = monthly_data['TRANSFER_RATIO'].apply(get_efficiency_level)
        
        transfer_ratio_data = {
            'overall_transfer_ratio': float(transfer_ratio),
            'total_retail_sales': total_retail_sales,
            'total_retail_transfers': total_retail_transfers,
            'total_retail_activity': total_retail_activity,
            'monthly_periods': [str(x) for x in monthly_data['PERIOD'].tolist()],
            'monthly_ratios': [float(x) for x in monthly_data['TRANSFER_RATIO'].tolist()],
            'monthly_retail_sales': [float(x) for x in monthly_data['RETAIL SALES'].tolist()],
            'monthly_retail_transfers': [float(x) for x in monthly_data['RETAIL TRANSFERS'].tolist()],
            'efficiency_levels': [str(x) for x in monthly_data['EFFICIENCY_LEVEL'].tolist()],
            'efficiency_rating': get_efficiency_level(transfer_ratio),
            'trend': 'Increasing' if len(monthly_data) > 1 and monthly_data.iloc[-1]['TRANSFER_RATIO'] > monthly_data.iloc[0]['TRANSFER_RATIO'] else 'Decreasing'
        }
        
        return jsonify(transfer_ratio_data)
    except Exception as e:
        return jsonify({'error': f'Error calculating transfer ratio: {str(e)}'})

# Month-over-Month Sales Growth - Trend KPI
@app.route('/api/month_over_month_growth', methods=['GET'])
def get_month_over_month_growth():
    try:
        if len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        # Calculate total sales by month
        monthly_sales = df.groupby(['YEAR', 'MONTH']).agg({
            'RETAIL SALES': 'sum',
            'RETAIL TRANSFERS': 'sum',
            'WAREHOUSE SALES': 'sum'
        }).reset_index()
        
        monthly_sales['TOTAL_SALES'] = (
            monthly_sales['RETAIL SALES'] + 
            monthly_sales['RETAIL TRANSFERS'] + 
            monthly_sales['WAREHOUSE SALES']
        )
        
        monthly_sales['PERIOD'] = monthly_sales['YEAR'].astype(str) + '-' + monthly_sales['MONTH'].astype(str).str.zfill(2)
        monthly_sales = monthly_sales.sort_values(['YEAR', 'MONTH'])
        
        # Calculate month-over-month growth
        monthly_sales['PREVIOUS_MONTH_SALES'] = monthly_sales['TOTAL_SALES'].shift(1)
        monthly_sales['MOM_GROWTH_AMOUNT'] = monthly_sales['TOTAL_SALES'] - monthly_sales['PREVIOUS_MONTH_SALES']
        monthly_sales['MOM_GROWTH_PERCENT'] = (
            (monthly_sales['TOTAL_SALES'] - monthly_sales['PREVIOUS_MONTH_SALES']) / 
            monthly_sales['PREVIOUS_MONTH_SALES'] * 100
        ).fillna(0)
        
        # Remove first row (no previous month for comparison)
        growth_data = monthly_sales[1:].copy()
        
        if len(growth_data) == 0:
            return jsonify({'error': 'Insufficient data for growth calculation'})
        
        # Growth trend categories
        def get_growth_category(percent):
            if percent >= 10:
                return 'Strong Growth'
            elif percent >= 5:
                return 'Moderate Growth'
            elif percent >= 0:
                return 'Slight Growth'
            elif percent >= -5:
                return 'Slight Decline'
            elif percent >= -10:
                return 'Moderate Decline'
            else:
                return 'Strong Decline'
        
        growth_data['GROWTH_CATEGORY'] = growth_data['MOM_GROWTH_PERCENT'].apply(get_growth_category)
        
        # Calculate average growth rate
        avg_growth_rate = float(growth_data['MOM_GROWTH_PERCENT'].mean())
        latest_growth = float(growth_data.iloc[-1]['MOM_GROWTH_PERCENT'])
        
        # Growth consistency
        positive_months = len(growth_data[growth_data['MOM_GROWTH_PERCENT'] > 0])
        total_months = len(growth_data)
        growth_consistency = (positive_months / total_months * 100) if total_months > 0 else 0
        
        mom_growth_data = {
            'periods': [str(x) for x in growth_data['PERIOD'].tolist()],
            'total_sales': [float(x) for x in growth_data['TOTAL_SALES'].tolist()],
            'previous_month_sales': [float(x) for x in growth_data['PREVIOUS_MONTH_SALES'].tolist()],
            'growth_amounts': [float(x) for x in growth_data['MOM_GROWTH_AMOUNT'].tolist()],
            'growth_percentages': [float(x) for x in growth_data['MOM_GROWTH_PERCENT'].tolist()],
            'growth_categories': [str(x) for x in growth_data['GROWTH_CATEGORY'].tolist()],
            'average_growth_rate': avg_growth_rate,
            'latest_growth_rate': latest_growth,
            'growth_consistency': float(growth_consistency),
            'positive_growth_months': int(positive_months),
            'total_comparison_months': int(total_months),
            'trend_direction': 'Positive' if avg_growth_rate > 0 else 'Negative',
            'latest_trend': get_growth_category(latest_growth)
        }
        
        return jsonify(mom_growth_data)
    except Exception as e:
        return jsonify({'error': f'Error calculating month-over-month growth: {str(e)}'})

# Inventory Turnover Rate - Efficiency KPI
@app.route('/api/inventory_turnover_rate', methods=['GET'])
def get_inventory_turnover_rate():
    try:
        if len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        # Calculate turnover by item type (proxy for inventory categories)
        item_turnover = df.groupby('ITEM TYPE').agg({
            'RETAIL SALES': 'sum',
            'RETAIL TRANSFERS': 'sum',
            'WAREHOUSE SALES': 'sum'
        }).reset_index()
        
        item_turnover['TOTAL_MOVEMENT'] = (
            item_turnover['RETAIL SALES'] + 
            item_turnover['RETAIL TRANSFERS'] + 
            item_turnover['WAREHOUSE SALES']
        )
        
        # Calculate average monthly movement per item type
        unique_months = len(df.groupby(['YEAR', 'MONTH']))
        item_turnover['MONTHLY_AVG_MOVEMENT'] = item_turnover['TOTAL_MOVEMENT'] / unique_months if unique_months > 0 else 0
        
        # Sort by total movement
        item_turnover = item_turnover.sort_values('TOTAL_MOVEMENT', ascending=False)
        
        # Calculate turnover efficiency rating
        def get_turnover_rating(monthly_avg):
            if monthly_avg >= 50000:
                return 'High Turnover'
            elif monthly_avg >= 20000:
                return 'Moderate Turnover'
            elif monthly_avg >= 5000:
                return 'Low Turnover'
            else:
                return 'Very Low Turnover'
        
        item_turnover['TURNOVER_RATING'] = item_turnover['MONTHLY_AVG_MOVEMENT'].apply(get_turnover_rating)
        
        # Calculate monthly turnover trends
        monthly_turnover = df.groupby(['YEAR', 'MONTH']).agg({
            'RETAIL SALES': 'sum',
            'RETAIL TRANSFERS': 'sum',
            'WAREHOUSE SALES': 'sum'
        }).reset_index()
        
        monthly_turnover['TOTAL_TURNOVER'] = (
            monthly_turnover['RETAIL SALES'] + 
            monthly_turnover['RETAIL TRANSFERS'] + 
            monthly_turnover['WAREHOUSE SALES']
        )
        
        monthly_turnover['PERIOD'] = monthly_turnover['YEAR'].astype(str) + '-' + monthly_turnover['MONTH'].astype(str).str.zfill(2)
        monthly_turnover = monthly_turnover.sort_values(['YEAR', 'MONTH'])
        
        # Overall metrics
        total_turnover = float(item_turnover['TOTAL_MOVEMENT'].sum())
        avg_monthly_turnover = total_turnover / unique_months if unique_months > 0 else 0
        
        # Top and bottom performers
        top_performer = str(item_turnover.iloc[0]['ITEM TYPE']) if len(item_turnover) > 0 else 'N/A'
        bottom_performer = str(item_turnover.iloc[-1]['ITEM TYPE']) if len(item_turnover) > 0 else 'N/A'
        
        turnover_data = {
            'item_types': [str(x) for x in item_turnover['ITEM TYPE'].tolist()],
            'total_movements': [float(x) for x in item_turnover['TOTAL_MOVEMENT'].tolist()],
            'monthly_avg_movements': [float(x) for x in item_turnover['MONTHLY_AVG_MOVEMENT'].tolist()],
            'turnover_ratings': [str(x) for x in item_turnover['TURNOVER_RATING'].tolist()],
            'retail_sales': [float(x) for x in item_turnover['RETAIL SALES'].tolist()],
            'retail_transfers': [float(x) for x in item_turnover['RETAIL TRANSFERS'].tolist()],
            'warehouse_sales': [float(x) for x in item_turnover['WAREHOUSE SALES'].tolist()],
            'monthly_periods': [str(x) for x in monthly_turnover['PERIOD'].tolist()],
            'monthly_turnovers': [float(x) for x in monthly_turnover['TOTAL_TURNOVER'].tolist()],
            'total_turnover': total_turnover,
            'average_monthly_turnover': float(avg_monthly_turnover),
            'unique_months_analyzed': int(unique_months),
            'top_turnover_category': top_performer,
            'lowest_turnover_category': bottom_performer,
            'high_turnover_categories': int(len(item_turnover[item_turnover['TURNOVER_RATING'] == 'High Turnover'])),
            'total_categories': int(len(item_turnover))
        }
        
        return jsonify(turnover_data)
    except Exception as e:
        return jsonify({'error': f'Error calculating inventory turnover: {str(e)}'})

# Sales per Supplier - Partnership KPI
@app.route('/api/sales_per_supplier', methods=['GET'])
def get_sales_per_supplier():
    try:
        if len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        # Calculate sales by supplier
        supplier_sales = df.groupby('SUPPLIER').agg({
            'RETAIL SALES': 'sum',
            'RETAIL TRANSFERS': 'sum',
            'WAREHOUSE SALES': 'sum'
        }).reset_index()
        
        supplier_sales['TOTAL_SALES'] = (
            supplier_sales['RETAIL SALES'] + 
            supplier_sales['RETAIL TRANSFERS'] + 
            supplier_sales['WAREHOUSE SALES']
        )
        
        # Sort by total sales
        supplier_sales = supplier_sales.sort_values('TOTAL_SALES', ascending=False)
        
        # Calculate market share
        total_market_sales = float(supplier_sales['TOTAL_SALES'].sum())
        supplier_sales['MARKET_SHARE'] = (supplier_sales['TOTAL_SALES'] / total_market_sales * 100) if total_market_sales > 0 else 0
        
        # Partnership performance tiers
        def get_partnership_tier(market_share):
            if market_share >= 15:
                return 'Strategic Partner'
            elif market_share >= 8:
                return 'Key Partner'
            elif market_share >= 3:
                return 'Important Partner'
            elif market_share >= 1:
                return 'Regular Partner'
            else:
                return 'Minor Partner'
        
        supplier_sales['PARTNERSHIP_TIER'] = supplier_sales['MARKET_SHARE'].apply(get_partnership_tier)
        
        # Calculate average sales per supplier
        avg_sales_per_supplier = float(supplier_sales['TOTAL_SALES'].mean())
        
        # Top performers analysis
        top_10_suppliers = supplier_sales.head(10).copy()
        top_10_total = float(top_10_suppliers['TOTAL_SALES'].sum())
        top_10_market_share = (top_10_total / total_market_sales * 100) if total_market_sales > 0 else 0
        
        # Performance distribution
        strategic_partners = len(supplier_sales[supplier_sales['PARTNERSHIP_TIER'] == 'Strategic Partner'])
        key_partners = len(supplier_sales[supplier_sales['PARTNERSHIP_TIER'] == 'Key Partner'])
        total_suppliers = len(supplier_sales)
        
        # Monthly trends for top suppliers (top 5)
        top_5_suppliers = supplier_sales.head(5)['SUPPLIER'].tolist()
        monthly_supplier_trends = df[df['SUPPLIER'].isin(top_5_suppliers)].groupby(['YEAR', 'MONTH', 'SUPPLIER']).agg({
            'RETAIL SALES': 'sum',
            'RETAIL TRANSFERS': 'sum',
            'WAREHOUSE SALES': 'sum'
        }).reset_index()
        
        monthly_supplier_trends['TOTAL_SALES'] = (
            monthly_supplier_trends['RETAIL SALES'] + 
            monthly_supplier_trends['RETAIL TRANSFERS'] + 
            monthly_supplier_trends['WAREHOUSE SALES']
        )
        
        monthly_supplier_trends['PERIOD'] = monthly_supplier_trends['YEAR'].astype(str) + '-' + monthly_supplier_trends['MONTH'].astype(str).str.zfill(2)
        
        sales_per_supplier_data = {
            'suppliers': [str(x) for x in supplier_sales['SUPPLIER'].tolist()],
            'total_sales': [float(x) for x in supplier_sales['TOTAL_SALES'].tolist()],
            'retail_sales': [float(x) for x in supplier_sales['RETAIL SALES'].tolist()],
            'retail_transfers': [float(x) for x in supplier_sales['RETAIL TRANSFERS'].tolist()],
            'warehouse_sales': [float(x) for x in supplier_sales['WAREHOUSE SALES'].tolist()],
            'market_shares': [float(x) for x in supplier_sales['MARKET_SHARE'].tolist()],
            'partnership_tiers': [str(x) for x in supplier_sales['PARTNERSHIP_TIER'].tolist()],
            'total_market_sales': total_market_sales,
            'average_sales_per_supplier': avg_sales_per_supplier,
            'total_suppliers': int(total_suppliers),
            'top_10_market_share': float(top_10_market_share),
            'strategic_partners_count': int(strategic_partners),
            'key_partners_count': int(key_partners),
            'top_supplier': str(supplier_sales.iloc[0]['SUPPLIER']) if len(supplier_sales) > 0 else 'N/A',
            'top_supplier_sales': float(supplier_sales.iloc[0]['TOTAL_SALES']) if len(supplier_sales) > 0 else 0,
            'top_supplier_share': float(supplier_sales.iloc[0]['MARKET_SHARE']) if len(supplier_sales) > 0 else 0,
            'supplier_diversity': 'High' if total_suppliers >= 20 else 'Moderate' if total_suppliers >= 10 else 'Low'
        }
        
        return jsonify(sales_per_supplier_data)
    except Exception as e:
        return jsonify({'error': f'Error calculating sales per supplier: {str(e)}'})

# Top Items by Retail Transfers - Logistics KPI
@app.route('/api/top_items_by_transfers', methods=['GET'])
def get_top_items_by_transfers():
    try:
        if len(df) == 0:
            return jsonify({'error': 'No data available'})
        
        # Calculate retail transfers by item
        item_transfers = df.groupby(['ITEM CODE', 'ITEM DESCRIPTION', 'ITEM TYPE']).agg({
            'RETAIL TRANSFERS': 'sum',
            'RETAIL SALES': 'sum'
        }).reset_index()
        
        # Filter items with retail transfers > 0
        item_transfers = item_transfers[item_transfers['RETAIL TRANSFERS'] > 0]
        
        if len(item_transfers) == 0:
            return jsonify({'error': 'No items with retail transfers found'})
        
        # Sort by retail transfers
        item_transfers = item_transfers.sort_values('RETAIL TRANSFERS', ascending=False)
        
        # Calculate transfer efficiency (transfers as % of total retail activity)
        item_transfers['TOTAL_RETAIL_ACTIVITY'] = item_transfers['RETAIL SALES'] + item_transfers['RETAIL TRANSFERS']
        item_transfers['TRANSFER_EFFICIENCY'] = (
            item_transfers['RETAIL TRANSFERS'] / item_transfers['TOTAL_RETAIL_ACTIVITY'] * 100
        ).fillna(0)
        
        # Get top 15 items by transfers
        top_transfers = item_transfers.head(15).copy()
        
        # Logistics performance categories
        def get_logistics_performance(efficiency):
            if efficiency >= 50:
                return 'High Transfer Focus'
            elif efficiency >= 30:
                return 'Moderate Transfer Focus'
            elif efficiency >= 15:
                return 'Balanced Distribution'
            elif efficiency >= 5:
                return 'Sales Focus'
            else:
                return 'Minimal Transfers'
        
        top_transfers['LOGISTICS_PERFORMANCE'] = top_transfers['TRANSFER_EFFICIENCY'].apply(get_logistics_performance)
        
        # Create display labels (truncated for charts)
        top_transfers['DISPLAY_LABEL'] = top_transfers.apply(
            lambda row: f"{row['ITEM CODE']} - {str(row['ITEM DESCRIPTION'])[:20]}..." 
            if len(str(row['ITEM DESCRIPTION'])) > 20 
            else f"{row['ITEM CODE']} - {str(row['ITEM DESCRIPTION'])}", 
            axis=1
        )
        
        # Calculate totals and metrics
        total_transfers = float(df['RETAIL TRANSFERS'].sum())
        top_15_transfers_total = float(top_transfers['RETAIL TRANSFERS'].sum())
        top_15_percentage = (top_15_transfers_total / total_transfers * 100) if total_transfers > 0 else 0
        
        # Item type analysis
        transfers_by_type = top_transfers.groupby('ITEM TYPE')['RETAIL TRANSFERS'].sum().sort_values(ascending=False)
        
        # Monthly transfer trends for top item
        if len(top_transfers) > 0:
            top_item_code = top_transfers.iloc[0]['ITEM CODE']
            monthly_trends = df[df['ITEM CODE'] == top_item_code].groupby(['YEAR', 'MONTH'])['RETAIL TRANSFERS'].sum().reset_index()
            monthly_trends['PERIOD'] = monthly_trends['YEAR'].astype(str) + '-' + monthly_trends['MONTH'].astype(str).str.zfill(2)
            monthly_trends = monthly_trends.sort_values(['YEAR', 'MONTH'])
        else:
            monthly_trends = pd.DataFrame()
        
        # Reverse order for horizontal bar chart display
        top_transfers_display = top_transfers.iloc[::-1].reset_index(drop=True)
        
        top_items_transfers_data = {
            'item_codes': [str(x) for x in top_transfers_display['ITEM CODE'].tolist()],
            'display_labels': [str(x) for x in top_transfers_display['DISPLAY_LABEL'].tolist()],
            'item_descriptions': [str(x) for x in top_transfers_display['ITEM DESCRIPTION'].tolist()],
            'item_types': [str(x) for x in top_transfers_display['ITEM TYPE'].tolist()],
            'retail_transfers': [float(x) for x in top_transfers_display['RETAIL TRANSFERS'].tolist()],
            'retail_sales': [float(x) for x in top_transfers_display['RETAIL SALES'].tolist()],
            'transfer_efficiencies': [float(x) for x in top_transfers_display['TRANSFER_EFFICIENCY'].tolist()],
            'logistics_performances': [str(x) for x in top_transfers_display['LOGISTICS_PERFORMANCE'].tolist()],
            'total_retail_transfers': total_transfers,
            'top_15_transfers_total': top_15_transfers_total,
            'top_15_percentage': float(top_15_percentage),
            'top_transfer_item': str(item_transfers.iloc[0]['ITEM CODE']) if len(item_transfers) > 0 else 'N/A',
            'top_transfer_amount': float(item_transfers.iloc[0]['RETAIL TRANSFERS']) if len(item_transfers) > 0 else 0,
            'transfer_focused_items': int(len(top_transfers[top_transfers['LOGISTICS_PERFORMANCE'].isin(['High Transfer Focus', 'Moderate Transfer Focus'])])),
            'total_transfer_items': int(len(item_transfers)),
            'dominant_transfer_type': str(transfers_by_type.index[0]) if len(transfers_by_type) > 0 else 'N/A'
        }
        
        return jsonify(top_items_transfers_data)
    except Exception as e:
        return jsonify({'error': f'Error calculating top items by transfers: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000)
