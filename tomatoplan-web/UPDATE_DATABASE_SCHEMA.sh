#!/bin/bash
#
# Script de mise à jour du schéma de base de données
# Ajoute le champ telephone aux tables SST et Chauffeurs
#

set -e

echo "🔧 Mise à jour du schéma de base de données..."

# Obtenir le répertoire du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Exécuter les migrations avec Python
./venv/bin/python3 << 'PYPYTHON'
import sys
import os
import sqlite3

# Ajouter le répertoire au path
sys.path.insert(0, os.getcwd())

from app import create_app

# Créer l'application
app = create_app()

with app.app_context():
    # Récupérer le chemin de la base de données
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    db_path = db_uri.replace('sqlite:///', '')

    print(f"📁 Base de données: {db_path}")

    # Connexion à la base de données
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Vérifier et ajouter telephone à la table sst
        cursor.execute("PRAGMA table_info(sst)")
        sst_columns = [column[1] for column in cursor.fetchall()]

        if 'telephone' not in sst_columns:
            print("  ➕ Ajout de la colonne 'telephone' à la table 'sst'...")
            cursor.execute("ALTER TABLE sst ADD COLUMN telephone VARCHAR(20)")
            conn.commit()
            print("  ✅ Colonne 'telephone' ajoutée à 'sst'")
        else:
            print("  ✓ La colonne 'telephone' existe déjà dans 'sst'")

        # Vérifier et ajouter telephone à la table chauffeurs
        cursor.execute("PRAGMA table_info(chauffeurs)")
        chauffeurs_columns = [column[1] for column in cursor.fetchall()]

        if 'telephone' not in chauffeurs_columns:
            print("  ➕ Ajout de la colonne 'telephone' à la table 'chauffeurs'...")
            cursor.execute("ALTER TABLE chauffeurs ADD COLUMN telephone VARCHAR(20)")
            conn.commit()
            print("  ✅ Colonne 'telephone' ajoutée à 'chauffeurs'")
        else:
            print("  ✓ La colonne 'telephone' existe déjà dans 'chauffeurs'")

        print("\n✅ Migration terminée avec succès!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erreur lors de la migration: {e}")
        sys.exit(1)
    finally:
        conn.close()

PYPYTHON

echo ""
echo "✅ Mise à jour du schéma terminée!"
echo ""
echo "ℹ️  Pour appliquer les changements, redémarrez le service:"
echo "   sudo systemctl restart tomatoplan"
