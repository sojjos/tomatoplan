#!/bin/bash
#
# Script de déploiement complet pour la production
#

set -e

echo "========================================="
echo "🚀 DÉPLOIEMENT TOMATOPLAN WEB"
echo "========================================="
echo ""

# Vérifier qu'on est dans le bon répertoire
if [ ! -f "run.py" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis /opt/tomatoplan/tomatoplan-web"
    exit 1
fi

# 1. Pull les dernières modifications
echo "📥 Étape 1/4: Récupération des dernières modifications..."
sudo -u tomatoplan git fetch origin
sudo -u tomatoplan git pull origin claude/web-app-sqlite-auth-sKRgj
echo "✅ Code mis à jour"
echo ""

# 2. Migration de la base de données
echo "🔧 Étape 2/4: Migration de la base de données..."
sudo -u tomatoplan ./venv/bin/python3 << 'PYPYTHON'
import sys
import os
import sqlite3

# Ajouter le répertoire au path
sys.path.insert(0, '/opt/tomatoplan/tomatoplan-web')

from app import create_app

# Créer l'application
app = create_app()

with app.app_context():
    # Récupérer le chemin de la base de données
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    db_path = db_uri.replace('sqlite:///', '')

    print(f"   📁 Base de données: {db_path}")

    # Connexion à la base de données
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Vérifier et ajouter telephone à la table sst
        cursor.execute("PRAGMA table_info(sst)")
        sst_columns = [column[1] for column in cursor.fetchall()]

        if 'telephone' not in sst_columns:
            print("   ➕ Ajout de la colonne 'telephone' à la table 'sst'...")
            cursor.execute("ALTER TABLE sst ADD COLUMN telephone VARCHAR(20)")
            conn.commit()
            print("   ✅ Colonne 'telephone' ajoutée à 'sst'")
        else:
            print("   ✓ La colonne 'telephone' existe déjà dans 'sst'")

        # Vérifier et ajouter telephone à la table chauffeurs
        cursor.execute("PRAGMA table_info(chauffeurs)")
        chauffeurs_columns = [column[1] for column in cursor.fetchall()]

        if 'telephone' not in chauffeurs_columns:
            print("   ➕ Ajout de la colonne 'telephone' à la table 'chauffeurs'...")
            cursor.execute("ALTER TABLE chauffeurs ADD COLUMN telephone VARCHAR(20)")
            conn.commit()
            print("   ✅ Colonne 'telephone' ajoutée à 'chauffeurs'")
        else:
            print("   ✓ La colonne 'telephone' existe déjà dans 'chauffeurs'")

        # Vérifier et ajouter prenom à la table chauffeurs
        if 'prenom' not in chauffeurs_columns:
            print("   ➕ Ajout de la colonne 'prenom' à la table 'chauffeurs'...")
            cursor.execute("ALTER TABLE chauffeurs ADD COLUMN prenom VARCHAR(100)")
            conn.commit()
            print("   ✅ Colonne 'prenom' ajoutée à 'chauffeurs'")
        else:
            print("   ✓ La colonne 'prenom' existe déjà dans 'chauffeurs'")

        # Vérifier et ajouter sst_id à la table chauffeurs
        cursor.execute("PRAGMA table_info(chauffeurs)")
        chauffeurs_columns = [column[1] for column in cursor.fetchall()]

        if 'sst_id' not in chauffeurs_columns:
            print("   ➕ Ajout de la colonne 'sst_id' à la table 'chauffeurs'...")
            cursor.execute("ALTER TABLE chauffeurs ADD COLUMN sst_id INTEGER")
            conn.commit()
            print("   ✅ Colonne 'sst_id' ajoutée à 'chauffeurs'")

            # Migrer les données de sst vers sst_id
            print("   🔄 Migration des données SST...")
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

            conn.commit()
            print(f"   ✅ {len(migrations)} chauffeurs migrés vers le nouveau système SST")
        else:
            print("   ✓ La colonne 'sst_id' existe déjà dans 'chauffeurs'")

        print("   ✅ Migration terminée avec succès!")

    except Exception as e:
        conn.rollback()
        print(f"   ❌ Erreur lors de la migration: {e}")
        sys.exit(1)
    finally:
        conn.close()

PYPYTHON

echo "✅ Migration terminée"
echo ""

# 3. Redémarrer le service
echo "🔄 Étape 3/4: Redémarrage du service..."
sudo systemctl restart tomatoplan
sleep 2
echo "✅ Service redémarré"
echo ""

# 4. Vérifier le statut
echo "🔍 Étape 4/4: Vérification du statut..."
if sudo systemctl is-active --quiet tomatoplan; then
    echo "✅ Service actif"
else
    echo "❌ Service inactif - Vérifier les logs ci-dessous"
fi
echo ""

echo "========================================="
echo "📋 LOGS DES 20 DERNIÈRES LIGNES:"
echo "========================================="
sudo journalctl -u tomatoplan.service -n 20 --no-pager
echo ""

echo "========================================="
echo "✅ DÉPLOIEMENT TERMINÉ"
echo "========================================="
echo ""
echo "🌐 Testez l'application sur: https://projectviewer.fun"
echo ""
echo "💡 Pour voir plus de logs en temps réel:"
echo "   sudo journalctl -u tomatoplan.service -f"
echo ""
