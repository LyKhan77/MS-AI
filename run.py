"""
Flask Application Entry Point
Metal Sheet QC Detection System
"""

from app import create_app
import os

# Get environment from ENV variable, default to development
env = os.environ.get('FLASK_ENV', 'development')

# Create Flask app
app = create_app(env)

if __name__ == '__main__':
    # Get host and port from environment or use defaults
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print(f"\nStarting Metal Sheet QC Detection System...")
    print(f"Environment: {env}")
    print(f"Server: http://{host}:{port}")
    print(f"\nPress CTRL+C to quit\n")
    
    # Run Flask app
    # threaded=True allows handling multiple requests concurrently
    # Important for video streaming while serving API requests
    app.run(
        host=host,
        port=port,
        threaded=True,
        debug=(env == 'development')
    )
