"""
Système de gestion des permissions
"""
from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user


def permission_required(permission):
    """
    Décorateur pour vérifier qu'un utilisateur a une permission spécifique

    Usage:
        @permission_required('edit_planning')
        def edit_mission():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
                return redirect(url_for('auth.login'))

            if not current_user.has_permission(permission):
                flash('Vous n\'avez pas les droits nécessaires pour accéder à cette page.', 'danger')
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_required(role):
    """
    Décorateur pour vérifier qu'un utilisateur a un rôle spécifique

    Usage:
        @role_required('admin')
        def admin_panel():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
                return redirect(url_for('auth.login'))

            if current_user.role != role:
                flash('Vous n\'avez pas les droits nécessaires pour accéder à cette page.', 'danger')
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def any_permission_required(*permissions):
    """
    Décorateur pour vérifier qu'un utilisateur a au moins une des permissions listées

    Usage:
        @any_permission_required('view_planning', 'edit_planning')
        def view_planning():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
                return redirect(url_for('auth.login'))

            has_any = any(current_user.has_permission(perm) for perm in permissions)
            if not has_any:
                flash('Vous n\'avez pas les droits nécessaires pour accéder à cette page.', 'danger')
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator
