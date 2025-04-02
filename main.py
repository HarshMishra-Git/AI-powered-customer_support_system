from app import app
from routes import register_routes
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Register all routes within app context to ensure database is accessible
with app.app_context():
    logger.info("Registering routes...")
    register_routes(app)
    logger.info("Routes registered successfully")

if __name__ == "__main__":
    # Use Flask development server with proper host binding
    app.run(host="0.0.0.0", port=5000, debug=True)
