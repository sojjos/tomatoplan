"""
Routes pour la gestion du planning
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
import json

from app.models import db, Mission, Chauffeur, Voyage, SST, ActivityLog
from app.permissions import permission_required

bp = Blueprint('planning', __name__, url_prefix='/planning')


@bp.route('/')
@login_required
@permission_required('view_planning')
def index():
    """Page principale du planning"""
    # Date par défaut: aujourd'hui
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = datetime.now().date()

    # Récupérer les missions pour cette date
    missions = Mission.query.filter_by(date=selected_date).order_by(
        Mission.heure, Mission.voyage
    ).all()

    # Récupérer les chauffeurs actifs
    chauffeurs = Chauffeur.query.filter_by(actif=True).order_by(Chauffeur.nom).all()

    # Récupérer les voyages actifs
    voyages = Voyage.query.filter_by(actif=True).order_by(Voyage.code).all()

    # Récupérer les SST
    sst_list = SST.query.filter_by(actif=True).order_by(SST.nom).all()

    # Permissions de l'utilisateur
    can_edit = current_user.has_permission('edit_planning')
    can_edit_past = current_user.has_permission('edit_past_planning')

    # Vérifier si c'est une date passée
    is_past_date = selected_date < datetime.now().date()

    return render_template(
        'planning/index.html',
        missions=missions,
        chauffeurs=chauffeurs,
        voyages=voyages,
        sst_list=sst_list,
        selected_date=selected_date,
        can_edit=can_edit and (not is_past_date or can_edit_past),
        is_past_date=is_past_date
    )


@bp.route('/mission/create', methods=['POST'])
@login_required
@permission_required('edit_planning')
def create_mission():
    """Créer une nouvelle mission"""
    data = request.get_json()

    # Vérifier la date
    mission_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    is_past_date = mission_date < datetime.now().date()

    if is_past_date and not current_user.has_permission('edit_past_planning'):
        return jsonify({'error': 'Vous n\'avez pas les droits pour modifier le planning passé'}), 403

    # Créer la mission
    mission = Mission(
        date=mission_date,
        heure=data.get('heure', '00:00'),
        type=data.get('type', 'LIVRAISON'),
        voyage=data.get('voyage', ''),
        sst=data.get('sst', ''),
        chauffeur=data.get('chauffeur'),
        palettes=int(data.get('palettes', 0)),
        numero=data.get('numero'),
        pays=data.get('pays', 'Belgique'),
        ramasse=data.get('ramasse', False),
        infos=data.get('infos'),
        effectue=data.get('effectue', False),
        sans_sst=data.get('sans_sst', False),
        revenus=float(data.get('revenus', 0)),
        couts=float(data.get('couts', 0)),
        marge=float(data.get('marge', 0)),
        created_by=current_user.id
    )

    db.session.add(mission)
    db.session.commit()

    # Log l'activité
    log = ActivityLog(
        user_id=current_user.id,
        action='CREATE',
        entity_type='Mission',
        entity_id=mission.id,
        details=json.dumps(mission.to_dict()),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'success': True,
        'mission': mission.to_dict(),
        'message': 'Mission créée avec succès'
    })


@bp.route('/mission/<mission_id>/update', methods=['PUT'])
@login_required
@permission_required('edit_planning')
def update_mission(mission_id):
    """Mettre à jour une mission"""
    mission = Mission.query.get_or_404(mission_id)

    # Vérifier la date
    is_past_date = mission.date < datetime.now().date()
    if is_past_date and not current_user.has_permission('edit_past_planning'):
        return jsonify({'error': 'Vous n\'avez pas les droits pour modifier le planning passé'}), 403

    # Sauvegarder l'état avant modification
    old_data = mission.to_dict()

    # Mettre à jour
    data = request.get_json()
    if 'heure' in data:
        mission.heure = data['heure']
    if 'type' in data:
        mission.type = data['type']
    if 'voyage' in data:
        mission.voyage = data['voyage']
    if 'sst' in data:
        mission.sst = data['sst']
    if 'chauffeur' in data:
        mission.chauffeur = data['chauffeur']
    if 'palettes' in data:
        mission.palettes = int(data['palettes'])
    if 'numero' in data:
        mission.numero = data['numero']
    if 'pays' in data:
        mission.pays = data['pays']
    if 'ramasse' in data:
        mission.ramasse = data['ramasse']
    if 'infos' in data:
        mission.infos = data['infos']
    if 'effectue' in data:
        mission.effectue = data['effectue']
    if 'sans_sst' in data:
        mission.sans_sst = data['sans_sst']
    if 'revenus' in data:
        mission.revenus = float(data['revenus'])
    if 'couts' in data:
        mission.couts = float(data['couts'])
    if 'marge' in data:
        mission.marge = float(data['marge'])

    db.session.commit()

    # Log l'activité
    log = ActivityLog(
        user_id=current_user.id,
        action='EDIT',
        entity_type='Mission',
        entity_id=mission.id,
        details=json.dumps({
            'before': old_data,
            'after': mission.to_dict()
        }),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'success': True,
        'mission': mission.to_dict(),
        'message': 'Mission mise à jour avec succès'
    })


@bp.route('/mission/<mission_id>/delete', methods=['DELETE'])
@login_required
@permission_required('edit_planning')
def delete_mission(mission_id):
    """Supprimer une mission"""
    mission = Mission.query.get_or_404(mission_id)

    # Vérifier la date
    is_past_date = mission.date < datetime.now().date()
    if is_past_date and not current_user.has_permission('edit_past_planning'):
        return jsonify({'error': 'Vous n\'avez pas les droits pour modifier le planning passé'}), 403

    # Sauvegarder les données avant suppression
    mission_data = mission.to_dict()

    db.session.delete(mission)
    db.session.commit()

    # Log l'activité
    log = ActivityLog(
        user_id=current_user.id,
        action='DELETE',
        entity_type='Mission',
        entity_id=mission_id,
        details=json.dumps(mission_data),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Mission supprimée avec succès'
    })


@bp.route('/suivi')
@login_required
@permission_required('view_planning')
def suivi():
    """Page de suivi des missions (Gantt)"""
    # Date par défaut: aujourd'hui
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = datetime.now().date()

    # Récupérer les missions pour cette date, groupées par chauffeur
    missions = Mission.query.filter_by(date=selected_date).order_by(
        Mission.chauffeur, Mission.heure
    ).all()

    # Grouper par chauffeur
    missions_par_chauffeur = {}
    for mission in missions:
        chauffeur = mission.chauffeur or 'Non assigné'
        if chauffeur not in missions_par_chauffeur:
            missions_par_chauffeur[chauffeur] = []
        missions_par_chauffeur[chauffeur].append(mission)

    return render_template(
        'planning/suivi.html',
        missions_par_chauffeur=missions_par_chauffeur,
        selected_date=selected_date
    )


@bp.route('/api/missions')
@login_required
@permission_required('view_planning')
def api_missions():
    """API pour récupérer les missions (pour AJAX)"""
    date_str = request.args.get('date')
    chauffeur = request.args.get('chauffeur')
    sst = request.args.get('sst')

    query = Mission.query

    if date_str:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter_by(date=date)
        except ValueError:
            pass

    if chauffeur:
        query = query.filter_by(chauffeur=chauffeur)

    if sst:
        query = query.filter_by(sst=sst)

    missions = query.order_by(Mission.date, Mission.heure).all()

    return jsonify({
        'missions': [m.to_dict() for m in missions]
    })
