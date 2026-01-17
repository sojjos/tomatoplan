"""
Configuration de l'application TomatoPlan Web
"""
import os
from datetime import timedelta

class Config:
    """Configuration de base"""

    # Clé secrète pour les sessions (À CHANGER EN PRODUCTION!)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-123456789'

    # Base de données SQLite
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'tomatoplan.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    SESSION_COOKIE_SECURE = False  # Mettre True en production avec HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Upload
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max

    # Export
    EXPORT_FOLDER = os.path.join(BASE_DIR, 'exports')

    # Email (configuration optionnelle pour les annonces SST)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@tomatoplan.com'

    # Langue par défaut
    DEFAULT_LANGUAGE = 'fr'

    # Pagination
    ITEMS_PER_PAGE = 50

    # Logs
    LOG_FOLDER = os.path.join(BASE_DIR, 'logs')

    # Rôles et permissions (comme l'application originale)
    ROLES = {
        'viewer': {
            'name': 'Consultation',
            'permissions': ['view_planning', 'view_drivers']
        },
        'planner': {
            'name': 'Planificateur',
            'permissions': ['view_planning', 'edit_planning', 'view_drivers']
        },
        'planner_advanced': {
            'name': 'Planificateur Avancé',
            'permissions': [
                'view_planning', 'edit_planning', 'view_drivers',
                'edit_past_planning', 'view_finance', 'view_sauron'
            ]
        },
        'driver_admin': {
            'name': 'Admin Chauffeurs',
            'permissions': [
                'view_planning', 'edit_planning', 'view_drivers',
                'manage_drivers', 'edit_driver_planning'
            ]
        },
        'finance': {
            'name': 'Finance',
            'permissions': [
                'view_planning', 'view_drivers', 'view_finance',
                'manage_finance', 'view_analyse'
            ]
        },
        'analyse': {
            'name': 'Analyse',
            'permissions': [
                'view_planning', 'view_drivers', 'view_finance',
                'view_analyse'
            ]
        },
        'admin': {
            'name': 'Administrateur',
            'permissions': [
                'view_planning', 'edit_planning', 'view_drivers',
                'manage_drivers', 'edit_driver_planning', 'manage_rights',
                'manage_voyages', 'generate_planning', 'edit_past_planning',
                'edit_past_planning_advanced', 'view_finance', 'manage_finance',
                'view_analyse', 'view_sauron', 'send_announcements',
                'manage_announcements_config'
            ]
        }
    }

    # Toutes les permissions disponibles
    ALL_PERMISSIONS = [
        'view_planning',
        'edit_planning',
        'view_drivers',
        'manage_drivers',
        'edit_driver_planning',
        'manage_rights',
        'manage_voyages',
        'generate_planning',
        'edit_past_planning',
        'edit_past_planning_advanced',
        'view_finance',
        'manage_finance',
        'view_analyse',
        'view_sauron',
        'send_announcements',
        'manage_announcements_config'
    ]


class DevelopmentConfig(Config):
    """Configuration de développement"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuration de production"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Configuration de test"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Configuration par défaut
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
