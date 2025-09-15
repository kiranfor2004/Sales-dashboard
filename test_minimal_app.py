from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '''
    <h1>🎯 Sales Dashboard - Test Mode</h1>
    <p>Basic Flask app is working!</p>
    <p>If you see this, the deployment pipeline is functional.</p>
    <p>Next step: Debug the full application imports.</p>
    '''

@app.route('/health')
def health():
    return {'status': 'ok', 'message': 'Basic test app running'}

if __name__ == '__main__':
    app.run(debug=False)