"""
Routes pour la gestion financière
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
import json

from app.models import db, Mission, SST, TarifSST, RevenuPalette, ActivityLog
from app.permissions import permission_required

bp = Blueprint('finance', __name__, url_prefix='/finance')


@bp.route('/')
@login_required
@permission_required('view_finance')
def index():
    """Dashboard financier"""
    # Période par défaut: 30 derniers jours
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)

    # Permettre de filtrer par période
    start_str = request.args.get('start', start_date.strftime('%Y-%m-%d'))
    end_str = request.args.get('end', end_date.strftime('%Y-%m-%d'))

    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    except ValueError:
        pass

    # Statistiques globales
    stats = db.session.query(
        func.sum(Mission.revenus).label('total_revenus'),
        func.sum(Mission.couts).label('total_couts'),
        func.sum(Mission.marge).label('total_marge'),
        func.count(Mission.id).label('total_missions')
    ).filter(
        Mission.date >= start_date,
        Mission.date <= end_date
    ).first()

    # Stats par SST
    stats_par_sst = db.session.query(
        Mission.sst,
        func.sum(Mission.revenus).label('revenus'),
        func.sum(Mission.couts).label('couts'),
        func.sum(Mission.marge).label('marge'),
        func.count(Mission.id).label('missions')
    ).filter(
        Mission.date >= start_date,
        Mission.date <= end_date
    ).group_by(
        Mission.sst
    ).order_by(
        func.sum(Mission.marge).desc()
    ).all()

    # Stats par voyage
    stats_par_voyage = db.session.query(
        Mission.voyage,
        func.sum(Mission.revenus).label('revenus'),
        func.sum(Mission.couts).label('couts'),
        func.sum(Mission.marge).label('marge'),
        func.count(Mission.id).label('missions')
    ).filter(
        Mission.date >= start_date,
        Mission.date <= end_date
    ).group_by(
        Mission.voyage
    ).order_by(
        func.sum(Mission.marge).desc()
    ).all()

    can_manage = current_user.has_permission('manage_finance')

    return render_template(
        'finance/index.html',
        stats=stats,
        stats_par_sst=stats_par_sst,
        stats_par_voyage=stats_par_voyage,
        start_date=start_date,
        end_date=end_date,
        can_manage=can_manage
    )


@bp.route('/tarifs')
@login_required
@permission_required('manage_finance')
def tarifs():
    """Gestion des tarifs SST"""
    sst_list = SST.query.filter_by(actif=True).order_by(SST.nom).all()
    all_tarifs = TarifSST.query.all()

    # Organiser les tarifs par SST
    tarifs_par_sst = {}
    for tarif in all_tarifs:
        if tarif.sst_id not in tarifs_par_sst:
            tarifs_par_sst[tarif.sst_id] = []
        tarifs_par_sst[tarif.sst_id].append(tarif)

    return render_template(
        'finance/tarifs.html',
        sst_list=sst_list,
        tarifs_par_sst=tarifs_par_sst
    )


@bp.route('/tarifs/update', methods=['POST'])
@login_required
@permission_required('manage_finance')
def update_tarif():
    """Mettre à jour un tarif SST"""
    data = request.get_json()

    sst = SST.query.filter_by(nom=data['sst']).first()
    if not sst:
        return jsonify({'error': 'SST non trouvé'}), 404

    tarif = TarifSST.query.filter_by(
        sst_id=sst.id,
        voyage=data['voyage']
    ).first()

    if tarif:
        old_value = tarif.tarif
        tarif.tarif = float(data['tarif'])
        action = 'EDIT'
    else:
        tarif = TarifSST(
            sst_id=sst.id,
            voyage=data['voyage'],
            tarif=float(data['tarif'])
        )
        db.session.add(tarif)
        old_value = None
        action = 'CREATE'

    db.session.commit()

    log = ActivityLog(
        user_id=current_user.id,
        action=action,
        entity_type='TarifSST',
        entity_id=str(tarif.id),
        details=json.dumps({
            'sst': data['sst'],
            'voyage': data['voyage'],
            'old_tarif': old_value,
            'new_tarif': tarif.tarif
        }),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'success': True})


@bp.route('/revenus-palettes')
@login_required
@permission_required('manage_finance')
def revenus_palettes():
    """Gestion des revenus par palette"""
    revenus = RevenuPalette.query.order_by(RevenuPalette.voyage, RevenuPalette.palettes_min).all()
    return render_template('finance/revenus_palettes.html', revenus=revenus)


@bp.route('/revenus-palettes/update', methods=['POST'])
@login_required
@permission_required('manage_finance')
def update_revenu_palette():
    """Mettre à jour un revenu palette"""
    data = request.get_json()

    revenu = RevenuPalette(
        voyage=data['voyage'],
        palettes_min=int(data['palettes_min']),
        palettes_max=int(data['palettes_max']),
        revenu=float(data['revenu'])
    )

    db.session.add(revenu)
    db.session.commit()

    log = ActivityLog(
        user_id=current_user.id,
        action='CREATE',
        entity_type='RevenuPalette',
        entity_id=str(revenu.id),
        details=json.dumps({
            'voyage': data['voyage'],
            'palettes_min': data['palettes_min'],
            'palettes_max': data['palettes_max'],
            'revenu': data['revenu']
        }),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'success': True})
