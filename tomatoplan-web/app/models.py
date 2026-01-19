"""
Modèles de base de données pour TomatoPlan Web
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Modèle utilisateur pour l'authentification"""
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    role = db.Column(db.String(50), nullable=False, default='viewer')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # Relations
    activity_logs = db.relationship('ActivityLog', backref='user', lazy='dynamic')

    def set_password(self, password):
        """Hash et stocke le mot de passe"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Vérifie le mot de passe"""
        return check_password_hash(self.password_hash, password)

    def has_permission(self, permission):
        """Vérifie si l'utilisateur a une permission spécifique"""
        from config import Config
        role_permissions = Config.ROLES.get(self.role, {}).get('permissions', [])
        return permission in role_permissions

    def get_permissions(self):
        """Retourne toutes les permissions de l'utilisateur"""
        from config import Config
        return Config.ROLES.get(self.role, {}).get('permissions', [])

    def __repr__(self):
        return f'<User {self.username}>'


class Mission(db.Model):
    """Modèle mission de transport"""
    __tablename__ = 'missions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = db.Column(db.Date, nullable=False, index=True)
    heure = db.Column(db.String(5), nullable=False)  # Format HH:MM
    type = db.Column(db.String(50), nullable=False)  # LIVRAISON, etc.
    voyage = db.Column(db.String(50), nullable=False, index=True)
    sst = db.Column(db.String(100), nullable=False, index=True)
    chauffeur = db.Column(db.String(100), nullable=True, index=True)
    palettes = db.Column(db.Integer, default=0)
    numero = db.Column(db.String(50), nullable=True)
    pays = db.Column(db.String(50), default='Belgique')
    ramasse = db.Column(db.Boolean, default=False)
    infos = db.Column(db.Text, nullable=True)
    effectue = db.Column(db.Boolean, default=False)
    sans_sst = db.Column(db.Boolean, default=False)
    revenus = db.Column(db.Float, default=0.0)
    couts = db.Column(db.Float, default=0.0)
    marge = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        """Convertit en dictionnaire"""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'heure': self.heure,
            'type': self.type,
            'voyage': self.voyage,
            'sst': self.sst,
            'chauffeur': self.chauffeur,
            'palettes': self.palettes,
            'numero': self.numero,
            'pays': self.pays,
            'ramasse': self.ramasse,
            'infos': self.infos,
            'effectue': self.effectue,
            'sans_sst': self.sans_sst,
            'revenus': self.revenus,
            'couts': self.couts,
            'marge': self.marge
        }

    def __repr__(self):
        return f'<Mission {self.date} {self.heure} {self.voyage}>'


class Chauffeur(db.Model):
    """Modèle chauffeur"""
    __tablename__ = 'chauffeurs'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nom = db.Column(db.String(100), nullable=False, unique=True, index=True)
    prenom = db.Column(db.String(100), nullable=True)
    sst_id = db.Column(db.Integer, db.ForeignKey('sst.id'), nullable=True, index=True)
    telephone = db.Column(db.String(20), nullable=True)
    actif = db.Column(db.Boolean, default=True, index=True)
    infos = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    sst = db.relationship('SST', backref='chauffeurs', lazy='joined')
    disponibilites = db.relationship('DisponibiliteChauffeur', backref='chauffeur', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        """Convertit en dictionnaire"""
        return {
            'id': self.id,
            'nom': self.nom,
            'prenom': self.prenom,
            'sst': self.sst.nom if self.sst else None,
            'sst_id': self.sst_id,
            'telephone': self.telephone,
            'actif': self.actif,
            'infos': self.infos,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Chauffeur {self.nom}>'


class DisponibiliteChauffeur(db.Model):
    """Disponibilité des chauffeurs par date"""
    __tablename__ = 'disponibilites_chauffeurs'

    id = db.Column(db.Integer, primary_key=True)
    chauffeur_id = db.Column(db.String(36), db.ForeignKey('chauffeurs.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    disponible = db.Column(db.Boolean, default=True)
    raison = db.Column(db.String(200), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('chauffeur_id', 'date', name='unique_dispo_chauffeur_date'),
    )

    def __repr__(self):
        return f'<Dispo {self.chauffeur_id} {self.date}>'


class Voyage(db.Model):
    """Modèle voyage/tournée"""
    __tablename__ = 'voyages'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False, unique=True, index=True)
    type = db.Column(db.String(50), nullable=False)
    actif = db.Column(db.Boolean, default=True)
    country = db.Column(db.String(50), default='Belgique')
    duree = db.Column(db.Integer, default=60)  # en minutes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convertit en dictionnaire"""
        return {
            'id': self.id,
            'code': self.code,
            'type': self.type,
            'actif': self.actif,
            'country': self.country,
            'duree': self.duree
        }

    def __repr__(self):
        return f'<Voyage {self.code}>'


class SST(db.Model):
    """Modèle sous-traitant"""
    __tablename__ = 'sst'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True, index=True)
    actif = db.Column(db.Boolean, default=True)
    emails = db.Column(db.Text, nullable=True)  # JSON array of emails
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    tarifs = db.relationship('TarifSST', backref='sst_rel', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        """Convertit en dictionnaire"""
        import json
        return {
            'id': self.id,
            'nom': self.nom,
            'actif': self.actif,
            'emails': json.loads(self.emails) if self.emails else []
        }

    def __repr__(self):
        return f'<SST {self.nom}>'


class TarifSST(db.Model):
    """Tarifs par SST"""
    __tablename__ = 'tarifs_sst'

    id = db.Column(db.Integer, primary_key=True)
    sst_id = db.Column(db.Integer, db.ForeignKey('sst.id'), nullable=False, index=True)
    voyage = db.Column(db.String(50), nullable=False, index=True)
    tarif = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('sst_id', 'voyage', name='unique_tarif_sst_voyage'),
    )

    def __repr__(self):
        return f'<TarifSST {self.sst_id} {self.voyage}>'


class RevenuPalette(db.Model):
    """Revenus par palette"""
    __tablename__ = 'revenus_palettes'

    id = db.Column(db.Integer, primary_key=True)
    voyage = db.Column(db.String(50), nullable=False, index=True)
    palettes_min = db.Column(db.Integer, nullable=False)
    palettes_max = db.Column(db.Integer, nullable=False)
    revenu = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<RevenuPalette {self.voyage} {self.palettes_min}-{self.palettes_max}>'


class ActivityLog(db.Model):
    """Logs d'activité (SAURON)"""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    action = db.Column(db.String(50), nullable=False)  # CREATE, EDIT, DELETE, LOGIN, LOGOUT, etc.
    entity_type = db.Column(db.String(50), nullable=False)  # Mission, Chauffeur, etc.
    entity_id = db.Column(db.String(36), nullable=True)
    details = db.Column(db.Text, nullable=True)  # JSON avec détails de l'action
    ip_address = db.Column(db.String(45), nullable=True)

    def to_dict(self):
        """Convertit en dictionnaire"""
        import json
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'details': json.loads(self.details) if self.details else None,
            'ip_address': self.ip_address
        }

    def __repr__(self):
        return f'<ActivityLog {self.action} {self.entity_type}>'


class AnnouncementConfig(db.Model):
    """Configuration des annonces SST"""
    __tablename__ = 'announcement_configs'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False, unique=True)
    value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<AnnouncementConfig {self.key}>'


class AnnouncementHistory(db.Model):
    """Historique des annonces envoyées"""
    __tablename__ = 'announcement_history'

    id = db.Column(db.Integer, primary_key=True)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    sent_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    target_date = db.Column(db.Date, nullable=False)
    sst_name = db.Column(db.String(100), nullable=False)
    recipient_emails = db.Column(db.Text, nullable=False)  # JSON array
    missions_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='sent')  # sent, failed
    error_message = db.Column(db.Text, nullable=True)

    def to_dict(self):
        """Convertit en dictionnaire"""
        import json
        return {
            'id': self.id,
            'sent_at': self.sent_at.isoformat(),
            'sent_by': self.sent_by,
            'target_date': self.target_date.isoformat(),
            'sst_name': self.sst_name,
            'recipient_emails': json.loads(self.recipient_emails) if self.recipient_emails else [],
            'missions_count': self.missions_count,
            'status': self.status,
            'error_message': self.error_message
        }

    def __repr__(self):
        return f'<AnnouncementHistory {self.target_date} {self.sst_name}>'
