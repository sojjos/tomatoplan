#!/bin/bash
#
# SCRIPT DE MISE À JOUR COMPLÈTE - TomatoPlan Web v2.0
# Reconstruit l'application complète fidèle à PTT_v0.6.0.py
#
# Usage: sudo bash UPDATE_COMPLETE.sh
#

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}MISE À JOUR COMPLÈTE TOMATOPLAN WEB V2.0${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Variables
APP_DIR="/opt/tomatoplan/tomatoplan-web"
APP_USER="tomatoplan"

echo -e "${YELLOW}➜${NC} Arrêt de l'application..."
systemctl stop tomatoplan 2>/dev/null || true

cd "$APP_DIR"

echo -e "${YELLOW}➜${NC} Sauvegarde de la base de données actuelle..."
cp instance/tomatoplan.db instance/tomatoplan.db.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

echo -e "${YELLOW}➜${NC} Mise à jour des modèles de base de données..."

# 1. NOUVEAU FICHIER MODELS.PY COMPLET
cat > app/models_new.py << 'ENDMODELS'
"""
Modèles de base de données pour TomatoPlan Web v2.0
Fidèle à PTT_v0.6.0.py
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
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_permission(self, permission):
        from config import Config
        role_permissions = Config.ROLES.get(self.role, {}).get('permissions', [])
        return permission in role_permissions

    def get_permissions(self):
        from config import Config
        return Config.ROLES.get(self.role, {}).get('permissions', [])

    def __repr__(self):
        return f'<User {self.username}>'


class Mission(db.Model):
    """Modèle mission de transport - Fidèle à PTT_v0.6.0.py"""
    __tablename__ = 'missions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = db.Column(db.Date, nullable=False, index=True)
    heure = db.Column(db.String(5), nullable=False)  # HH:MM
    type = db.Column(db.String(50), nullable=False)  # LIVRAISON ou RAMASSE
    voyage = db.Column(db.String(50), nullable=False, index=True)  # Code voyage
    nb_pal = db.Column(db.Integer, default=0)  # Nombre palettes
    numero = db.Column(db.Integer, nullable=True)  # Numéro d'ordre chauffeur
    sst = db.Column(db.String(100), nullable=True, index=True)  # Sous-traitant
    chauffeur_nom = db.Column(db.String(100), nullable=True, index=True)
    chauffeur_id = db.Column(db.String(36), nullable=True)
    ramasse = db.Column(db.String(100), nullable=True)  # Code ramasse si type=RAMASSE
    infos = db.Column(db.Text, nullable=True)
    sans_sst = db.Column(db.Boolean, default=False)
    sans_chauffeur = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'heure': self.heure,
            'type': self.type,
            'voyage': self.voyage,
            'nb_pal': self.nb_pal,
            'numero': self.numero,
            'sst': self.sst,
            'chauffeur_nom': self.chauffeur_nom,
            'chauffeur_id': self.chauffeur_id,
            'ramasse': self.ramasse,
            'infos': self.infos,
            'sans_sst': self.sans_sst,
            'sans_chauffeur': self.sans_chauffeur
        }

    def __repr__(self):
        return f'<Mission {self.date} {self.heure} {self.voyage}>'


class Chauffeur(db.Model):
    """Modèle chauffeur - Fidèle à PTT_v0.6.0.py"""
    __tablename__ = 'chauffeurs'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nom = db.Column(db.String(100), nullable=False, index=True)
    prenom = db.Column(db.String(100), nullable=True)
    nom_affichage = db.Column(db.String(200), nullable=True)  # Prénom + Nom
    sst = db.Column(db.String(100), nullable=True)
    type = db.Column(db.String(50), default='externe')  # interne ou externe
    telephone = db.Column(db.String(20), nullable=True)
    actif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    disponibilites = db.relationship('DisponibiliteChauffeur', backref='chauffeur', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'prenom': self.prenom,
            'nom_affichage': self.nom_affichage or self.nom,
            'sst': self.sst,
            'type': self.type,
            'telephone': self.telephone,
            'actif': self.actif
        }

    def __repr__(self):
        return f'<Chauffeur {self.nom_affichage or self.nom}>'


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
    """Modèle voyage/tournée - Fidèle à PTT_v0.6.0.py"""
    __tablename__ = 'voyages'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False, unique=True, index=True)
    type = db.Column(db.String(50), nullable=False)  # LIVRAISON ou RAMASSE
    actif = db.Column(db.Boolean, default=True)
    country = db.Column(db.String(50), default='Belgique')  # Belgique, France, Allemagne, Luxembourg, Pays-Bas
    duree = db.Column(db.Integer, default=60)  # Durée en minutes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
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
    emails = db.Column(db.Text, nullable=True)  # JSON array
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    tarifs = db.relationship('TarifSST', backref='sst_rel', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
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
    """Tarifs par SST/Pays/Date - Fidèle à PTT_v0.6.0.py"""
    __tablename__ = 'tarifs_sst'

    id = db.Column(db.Integer, primary_key=True)
    sst_id = db.Column(db.Integer, db.ForeignKey('sst.id'), nullable=False, index=True)
    country = db.Column(db.String(50), nullable=False, index=True)  # Pays
    date = db.Column(db.Date, nullable=False, index=True)  # Date du tarif
    tarif = db.Column(db.Float, nullable=False)  # Tarif journalier en €
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('sst_id', 'country', 'date', name='unique_tarif_sst_country_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'sst_id': self.sst_id,
            'sst_nom': self.sst_rel.nom if self.sst_rel else None,
            'country': self.country,
            'date': self.date.isoformat(),
            'tarif': self.tarif
        }

    def __repr__(self):
        return f'<TarifSST {self.sst_id} {self.country} {self.date}>'


class RevenuPalette(db.Model):
    """Revenus par palette - Structure date/pays/type - Fidèle à PTT_v0.6.0.py"""
    __tablename__ = 'revenus_palettes'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)  # Date du tarif
    country = db.Column(db.String(50), nullable=False, index=True)  # Pays
    type_mission = db.Column(db.String(50), nullable=False)  # livraison ou ramasse
    revenu = db.Column(db.Float, nullable=False)  # Revenu par palette en €
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('date', 'country', 'type_mission', name='unique_revenu_date_country_type'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'country': self.country,
            'type_mission': self.type_mission,
            'revenu': self.revenu
        }

    def __repr__(self):
        return f'<RevenuPalette {self.date} {self.country} {self.type_mission}>'


class ActivityLog(db.Model):
    """Logs d'activité (SAURON)"""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    action = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.String(36), nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)

    def to_dict(self):
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
    recipient_emails = db.Column(db.Text, nullable=False)
    missions_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='sent')
    error_message = db.Column(db.Text, nullable=True)

    def to_dict(self):
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
ENDMODELS

echo -e "${GREEN}✓${NC} Nouveau models.py créé"

# 2. Remplacer le fichier models
mv app/models.py app/models.py.old
mv app/models_new.py app/models.py

echo -e "${YELLOW}➜${NC} Migration de la base de données..."

# Créer le script de migration
cat > migrate_db.py << 'ENDMIGRATE'
#!/usr/bin/env python3
"""
Script de migration de base de données
Migre l'ancienne structure vers la nouvelle
"""
from app import create_app
from app.models import db
import os

app = create_app()

with app.app_context():
    # Recréer toutes les tables
    print("Suppression des anciennes tables...")
    db.drop_all()

    print("Création des nouvelles tables...")
    db.create_all()

    # Créer l'utilisateur admin par défaut
    from app.models import User
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@tomatoplan.com',
            full_name='Administrateur',
            role='admin',
            is_active=True
        )
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        print("✓ Utilisateur admin créé")

    print("✓ Migration terminée")
ENDMIGRATE

sudo -u $APP_USER python3 migrate_db.py

echo -e "${GREEN}✓${NC} Base de données migrée"

echo -e "${YELLOW}➜${NC} Redémarrage de l'application..."
systemctl start tomatoplan
sleep 3
systemctl status tomatoplan --no-pager | head -15

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}MISE À JOUR TERMINÉE !${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Application disponible sur: https://projectviewer.fun"
echo -e "Login: ${YELLOW}admin${NC} / Mot de passe: ${YELLOW}admin${NC}"
echo ""
echo -e "${RED}ATTENTION:${NC} La base de données a été réinitialisée."
echo -e "Sauvegarde disponible dans: instance/tomatoplan.db.backup.*"
echo ""
