"""
Routes API générales
"""
from flask import Blueprint, jsonify, request, send_file
from flask_login import login_required, current_user
from datetime import datetime
import os

from app.models import db, Mission, Chauffeur, Voyage, SST
from app.permissions import permission_required

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/search')
@login_required
def search():
    """Recherche globale"""
    query_str = request.args.get('q', '').strip()
    entity_type = request.args.get('type', 'all')

    if not query_str or len(query_str) < 2:
        return jsonify({'results': []})

    results = {
        'missions': [],
        'chauffeurs': [],
        'voyages': [],
        'sst': []
    }

    if entity_type in ['all', 'missions'] and current_user.has_permission('view_planning'):
        missions = Mission.query.filter(
            db.or_(
                Mission.voyage.ilike(f'%{query_str}%'),
                Mission.chauffeur.ilike(f'%{query_str}%'),
                Mission.sst.ilike(f'%{query_str}%'),
                Mission.numero.ilike(f'%{query_str}%')
            )
        ).limit(10).all()
        results['missions'] = [m.to_dict() for m in missions]

    if entity_type in ['all', 'chauffeurs'] and current_user.has_permission('view_drivers'):
        chauffeurs = Chauffeur.query.filter(
            Chauffeur.nom.ilike(f'%{query_str}%')
        ).limit(10).all()
        results['chauffeurs'] = [c.to_dict() for c in chauffeurs]

    if entity_type in ['all', 'voyages']:
        voyages = Voyage.query.filter(
            Voyage.code.ilike(f'%{query_str}%')
        ).limit(10).all()
        results['voyages'] = [v.to_dict() for v in voyages]

    if entity_type in ['all', 'sst']:
        sst = SST.query.filter(
            SST.nom.ilike(f'%{query_str}%')
        ).limit(10).all()
        results['sst'] = [s.to_dict() for s in sst]

    return jsonify({'results': results})


@bp.route('/export/missions')
@login_required
@permission_required('view_planning')
def export_missions():
    """Exporter les missions en Excel"""
    from app.utils.exports import export_missions_to_excel

    # Paramètres
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    format_type = request.args.get('format', 'excel')  # excel ou pdf

    if not start_date or not end_date:
        return jsonify({'error': 'Dates manquantes'}), 400

    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Format de date invalide'}), 400

    # Récupérer les missions
    missions = Mission.query.filter(
        Mission.date >= start,
        Mission.date <= end
    ).order_by(Mission.date, Mission.heure).all()

    if format_type == 'excel':
        filepath = export_missions_to_excel(missions, start, end)
        return send_file(
            filepath,
            as_attachment=True,
            download_name=f'missions_{start}_{end}.xlsx'
        )
    elif format_type == 'pdf':
        from app.utils.exports import export_missions_to_pdf
        filepath = export_missions_to_pdf(missions, start, end)
        return send_file(
            filepath,
            as_attachment=True,
            download_name=f'missions_{start}_{end}.pdf'
        )
    else:
        return jsonify({'error': 'Format non supporté'}), 400


@bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })


@bp.route('/calcul-mission')
@login_required
def calcul_mission():
    """Calcule automatiquement les revenus, coûts et marge d'une mission"""
    from app.utils.calculs import calculer_mission_complete

    voyage_code = request.args.get('voyage')
    sst_nom = request.args.get('sst')
    palettes = request.args.get('palettes', type=int, default=0)

    if not voyage_code or not sst_nom:
        return jsonify({'error': 'Paramètres manquants'}), 400

    try:
        calculs = calculer_mission_complete(voyage_code, palettes, sst_nom)
        return jsonify(calculs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/chauffeurs-par-sst')
@login_required
def chauffeurs_par_sst():
    """Retourne les chauffeurs filtrés par SST"""
    sst_nom = request.args.get('sst')

    if not sst_nom:
        # Retourner tous les chauffeurs actifs
        chauffeurs = Chauffeur.query.filter_by(actif=True).order_by(Chauffeur.nom).all()
    else:
        # Trouver le SST
        sst = SST.query.filter_by(nom=sst_nom).first()
        if not sst:
            return jsonify({'error': 'SST non trouvé'}), 404

        # Retourner uniquement les chauffeurs de ce SST
        chauffeurs = Chauffeur.query.filter_by(
            sst_id=sst.id,
            actif=True
        ).order_by(Chauffeur.nom).all()

    return jsonify({
        'chauffeurs': [{'id': c.id, 'nom': c.nom, 'prenom': c.prenom} for c in chauffeurs]
    })

