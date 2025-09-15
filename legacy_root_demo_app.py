from flask import Flask
import sys
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return f"""
    <h1>Azure Legacy Demo App</h1>
    <p><strong>Python Version:</strong> {sys.version}</p>
    <p><strong>Current Directory:</strong> {os.getcwd()}</p>
    <p><strong>Files in Directory:</strong></p>
    <ul>
        {"".join([f"<li>{f}</li>" for f in os.listdir('.')])}
    </ul>
    <p>This legacy helper file was renamed to avoid interfering with pytest test discovery.</p>
    """

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)