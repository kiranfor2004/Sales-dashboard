from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

@app.route('/api/test_top_selling', methods=['GET'])
def test_top_selling():
    try:
        df = pd.read_csv('../Sales data', sep='\t')
        print("Data loaded, shape:", df.shape)
        
        # Group by ITEM CODE and sum retail sales
        item_sales = df.groupby(['ITEM CODE', 'ITEM DESCRIPTION'])['RETAIL SALES'].sum().reset_index()
        print("Items grouped, shape:", item_sales.shape)
        
        # Sort by retail sales and get top 10
        top_items = item_sales.sort_values('RETAIL SALES', ascending=False).head(10)
        print("Top 10 items:")
        print(top_items[['ITEM CODE', 'RETAIL SALES']])
        
        # Create simple response
        response_data = {
            'item_codes': top_items['ITEM CODE'].tolist(),
            'retail_sales': top_items['RETAIL SALES'].tolist(),
            'descriptions': top_items['ITEM DESCRIPTION'].tolist()
        }
        
        print("Response data keys:", list(response_data.keys()))
        print("First item:", response_data['item_codes'][0] if response_data['item_codes'] else 'No items')
        
        return jsonify(response_data)
        
    except Exception as e:
        print("ERROR:", str(e))
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
