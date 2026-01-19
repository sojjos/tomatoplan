# Scripts TomatoPlan Web

Ce répertoire contient des scripts utilitaires pour TomatoPlan Web.

## 📁 Contenu

### Scripts WebSSH

Scripts pour installer WebSSH (accès SSH via navigateur web) sans affecter TomatoPlan.

#### 1. `install_webssh.sh` ⭐

Script d'installation automatique de WebSSH.

**Usage:**
```bash
# Sur votre serveur de production
sudo ./install_webssh.sh
```

**Ce qu'il fait:**
- ✅ Installe toutes les dépendances nécessaires
- ✅ Crée un utilisateur dédié pour WebSSH
- ✅ Télécharge et configure WebSSH
- ✅ Crée un service systemd
- ✅ Configure le pare-feu
- ✅ Démarre WebSSH sur le port 8022

**Port utilisé:** 8022 (ne chevauche pas TomatoPlan)

#### 2. `nginx_webssh.sh`

Script de configuration Nginx + SSL pour WebSSH avec Let's Encrypt.

**Prérequis:**
- Un nom de domaine pointant vers votre serveur
- WebSSH déjà installé

**Usage:**
```bash
sudo ./nginx_webssh.sh
```

**Ce qu'il fait:**
- ✅ Installe Nginx et Certbot
- ✅ Configure un reverse proxy pour WebSSH
- ✅ Obtient un certificat SSL gratuit
- ✅ Active HTTPS automatiquement
- ✅ Configure le renouvellement automatique

#### 3. `WEBSSH_GUIDE.md` 📖

Guide complet d'installation, utilisation et dépannage de WebSSH.

**Sujets couverts:**
- Installation pas-à-pas
- Configuration SSL
- Utilisation
- Sécurité
- Dépannage
- Désinstallation

---

## 🚀 Installation rapide WebSSH

### Depuis votre ordinateur local:

```bash
# Transférer les scripts vers votre serveur
cd tomatoplan-web
scp scripts/install_webssh.sh ubuntu@votre-serveur:~
scp scripts/nginx_webssh.sh ubuntu@votre-serveur:~
```

### Sur votre serveur:

```bash
# Installer WebSSH
chmod +x install_webssh.sh
sudo ./install_webssh.sh

# (Optionnel) Configurer SSL si vous avez un domaine
chmod +x nginx_webssh.sh
sudo ./nginx_webssh.sh
```

### Accès:

- **Sans SSL:** `http://IP_SERVEUR:8022`
- **Avec SSL:** `https://ssh.votredomaine.com`

---

## ⚠️ Important

- WebSSH utilise le **port 8022**
- TomatoPlan n'est **pas affecté**
- Pour la production, **utilisez SSL** (nginx_webssh.sh)
- Consultez `WEBSSH_GUIDE.md` pour plus de détails

---

## 🔧 Scripts à venir

D'autres scripts utilitaires seront ajoutés ici :
- Monitoring et alertes
- Backup automatique
- Optimisation de performances
- Scripts de maintenance

---

## 📚 Documentation

Pour plus d'informations sur chaque script, consultez les commentaires dans les fichiers ou le guide complet `WEBSSH_GUIDE.md`.
