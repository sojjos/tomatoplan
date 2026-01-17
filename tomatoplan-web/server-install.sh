#!/bin/bash
#
# Script d'installation serveur TomatoPlan Web
# Pour Ubuntu 22.04 avec nginx et systemd
#
# Usage: curl -sSL https://raw.githubusercontent.com/sojjos/tomatoplan/claude/web-app-sqlite-auth-sKRgj/tomatoplan-web/server-install.sh | sudo bash
#

set -e  # Arrêt en cas d'erreur

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
DOMAIN="${DOMAIN:-projectviewer.fun}"
APP_USER="tomatoplan"
APP_DIR="/opt/tomatoplan"
REPO_URL="https://github.com/sojjos/tomatoplan.git"
BRANCH="claude/web-app-sqlite-auth-sKRgj"

# Fonctions
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
}

# Vérifier que le script est exécuté en root
if [[ $EUID -ne 0 ]]; then
   print_error "Ce script doit être exécuté en root (sudo)"
   exit 1
fi

print_header "INSTALLATION TOMATOPLAN WEB - SERVEUR"

print_info "Domaine: $DOMAIN"
print_info "Utilisateur: $APP_USER"
print_info "Répertoire: $APP_DIR"

# 1. Mise à jour du système
print_header "1. Mise à jour du système"
apt-get update -qq
apt-get upgrade -y -qq
print_success "Système mis à jour"

# 2. Installation des dépendances
print_header "2. Installation des dépendances"
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    supervisor \
    ufw

print_success "Dépendances installées"

# 3. Créer l'utilisateur applicatif
print_header "3. Création de l'utilisateur applicatif"
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash $APP_USER
    print_success "Utilisateur $APP_USER créé"
else
    print_info "Utilisateur $APP_USER existe déjà"
fi

# 4. Cloner le repository
print_header "4. Clonage du repository"
if [ -d "$APP_DIR" ]; then
    print_warning "Le répertoire $APP_DIR existe déjà, suppression..."
    rm -rf $APP_DIR
fi

mkdir -p $APP_DIR
cd $APP_DIR
git clone -b $BRANCH $REPO_URL .
cd tomatoplan-web
print_success "Repository cloné"

# 5. Installer l'application
print_header "5. Installation de l'application"
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip -q

# Installer les dépendances
pip install -r requirements.txt -q

# Ajouter gunicorn pour la production
pip install gunicorn -q

print_success "Application installée"

# 6. Configuration de l'environnement
print_header "6. Configuration de l'environnement"

# Générer une clé secrète sécurisée
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

cat > .env << EOF
# Configuration TomatoPlan Web - PRODUCTION
SECRET_KEY=$SECRET_KEY
FLASK_ENV=production
DATABASE_URL=sqlite:///$APP_DIR/tomatoplan-web/tomatoplan.db
FLASK_DEBUG=0

# Email (à configurer selon vos besoins)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=noreply@$DOMAIN
EOF

print_success "Fichier .env créé"

# 7. Initialiser la base de données
print_header "7. Initialisation de la base de données"
python3 -c "
from app import create_app
from app.models import db

app = create_app('production')
with app.app_context():
    db.create_all()
    print('✓ Base de données initialisée')
"
print_success "Base de données initialisée"

# 8. Créer les répertoires nécessaires
mkdir -p logs exports uploads
chown -R $APP_USER:$APP_USER $APP_DIR
print_success "Permissions configurées"

# 9. Configuration de Gunicorn avec systemd
print_header "9. Configuration du service systemd"
cat > /etc/systemd/system/tomatoplan.service << EOF
[Unit]
Description=TomatoPlan Web Application
After=network.target

[Service]
Type=notify
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR/tomatoplan-web
Environment="PATH=$APP_DIR/tomatoplan-web/venv/bin"
ExecStart=$APP_DIR/tomatoplan-web/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --access-logfile $APP_DIR/tomatoplan-web/logs/access.log \
    --error-logfile $APP_DIR/tomatoplan-web/logs/error.log \
    --log-level info \
    --timeout 120 \
    "app:create_app('production')"
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable tomatoplan
systemctl start tomatoplan
print_success "Service systemd configuré et démarré"

# 10. Configuration de Nginx
print_header "10. Configuration de Nginx"
cat > /etc/nginx/sites-available/tomatoplan << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    access_log $APP_DIR/tomatoplan-web/logs/nginx-access.log;
    error_log $APP_DIR/tomatoplan-web/logs/nginx-error.log;

    client_max_body_size 16M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        proxy_buffering off;
        proxy_connect_timeout 120;
        proxy_send_timeout 120;
        proxy_read_timeout 120;
    }

    location /static {
        alias $APP_DIR/tomatoplan-web/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Activer le site
ln -sf /etc/nginx/sites-available/tomatoplan /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Tester la configuration
nginx -t

# Redémarrer Nginx
systemctl restart nginx
systemctl enable nginx

print_success "Nginx configuré et démarré"

# 11. Configuration du firewall
print_header "11. Configuration du firewall"
ufw --force enable
ufw allow 22/tcp  # SSH
ufw allow 80/tcp  # HTTP
ufw allow 443/tcp # HTTPS
ufw status
print_success "Firewall configuré"

# 12. Installation du certificat SSL avec Let's Encrypt
print_header "12. Installation du certificat SSL"
print_info "Configuration de Let's Encrypt pour $DOMAIN"
print_warning "Assurez-vous que le domaine pointe vers ce serveur !"

read -p "Voulez-vous installer le certificat SSL maintenant ? (o/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Oo]$ ]]; then
    certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
    print_success "Certificat SSL installé"

    # Renouvellement automatique
    systemctl enable certbot.timer
    systemctl start certbot.timer
    print_success "Renouvellement automatique configuré"
else
    print_warning "SSL non installé. Vous pouvez l'installer plus tard avec:"
    print_info "certbot --nginx -d $DOMAIN -d www.$DOMAIN"
fi

# 13. Résumé de l'installation
print_header "INSTALLATION TERMINÉE !"

echo ""
echo -e "${GREEN}🎉 TomatoPlan Web est installé et opérationnel !${NC}"
echo ""
echo "📍 Informations importantes:"
echo "   - URL: http://$DOMAIN (ou https:// si SSL installé)"
echo "   - Utilisateur par défaut: admin"
echo "   - Mot de passe par défaut: admin"
echo "   ${RED}⚠ CHANGEZ LE MOT DE PASSE IMMÉDIATEMENT !${NC}"
echo ""
echo "📁 Emplacements:"
echo "   - Application: $APP_DIR/tomatoplan-web"
echo "   - Base de données: $APP_DIR/tomatoplan-web/tomatoplan.db"
echo "   - Logs: $APP_DIR/tomatoplan-web/logs/"
echo "   - Exports: $APP_DIR/tomatoplan-web/exports/"
echo ""
echo "🔧 Commandes utiles:"
echo "   - Statut: systemctl status tomatoplan"
echo "   - Logs: journalctl -u tomatoplan -f"
echo "   - Redémarrer: systemctl restart tomatoplan"
echo "   - Nginx logs: tail -f $APP_DIR/tomatoplan-web/logs/nginx-*.log"
echo ""
echo "🔒 Sécurité:"
echo "   - Configurez l'email dans .env pour les notifications"
echo "   - Sauvegardez régulièrement: $APP_DIR/tomatoplan-web/tomatoplan.db"
echo "   - Le firewall UFW est actif (SSH, HTTP, HTTPS autorisés)"
echo ""
echo "📚 Documentation complète:"
echo "   - $APP_DIR/tomatoplan-web/README.md"
echo ""
echo -e "${BLUE}Profitez de TomatoPlan Web ! 🍅${NC}"
echo ""
