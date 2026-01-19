#!/bin/bash
###############################################################################
# Script de désinstallation de WebSSH
# Supprime complètement WebSSH sans affecter TomatoPlan
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

# Vérifier les privilèges root
if [ "$EUID" -ne 0 ]; then
    error "Ce script doit être exécuté avec sudo"
    exit 1
fi

echo ""
echo "=================================================================="
echo "  Désinstallation de WebSSH"
echo "=================================================================="
echo ""
warning "Ce script va supprimer complètement WebSSH de votre système"
warning "TomatoPlan ne sera PAS affecté"
echo ""

read -p "Êtes-vous sûr de vouloir désinstaller WebSSH ? (O/n): " -r
if [[ ! $REPLY =~ ^[Oo]$ ]]; then
    info "Désinstallation annulée"
    exit 0
fi

WEBSSH_DIR="/opt/webssh"
WEBSSH_USER="webssh"

# Étape 1: Arrêter et désactiver le service
info "Arrêt du service WebSSH..."
if systemctl is-active --quiet webssh; then
    systemctl stop webssh
    success "Service arrêté"
fi

if systemctl is-enabled --quiet webssh 2>/dev/null; then
    systemctl disable webssh
    success "Service désactivé"
fi

# Étape 2: Supprimer le service systemd
info "Suppression du service systemd..."
if [ -f "/etc/systemd/system/webssh.service" ]; then
    rm /etc/systemd/system/webssh.service
    systemctl daemon-reload
    success "Service systemd supprimé"
fi

# Étape 3: Supprimer la configuration Nginx (si elle existe)
info "Suppression de la configuration Nginx..."
if [ -f "/etc/nginx/sites-enabled/webssh" ]; then
    rm /etc/nginx/sites-enabled/webssh
    success "Site Nginx désactivé"
fi

if [ -f "/etc/nginx/sites-available/webssh" ]; then
    rm /etc/nginx/sites-available/webssh
    success "Configuration Nginx supprimée"
fi

if systemctl is-active --quiet nginx; then
    systemctl reload nginx
    success "Nginx rechargé"
fi

# Étape 4: Supprimer les certificats SSL (optionnel)
if command -v certbot &> /dev/null; then
    info "Vérification des certificats SSL..."
    CERTS=$(certbot certificates 2>/dev/null | grep -i webssh || true)
    if [ -n "$CERTS" ]; then
        warning "Des certificats SSL pour WebSSH ont été trouvés"
        read -p "Voulez-vous les supprimer ? (o/N): " -r
        if [[ $REPLY =~ ^[Oo]$ ]]; then
            # Demander le domaine
            read -p "Entrez le domaine du certificat à supprimer: " DOMAIN
            if [ -n "$DOMAIN" ]; then
                certbot delete --cert-name "$DOMAIN"
                success "Certificat SSL supprimé"
            fi
        fi
    fi
fi

# Étape 5: Supprimer les fichiers WebSSH
info "Suppression des fichiers WebSSH..."
if [ -d "$WEBSSH_DIR" ]; then
    rm -rf "$WEBSSH_DIR"
    success "Fichiers WebSSH supprimés"
fi

# Étape 6: Supprimer l'utilisateur webssh
info "Suppression de l'utilisateur WebSSH..."
if id "$WEBSSH_USER" &>/dev/null; then
    userdel -r "$WEBSSH_USER" 2>/dev/null || userdel "$WEBSSH_USER"
    success "Utilisateur WebSSH supprimé"
fi

# Étape 7: Nettoyer les règles de pare-feu
info "Nettoyage des règles de pare-feu..."
if command -v ufw &> /dev/null; then
    # Supprimer la règle WebSSH (port 8022)
    ufw delete allow 8022/tcp 2>/dev/null && success "Règle pare-feu supprimée" || true
fi

# Étape 8: Nettoyer les dépendances (optionnel)
warning "Les dépendances système (Python, Node.js, etc.) n'ont PAS été supprimées"
warning "car elles peuvent être utilisées par d'autres applications"
echo ""
read -p "Voulez-vous supprimer les dépendances WebSSH spécifiques ? (o/N): " -r
if [[ $REPLY =~ ^[Oo]$ ]]; then
    info "Suppression des dépendances Python..."
    # Normalement déjà supprimées avec le répertoire, mais au cas où
    pip3 uninstall -y tornado 2>/dev/null || true
    success "Dépendances nettoyées"
fi

echo ""
echo "=================================================================="
success "Désinstallation de WebSSH terminée!"
echo "=================================================================="
echo ""
info "Résumé de ce qui a été supprimé:"
echo "  ✓ Service systemd webssh"
echo "  ✓ Configuration Nginx (si présente)"
echo "  ✓ Fichiers dans $WEBSSH_DIR"
echo "  ✓ Utilisateur $WEBSSH_USER"
echo "  ✓ Règles de pare-feu pour le port 8022"
echo ""
info "Ce qui n'a PAS été supprimé:"
echo "  - Python, Node.js, npm (peuvent être utilisés par d'autres apps)"
echo "  - Nginx (utilisé peut-être par TomatoPlan)"
echo "  - Certificats SSL (sauf si vous avez choisi de les supprimer)"
echo ""
success "TomatoPlan n'a pas été affecté par cette désinstallation"
echo ""
info "Pour vérifier que TomatoPlan fonctionne toujours:"
echo "  sudo systemctl status tomatoplan-web"
echo ""
