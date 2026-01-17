"""
Routes pour le système SAURON (surveillance et logs)
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from datetime import datetime, timedelta

from app.models import db, ActivityLog, User
from app.permissions import permission_required

bp = Blueprint('sauron', __name__, url_prefix='/sauron')


@bp.route('/')
@login_required
@permission_required('view_sauron')
def index():
    """Page principale SAURON"""
    # Filtres
    user_id = request.args.get('user')
    action = request.args.get('action')
    entity_type = request.args.get('entity_type')
    start_date = request.args.get('start')
    end_date = request.args.get('end')

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 50

    # Construire la requête
    query = ActivityLog.query

    if user_id:
        query = query.filter_by(user_id=user_id)

    if action:
        query = query.filter_by(action=action)

    if entity_type:
        query = query.filter_by(entity_type=entity_type)

    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(ActivityLog.timestamp >= start)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = end + timedelta(days=1)  # Inclure toute la journée
            query = query.filter(ActivityLog.timestamp < end)
        except ValueError:
            pass

    # Exécuter la requête avec pagination
    logs = query.order_by(ActivityLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Récupérer les utilisateurs pour le filtre
    users = User.query.order_by(User.username).all()

    # Types d'actions disponibles
    actions = ['CREATE', 'EDIT', 'DELETE', 'LOGIN', 'LOGOUT', 'CHANGE_PASSWORD', 'RESET_PASSWORD', 'SEND_ANNOUNCEMENT']

    # Types d'entités
    entity_types = ['Mission', 'Chauffeur', 'Voyage', 'SST', 'User', 'Session', 'TarifSST', 'RevenuPalette']

    return render_template(
        'sauron/index.html',
        logs=logs,
        users=users,
        actions=actions,
        entity_types=entity_types,
        selected_user=user_id,
        selected_action=action,
        selected_entity_type=entity_type,
        selected_start=start_date,
        selected_end=end_date
    )


@bp.route('/api/stats')
@login_required
@permission_required('view_sauron')
def api_stats():
    """Statistiques SAURON"""
    # 7 derniers jours
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    # Actions par jour
    from sqlalchemy import func, cast
    from sqlalchemy.types import Date

    daily_actions = db.session.query(
        cast(ActivityLog.timestamp, Date).label('date'),
        func.count(ActivityLog.id).label('count')
    ).filter(
        ActivityLog.timestamp >= start_date
    ).group_by(
        cast(ActivityLog.timestamp, Date)
    ).order_by(
        cast(ActivityLog.timestamp, Date)
    ).all()

    # Actions par type
    actions_by_type = db.session.query(
        ActivityLog.action,
        func.count(ActivityLog.id).label('count')
    ).filter(
        ActivityLog.timestamp >= start_date
    ).group_by(
        ActivityLog.action
    ).order_by(
        func.count(ActivityLog.id).desc()
    ).all()

    # Utilisateurs les plus actifs
    top_users = db.session.query(
        User.username,
        func.count(ActivityLog.id).label('count')
    ).join(
        ActivityLog, ActivityLog.user_id == User.id
    ).filter(
        ActivityLog.timestamp >= start_date
    ).group_by(
        User.username
    ).order_by(
        func.count(ActivityLog.id).desc()
    ).limit(5).all()

    return jsonify({
        'daily_actions': [
            {'date': str(row.date), 'count': row.count}
            for row in daily_actions
        ],
        'actions_by_type': [
            {'action': row.action, 'count': row.count}
            for row in actions_by_type
        ],
        'top_users': [
            {'username': row.username, 'count': row.count}
            for row in top_users
        ]
    })


@bp.route('/log/<int:log_id>')
@login_required
@permission_required('view_sauron')
def log_detail(log_id):
    """Détail d'un log"""
    log = ActivityLog.query.get_or_404(log_id)
    return render_template('sauron/detail.html', log=log)
