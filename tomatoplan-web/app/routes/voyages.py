"""
Routes pour la gestion des voyages/tournées
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
import json

from app.models import db, Voyage, ActivityLog
from app.permissions import permission_required

bp = Blueprint('voyages', __name__, url_prefix='/voyages')


@bp.route('/')
@login_required
@permission_required('manage_voyages')
def index():
    """Liste des voyages"""
    voyages = Voyage.query.order_by(Voyage.code).all()
    return render_template('voyages/index.html', voyages=voyages)


@bp.route('/create', methods=['POST'])
@login_required
@permission_required('manage_voyages')
def create():
    """Créer un nouveau voyage"""
    data = request.get_json()

    existing = Voyage.query.filter_by(code=data['code']).first()
    if existing:
        return jsonify({'error': 'Un voyage avec ce code existe déjà'}), 400

    voyage = Voyage(
        code=data['code'],
        type=data.get('type', 'LIVRAISON'),
        actif=data.get('actif', True),
        country=data.get('country', 'Belgique'),
        duree=int(data.get('duree', 60))
    )

    db.session.add(voyage)
    db.session.commit()

    log = ActivityLog(
        user_id=current_user.id,
        action='CREATE',
        entity_type='Voyage',
        entity_id=str(voyage.id),
        details=json.dumps(voyage.to_dict()),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'success': True, 'voyage': voyage.to_dict()})


@bp.route('/<int:voyage_id>/update', methods=['PUT'])
@login_required
@permission_required('manage_voyages')
def update(voyage_id):
    """Mettre à jour un voyage"""
    voyage = Voyage.query.get_or_404(voyage_id)
    old_data = voyage.to_dict()

    data = request.get_json()
    if 'type' in data:
        voyage.type = data['type']
    if 'actif' in data:
        voyage.actif = data['actif']
    if 'country' in data:
        voyage.country = data['country']
    if 'duree' in data:
        voyage.duree = int(data['duree'])

    db.session.commit()

    log = ActivityLog(
        user_id=current_user.id,
        action='EDIT',
        entity_type='Voyage',
        entity_id=str(voyage.id),
        details=json.dumps({'before': old_data, 'after': voyage.to_dict()}),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'success': True, 'voyage': voyage.to_dict()})


@bp.route('/<int:voyage_id>/delete', methods=['DELETE'])
@login_required
@permission_required('manage_voyages')
def delete(voyage_id):
    """Supprimer un voyage"""
    voyage = Voyage.query.get_or_404(voyage_id)
    voyage_data = voyage.to_dict()

    db.session.delete(voyage)
    db.session.commit()

    log = ActivityLog(
        user_id=current_user.id,
        action='DELETE',
        entity_type='Voyage',
        entity_id=str(voyage_id),
        details=json.dumps(voyage_data),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'success': True})


@bp.route('/api/list')
@login_required
@permission_required('manage_voyages')
def api_list():
    """Liste des voyages pour l'API"""
    voyages = Voyage.query.order_by(Voyage.code).all()
    return jsonify([v.to_dict() for v in voyages])


@bp.route('/api/<int:voyage_id>')
@login_required
@permission_required('manage_voyages')
def api_get(voyage_id):
    """Récupérer un voyage par ID"""
    voyage = Voyage.query.get_or_404(voyage_id)
    return jsonify(voyage.to_dict())
