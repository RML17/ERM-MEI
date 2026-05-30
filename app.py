import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix


# Configure logging
logging.basicConfig(level=logging.DEBUG)


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "sistema-gestao-empresarial-2025-key"
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # Needed for url_for to generate with https

# Configure the database
database_url = os.environ.get("DATABASE_URL")
# Fix for PostgreSQL URI format if needed
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
elif not database_url:
    database_url = "sqlite:///database.db"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# Add global context processor for all templates
from datetime import datetime
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Import and register blueprints
with app.app_context():
    # Import models to create tables
    import models  # noqa: F401
    
    # Import blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.invoices import invoices_bp
    from routes.inventory import inventory_bp
    from routes.reports import reports_bp
    from routes.payments import payments_bp
    from routes.logistics import logistics_bp
    from routes.taxes import taxes_bp
    from routes.currency import currency_bp
    from routes.hr import hr_bp

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(logistics_bp)
    app.register_blueprint(taxes_bp)
    app.register_blueprint(currency_bp)
    app.register_blueprint(hr_bp)

    # Create database tables
    db.create_all()

    from models import User, UserRole
    
    # Create a default admin user if no users exist
    def create_default_admin():
        try:
            # Verificar se já existe um usuário admin
            if User.query.filter_by(username="admin").first() is None and User.query.count() == 0:
                logging.info("Creating default admin user...")
                admin = User(
                    username="admin",
                    email="admin@example.com",
                    full_name="Administrador do Sistema",
                    role=UserRole.ADMIN,
                    is_active=True
                )
                admin.set_password("admin123")
                db.session.add(admin)
                db.session.commit()
                logging.info("Default admin user created successfully!")
        except Exception as e:
            logging.error(f"Error creating default admin user: {str(e)}")
            db.session.rollback()
    
    # Create the default admin user
    create_default_admin()
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
