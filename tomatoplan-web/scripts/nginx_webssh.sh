#!/bin/bash
###############################################################################
# Configuration Nginx + SSL pour WebSSH
# Utilise Let's Encrypt pour SSL
# Reverse proxy sécurisé
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
echo "  Configuration Nginx + SSL pour WebSSH"
echo "=================================================================="
echo ""

# Demander le nom de domaine
read -p "Entrez le nom de domaine pour WebSSH (ex: ssh.votredomaine.com): " DOMAIN
read -p "Entrez votre email pour Let's Encrypt: " EMAIL

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    error "Le domaine et l'email sont requis"
    exit 1
fi

WEBSSH_PORT=8022

info "Configuration:"
echo "  - Domaine: $DOMAIN"
echo "  - Email: $EMAIL"
echo "  - Port WebSSH interne: $WEBSSH_PORT"
echo ""

read -p "Continuer ? (O/n): " -r
if [[ $REPLY =~ ^[Nn]$ ]]; then
    exit 0
fi

# Installer Nginx et Certbot
info "Installation de Nginx et Certbot..."
apt update
apt install -y nginx certbot python3-certbot-nginx
success "Nginx et Certbot installés"

# Créer la configuration Nginx pour WebSSH
info "Création de la configuration Nginx..."
cat > "/etc/nginx/sites-available/webssh" << EOF
# Configuration Nginx pour WebSSH
upstream webssh {
    server 127.0.0.1:$WEBSSH_PORT;
}

server {
    listen 80;
    server_name $DOMAIN;

    # Redirection HTTP vers HTTPS (sera ajouté après certbot)
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # Les certificats SSL seront configurés par certbot

    # Logs
    access_log /var/log/nginx/webssh-access.log;
    error_log /var/log/nginx/webssh-error.log;

    # Sécurité
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy vers WebSSH
    location / {
        proxy_pass http://webssh;
        proxy_http_version 1.1;
        proxy_read_timeout 300;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Real-PORT \$remote_port;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Activer le site
ln -sf /etc/nginx/sites-available/webssh /etc/nginx/sites-enabled/
success "Configuration Nginx créée"

# Tester la configuration
info "Test de la configuration Nginx..."
nginx -t
success "Configuration Nginx valide"

# Recharger Nginx
systemctl reload nginx
success "Nginx rechargé"

# Obtenir le certificat SSL
info "Obtention du certificat SSL avec Let's Encrypt..."
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "$EMAIL" --redirect

if [ $? -eq 0 ]; then
    success "Certificat SSL obtenu et configuré!"
else
    error "Échec de l'obtention du certificat SSL"
    exit 1
fi

# Configurer le renouvellement automatique
info "Configuration du renouvellement automatique..."
systemctl enable certbot.timer
systemctl start certbot.timer
success "Renouvellement automatique configuré"

# Configurer le pare-feu
info "Configuration du pare-feu..."
if command -v ufw &> /dev/null; then
    ufw allow 'Nginx Full'
    success "Règles de pare-feu configurées"
fi

echo ""
echo "=================================================================="
success "Configuration Nginx + SSL terminée!"
echo "=================================================================="
echo ""
info "Votre WebSSH est maintenant accessible via:"
echo "  - https://$DOMAIN"
echo ""
info "Commandes utiles:"
echo "  - Tester Nginx: sudo nginx -t"
echo "  - Recharger Nginx: sudo systemctl reload nginx"
echo "  - Logs Nginx: sudo tail -f /var/log/nginx/webssh-error.log"
echo "  - Renouveler SSL: sudo certbot renew --dry-run"
echo ""
warning "IMPORTANT:"
echo "  1. Assurez-vous que votre DNS pointe vers ce serveur"
echo "  2. Protégez WebSSH avec une authentification supplémentaire si nécessaire"
echo "  3. Surveillez les logs régulièrement"
echo ""
