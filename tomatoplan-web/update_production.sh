#!/bin/bash
###############################################################################
# Script de mise à jour en production pour TomatoPlan Web
# Date: 2026-01-19
# Usage: ./update_production.sh [--auto]
###############################################################################

set -e  # Arrêter en cas d'erreur

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="${SERVICE_NAME:-tomatoplan-web}"
DB_PATH="${DB_PATH:-instance/tomatoplan.db}"
AUTO_MODE=false

# Vérifier le flag --auto
if [ "$1" = "--auto" ]; then
    AUTO_MODE=true
fi

echo ""
echo "=================================================================="
echo "  Mise à jour en production - TomatoPlan Web"
echo "=================================================================="
echo ""

# Fonction d'affichage
info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

# Fonction pour demander confirmation
confirm() {
    if [ "$AUTO_MODE" = true ]; then
        return 0
    fi

    read -p "$1 (O/n): " -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        return 1
    fi
    return 0
}

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "app/__init__.py" ]; then
    error "Erreur: Ce script doit être exécuté depuis le répertoire racine de tomatoplan-web"
    exit 1
fi

# Étape 1: Vérifier Git
info "Vérification du dépôt Git..."
if ! git status &>/dev/null; then
    error "Ce n'est pas un dépôt Git valide"
    exit 1
fi
success "Dépôt Git OK"

# Étape 2: Vérifier les changements non commités
UNCOMMITTED=$(git status --porcelain)
if [ -n "$UNCOMMITTED" ]; then
    warning "Attention: Des fichiers ont été modifiés localement:"
    git status --short
    echo ""
    if ! confirm "Voulez-vous continuer quand même?"; then
        info "Mise à jour annulée"
        exit 0
    fi
fi

# Étape 3: Afficher les informations
echo ""
info "Configuration:"
echo "  - Service: $SERVICE_NAME"
echo "  - Base de données: $DB_PATH"
echo "  - Branche actuelle: $(git branch --show-current)"
echo ""

if ! confirm "Voulez-vous continuer avec la mise à jour?"; then
    info "Mise à jour annulée"
    exit 0
fi

# Étape 4: Arrêter le service
info "Arrêt du service $SERVICE_NAME..."

# Détecter le gestionnaire de processus
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    sudo systemctl stop "$SERVICE_NAME"
    success "Service arrêté (systemd)"
    MANAGER="systemd"
elif command -v supervisorctl &>/dev/null && supervisorctl status "$SERVICE_NAME" &>/dev/null; then
    supervisorctl stop "$SERVICE_NAME"
    success "Service arrêté (supervisor)"
    MANAGER="supervisor"
else
    warning "Impossible de détecter le gestionnaire de processus"
    warning "Assurez-vous que l'application est arrêtée avant de continuer"
    if ! confirm "L'application est-elle arrêtée?"; then
        error "Veuillez arrêter l'application manuellement et relancer ce script"
        exit 1
    fi
    MANAGER="manual"
fi

# Étape 5: Créer une sauvegarde manuelle supplémentaire
info "Création d'une sauvegarde de sécurité..."
BACKUP_FILE="${DB_PATH}.backup_$(date +%Y%m%d_%H%M%S)_manual"
if [ -f "$DB_PATH" ]; then
    cp "$DB_PATH" "$BACKUP_FILE"
    success "Sauvegarde créée: $BACKUP_FILE"
else
    warning "Base de données non trouvée: $DB_PATH"
    warning "Ceci semble être une nouvelle installation"
fi

# Étape 6: Mettre à jour le code
info "Mise à jour du code depuis Git..."
CURRENT_COMMIT=$(git rev-parse HEAD)
info "Commit actuel: $CURRENT_COMMIT"

git fetch origin
git pull origin "$(git branch --show-current)"
success "Code mis à jour"

NEW_COMMIT=$(git rev-parse HEAD)
info "Nouveau commit: $NEW_COMMIT"

# Étape 7: Installer/Mettre à jour les dépendances
if [ -d "venv" ]; then
    info "Mise à jour des dépendances Python..."
    source venv/bin/activate
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    success "Dépendances mises à jour"
else
    warning "Environnement virtuel non trouvé, les dépendances ne seront pas mises à jour"
fi

# Étape 8: Exécuter la migration de base de données
if [ -f "$DB_PATH" ] && [ -f "migrations/migrate_chauffeur_schema.py" ]; then
    info "Exécution de la migration de base de données..."

    if [ "$AUTO_MODE" = true ]; then
        # En mode auto, passer "O" au script de migration
        echo "O" | python3 migrations/migrate_chauffeur_schema.py "$DB_PATH"
    else
        python3 migrations/migrate_chauffeur_schema.py "$DB_PATH"
    fi

    if [ $? -eq 0 ]; then
        success "Migration de base de données réussie"
    else
        error "La migration a échoué!"
        warning "Restauration de la sauvegarde..."
        cp "$BACKUP_FILE" "$DB_PATH"
        warning "Restauration du code précédent..."
        git checkout "$CURRENT_COMMIT"

        # Redémarrer le service même en cas d'échec
        if [ "$MANAGER" = "systemd" ]; then
            sudo systemctl start "$SERVICE_NAME"
        elif [ "$MANAGER" = "supervisor" ]; then
            supervisorctl start "$SERVICE_NAME"
        fi

        error "Mise à jour annulée suite à l'échec de la migration"
        exit 1
    fi
else
    warning "Migration de base de données non disponible ou base non trouvée"
fi

# Étape 9: Redémarrer le service
info "Redémarrage du service $SERVICE_NAME..."
if [ "$MANAGER" = "systemd" ]; then
    sudo systemctl start "$SERVICE_NAME"
    sleep 2
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        success "Service démarré avec succès"
    else
        error "Le service n'a pas démarré correctement!"
        sudo systemctl status "$SERVICE_NAME"
        exit 1
    fi
elif [ "$MANAGER" = "supervisor" ]; then
    supervisorctl start "$SERVICE_NAME"
    sleep 2
    success "Service démarré"
elif [ "$MANAGER" = "manual" ]; then
    warning "Veuillez redémarrer l'application manuellement"
fi

# Étape 10: Vérification finale
info "Vérification finale..."

if [ -f "$DB_PATH" ]; then
    # Vérifier le schéma
    SCHEMA_CHECK=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM pragma_table_info('chauffeurs') WHERE name IN ('prenom', 'telephone', 'sst_id')")
    if [ "$SCHEMA_CHECK" -eq 3 ]; then
        success "Schéma de base de données vérifié"
    else
        warning "Le schéma ne semble pas correct (colonnes manquantes)"
    fi
fi

echo ""
echo "=================================================================="
success "Mise à jour terminée avec succès!"
echo "=================================================================="
echo ""
info "Sauvegardes disponibles:"
ls -lh "${DB_PATH}.backup_"* 2>/dev/null | tail -5 || echo "  Aucune sauvegarde"
echo ""
info "Actions recommandées:"
echo "  1. Vérifier que l'application fonctionne correctement"
echo "  2. Tester la page des chauffeurs"
echo "  3. Vérifier les logs pour détecter d'éventuelles erreurs"
echo ""

if [ "$MANAGER" = "systemd" ]; then
    info "Commandes utiles:"
    echo "  - Statut: sudo systemctl status $SERVICE_NAME"
    echo "  - Logs: sudo journalctl -u $SERVICE_NAME -f"
elif [ "$MANAGER" = "supervisor" ]; then
    info "Commandes utiles:"
    echo "  - Statut: supervisorctl status $SERVICE_NAME"
    echo "  - Logs: tail -f /var/log/supervisor/$SERVICE_NAME.log"
fi

echo ""
