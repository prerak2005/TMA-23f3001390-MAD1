from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from app.admin_routes import admin as admin_blueprint
from app.staff_routes import staff as staff_blueprint
from app.user_routes import user as user_blueprint

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login' # Set the login view for @login_required

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    with app.app_context():
        db.create_all()  # Create database tables if they don't exist
        create_admin()  # Create default admin user if not exists

    app.register_blueprint(admin_blueprint)
    app.register_blueprint(staff_blueprint) 
    app.register_blueprint(user_blueprint)

    return app

def create_admin():
    from app.models import User
    from werkzeug.security import generate_password_hash

    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin_user = User(
            name='Admin User',
            email="admin@tma.com",
            password=generate_password_hash('admin123'),
            role='admin',
            status='active'
        )
        db.session.add(admin_user)
        db.session.commit()
