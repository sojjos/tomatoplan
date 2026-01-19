# Guide d'installation WebSSH pour TomatoPlan

## 📋 Vue d'ensemble

Ce guide vous permet d'installer WebSSH sur votre serveur **sans affecter** votre application TomatoPlan existante.

WebSSH vous permettra d'accéder à votre terminal Linux via un navigateur web, ce qui est très pratique pour :
- ✅ Accéder à votre serveur depuis n'importe où
- ✅ Ne pas installer de client SSH
- ✅ Utiliser des ordinateurs publics en toute sécurité
- ✅ Avoir une interface web moderne

**Important:** WebSSH utilisera le **port 8022** tandis que TomatoPlan utilise probablement le port 5000 ou 80/443. Ils ne se gêneront pas.

---

## 🚀 Installation rapide (3 étapes)

### Étape 1: Transférer les scripts sur votre serveur

Sur votre **ordinateur local** (pas le serveur):

```bash
# Depuis le répertoire tomatoplan-web
scp scripts/install_webssh.sh ubuntu@votre-serveur.com:~
scp scripts/nginx_webssh.sh ubuntu@votre-serveur.com:~
```

### Étape 2: Installer WebSSH

Sur votre **serveur de production**:

```bash
# Se connecter au serveur
ssh ubuntu@votre-serveur.com

# Rendre le script exécutable
chmod +x install_webssh.sh

# Exécuter l'installation
sudo ./install_webssh.sh
```

L'installation prend environ 2-3 minutes.

### Étape 3: Tester WebSSH

Ouvrez votre navigateur et accédez à:

```
http://ADRESSE_IP_SERVEUR:8022
```

Vous devriez voir l'interface WebSSH !

---

## 🔒 Configuration SSL (Recommandé pour production)

Si vous avez un nom de domaine pointant vers votre serveur:

```bash
# Sur votre serveur
chmod +x nginx_webssh.sh
sudo ./nginx_webssh.sh
```

Le script vous demandera:
- Votre nom de domaine (ex: ssh.monsite.com)
- Votre email pour Let's Encrypt

Après cela, WebSSH sera accessible via HTTPS !

---

## 📖 Utilisation de WebSSH

### Se connecter via WebSSH

1. Ouvrir votre navigateur
2. Aller sur `http://VOTRE_SERVEUR:8022` (ou `https://ssh.votredomaine.com` si SSL configuré)
3. Remplir le formulaire de connexion:
   - **Hostname:** localhost (ou 127.0.0.1)
   - **Port:** 22
   - **Username:** ubuntu (ou votre nom d'utilisateur)
   - **Password:** votre mot de passe SSH
4. Cliquer sur "Connect"

### Interface WebSSH

Une fois connecté, vous aurez un terminal complet dans votre navigateur avec:
- ✅ Autocomplétion (Tab)
- ✅ Historique des commandes (↑↓)
- ✅ Copier/coller
- ✅ Redimensionnement
- ✅ Raccourcis clavier (Ctrl+C, Ctrl+Z, etc.)

---

## 🛡️ Sécurité

### Configuration par défaut (sécurisée)

WebSSH est configuré en mode **"same"**, ce qui signifie:
- ✅ Vous pouvez seulement vous connecter au serveur local (127.0.0.1)
- ✅ Impossible de l'utiliser comme proxy vers d'autres serveurs
- ✅ Protection contre l'utilisation abusive

### Recommandations de sécurité

1. **Utilisez HTTPS en production**
   ```bash
   sudo ./nginx_webssh.sh
   ```

2. **Limitez l'accès par IP (optionnel)**

   Éditez `/etc/nginx/sites-available/webssh` et ajoutez:
   ```nginx
   # Autoriser seulement certaines IPs
   allow 1.2.3.4;  # Votre IP
   deny all;
   ```

3. **Utilisez des clés SSH au lieu de mots de passe**

4. **Surveillez les logs**
   ```bash
   sudo journalctl -u webssh -f
   ```

5. **Changez le port par défaut (optionnel)**

   Éditez la variable `WEBSSH_PORT` dans `install_webssh.sh` avant l'installation

---

## 🔧 Gestion de WebSSH

### Commandes utiles

```bash
# Statut du service
sudo systemctl status webssh

# Démarrer
sudo systemctl start webssh

# Arrêter
sudo systemctl stop webssh

# Redémarrer
sudo systemctl restart webssh

# Voir les logs
sudo journalctl -u webssh -f

# Voir les logs Nginx (si SSL configuré)
sudo tail -f /var/log/nginx/webssh-error.log
```

### Vérifier que TomatoPlan n'est pas affecté

```bash
# Vérifier TomatoPlan
sudo systemctl status tomatoplan-web

# Tester l'accès à TomatoPlan
curl http://localhost:5000
```

---

## 🔥 Configuration du pare-feu

### UFW (Ubuntu Firewall)

Si vous utilisez UFW:

```bash
# Permettre WebSSH
sudo ufw allow 8022/tcp comment 'WebSSH'

# Si SSL configuré
sudo ufw allow 'Nginx Full'

# Vérifier les règles
sudo ufw status
```

### Autres pare-feu

- **AWS Security Group:** Ajoutez une règle pour le port 8022 (TCP)
- **Google Cloud Firewall:** Créez une règle pour tcp:8022
- **Azure NSG:** Ajoutez une règle entrante pour le port 8022

---

## 🌐 Accès depuis Internet

### Sans nom de domaine

Si vous n'avez pas de nom de domaine, vous pouvez accéder via IP:

```
http://VOTRE_IP_PUBLIQUE:8022
```

⚠️ **Attention:** Sans SSL, vos mots de passe seront transmis en clair !

### Avec nom de domaine + SSL (Recommandé)

1. **Configurer le DNS**

   Créez un enregistrement A pointant vers votre serveur:
   ```
   ssh.votredomaine.com  →  IP_DE_VOTRE_SERVEUR
   ```

2. **Exécuter le script SSL**
   ```bash
   sudo ./nginx_webssh.sh
   ```

3. **Accéder via HTTPS**
   ```
   https://ssh.votredomaine.com
   ```

---

## 📊 Ports utilisés

| Service | Port | Description |
|---------|------|-------------|
| TomatoPlan | 80/443 ou 5000 | Application principale (NON AFFECTÉ) |
| WebSSH | 8022 | Accès WebSSH direct |
| WebSSH + SSL | 443 | Via Nginx reverse proxy (si configuré) |
| SSH | 22 | SSH traditionnel (inchangé) |

---

## ❌ Désinstallation

Si vous souhaitez désinstaller WebSSH:

```bash
# Arrêter et désactiver le service
sudo systemctl stop webssh
sudo systemctl disable webssh

# Supprimer le service
sudo rm /etc/systemd/system/webssh.service
sudo systemctl daemon-reload

# Supprimer les fichiers
sudo rm -rf /opt/webssh
sudo userdel webssh

# Supprimer la configuration Nginx (si configurée)
sudo rm /etc/nginx/sites-enabled/webssh
sudo rm /etc/nginx/sites-available/webssh
sudo systemctl reload nginx

# Fermer le port du pare-feu
sudo ufw delete allow 8022/tcp
```

---

## 🆘 Dépannage

### WebSSH ne démarre pas

```bash
# Vérifier les logs
sudo journalctl -u webssh -n 50

# Vérifier que le port n'est pas déjà utilisé
sudo netstat -tlnp | grep 8022

# Tester manuellement
sudo su - webssh
source /opt/webssh/venv/bin/activate
cd /opt/webssh/webssh
python run.py --port=8022
```

### Impossible de se connecter via le navigateur

1. Vérifier que le service est actif:
   ```bash
   sudo systemctl status webssh
   ```

2. Vérifier le pare-feu:
   ```bash
   sudo ufw status
   ```

3. Tester en local:
   ```bash
   curl http://localhost:8022
   ```

### Erreur "Connection refused" dans WebSSH

Cela signifie généralement que:
- Le serveur SSH (port 22) n'est pas actif
- Les credentials sont incorrects
- Le hostname/IP est incorrect

Vérifiez:
```bash
# Vérifier que SSH fonctionne
sudo systemctl status ssh

# Tester SSH traditionnel
ssh localhost
```

### TomatoPlan ne fonctionne plus après installation

WebSSH ne devrait PAS affecter TomatoPlan. Si c'est le cas:

1. Vérifier TomatoPlan:
   ```bash
   sudo systemctl status tomatoplan-web
   ```

2. Arrêter temporairement WebSSH:
   ```bash
   sudo systemctl stop webssh
   ```

3. Redémarrer TomatoPlan:
   ```bash
   sudo systemctl restart tomatoplan-web
   ```

---

## 📝 Notes importantes

1. **WebSSH est une couche supplémentaire**, il ne remplace pas SSH traditionnel
2. **Utilisez TOUJOURS SSL en production** pour protéger vos mots de passe
3. **WebSSH partage les mêmes utilisateurs** que votre système Linux
4. **Les connexions WebSSH sont enregistrées** dans les logs système
5. **Performance:** WebSSH utilise très peu de ressources (< 50 MB RAM)

---

## 🔗 Ressources

- [Documentation WebSSH](https://github.com/huashengdun/webssh)
- [Let's Encrypt](https://letsencrypt.org/)
- [Nginx documentation](https://nginx.org/en/docs/)

---

## ✅ Checklist post-installation

- [ ] WebSSH est accessible via le navigateur
- [ ] Je peux me connecter avec mes credentials SSH
- [ ] TomatoPlan fonctionne toujours normalement
- [ ] SSL est configuré (pour production)
- [ ] Le pare-feu autorise le port WebSSH
- [ ] Les logs ne montrent pas d'erreurs
- [ ] Je peux exécuter des commandes dans le terminal web
- [ ] J'ai testé la déconnexion/reconnexion
- [ ] J'ai noté mes credentials quelque part de sûr

---

## 🎉 C'est tout !

Vous avez maintenant un accès SSH moderne via navigateur, sans avoir perturbé TomatoPlan !

Pour toute question, consultez les logs ou contactez le support.
