#!/usr/bin/env python3
"""
Script de migration pour mettre à jour le schéma de la table chauffeurs
Date: 2026-01-19

Ce script migre la base de données existante pour:
1. Ajouter les colonnes 'prenom' et 'telephone' à la table chauffeurs
2. Remplacer la colonne 'sst' (texte) par 'sst_id' (clé étrangère)

IMPORTANT: Ce script fait automatiquement une sauvegarde de la base de données
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime

# Couleurs pour l'affichage
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_info(msg):
    print(f"{Colors.OKBLUE}ℹ {msg}{Colors.ENDC}")

def print_success(msg):
    print(f"{Colors.OKGREEN}✓ {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}✗ {msg}{Colors.ENDC}")

def backup_database(db_path):
    """Crée une sauvegarde de la base de données"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"

    print_info(f"Création d'une sauvegarde: {backup_path}")
    shutil.copy2(db_path, backup_path)
    print_success(f"Sauvegarde créée: {backup_path}")

    return backup_path

def check_table_exists(cursor, table_name):
    """Vérifie si une table existe"""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None

def get_table_columns(cursor, table_name):
    """Récupère la liste des colonnes d'une table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1]: row for row in cursor.fetchall()}

def migrate_chauffeurs_table(db_path):
    """Migre la table chauffeurs vers le nouveau schéma"""

    print()
    print("=" * 70)
    print(f"{Colors.BOLD}Migration du schéma de la table chauffeurs{Colors.ENDC}")
    print("=" * 70)
    print()

    # Vérifier que la base de données existe
    if not os.path.exists(db_path):
        print_error(f"Base de données non trouvée: {db_path}")
        print_info("Si c'est une nouvelle installation, aucune migration n'est nécessaire.")
        return False

    # Créer une sauvegarde
    backup_path = backup_database(db_path)

    try:
        # Connexion à la base de données
        print_info("Connexion à la base de données...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Vérifier que la table chauffeurs existe
        if not check_table_exists(cursor, 'chauffeurs'):
            print_error("La table 'chauffeurs' n'existe pas!")
            conn.close()
            return False

        # Vérifier que la table SST existe
        if not check_table_exists(cursor, 'sst'):
            print_error("La table 'sst' n'existe pas!")
            print_warning("Créez d'abord les tables SST avant de migrer les chauffeurs.")
            conn.close()
            return False

        # Récupérer les colonnes actuelles
        print_info("Analyse du schéma actuel...")
        columns = get_table_columns(cursor, 'chauffeurs')

        # Vérifier si la migration est nécessaire
        needs_migration = False
        if 'sst' in columns and 'sst_id' not in columns:
            print_warning("La colonne 'sst' (texte) doit être migrée vers 'sst_id' (FK)")
            needs_migration = True

        if 'prenom' not in columns:
            print_warning("La colonne 'prenom' n'existe pas et sera ajoutée")
            needs_migration = True

        if 'telephone' not in columns:
            print_warning("La colonne 'telephone' n'existe pas et sera ajoutée")
            needs_migration = True

        if not needs_migration:
            print_success("La table chauffeurs est déjà à jour!")
            conn.close()
            return True

        print()
        print_info("Début de la migration...")
        print()

        # Désactiver les contraintes de clé étrangère temporairement
        cursor.execute("PRAGMA foreign_keys = OFF")

        # Démarrer une transaction
        cursor.execute("BEGIN TRANSACTION")

        # Créer la nouvelle table
        print_info("Création de la nouvelle table chauffeurs_new...")
        cursor.execute("""
            CREATE TABLE chauffeurs_new (
                id TEXT PRIMARY KEY,
                nom TEXT NOT NULL UNIQUE,
                prenom TEXT,
                sst_id INTEGER,
                telephone TEXT,
                actif INTEGER DEFAULT 1,
                infos TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (sst_id) REFERENCES sst (id)
            )
        """)

        # Copier les données
        print_info("Copie des données existantes...")

        if 'sst' in columns:
            # Ancienne structure avec colonne sst en texte
            cursor.execute("""
                INSERT INTO chauffeurs_new (id, nom, prenom, sst_id, telephone, actif, infos, created_at, updated_at)
                SELECT
                    c.id,
                    c.nom,
                    NULL as prenom,
                    s.id as sst_id,
                    NULL as telephone,
                    c.actif,
                    c.infos,
                    c.created_at,
                    c.updated_at
                FROM chauffeurs c
                LEFT JOIN sst s ON c.sst = s.nom
            """)
        else:
            # Structure déjà avec sst_id (migration partielle)
            cursor.execute("""
                INSERT INTO chauffeurs_new (id, nom, prenom, sst_id, telephone, actif, infos, created_at, updated_at)
                SELECT
                    id,
                    nom,
                    prenom,
                    sst_id,
                    telephone,
                    actif,
                    infos,
                    created_at,
                    updated_at
                FROM chauffeurs
            """)

        rows_copied = cursor.rowcount
        print_success(f"{rows_copied} chauffeur(s) copié(s)")

        # Supprimer l'ancienne table
        print_info("Suppression de l'ancienne table...")
        cursor.execute("DROP TABLE chauffeurs")

        # Renommer la nouvelle table
        print_info("Renommage de la nouvelle table...")
        cursor.execute("ALTER TABLE chauffeurs_new RENAME TO chauffeurs")

        # Recréer les index
        print_info("Création des index...")
        cursor.execute("CREATE INDEX ix_chauffeurs_nom ON chauffeurs (nom)")
        cursor.execute("CREATE INDEX ix_chauffeurs_sst_id ON chauffeurs (sst_id)")
        cursor.execute("CREATE INDEX ix_chauffeurs_actif ON chauffeurs (actif)")

        # Valider la transaction
        print_info("Validation de la migration...")
        conn.commit()

        # Réactiver les contraintes de clé étrangère
        cursor.execute("PRAGMA foreign_keys = ON")

        # Vérification
        print()
        print_info("Vérification de la migration...")
        cursor.execute("SELECT COUNT(*) FROM chauffeurs")
        total = cursor.fetchone()[0]
        print_success(f"Total de chauffeurs: {total}")

        cursor.execute("SELECT COUNT(*) FROM chauffeurs WHERE sst_id IS NOT NULL")
        with_sst = cursor.fetchone()[0]
        print_success(f"Chauffeurs avec SST assigné: {with_sst}")

        # Fermer la connexion
        conn.close()

        print()
        print("=" * 70)
        print_success("Migration terminée avec succès!")
        print_info(f"Sauvegarde disponible: {backup_path}")
        print("=" * 70)
        print()

        return True

    except Exception as e:
        print()
        print_error(f"Erreur lors de la migration: {e}")

        # Restaurer la sauvegarde
        print_warning("Restauration de la sauvegarde...")
        try:
            shutil.copy2(backup_path, db_path)
            print_success("Base de données restaurée depuis la sauvegarde")
        except Exception as restore_error:
            print_error(f"Erreur lors de la restauration: {restore_error}")
            print_warning(f"Veuillez restaurer manuellement depuis: {backup_path}")

        return False

def main():
    """Point d'entrée principal"""

    # Déterminer le chemin de la base de données
    db_path = os.environ.get('DATABASE_PATH', 'instance/tomatoplan.db')

    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    print()
    print(f"{Colors.BOLD}Script de migration - Schéma Chauffeur{Colors.ENDC}")
    print(f"Base de données: {db_path}")
    print()

    response = input(f"{Colors.WARNING}Voulez-vous continuer avec la migration ? (O/n): {Colors.ENDC}").lower()
    if response == 'n':
        print_info("Migration annulée")
        sys.exit(0)

    success = migrate_chauffeurs_table(db_path)

    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("Migration annulée par l'utilisateur")
        sys.exit(1)
