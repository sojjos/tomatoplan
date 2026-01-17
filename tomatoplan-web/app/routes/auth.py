"""
Routes d'authentification
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from datetime import datetime
from app.models import db, User, ActivityLog

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False) == 'on'

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'danger')
            return redirect(url_for('auth.login'))

        if not user.is_active:
            flash('Votre compte a été désactivé. Contactez un administrateur.', 'warning')
            return redirect(url_for('auth.login'))

        # Connexion réussie
        login_user(user, remember=remember)
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Log l'activité
        log = ActivityLog(
            user_id=user.id,
            action='LOGIN',
            entity_type='Session',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

        flash(f'Bienvenue {user.full_name or user.username} !', 'success')

        # Redirection vers la page demandée ou l'accueil
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.index')

        return redirect(next_page)

    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    """Déconnexion"""
    if current_user.is_authenticated:
        # Log l'activité
        log = ActivityLog(
            user_id=current_user.id,
            action='LOGOUT',
            entity_type='Session',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

        logout_user()
        flash('Vous avez été déconnecté.', 'info')

    return redirect(url_for('auth.login'))


@bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    """Changement de mot de passe"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not current_user.check_password(current_password):
            flash('Mot de passe actuel incorrect.', 'danger')
            return redirect(url_for('auth.change_password'))

        if new_password != confirm_password:
            flash('Les nouveaux mots de passe ne correspondent pas.', 'danger')
            return redirect(url_for('auth.change_password'))

        if len(new_password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères.', 'danger')
            return redirect(url_for('auth.change_password'))

        current_user.set_password(new_password)
        db.session.commit()

        # Log l'activité
        log = ActivityLog(
            user_id=current_user.id,
            action='CHANGE_PASSWORD',
            entity_type='User',
            entity_id=current_user.id,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

        flash('Mot de passe modifié avec succès.', 'success')
        return redirect(url_for('main.index'))

    return render_template('auth/change_password.html')
