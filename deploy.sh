#!/bin/bash
set -e

echo "================================================"
echo "   DÉPLOIEMENT TOMATOPLAN - Mise à jour"
echo "================================================"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Trouver le répertoire du projet
if [ -d "/opt/tomatoplan" ]; then
    PROJECT_DIR="/opt/tomatoplan"
elif [ -d "/var/www/tomatoplan" ]; then
    PROJECT_DIR="/var/www/tomatoplan"
else
    echo -e "${RED}Erreur: Répertoire du projet non trouvé${NC}"
    exit 1
fi

echo "Répertoire du projet: $PROJECT_DIR"
cd "$PROJECT_DIR"

# Corriger les permissions git si nécessaire
echo -e "\n${YELLOW}Étape 1/4: Configuration git...${NC}"
git config --global --add safe.directory "$PROJECT_DIR" 2>/dev/null || true

# Récupérer les modifications
echo -e "\n${YELLOW}Étape 2/4: Récupération des modifications...${NC}"
git fetch origin
git checkout claude/fix-database-schema-zUmLZ
git pull origin claude/fix-database-schema-zUmLZ

echo -e "${GREEN}✓ Code mis à jour${NC}"

# Redémarrer le service
echo -e "\n${YELLOW}Étape 3/4: Redémarrage du service...${NC}"
sudo systemctl restart tomatoplan

# Attendre un peu que le service démarre
sleep 2

# Vérifier le statut
echo -e "\n${YELLOW}Étape 4/4: Vérification du service...${NC}"
if sudo systemctl is-active --quiet tomatoplan; then
    echo -e "${GREEN}✓ Service démarré avec succès${NC}"
    echo ""
    echo "================================================"
    echo -e "${GREEN}   DÉPLOIEMENT TERMINÉ AVEC SUCCÈS${NC}"
    echo "================================================"
    echo ""
    echo "Votre application est maintenant à jour !"
    echo ""
else
    echo -e "${RED}✗ Erreur: Le service n'a pas démarré correctement${NC}"
    echo ""
    echo "Logs d'erreur:"
    sudo journalctl -u tomatoplan -n 20 --no-pager
    exit 1
fi
