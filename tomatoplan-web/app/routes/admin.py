"""
Routes d'administration
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
import json

from app.models import db, User, SST, AnnouncementConfig, ActivityLog
from app.permissions import permission_required, role_required
from config import Config

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/')
@login_required
@role_required('admin')
def index():
    """Panel d'administration"""
    return render_template('admin/index.html')


@bp.route('/users')
@login_required
@permission_required('manage_rights')
def users():
    """Gestion des utilisateurs"""
    all_users = User.query.order_by(User.username).all()
    roles = Config.ROLES

    return render_template(
        'admin/users.html',
        users=all_users,
        roles=roles
    )


@bp.route('/users/create', methods=['POST'])
@login_required
@permission_required('manage_rights')
def create_user():
    """Créer un nouvel utilisateur"""
    data = request.get_json()

    # Vérifier si l'utilisateur existe
    existing = User.query.filter_by(username=data['username']).first()
    if existing:
        return jsonify({'error': 'Cet nom d\'utilisateur existe déjà'}), 400

    user = User(
        username=data['username'],
        email=data.get('email'),
        full_name=data.get('full_name'),
        role=data.get('role', 'viewer'),
        is_active=data.get('is_active', True)
    )
    user.set_password(data.get('password', 'changeme'))

    db.session.add(user)
    db.session.commit()

    log = ActivityLog(
        user_id=current_user.id,
        action='CREATE',
        entity_type='User',
        entity_id=user.id,
        details=json.dumps({
            'username': user.username,
            'role': user.role
        }),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Utilisateur créé avec succès'
    })


@bp.route('/users/<user_id>/update', methods=['PUT'])
@login_required
@permission_required('manage_rights')
def update_user(user_id):
    """Mettre à jour un utilisateur"""
    user = User.query.get_or_404(user_id)

    data = request.get_json()
    old_role = user.role

    if 'role' in data:
        user.role = data['role']
    if 'is_active' in data:
        user.is_active = data['is_active']
    if 'email' in data:
        user.email = data['email']
    if 'full_name' in data:
        user.full_name = data['full_name']

    db.session.commit()

    log = ActivityLog(
        user_id=current_user.id,
        action='EDIT',
        entity_type='User',
        entity_id=user.id,
        details=json.dumps({
            'username': user.username,
            'old_role': old_role,
            'new_role': user.role
        }),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Utilisateur mis à jour avec succès'
    })


@bp.route('/users/<user_id>/reset-password', methods=['POST'])
@login_required
@permission_required('manage_rights')
def reset_password(user_id):
    """Réinitialiser le mot de passe d'un utilisateur"""
    user = User.query.get_or_404(user_id)

    data = request.get_json()
    new_password = data.get('password', 'changeme')

    user.set_password(new_password)
    db.session.commit()

    log = ActivityLog(
        user_id=current_user.id,
        action='RESET_PASSWORD',
        entity_type='User',
        entity_id=user.id,
        details=json.dumps({'username': user.username}),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Mot de passe réinitialisé avec succès'
    })


# ===== GESTION DES SST (Sous-traitants) =====

@bp.route('/sst')
@login_required
@permission_required('manage_rights')
def sst():
    """Liste des SST"""
    sst_all = SST.query.order_by(SST.nom).all()
    return render_template('admin/sst.html', sst_list=sst_all)


@bp.route('/sst/create', methods=['POST'])
@login_required
@permission_required('manage_rights')
def create_sst():
    """Créer un nouveau SST"""
    data = request.get_json()

    # Vérifier si le SST existe déjà
    existing = SST.query.filter_by(nom=data['nom']).first()
    if existing:
        return jsonify({'error': 'Un SST avec ce nom existe déjà'}), 400

    # Parser les emails (format: "email1, email2, email3")
    emails_str = data.get('emails', '')
    emails_list = [e.strip() for e in emails_str.split(',') if e.strip()]

    sst = SST(
        nom=data['nom'],
        telephone=data.get('telephone'),
        emails=json.dumps(emails_list),
        actif=data.get('actif', True)
    )

    db.session.add(sst)
    db.session.commit()

    log = ActivityLog(
        user_id=current_user.id,
        action='CREATE',
        entity_type='SST',
        entity_id=str(sst.id),
        details=json.dumps(sst.to_dict()),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'success': True,
        'sst': sst.to_dict(),
        'message': 'SST créé avec succès'
    })


@bp.route('/sst/<int:sst_id>/update', methods=['PUT'])
@login_required
@permission_required('manage_rights')
def update_sst(sst_id):
    """Mettre à jour un SST"""
    sst = SST.query.get_or_404(sst_id)
    old_data = sst.to_dict()

    data = request.get_json()

    if 'nom' in data:
        # Vérifier si le nouveau nom existe déjà
        if data['nom'] != sst.nom:
            existing = SST.query.filter_by(nom=data['nom']).first()
            if existing:
                return jsonify({'error': 'Un SST avec ce nom existe déjà'}), 400
        sst.nom = data['nom']

    if 'telephone' in data:
        sst.telephone = data['telephone']

    if 'emails' in data:
        emails_str = data['emails']
        emails_list = [e.strip() for e in emails_str.split(',') if e.strip()]
        sst.emails = json.dumps(emails_list)

    if 'actif' in data:
        sst.actif = data['actif']

    db.session.commit()

    log = ActivityLog(
        user_id=current_user.id,
        action='EDIT',
        entity_type='SST',
        entity_id=str(sst.id),
        details=json.dumps({
            'before': old_data,
            'after': sst.to_dict()
        }),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'success': True,
        'sst': sst.to_dict(),
        'message': 'SST mis à jour avec succès'
    })


@bp.route('/sst/<int:sst_id>/delete', methods=['DELETE'])
@login_required
@permission_required('manage_rights')
def delete_sst(sst_id):
    """Supprimer un SST"""
    sst = SST.query.get_or_404(sst_id)
    sst_data = sst.to_dict()

    db.session.delete(sst)
    db.session.commit()

    log = ActivityLog(
        user_id=current_user.id,
        action='DELETE',
        entity_type='SST',
        entity_id=str(sst_id),
        details=json.dumps(sst_data),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'SST supprimé avec succès'
    })


@bp.route('/announcements')
@login_required
@permission_required('manage_announcements_config')
def announcements_config():
    """Configuration des annonces"""
    configs = AnnouncementConfig.query.all()
    config_dict = {c.key: c.value for c in configs}

    return render_template('admin/announcements.html', config=config_dict)


@bp.route('/announcements/update', methods=['POST'])
@login_required
@permission_required('manage_announcements_config')
def update_announcement_config():
    """Mettre à jour la configuration des annonces"""
    data = request.get_json()

    for key, value in data.items():
        config = AnnouncementConfig.query.filter_by(key=key).first()
        if config:
            config.value = value
        else:
            config = AnnouncementConfig(key=key, value=value)
            db.session.add(config)

    db.session.commit()

    return jsonify({'success': True})
