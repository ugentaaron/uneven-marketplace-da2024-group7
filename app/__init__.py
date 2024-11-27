# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config
from .models import db
import os



migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from .routes import main
        app.register_blueprint(main)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    

    @app.context_processor
    def inject_user():
        from .models import User
        from flask import session

        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                return {'username': user.username}
        return {'username': None}

    @app.context_processor
    def inject_notifications_unread_count():
        from flask import session
        from .models import Notification  # Pas dit aan naar jouw projectstructuur
        
        if 'user_id' in session:
            user_id = session['user_id']
            unread_count = Notification.query.filter_by(receiver_id=user_id, viewed=False).count()
            return {'notifications_unread_count': unread_count}
        return {'notifications_unread_count': 0}
    return app
