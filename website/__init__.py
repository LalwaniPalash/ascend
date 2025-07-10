from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from os import path


db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config['SECRET_KEY'] = "you-will-never-guess"
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User
    from .utils import reset_budgets, add_auto_transactions

    with app.app_context():
        create_database()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    # Scheduler setup
    scheduler = BackgroundScheduler(timezone='UTC')
    scheduler.add_job(func=reset_budgets, trigger="interval", days=30, args=[app])
    scheduler.add_job(func=add_auto_transactions, trigger="interval", days=30, args=[app])
    scheduler.start()

    return app

def create_database():
    if not path.exists('website/' + DB_NAME):
        db.create_all()
        print('Created Database!')

