#!/bin/bash
###############################################################################
# Script d'installation de WebSSH pour accès SSH via navigateur
# Compatible avec TomatoPlan (utilise un port différent)
# Date: 2026-01-19
###############################################################################

set -e  # Arrêter en cas d'erreur

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
WEBSSH_PORT="${WEBSSH_PORT:-8022}"  # Port différent de TomatoPlan
WEBSSH_DIR="/opt/webssh"
WEBSSH_USER="webssh"

info() { echo -e "${BLUE}ℹ${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warning() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }

echo ""
echo "=================================================================="
echo "  Installation de WebSSH - Accès SSH via navigateur"
echo "=================================================================="
echo ""
info "Configuration:"
echo "  - Port WebSSH: $WEBSSH_PORT"
echo "  - Répertoire: $WEBSSH_DIR"
echo "  - Utilisateur: $WEBSSH_USER"
echo ""

# Vérifier les privilèges root
if [ "$EUID" -ne 0 ]; then
    error "Ce script doit être exécuté avec sudo"
    exit 1
fi

# Étape 1: Mise à jour du système et installation des dépendances
info "Étape 1/8: Installation des dépendances système..."
apt update
apt install -y git nodejs npm build-essential ufw
success "Dépendances installées"

# Vérifier les versions
NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)
info "Node.js version: $NODE_VERSION"
info "npm version: $NPM_VERSION"

# Étape 2: Créer un utilisateur dédié pour WebSSH
info "Étape 2/8: Création de l'utilisateur $WEBSSH_USER..."
if id "$WEBSSH_USER" &>/dev/null; then
    warning "L'utilisateur $WEBSSH_USER existe déjà"
else
    useradd -r -m -s /bin/bash -d "$WEBSSH_DIR" "$WEBSSH_USER"
    success "Utilisateur $WEBSSH_USER créé"
fi

# Étape 3: Cloner le dépôt WebSSH
info "Étape 3/8: Téléchargement de WebSSH..."
if [ -d "$WEBSSH_DIR/webssh" ]; then
    warning "WebSSH est déjà téléchargé, mise à jour..."
    cd "$WEBSSH_DIR/webssh"
    sudo -u "$WEBSSH_USER" git pull
else
    sudo -u "$WEBSSH_USER" git clone https://github.com/huashengdun/webssh.git "$WEBSSH_DIR/webssh"
    success "WebSSH téléchargé"
fi

cd "$WEBSSH_DIR/webssh"

# Étape 4: Créer un environnement virtuel Python
info "Étape 4/8: Configuration de l'environnement Python..."
apt install -y python3 python3-pip python3-venv
sudo -u "$WEBSSH_USER" python3 -m venv "$WEBSSH_DIR/venv"
success "Environnement virtuel créé"

# Étape 5: Installer les dépendances Python
info "Étape 5/8: Installation des dépendances WebSSH..."
sudo -u "$WEBSSH_USER" bash << EOF
source "$WEBSSH_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt
EOF
success "Dépendances WebSSH installées"

# Étape 6: Créer le fichier de configuration
info "Étape 6/8: Configuration de WebSSH..."
cat > "$WEBSSH_DIR/webssh/config.conf" << EOF
# Configuration WebSSH
# Port d'écoute (différent de TomatoPlan)
port = $WEBSSH_PORT

# Interface d'écoute (0.0.0.0 = toutes les interfaces)
address = 0.0.0.0

# Niveau de log
logging = info

# Politique de connexion
# - same: Seulement vers le serveur local
# - different: Vers n'importe quel serveur
# - all: Pas de restriction (ATTENTION: potentiellement dangereux)
policy = same

# Nombre maximum de connexions par worker
maxconn = 20

# Timeout en secondes
timeout = 3

# Délai avant fermeture de connexion inactive (en secondes)
delay = 3

# Workers (processes)
workers = 1
EOF

chown "$WEBSSH_USER:$WEBSSH_USER" "$WEBSSH_DIR/webssh/config.conf"
success "Configuration créée"

# Étape 7: Créer le service systemd
info "Étape 7/8: Création du service systemd..."
cat > /etc/systemd/system/webssh.service << EOF
[Unit]
Description=WebSSH - SSH Access via Web Browser
After=network.target

[Service]
Type=simple
User=$WEBSSH_USER
Group=$WEBSSH_USER
WorkingDirectory=$WEBSSH_DIR/webssh
Environment="PATH=$WEBSSH_DIR/venv/bin"
ExecStart=$WEBSSH_DIR/venv/bin/python $WEBSSH_DIR/webssh/run.py --port=$WEBSSH_PORT --address=0.0.0.0 --policy=same
Restart=always
RestartSec=10

# Sécurité
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$WEBSSH_DIR

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
success "Service systemd créé"

# Étape 8: Configuration du pare-feu
info "Étape 8/8: Configuration du pare-feu..."
if command -v ufw &> /dev/null; then
    ufw allow "$WEBSSH_PORT/tcp" comment 'WebSSH'
    success "Règle de pare-feu ajoutée"
else
    warning "UFW non installé, configurez manuellement votre pare-feu"
fi

# Démarrer WebSSH
info "Démarrage de WebSSH..."
systemctl enable webssh
systemctl start webssh

sleep 2

if systemctl is-active --quiet webssh; then
    success "WebSSH démarré avec succès!"
else
    error "WebSSH n'a pas démarré correctement"
    systemctl status webssh
    exit 1
fi

# Afficher les informations de connexion
echo ""
echo "=================================================================="
success "Installation de WebSSH terminée!"
echo "=================================================================="
echo ""
info "Informations de connexion:"
echo "  - URL locale: http://localhost:$WEBSSH_PORT"
echo "  - URL externe: http://$(hostname -I | awk '{print $1}'):$WEBSSH_PORT"
echo ""
info "Commandes utiles:"
echo "  - Statut: sudo systemctl status webssh"
echo "  - Logs: sudo journalctl -u webssh -f"
echo "  - Redémarrer: sudo systemctl restart webssh"
echo "  - Arrêter: sudo systemctl stop webssh"
echo ""
warning "IMPORTANT - Sécurité:"
echo "  1. WebSSH est configuré en mode 'same' (connexion uniquement vers ce serveur)"
echo "  2. Pour un accès depuis Internet, configurez Nginx avec SSL (voir script nginx_webssh.sh)"
echo "  3. Protégez WebSSH avec un mot de passe ou une authentification"
echo ""
info "Pour vérifier que TomatoPlan n'est pas affecté:"
echo "  - sudo systemctl status tomatoplan-web"
echo "  - Accédez à votre URL TomatoPlan habituelle"
echo ""
