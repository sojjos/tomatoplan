#!/bin/bash
#
# Script de mise à jour du schéma chauffeur
# Ajoute les champs prenom et sst_id
#

set -e

echo "🔧 Mise à jour du schéma chauffeur..."

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
        # Vérifier et ajouter prenom à la table chauffeurs
        cursor.execute("PRAGMA table_info(chauffeurs)")
        chauffeurs_columns = [column[1] for column in cursor.fetchall()]

        if 'prenom' not in chauffeurs_columns:
            print("  ➕ Ajout de la colonne 'prenom' à la table 'chauffeurs'...")
            cursor.execute("ALTER TABLE chauffeurs ADD COLUMN prenom VARCHAR(100)")
            conn.commit()
            print("  ✅ Colonne 'prenom' ajoutée à 'chauffeurs'")
        else:
            print("  ✓ La colonne 'prenom' existe déjà dans 'chauffeurs'")

        # Vérifier et ajouter sst_id à la table chauffeurs
        if 'sst_id' not in chauffeurs_columns:
            print("  ➕ Ajout de la colonne 'sst_id' à la table 'chauffeurs'...")
            cursor.execute("ALTER TABLE chauffeurs ADD COLUMN sst_id INTEGER")
            conn.commit()
            print("  ✅ Colonne 'sst_id' ajoutée à 'chauffeurs'")

            # Migrer les données de sst vers sst_id
            print("  🔄 Migration des données SST...")
            cursor.execute("""
                SELECT chauffeurs.id, chauffeurs.sst, sst.id
                FROM chauffeurs
                LEFT JOIN sst ON sst.nom = chauffeurs.sst
                WHERE chauffeurs.sst IS NOT NULL AND chauffeurs.sst != ''
            """)
            migrations = cursor.fetchall()

            for chauffeur_id, sst_nom, sst_id in migrations:
                if sst_id:
                    cursor.execute(
                        "UPDATE chauffeurs SET sst_id = ? WHERE id = ?",
                        (sst_id, chauffeur_id)
                    )
                    print(f"    ✓ Chauffeur {chauffeur_id}: {sst_nom} → SST ID {sst_id}")

            conn.commit()
            print(f"  ✅ {len(migrations)} chauffeurs migrés vers le nouveau système SST")
        else:
            print("  ✓ La colonne 'sst_id' existe déjà dans 'chauffeurs'")

        print("\n✅ Migration terminée avec succès!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()

PYPYTHON

echo ""
echo "✅ Mise à jour du schéma terminée!"
echo ""
echo "ℹ️  Pour appliquer les changements, redémarrez le service:"
echo "   sudo systemctl restart tomatoplan"
