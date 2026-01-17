#!/usr/bin/env python3
"""
Script d'installation de TomatoPlan Web

Ce script installe et configure TomatoPlan Web de manière automatique et interactive.
"""

import os
import sys
import subprocess
import platform
import secrets
from pathlib import Path

# Couleurs pour le terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Affiche un en-tête stylisé"""
    print()
    print(Colors.HEADER + Colors.BOLD + '=' * 60 + Colors.ENDC)
    print(Colors.HEADER + Colors.BOLD + text.center(60) + Colors.ENDC)
    print(Colors.HEADER + Colors.BOLD + '=' * 60 + Colors.ENDC)
    print()


def print_success(text):
    """Affiche un message de succès"""
    print(Colors.GREEN + '✓ ' + text + Colors.ENDC)


def print_info(text):
    """Affiche un message d'information"""
    print(Colors.CYAN + 'ℹ ' + text + Colors.ENDC)


def print_warning(text):
    """Affiche un avertissement"""
    print(Colors.WARNING + '⚠ ' + text + Colors.ENDC)


def print_error(text):
    """Affiche une erreur"""
    print(Colors.FAIL + '✗ ' + text + Colors.ENDC)


def run_command(command, description, show_output=False):
    """Exécute une commande et affiche le résultat"""
    print_info(f'{description}...')
    try:
        if show_output:
            result = subprocess.run(command, shell=True, check=True)
        else:
            result = subprocess.run(
                command, shell=True, check=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        print_success(f'{description} - Terminé')
        return True
    except subprocess.CalledProcessError as e:
        print_error(f'{description} - Échec')
        if not show_output:
            print(e.stderr.decode() if e.stderr else str(e))
        return False


def check_python_version():
    """Vérifie que Python 3.8+ est installé"""
    print_info('Vérification de la version de Python...')
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f'Python 3.8+ requis, vous avez Python {version.major}.{version.minor}')
        return False
    print_success(f'Python {version.major}.{version.minor}.{version.micro} détecté')
    return True


def create_virtual_environment():
    """Crée un environnement virtuel"""
    if os.path.exists('venv'):
        print_info('Environnement virtuel existant trouvé')
        response = input('Voulez-vous le recréer ? (o/N): ').lower()
        if response == 'o':
            run_command('rm -rf venv', 'Suppression de l\'ancien environnement')
        else:
            return True

    return run_command(
        f'{sys.executable} -m venv venv',
        'Création de l\'environnement virtuel'
    )


def get_pip_command():
    """Retourne la commande pip appropriée selon l'OS"""
    if platform.system() == 'Windows':
        return 'venv\\Scripts\\pip.exe'
    return 'venv/bin/pip'


def get_python_command():
    """Retourne la commande python appropriée selon l'OS"""
    if platform.system() == 'Windows':
        return 'venv\\Scripts\\python.exe'
    return 'venv/bin/python'


def install_dependencies():
    """Installe les dépendances Python"""
    pip_cmd = get_pip_command()

    # Mise à jour de pip
    run_command(
        f'{pip_cmd} install --upgrade pip',
        'Mise à jour de pip'
    )

    # Installation des dépendances
    return run_command(
        f'{pip_cmd} install -r requirements.txt',
        'Installation des dépendances',
        show_output=True
    )


def generate_secret_key():
    """Génère une clé secrète sécurisée"""
    return secrets.token_hex(32)


def create_env_file():
    """Crée le fichier .env avec la configuration"""
    print_info('Configuration de l\'environnement...')

    env_exists = os.path.exists('.env')
    if env_exists:
        response = input('.env existe déjà. Recréer ? (o/N): ').lower()
        if response != 'o':
            print_info('.env conservé')
            return True

    secret_key = generate_secret_key()

    env_content = f"""# Configuration TomatoPlan Web
# Généré automatiquement par install.py

# Clé secrète (À GARDER CONFIDENTIELLE!)
SECRET_KEY={secret_key}

# Environnement (development, production)
FLASK_ENV=development

# Base de données
DATABASE_URL=sqlite:///tomatoplan.db

# Configuration email (optionnel, pour les annonces SST)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=noreply@tomatoplan.com

# Debug
FLASK_DEBUG=1
"""

    with open('.env', 'w') as f:
        f.write(env_content)

    print_success('Fichier .env créé')
    return True


def initialize_database():
    """Initialise la base de données"""
    python_cmd = get_python_command()

    print_info('Initialisation de la base de données...')

    # Créer les tables
    init_script = """
from app import create_app
from app.models import db

app = create_app()
with app.app_context():
    db.create_all()
    print('✓ Base de données initialisée')
"""

    with open('_temp_init.py', 'w') as f:
        f.write(init_script)

    result = run_command(
        f'{python_cmd} _temp_init.py',
        'Création des tables'
    )

    os.remove('_temp_init.py')

    return result


def create_directories():
    """Crée les répertoires nécessaires"""
    print_info('Création des répertoires...')

    dirs = [
        'uploads',
        'exports',
        'logs',
        'instance'
    ]

    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        print_success(f'Répertoire {directory} créé')

    return True


def display_completion_message():
    """Affiche le message de fin d'installation"""
    print_header('INSTALLATION TERMINÉE')

    print(Colors.GREEN + Colors.BOLD)
    print('🎉 TomatoPlan Web a été installé avec succès!')
    print(Colors.ENDC)
    print()
    print('Pour démarrer l\'application:')
    print()

    if platform.system() == 'Windows':
        print(Colors.CYAN + '  1. Activez l\'environnement virtuel:' + Colors.ENDC)
        print('     venv\\Scripts\\activate')
        print()
        print(Colors.CYAN + '  2. Démarrez le serveur:' + Colors.ENDC)
        print('     python run.py')
    else:
        print(Colors.CYAN + '  1. Activez l\'environnement virtuel:' + Colors.ENDC)
        print('     source venv/bin/activate')
        print()
        print(Colors.CYAN + '  2. Démarrez le serveur:' + Colors.ENDC)
        print('     python run.py')

    print()
    print(Colors.CYAN + '  3. Ouvrez votre navigateur à:' + Colors.ENDC)
    print('     http://127.0.0.1:5000')
    print()
    print(Colors.CYAN + '  4. Connectez-vous avec:' + Colors.ENDC)
    print('     Utilisateur: admin')
    print('     Mot de passe: admin')
    print()
    print(Colors.WARNING + '⚠️  IMPORTANT: Changez le mot de passe admin immédiatement!' + Colors.ENDC)
    print()
    print('Documentation complète dans README.md')
    print()


def main():
    """Fonction principale d'installation"""
    print_header('INSTALLATION DE TOMATOPLAN WEB')

    print("""
    Ce script va installer TomatoPlan Web avec toutes ses dépendances.

    Étapes:
    1. Vérification de Python
    2. Création de l'environnement virtuel
    3. Installation des dépendances
    4. Configuration de l'environnement
    5. Initialisation de la base de données
    6. Création des répertoires
    """)

    response = input('Voulez-vous continuer ? (O/n): ').lower()
    if response == 'n':
        print_info('Installation annulée')
        sys.exit(0)

    # Vérifier qu'on est dans le bon répertoire
    if not os.path.exists('requirements.txt'):
        print_error('requirements.txt non trouvé')
        print_error('Veuillez lancer ce script depuis le répertoire tomatoplan-web/')
        sys.exit(1)

    # Étapes d'installation
    steps = [
        ('Vérification de Python', check_python_version),
        ('Création de l\'environnement virtuel', create_virtual_environment),
        ('Installation des dépendances', install_dependencies),
        ('Configuration de l\'environnement', create_env_file),
        ('Création des répertoires', create_directories),
        ('Initialisation de la base de données', initialize_database),
    ]

    print_header('INSTALLATION EN COURS')

    for step_name, step_func in steps:
        print()
        if not step_func():
            print_error(f'Échec lors de: {step_name}')
            print_error('Installation interrompue')
            sys.exit(1)

    display_completion_message()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning('Installation interrompue par l\'utilisateur')
        sys.exit(1)
    except Exception as e:
        print()
        print_error(f'Erreur inattendue: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
