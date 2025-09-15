# Sales Dashboard

This project is a simple sales dashboard that visualizes sales data. It consists of a Python Flask backend and a frontend built with HTML, CSS, and JavaScript.

## Setup and Running

### Backend

1.  Navigate to the `backend` directory.
2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the Flask application:
    ```bash
    python app.py
    ```
    The backend server will start on `http://127.0.0.1:5000`.

### Frontend

1.  Open the `frontend/index.html` file in a web browser.

The dashboard will display a bar chart showing the total retail sales by item type.

## Deployment (Azure App Service)

Production entrypoint: `deploy_ready_app.py` (Flask app instance exposed as `app`).

Procfile (root):
```
web: gunicorn --bind 0.0.0.0:$PORT deploy_ready_app:app
```

Python version: specified in `runtime.txt` (`python-3.11`).

Single authoritative dependency file: `requirements.txt` (root). Remove any old per-folder requirement files to avoid confusion.

### Redeploy Steps
1. Commit any code / requirements changes.
2. Push to the `main` branch (or trigger your GitHub Action / deployment pipeline).
3. Azure build should reinstall dependencies (Oryx) when `requirements.txt` hash changes.
4. Verify health: `https://<your-app>.azurewebsites.net/api/health`.
5. If a stale environment persists, force a rebuild by making a trivial edit to `requirements.txt` (comment) and redeploy.

### Troubleshooting Missing Modules
If you see `ModuleNotFoundError` for a package that exists in `requirements.txt`:
* Confirm the Procfile is at the root and being honored (Linux App Service required).
* Ensure no custom Startup Command overrides gunicorn in the Azure Portal.
* Check Kudu console `/home/site/wwwroot` for presence of your updated files.
* Add / view App Setting `SCM_DO_BUILD_DURING_DEPLOYMENT=true` to force build.

### Local Production-like Run
```bash
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:5000 deploy_ready_app:app
```

### Tests
Minimal smoke test `test_import_app.py` ensures the app imports without missing dependencies.
