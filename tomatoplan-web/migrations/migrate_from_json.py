#!/usr/bin/env python3
"""
Script de migration des données JSON vers SQLite

Ce script importe les données de l'ancienne application Tkinter (JSON)
vers la nouvelle application web (SQLite).
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import (
    db, User, Mission, Chauffeur, DisponibiliteChauffeur,
    Voyage, SST, TarifSST, RevenuPalette, AnnouncementConfig
)


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'


def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.ENDC} {msg}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.ENDC} {msg}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.ENDC} {msg}")


def print_error(msg):
    print(f"{Colors.RED}✗{Colors.ENDC} {msg}")


def load_json_file(filepath):
    """Charge un fichier JSON s'il existe"""
    if not os.path.exists(filepath):
        print_warning(f"Fichier non trouvé: {filepath}")
        return None

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Erreur lors de la lecture de {filepath}: {e}")
        return None


def migrate_chauffeurs(data_dir, sst_ids):
    """Migre les chauffeurs"""
    print_info("Migration des chauffeurs...")

    filepath = os.path.join(data_dir, 'chauffeurs.json')
    data = load_json_file(filepath)

    if not data:
        return 0

    count = 0
    for chauffeur_data in data:
        # Convertir le nom SST en ID si présent
        sst_id = None
        if chauffeur_data.get('sst') and chauffeur_data['sst'] in sst_ids:
            sst_id = sst_ids[chauffeur_data['sst']]
        elif chauffeur_data.get('sst_id'):
            sst_id = chauffeur_data['sst_id']

        chauffeur = Chauffeur(
            id=chauffeur_data.get('id'),
            nom=chauffeur_data['nom'],
            prenom=chauffeur_data.get('prenom'),
            sst_id=sst_id,
            telephone=chauffeur_data.get('telephone'),
            actif=chauffeur_data.get('actif', True),
            infos=chauffeur_data.get('infos')
        )
        db.session.add(chauffeur)
        count += 1

    db.session.commit()
    print_success(f"{count} chauffeurs migrés")
    return count


def migrate_voyages(data_dir):
    """Migre les voyages"""
    print_info("Migration des voyages...")

    filepath = os.path.join(data_dir, 'voyages.json')
    data = load_json_file(filepath)

    if not data:
        return 0

    count = 0
    for voyage_data in data:
        voyage = Voyage(
            code=voyage_data['code'],
            type=voyage_data.get('type', 'LIVRAISON'),
            actif=voyage_data.get('actif', True),
            country=voyage_data.get('country', 'Belgique'),
            duree=voyage_data.get('duree', 60)
        )
        db.session.add(voyage)
        count += 1

    db.session.commit()
    print_success(f"{count} voyages migrés")
    return count


def migrate_sst(data_dir):
    """Migre les SST"""
    print_info("Migration des SST...")

    filepath = os.path.join(data_dir, 'sst.json')
    data = load_json_file(filepath)

    if not data:
        return 0

    count = 0
    sst_ids = {}  # Mapping nom -> id

    for sst_name in data:
        # Charger les emails depuis sst_emails.json
        emails_file = os.path.join(data_dir, 'sst_emails.json')
        emails_data = load_json_file(emails_file) or {}
        emails = emails_data.get(sst_name, [])

        sst = SST(
            nom=sst_name,
            actif=True,
            emails=json.dumps(emails)
        )
        db.session.add(sst)
        db.session.flush()  # Pour obtenir l'ID
        sst_ids[sst_name] = sst.id
        count += 1

    db.session.commit()
    print_success(f"{count} SST migrés")
    return sst_ids


def migrate_tarifs_sst(data_dir, sst_ids):
    """Migre les tarifs SST"""
    print_info("Migration des tarifs SST...")

    filepath = os.path.join(data_dir, 'tarifs_sst.json')
    data = load_json_file(filepath)

    if not data:
        return 0

    count = 0
    for sst_name, tarifs in data.items():
        if sst_name not in sst_ids:
            print_warning(f"SST {sst_name} non trouvé, création...")
            sst = SST(nom=sst_name, actif=True, emails='[]')
            db.session.add(sst)
            db.session.flush()
            sst_ids[sst_name] = sst.id

        for voyage, tarif in tarifs.items():
            tarif_sst = TarifSST(
                sst_id=sst_ids[sst_name],
                voyage=voyage,
                tarif=float(tarif)
            )
            db.session.add(tarif_sst)
            count += 1

    db.session.commit()
    print_success(f"{count} tarifs migrés")
    return count


def migrate_revenus_palettes(data_dir):
    """Migre les revenus par palette"""
    print_info("Migration des revenus par palette...")

    filepath = os.path.join(data_dir, 'revenus_palettes.json')
    data = load_json_file(filepath)

    if not data:
        return 0

    count = 0
    for voyage, configs in data.items():
        for config in configs:
            revenu = RevenuPalette(
                voyage=voyage,
                palettes_min=config['min'],
                palettes_max=config['max'],
                revenu=float(config['revenu'])
            )
            db.session.add(revenu)
            count += 1

    db.session.commit()
    print_success(f"{count} configurations de revenus migrées")
    return count


def migrate_missions(data_dir):
    """Migre les missions"""
    print_info("Migration des missions...")

    filepath = os.path.join(data_dir, 'missions.json')
    data = load_json_file(filepath)

    if not data:
        return 0

    count = 0
    for mission_data in data:
        try:
            # Parser la date
            date_str = mission_data.get('date')
            if date_str:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                continue

            mission = Mission(
                id=mission_data.get('id'),
                date=date,
                heure=mission_data.get('heure', '00:00'),
                type=mission_data.get('type', 'LIVRAISON'),
                voyage=mission_data.get('voyage', ''),
                sst=mission_data.get('sst', ''),
                chauffeur=mission_data.get('chauffeur'),
                palettes=mission_data.get('palettes', 0),
                numero=mission_data.get('numero'),
                pays=mission_data.get('pays', 'Belgique'),
                ramasse=mission_data.get('ramasse', False),
                infos=mission_data.get('infos'),
                effectue=mission_data.get('effectue', False),
                sans_sst=mission_data.get('sans_sst', False),
                revenus=float(mission_data.get('revenus', 0)),
                couts=float(mission_data.get('couts', 0)),
                marge=float(mission_data.get('marge', 0))
            )
            db.session.add(mission)
            count += 1

            if count % 100 == 0:
                db.session.commit()
                print_info(f"  {count} missions migrées...")

        except Exception as e:
            print_warning(f"Erreur pour mission {mission_data.get('id')}: {e}")
            continue

    db.session.commit()
    print_success(f"{count} missions migrées")
    return count


def migrate_announcement_config(data_dir):
    """Migre la configuration des annonces"""
    print_info("Migration de la configuration des annonces...")

    filepath = os.path.join(data_dir, 'announcement_config.json')
    data = load_json_file(filepath)

    if not data:
        return 0

    count = 0
    for key, value in data.items():
        config = AnnouncementConfig(
            key=key,
            value=str(value)
        )
        db.session.add(config)
        count += 1

    db.session.commit()
    print_success(f"{count} configurations d'annonces migrées")
    return count


def main():
    """Fonction principale de migration"""
    print()
    print("=" * 60)
    print("  MIGRATION DES DONNÉES JSON → SQLite")
    print("=" * 60)
    print()

    # Demander le répertoire des données
    print("Veuillez indiquer le chemin vers le répertoire _data de l'ancienne application")
    print("Exemple: C:/Users/user/OneDrive - STEF/.../_data")
    print()

    data_dir = input("Chemin du répertoire _data: ").strip()

    if not os.path.exists(data_dir):
        print_error(f"Répertoire non trouvé: {data_dir}")
        sys.exit(1)

    if not os.path.isdir(data_dir):
        print_error(f"Le chemin n'est pas un répertoire: {data_dir}")
        sys.exit(1)

    print()
    print_info(f"Répertoire source: {data_dir}")
    print()

    response = input("Continuer la migration ? (O/n): ").lower()
    if response == 'n':
        print_info("Migration annulée")
        sys.exit(0)

    # Créer l'application
    app = create_app()

    with app.app_context():
        print()
        print_info("Début de la migration...")
        print()

        total_count = 0

        # Migration dans l'ordre des dépendances
        try:
            # Migrer les SST d'abord (nécessaire pour les chauffeurs)
            sst_ids = migrate_sst(data_dir)
            total_count += len(sst_ids)

            # Puis migrer les chauffeurs avec les sst_ids
            total_count += migrate_chauffeurs(data_dir, sst_ids)
            total_count += migrate_voyages(data_dir)
            total_count += migrate_tarifs_sst(data_dir, sst_ids)
            total_count += migrate_revenus_palettes(data_dir)
            total_count += migrate_missions(data_dir)
            total_count += migrate_announcement_config(data_dir)

            print()
            print("=" * 60)
            print_success(f"Migration terminée ! {total_count} éléments migrés")
            print("=" * 60)
            print()

        except Exception as e:
            print()
            print_error(f"Erreur lors de la migration: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("Migration interrompue par l'utilisateur")
        sys.exit(1)
