"""
Routes principales
"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from app.models import db, Mission, Chauffeur, ActivityLog

bp = Blueprint('main', __name__)


@bp.route('/')
@login_required
def index():
    """Page d'accueil / Dashboard"""

    # Statistiques pour aujourd'hui
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    missions_today = Mission.query.filter_by(date=today).count()
    missions_tomorrow = Mission.query.filter_by(date=tomorrow).count()
    missions_effectuees = Mission.query.filter_by(date=today, effectue=True).count()

    # Chauffeurs actifs
    chauffeurs_actifs = Chauffeur.query.filter_by(actif=True).count()

    # Missions par SST aujourd'hui
    missions_par_sst = db.session.query(
        Mission.sst,
        func.count(Mission.id).label('count')
    ).filter(
        Mission.date == today
    ).group_by(
        Mission.sst
    ).order_by(
        func.count(Mission.id).desc()
    ).limit(5).all()

    # Dernières activités (si l'utilisateur a la permission)
    recent_activities = []
    if current_user.has_permission('view_sauron'):
        recent_activities = ActivityLog.query.order_by(
            ActivityLog.timestamp.desc()
        ).limit(10).all()

    # Missions à venir dans les 7 prochains jours
    upcoming_missions = Mission.query.filter(
        Mission.date >= today,
        Mission.date <= today + timedelta(days=7)
    ).order_by(Mission.date, Mission.heure).limit(20).all()

    return render_template(
        'main/index.html',
        missions_today=missions_today,
        missions_tomorrow=missions_tomorrow,
        missions_effectuees=missions_effectuees,
        chauffeurs_actifs=chauffeurs_actifs,
        missions_par_sst=missions_par_sst,
        recent_activities=recent_activities,
        upcoming_missions=upcoming_missions,
        today=today
    )


@bp.route('/aide')
@login_required
def aide():
    """Page d'aide"""
    return render_template('main/aide.html')


@bp.route('/about')
@login_required
def about():
    """À propos de l'application"""
    return render_template('main/about.html')
