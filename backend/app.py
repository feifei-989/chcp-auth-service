"""
CHCP Backend - Flask Application Entry Point
"""
import os
import logging
from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load .env before anything else
load_dotenv()

from config import Config
from controllers.webhook_controller import webhook_bp
from controllers.user_controller import user_bp

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__, static_folder=None)
    app.config.from_object(Config)

    # Extensions
    CORS(app, origins=app.config['CORS_ORIGINS'])

    # Blueprints
    app.register_blueprint(webhook_bp)
    app.register_blueprint(user_bp)

    # Serve frontend static files
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    frontend_dir = os.path.abspath(frontend_dir)

    @app.route('/')
    def serve_index():
        return send_from_directory(frontend_dir, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory(frontend_dir, path)

    @app.route('/api/health')
    def health():
        return {'status': 'ok'}

    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
