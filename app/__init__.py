"""
Flask Application Factory
Metal Sheet QC Detection System
"""

from flask import Flask
from pathlib import Path
import os

def create_app(config_name='default'):
    """
    Application factory pattern
    
    Args:
        config_name: Configuration environment ('development', 'production', 'default')
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    from app.config import get_config
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    # Ensure required directories exist
    ensure_directories(app)
    
    # Register blueprints (routes)
    register_blueprints(app)
    
    # Initialize extensions if needed
    # (Currently no extensions needed - no database)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Context processors for templates
    register_context_processors(app)
    
    return app


def ensure_directories(app):
    """Ensure all required directories exist"""
    directories = [
        app.config['WEIGHTS_DIR'],
        app.config['CAPTURES_DIR'],
        app.config['STATIC_DIR'] / 'css',
        app.config['STATIC_DIR'] / 'js',
        app.config['STATIC_DIR'] / 'audio',
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Create sessions index file if not exists
    sessions_index = app.config['SESSIONS_INDEX_FILE']
    if not sessions_index.exists():
        import json
        initial_data = {
            "sessions": [],
            "last_updated": None
        }
        with open(sessions_index, 'w') as f:
            json.dump(initial_data, f, indent=2)


def register_blueprints(app):
    """Register Flask blueprints for routes"""
    from app.routes import main_routes, api_routes, video_routes
    
    # Main pages (HTML rendering)
    app.register_blueprint(main_routes.bp)
    
    # API endpoints (JSON)
    app.register_blueprint(api_routes.bp, url_prefix='/api')
    
    # Video streaming
    app.register_blueprint(video_routes.bp)


def register_error_handlers(app):
    """Register custom error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template, request
        if request.path.startswith('/api/'):
            # JSON response for API endpoints
            return {'error': 'Not found'}, 404
        # HTML response for web pages
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template, request
        if request.path.startswith('/api/'):
            return {'error': 'Internal server error'}, 500
        return render_template('500.html'), 500


def register_context_processors(app):
    """Register template context processors"""
    
    @app.context_processor
    def inject_config():
        """Inject configuration into all templates"""
        return {
            'PRIMARY_COLOR': app.config['PRIMARY_COLOR'],
            'THEME': app.config['THEME'],
        }
