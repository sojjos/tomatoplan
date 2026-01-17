#!/usr/bin/env python3
"""
Script de démarrage de TomatoPlan Web

Usage:
    python run.py                    # Mode développement
    python run.py --production       # Mode production
    python run.py --host 0.0.0.0     # Accessible depuis le réseau
    python run.py --port 8080        # Port personnalisé
"""

import os
import sys
import argparse
from app import create_app

def main():
    parser = argparse.ArgumentParser(description='Démarrer TomatoPlan Web')
    parser.add_argument('--production', action='store_true',
                        help='Démarrer en mode production')
    parser.add_argument('--host', default='127.0.0.1',
                        help='Adresse d\'écoute (défaut: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000,
                        help='Port d\'écoute (défaut: 5000)')
    parser.add_argument('--debug', action='store_true',
                        help='Activer le mode debug')

    args = parser.parse_args()

    # Déterminer le mode de configuration
    if args.production:
        config_name = 'production'
        print('🚀 Démarrage en mode PRODUCTION')
        print('⚠️  Assurez-vous que :')
        print('   - La clé secrète est configurée (SECRET_KEY)')
        print('   - Le HTTPS est activé')
        print('   - Les sauvegardes sont en place')
        print()
    else:
        config_name = 'development'
        print('🔧 Démarrage en mode DÉVELOPPEMENT')
        print()

    # Créer l'application
    app = create_app(config_name)

    # Informations de démarrage
    print('=' * 60)
    print(f'  TomatoPlan Web - Gestion de planning de transport')
    print('=' * 60)
    print(f'  Environnement: {config_name.upper()}')
    print(f'  URL: http://{args.host}:{args.port}')
    print(f'  Base de données: {app.config["SQLALCHEMY_DATABASE_URI"]}')
    print('=' * 60)
    print()
    print('ℹ️  Première connexion: admin / admin')
    print('⚠️  IMPORTANT: Changez le mot de passe admin immédiatement!')
    print()
    print('📚 Pour arrêter le serveur: Ctrl+C')
    print()

    # Démarrer le serveur
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug or not args.production,
            use_reloader=not args.production
        )
    except KeyboardInterrupt:
        print('\n\n👋 Arrêt du serveur...')
        sys.exit(0)
    except Exception as e:
        print(f'\n❌ Erreur lors du démarrage: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
