# Archived legacy production-like backend (moved from backend/app_stable.py)
# Retained for reference while new unified deploy_ready_app.py serves production.

from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

print("Loading filtered sales data (2024-2025 only)...")
try:
    data_paths = [
        '../Sales data - Filtered',
        'Sales data - Filtered',
        './Sales data - Filtered',
        '/home/site/wwwroot/Sales data - Filtered',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Sales data - Filtered')
    ]
    df = None
    for path in data_paths:
        try:
            df = pd.read_csv(path, sep='\t')
            print(f"Data loaded from: {path}")
            break
        except FileNotFoundError:
            continue
    if df is not None:
        print(f"Filtered data loaded successfully! Shape: {df.shape}")
        print(f"Years included: {sorted(df['YEAR'].unique())}")
    else:
        raise FileNotFoundError("Could not find data file in any expected location")
except Exception as e:
    print(f"Error loading filtered data: {e}")
    df = pd.DataFrame()

def filter_data_by_period(data, period='MTD'):
    if len(data) == 0:
        return data
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    if period == 'MTD':
        return data[(data['YEAR'] == current_year) & (data['MONTH'] == current_month)]
    if period == 'YTD':
        return data[(data['YEAR'] == current_year) & (data['MONTH'] <= current_month)]
    return data

def get_period_from_request():
    return request.args.get('period', 'ALL')

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'message': 'Backend is working', 'data_loaded': len(df) > 0, 'records': len(df)})

# (Remaining endpoints omitted in archive for brevity—see active deploy_ready_app.py for latest versions.)
