#!/bin/bash
###############################################################################
# Script de correction complète pour TomatoPlan en production
# Fixe le problème de schéma de base de données et restaure l'application
# Date: 2026-01-19
###############################################################################

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}ℹ${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warning() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }

# Configuration
PROD_DIR="/opt/tomatoplan/tomatoplan-web"
DB_PATH="$PROD_DIR/tomatoplan.db"
MIGRATION_SCRIPT="$PROD_DIR/migrations/migrate_chauffeur_schema.py"
SERVICE_NAME="tomatoplan-web"

echo ""
echo "=================================================================="
echo "  Script de correction complète - TomatoPlan Production"
echo "=================================================================="
echo ""

# Vérifier les privilèges root
if [ "$EUID" -ne 0 ]; then
    error "Ce script doit être exécuté avec sudo"
    exit 1
fi

info "Configuration:"
echo "  - Répertoire: $PROD_DIR"
echo "  - Base de données: $DB_PATH"
echo "  - Service: $SERVICE_NAME"
echo ""

warning "Ce script va:"
echo "  1. Arrêter l'application TomatoPlan"
echo "  2. Nettoyer le cache Python"
echo "  3. Créer une sauvegarde de la base de données"
echo "  4. Migrer le schéma de la base de données"
echo "  5. Redémarrer l'application"
echo ""

read -p "Voulez-vous continuer ? (O/n): " -r
if [[ $REPLY =~ ^[Nn]$ ]]; then
    info "Opération annulée"
    exit 0
fi

echo ""
echo "=================================================================="
echo "Étape 1/7: Arrêt de l'application"
echo "=================================================================="
echo ""

info "Arrêt du service $SERVICE_NAME..."
if systemctl is-active --quiet "$SERVICE_NAME"; then
    systemctl stop "$SERVICE_NAME"
    success "Service arrêté"
else
    warning "Le service n'était pas actif"
fi

# Tuer tous les processus gunicorn restants
info "Vérification des processus gunicorn restants..."
if pgrep -f "gunicorn.*tomatoplan" > /dev/null; then
    warning "Processus gunicorn détectés, arrêt forcé..."
    pkill -9 -f "gunicorn.*tomatoplan" || true
    sleep 2
    success "Processus gunicorn arrêtés"
fi

echo ""
echo "=================================================================="
echo "Étape 2/7: Nettoyage du cache Python"
echo "=================================================================="
echo ""

info "Suppression des fichiers cache Python..."
find "$PROD_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PROD_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
success "Cache Python nettoyé"

echo ""
echo "=================================================================="
echo "Étape 3/7: Vérification de la base de données actuelle"
echo "=================================================================="
echo ""

if [ -f "$DB_PATH" ]; then
    info "Base de données trouvée"

    # Afficher le schéma actuel
    info "Schéma actuel de la table chauffeurs:"
    echo ""
    sqlite3 "$DB_PATH" "PRAGMA table_info(chauffeurs);" 2>/dev/null || {
        error "Impossible de lire la base de données"
        exit 1
    }
    echo ""

    # Compter les chauffeurs
    CHAUFFEUR_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM chauffeurs;" 2>/dev/null || echo "0")
    info "Nombre de chauffeurs dans la base: $CHAUFFEUR_COUNT"
else
    error "Base de données non trouvée: $DB_PATH"
    exit 1
fi

echo ""
echo "=================================================================="
echo "Étape 4/7: Création d'une sauvegarde de sécurité"
echo "=================================================================="
echo ""

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${DB_PATH}.backup_fix_${TIMESTAMP}"

info "Création de la sauvegarde: $BACKUP_PATH"
cp "$DB_PATH" "$BACKUP_PATH"
success "Sauvegarde créée"

# Vérifier l'intégrité de la sauvegarde
info "Vérification de l'intégrité de la sauvegarde..."
sqlite3 "$BACKUP_PATH" "PRAGMA integrity_check;" > /dev/null
success "Sauvegarde vérifiée"

echo ""
echo "=================================================================="
echo "Étape 5/7: Migration du schéma de la base de données"
echo "=================================================================="
echo ""

if [ ! -f "$MIGRATION_SCRIPT" ]; then
    error "Script de migration non trouvé: $MIGRATION_SCRIPT"
    error "Assurez-vous que le code est à jour sur le serveur"
    exit 1
fi

info "Exécution du script de migration..."
echo ""

# Exécuter le script de migration en mode non-interactif
cd "$PROD_DIR"
export DATABASE_PATH="$DB_PATH"

# Créer un script Python temporaire pour l'exécution automatique
cat > /tmp/run_migration.py << 'PYEOF'
import os
import sys
sys.path.insert(0, '/opt/tomatoplan/tomatoplan-web')
from migrations.migrate_chauffeur_schema import migrate_chauffeurs_table

db_path = os.environ.get('DATABASE_PATH', 'tomatoplan.db')
print(f"\nExécution de la migration sur: {db_path}\n")

success = migrate_chauffeurs_table(db_path)
sys.exit(0 if success else 1)
PYEOF

python3 /tmp/run_migration.py
MIGRATION_STATUS=$?

rm -f /tmp/run_migration.py

if [ $MIGRATION_STATUS -eq 0 ]; then
    echo ""
    success "Migration terminée avec succès!"
else
    echo ""
    error "La migration a échoué"
    warning "La sauvegarde est disponible: $BACKUP_PATH"
    exit 1
fi

echo ""
echo "=================================================================="
echo "Étape 6/7: Vérification du nouveau schéma"
echo "=================================================================="
echo ""

info "Nouveau schéma de la table chauffeurs:"
echo ""
sqlite3 "$DB_PATH" "PRAGMA table_info(chauffeurs);"
echo ""

# Vérifier que les colonnes requises existent
info "Vérification des colonnes requises..."
SCHEMA=$(sqlite3 "$DB_PATH" "PRAGMA table_info(chauffeurs);")

if echo "$SCHEMA" | grep -q "prenom"; then
    success "Colonne 'prenom' présente"
else
    error "Colonne 'prenom' manquante!"
    exit 1
fi

if echo "$SCHEMA" | grep -q "sst_id"; then
    success "Colonne 'sst_id' présente"
else
    error "Colonne 'sst_id' manquante!"
    exit 1
fi

if echo "$SCHEMA" | grep -q "telephone"; then
    success "Colonne 'telephone' présente"
else
    error "Colonne 'telephone' manquante!"
    exit 1
fi

# Vérifier le nombre de chauffeurs après migration
NEW_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM chauffeurs;" 2>/dev/null || echo "0")
info "Nombre de chauffeurs après migration: $NEW_COUNT"

if [ "$NEW_COUNT" != "$CHAUFFEUR_COUNT" ]; then
    error "Le nombre de chauffeurs a changé! Avant: $CHAUFFEUR_COUNT, Après: $NEW_COUNT"
    warning "Restauration de la sauvegarde..."
    cp "$BACKUP_PATH" "$DB_PATH"
    error "Base de données restaurée. Veuillez vérifier les données."
    exit 1
fi

success "Aucune perte de données détectée"

echo ""
echo "=================================================================="
echo "Étape 7/7: Redémarrage de l'application"
echo "=================================================================="
echo ""

info "Redémarrage du service $SERVICE_NAME..."
systemctl start "$SERVICE_NAME"
sleep 3

if systemctl is-active --quiet "$SERVICE_NAME"; then
    success "Service redémarré avec succès"
else
    error "Le service n'a pas démarré correctement"
    systemctl status "$SERVICE_NAME"
    exit 1
fi

# Vérifier les logs
info "Vérification des logs (5 dernières secondes)..."
sleep 2
journalctl -u "$SERVICE_NAME" --since "5 seconds ago" --no-pager | tail -n 10

echo ""
echo "=================================================================="
success "Correction complète terminée avec succès!"
echo "=================================================================="
echo ""

info "Résumé:"
echo "  ✓ Application arrêtée"
echo "  ✓ Cache Python nettoyé"
echo "  ✓ Sauvegarde créée: $BACKUP_PATH"
echo "  ✓ Migration de la base de données réussie"
echo "  ✓ Schéma vérifié (prenom, sst_id, telephone présents)"
echo "  ✓ Aucune perte de données ($CHAUFFEUR_COUNT chauffeurs préservés)"
echo "  ✓ Application redémarrée"
echo ""

info "Commandes utiles:"
echo "  - Vérifier le service: sudo systemctl status $SERVICE_NAME"
echo "  - Voir les logs: sudo journalctl -u $SERVICE_NAME -f"
echo "  - Restaurer la sauvegarde: sudo cp $BACKUP_PATH $DB_PATH"
echo ""

warning "IMPORTANT:"
echo "  1. Testez l'application web pour confirmer que tout fonctionne"
echo "  2. Vérifiez que vous pouvez voir et éditer les chauffeurs"
echo "  3. La sauvegarde reste disponible en cas de besoin"
echo ""

info "Test rapide:"
echo "  curl -I http://localhost:5000"
echo ""

# Test rapide de connectivité
info "Test de l'application..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 | grep -q "200\|302"; then
    success "L'application répond correctement!"
else
    warning "L'application ne répond pas comme attendu, vérifiez les logs"
fi

echo ""
