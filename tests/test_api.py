import json
import deploy_ready_app as appmod

def client():
    appmod.app.config['TESTING'] = True
    return appmod.app.test_client()

def test_health(client=client):
    c = client()
    r = c.get('/api/health')
    assert r.status_code == 200
    data = r.get_json()
    assert 'status' in data

def test_data_info(client=client):
    c = client()
    r = c.get('/api/data-info')
    assert r.status_code == 200 or r.status_code == 200

def test_sales_performance(client=client):
    c = client()
    r = c.get('/api/overall_sales_performance')
    assert r.status_code == 200
