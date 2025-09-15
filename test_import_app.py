def test_import_production_app():
    # Ensures the production entrypoint referenced in Procfile imports cleanly
    import deploy_ready_app  # noqa: F401
    assert hasattr(deploy_ready_app, 'app'), 'deploy_ready_app should expose a Flask app variable named app'
