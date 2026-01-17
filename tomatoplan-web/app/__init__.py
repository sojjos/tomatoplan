"""
Initialisation de l'application Flask TomatoPlan Web
"""
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
import os

from app.models import db, User
from config import config

# Initialisation des extensions
login_manager = LoginManager()
migrate = Migrate()


def create_app(config_name='default'):
    """Factory pour créer l'application Flask"""

    app = Flask(__name__)

    # Charger la configuration
    app.config.from_object(config[config_name])

    # Créer les dossiers nécessaires
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['LOG_FOLDER'], exist_ok=True)

    # Initialiser les extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Configuration de Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        """Charge l'utilisateur depuis la base de données"""
        return User.query.get(user_id)

    # Enregistrer les blueprints
    from app.routes import auth, main, planning, chauffeurs, voyages, finance, analyse, admin, sauron, api

    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(planning.bp)
    app.register_blueprint(chauffeurs.bp)
    app.register_blueprint(voyages.bp)
    app.register_blueprint(finance.bp)
    app.register_blueprint(analyse.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(sauron.bp)
    app.register_blueprint(api.bp)

    # Contexte des templates - ajouter des fonctions utilitaires
    @app.context_processor
    def utility_processor():
        """Ajoute des fonctions utilitaires aux templates"""
        from flask_login import current_user

        def has_permission(permission):
            """Vérifie si l'utilisateur a une permission"""
            if not current_user.is_authenticated:
                return False
            return current_user.has_permission(permission)

        def get_role_name(role):
            """Retourne le nom d'un rôle"""
            from config import Config
            return Config.ROLES.get(role, {}).get('name', role)

        return dict(
            has_permission=has_permission,
            get_role_name=get_role_name
        )

    # Créer les tables si elles n'existent pas
    with app.app_context():
        db.create_all()

        # Créer un utilisateur admin par défaut si aucun utilisateur n'existe
        if User.query.count() == 0:
            admin = User(
                username='admin',
                email='admin@tomatoplan.com',
                full_name='Administrateur',
                role='admin',
                is_active=True
            )
            admin.set_password('admin')  # À CHANGER IMMÉDIATEMENT APRÈS LA PREMIÈRE CONNEXION!
            db.session.add(admin)
            db.session.commit()
            print("✓ Utilisateur admin créé (username: admin, password: admin)")

    return app
