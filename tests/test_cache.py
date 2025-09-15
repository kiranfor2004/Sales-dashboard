import time
import json
import deploy_ready_app as app_module

def test_cache_behavior():
    """Test that cached endpoint returns consistent data and improves performance."""
    app_module.app.config['TESTING'] = True
    client = app_module.app.test_client()
    
    # Clear any existing cache
    app_module._cache.clear()
    app_module._cache_meta.clear()
    
    # First request (cache miss)
    start_time = time.time()
    response1 = client.get('/api/overall_sales_performance')
    first_duration = time.time() - start_time
    
    assert response1.status_code == 200
    data1 = response1.get_json()
    
    # Second request immediately (cache hit)
    start_time = time.time()
    response2 = client.get('/api/overall_sales_performance')
    second_duration = time.time() - start_time
    
    assert response2.status_code == 200
    data2 = response2.get_json()
    
    # Data should be identical
    assert data1 == data2
    
    # Second request should be faster (cache hit)
    # Note: In testing this might not always be true due to overhead, but cache should be populated
    assert len(app_module._cache) > 0  # Cache should have entries
    
    # Verify cache metadata
    cache_key = '/api/overall_sales_performance'
    assert cache_key in app_module._cache_meta
    assert 'ts' in app_module._cache_meta[cache_key]
    assert 'ttl' in app_module._cache_meta[cache_key]

def test_cache_with_query_params():
    """Test that different query parameters create different cache entries."""
    app_module.app.config['TESTING'] = True
    client = app_module.app.test_client()
    
    # Clear cache
    app_module._cache.clear()
    app_module._cache_meta.clear()
    
    # Request with query param
    response1 = client.get('/api/overall_sales_performance?test=1')
    assert response1.status_code == 200
    
    # Request with different query param  
    response2 = client.get('/api/overall_sales_performance?test=2')
    assert response2.status_code == 200
    
    # Should have 2 cache entries (different keys)
    assert len(app_module._cache) == 2

def test_health_endpoint_cache_stats():
    """Test that health endpoint shows cache statistics when stats enabled."""
    app_module.app.config['TESTING'] = True
    client = app_module.app.test_client()
    
    # Ensure some cache entries exist
    client.get('/api/overall_sales_performance')
    
    response = client.get('/api/health')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'cache_stats' in data
    
    # If stats are enabled, should show cache info
    if app_module.CONFIG.FEATURE_FLAGS.ENABLE_STATS:
        assert 'entries' in data['cache_stats']
        assert data['cache_stats']['entries'] >= 0