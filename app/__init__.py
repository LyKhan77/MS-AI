"""
Flask Application Factory
Metal Sheet QC Detection System
"""

from flask import Flask
from pathlib import Path
import os
import atexit

# Global session manager instance
session_manager_instance = None

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
    
    # Initialize session manager
    init_session_manager(app)
    
    # Register blueprints (routes)
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register context processors for templates
    register_context_processors(app)
    
    # Register shutdown handler
    register_shutdown_handler(app)
    
    return app


def ensure_directories(app):
    """Ensure all required directories exist"""
    directories = [
        app.config['WEIGHTS_DIR'],
        app.config['CAPTURES_DIR'],
        app.config['STATIC_DIR'] / 'css',
        app.config['STATIC_DIR'] / 'js',
        app.config['STATIC_DIR'] / 'audio',
        app.config['STATIC_DIR'] / 'uploads',
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


def init_session_manager(app):
    """Initialize session manager and services"""
    global session_manager_instance
    
    from app.services.session_manager import SessionManager
    
    print("\n" + "="*60)
    print("Initializing SessionManager...")
    print("="*60)
    
    # Create session manager
    session_manager_instance = SessionManager(app.config)
    
    # Initialize services (camera, AI model)
    success = session_manager_instance.initialize_services()
    
    if not success:
        print("⚠️  Warning: Some services failed to initialize")
        print("   System will continue but functionality may be limited")
    else:
        print("✓ All services initialized successfully")
    
    print("="*60 + "\n")
    
    # Store in app context for access in routes
    app.session_manager = session_manager_instance


def register_blueprints(app):
    """Register Flask blueprints for routes"""
    from app.routes import main_routes, api_routes, video_routes
    
    # Main pages (HTML rendering)
    app.register_blueprint(main_routes.bp)
    
    # API endpoints (JSON)
    app.register_blueprint(api_routes.bp, url_prefix='/api')
    api_routes.set_session_manager(session_manager_instance)
    
    # Video streaming
    app.register_blueprint(video_routes.bp)
    video_routes.set_session_manager(session_manager_instance)


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


def register_shutdown_handler(app):
    """Register app shutdown handler"""
    
    def shutdown():
        """Cleanup on app shutdown"""
        global session_manager_instance
        if session_manager_instance:
            session_manager_instance.shutdown()
    
    atexit.register(shutdown)
