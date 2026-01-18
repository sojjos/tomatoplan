#!/bin/bash
#
# SCRIPT DE DÉPLOIEMENT - Ajout gestion SST et téléphone
#
# Usage sur le serveur:
# cd /opt/tomatoplan/tomatoplan-web
# sudo bash DEPLOY_SST_UPDATE.sh
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}DÉPLOIEMENT - Gestion SST + Téléphone${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

APP_DIR="/opt/tomatoplan/tomatoplan-web"
APP_USER="tomatoplan"

cd "$APP_DIR"

echo -e "${YELLOW}➜${NC} Récupération des dernières modifications..."
sudo -u $APP_USER git fetch origin
sudo -u $APP_USER git pull origin claude/web-app-sqlite-auth-sKRgj

echo -e "${YELLOW}➜${NC} Mise à jour de la base de données..."

# Script Python pour ajouter la colonne telephone à SST
sudo -u $APP_USER ./venv/bin/python3 << 'PYPYTHON'
from run import app
from app.models import db
import sqlite3

with app.app_context():
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Vérifier si la colonne telephone existe déjà dans SST
    cursor.execute("PRAGMA table_info(sst)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'telephone' not in columns:
        print("  → Ajout de la colonne 'telephone' à la table SST...")
        cursor.execute("ALTER TABLE sst ADD COLUMN telephone VARCHAR(20)")
        conn.commit()
        print("  ✓ Colonne 'telephone' ajoutée")
    else:
        print("  ✓ Colonne 'telephone' déjà présente")
    
    # Vérifier Chauffeur (devrait déjà avoir telephone)
    cursor.execute("PRAGMA table_info(chauffeurs)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'telephone' in columns:
        print("  ✓ Colonne 'telephone' présente dans chauffeurs")
    else:
        print("  ⚠ ATTENTION: Colonne 'telephone' manquante dans chauffeurs")
    
    conn.close()
    print("\n✓ Base de données mise à jour")
PYPYTHON

echo ""
echo -e "${YELLOW}➜${NC} Redémarrage de l'application..."
systemctl restart tomatoplan
sleep 3

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}DÉPLOIEMENT TERMINÉ !${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Nouvelles fonctionnalités disponibles:"
echo "  • Gestion complète des SST (Admin > SST)"
echo "  • Téléphone pour les SST"
echo "  • Téléphone pour les chauffeurs"
echo ""
echo "Accédez à: https://projectviewer.fun/admin/sst"
echo ""

systemctl status tomatoplan --no-pager | head -15
