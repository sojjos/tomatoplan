"""
Routes pour la gestion des chauffeurs
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
import json

from app.models import db, Chauffeur, DisponibiliteChauffeur, ActivityLog
from app.permissions import permission_required

bp = Blueprint('chauffeurs', __name__, url_prefix='/chauffeurs')


@bp.route('/')
@login_required
@permission_required('view_drivers')
def index():
    """Liste des chauffeurs"""
    from app.models import SST
    actifs_only = request.args.get('actifs', 'true') == 'true'

    if actifs_only:
        chauffeurs = Chauffeur.query.filter_by(actif=True).order_by(Chauffeur.nom).all()
    else:
        chauffeurs = Chauffeur.query.order_by(Chauffeur.nom).all()

    # Récupérer tous les SST actifs pour le dropdown
    sst_list = SST.query.filter_by(actif=True).order_by(SST.nom).all()

    can_manage = current_user.has_permission('manage_drivers')

    return render_template(
        'chauffeurs/index.html',
        chauffeurs=chauffeurs,
        sst_list=sst_list,
        can_manage=can_manage,
        actifs_only=actifs_only
    )


@bp.route('/create', methods=['POST'])
@login_required
@permission_required('manage_drivers')
def create():
    """Créer un nouveau chauffeur"""
    data = request.get_json()

    # Si SST fourni, vérifier qu'il est actif
    sst_id = data.get('sst_id')
    if sst_id:
        from app.models import SST
        sst = SST.query.get(sst_id)
        if not sst:
            return jsonify({'error': 'SST non trouvé'}), 400
        if not sst.actif:
            return jsonify({'error': 'Impossible de créer un chauffeur pour un SST désactivé'}), 400

    chauffeur = Chauffeur(
        nom=data['nom'],
        prenom=data.get('prenom'),
        sst_id=sst_id,
        telephone=data.get('telephone'),
        actif=data.get('actif', True),
        infos=data.get('infos')
    )

    db.session.add(chauffeur)
    db.session.commit()

    # Log l'activité
    log = ActivityLog(
        user_id=current_user.id,
        action='CREATE',
        entity_type='Chauffeur',
        entity_id=chauffeur.id,
        details=json.dumps(chauffeur.to_dict()),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'success': True,
        'chauffeur': chauffeur.to_dict(),
        'message': 'Chauffeur créé avec succès'
    })


@bp.route('/<chauffeur_id>/update', methods=['PUT'])
@login_required
@permission_required('manage_drivers')
def update(chauffeur_id):
    """Mettre à jour un chauffeur"""
    chauffeur = Chauffeur.query.get_or_404(chauffeur_id)

    old_data = chauffeur.to_dict()

    data = request.get_json()

    # Vérifier si le SST est actif si on tente de réactiver le chauffeur
    if 'actif' in data and data['actif'] and not chauffeur.actif:
        if chauffeur.sst_id:
            from app.models import SST
            sst = SST.query.get(chauffeur.sst_id)
            if sst and not sst.actif:
                return jsonify({'error': 'Impossible de réactiver un chauffeur dont le SST est désactivé'}), 400

    # Vérifier si on change de SST
    if 'sst_id' in data:
        new_sst_id = data['sst_id']
        if new_sst_id:
            from app.models import SST
            sst = SST.query.get(new_sst_id)
            if not sst:
                return jsonify({'error': 'SST non trouvé'}), 400
            if not sst.actif:
                return jsonify({'error': 'Impossible d\'assigner un chauffeur à un SST désactivé'}), 400
        chauffeur.sst_id = new_sst_id

    if 'nom' in data:
        chauffeur.nom = data['nom']
    if 'prenom' in data:
        chauffeur.prenom = data['prenom']
    if 'telephone' in data:
        chauffeur.telephone = data['telephone']
    if 'actif' in data:
        chauffeur.actif = data['actif']
    if 'infos' in data:
        chauffeur.infos = data['infos']

    db.session.commit()

    # Log l'activité
    log = ActivityLog(
        user_id=current_user.id,
        action='EDIT',
        entity_type='Chauffeur',
        entity_id=chauffeur.id,
        details=json.dumps({
            'before': old_data,
            'after': chauffeur.to_dict()
        }),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'success': True,
        'chauffeur': chauffeur.to_dict(),
        'message': 'Chauffeur mis à jour avec succès'
    })


@bp.route('/<chauffeur_id>/delete', methods=['DELETE'])
@login_required
@permission_required('manage_drivers')
def delete(chauffeur_id):
    """Supprimer un chauffeur"""
    chauffeur = Chauffeur.query.get_or_404(chauffeur_id)

    chauffeur_data = chauffeur.to_dict()

    db.session.delete(chauffeur)
    db.session.commit()

    # Log l'activité
    log = ActivityLog(
        user_id=current_user.id,
        action='DELETE',
        entity_type='Chauffeur',
        entity_id=chauffeur_id,
        details=json.dumps(chauffeur_data),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Chauffeur supprimé avec succès'
    })


@bp.route('/disponibilites')
@login_required
@permission_required('edit_driver_planning')
def disponibilites():
    """Gérer les disponibilités des chauffeurs"""
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = datetime.now().date()

    chauffeurs = Chauffeur.query.filter_by(actif=True).order_by(Chauffeur.nom).all()

    # Récupérer les disponibilités pour cette date
    dispos = {}
    for chauffeur in chauffeurs:
        dispo = DisponibiliteChauffeur.query.filter_by(
            chauffeur_id=chauffeur.id,
            date=selected_date
        ).first()
        dispos[chauffeur.id] = dispo

    return render_template(
        'chauffeurs/disponibilites.html',
        chauffeurs=chauffeurs,
        dispos=dispos,
        selected_date=selected_date
    )


@bp.route('/disponibilites/update', methods=['POST'])
@login_required
@permission_required('edit_driver_planning')
def update_disponibilite():
    """Mettre à jour la disponibilité d'un chauffeur"""
    data = request.get_json()

    chauffeur_id = data['chauffeur_id']
    date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    disponible = data['disponible']
    raison = data.get('raison')

    # Chercher ou créer la disponibilité
    dispo = DisponibiliteChauffeur.query.filter_by(
        chauffeur_id=chauffeur_id,
        date=date
    ).first()

    if dispo:
        dispo.disponible = disponible
        dispo.raison = raison
    else:
        dispo = DisponibiliteChauffeur(
            chauffeur_id=chauffeur_id,
            date=date,
            disponible=disponible,
            raison=raison
        )
        db.session.add(dispo)

    db.session.commit()

    # Log l'activité
    log = ActivityLog(
        user_id=current_user.id,
        action='EDIT',
        entity_type='DisponibiliteChauffeur',
        details=json.dumps({
            'chauffeur_id': chauffeur_id,
            'date': date.isoformat(),
            'disponible': disponible,
            'raison': raison
        }),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Disponibilité mise à jour avec succès'
    })
