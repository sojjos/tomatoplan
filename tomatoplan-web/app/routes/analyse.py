"""
Routes pour l'analyse avancée
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from datetime import datetime, timedelta
from sqlalchemy import func

from app.models import db, Mission
from app.permissions import permission_required

bp = Blueprint('analyse', __name__, url_prefix='/analyse')


@bp.route('/')
@login_required
@permission_required('view_analyse')
def index():
    """Dashboard d'analyse avancée"""
    # Période par défaut: 30 derniers jours
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)

    start_str = request.args.get('start', start_date.strftime('%Y-%m-%d'))
    end_str = request.args.get('end', end_date.strftime('%Y-%m-%d'))

    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    except ValueError:
        pass

    return render_template(
        'analyse/index.html',
        start_date=start_date,
        end_date=end_date
    )


@bp.route('/api/data')
@login_required
@permission_required('view_analyse')
def api_data():
    """API pour les données d'analyse"""
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    group_by = request.args.get('group_by', 'sst')  # sst, voyage, chauffeur, date

    start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_str, '%Y-%m-%d').date()

    # Construire la requête selon le groupement
    if group_by == 'sst':
        group_field = Mission.sst
    elif group_by == 'voyage':
        group_field = Mission.voyage
    elif group_by == 'chauffeur':
        group_field = Mission.chauffeur
    elif group_by == 'date':
        group_field = Mission.date
    else:
        group_field = Mission.sst

    results = db.session.query(
        group_field.label('label'),
        func.count(Mission.id).label('missions'),
        func.sum(Mission.revenus).label('revenus'),
        func.sum(Mission.couts).label('couts'),
        func.sum(Mission.marge).label('marge'),
        func.sum(Mission.palettes).label('palettes')
    ).filter(
        Mission.date >= start_date,
        Mission.date <= end_date
    ).group_by(
        group_field
    ).order_by(
        func.sum(Mission.marge).desc()
    ).all()

    data = []
    for row in results:
        data.append({
            'label': str(row.label) if row.label else 'Non défini',
            'missions': row.missions,
            'revenus': float(row.revenus or 0),
            'couts': float(row.couts or 0),
            'marge': float(row.marge or 0),
            'palettes': row.palettes or 0
        })

    return jsonify({'data': data})


@bp.route('/api/timeline')
@login_required
@permission_required('view_analyse')
def api_timeline():
    """API pour les données temporelles"""
    start_str = request.args.get('start')
    end_str = request.args.get('end')

    start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_str, '%Y-%m-%d').date()

    results = db.session.query(
        Mission.date,
        func.count(Mission.id).label('missions'),
        func.sum(Mission.revenus).label('revenus'),
        func.sum(Mission.couts).label('couts'),
        func.sum(Mission.marge).label('marge')
    ).filter(
        Mission.date >= start_date,
        Mission.date <= end_date
    ).group_by(
        Mission.date
    ).order_by(
        Mission.date
    ).all()

    data = []
    for row in results:
        data.append({
            'date': row.date.isoformat(),
            'missions': row.missions,
            'revenus': float(row.revenus or 0),
            'couts': float(row.couts or 0),
            'marge': float(row.marge or 0)
        })

    return jsonify({'data': data})
