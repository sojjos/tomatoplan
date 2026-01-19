# Guide de Migration - Mise à jour du schéma Chauffeur

## 📋 Vue d'ensemble

Cette migration met à jour le schéma de la table `chauffeurs` pour:
- ✅ Ajouter les colonnes `prenom` et `telephone`
- ✅ Remplacer la colonne `sst` (texte) par `sst_id` (clé étrangère vers la table SST)
- ✅ Améliorer l'intégrité référentielle de la base de données

**Date:** 2026-01-19
**Version:** 1.0

---

## ⚠️ IMPORTANT - À lire avant de commencer

1. **Sauvegarde obligatoire** : Cette migration modifie la structure de la base de données
2. **Arrêt de l'application** : L'application doit être arrêtée pendant la migration
3. **Temps d'arrêt** : Prévoir 2-5 minutes selon la taille de la base
4. **Testez d'abord** : Testez la migration sur une copie de la base avant de la faire en production

---

## 🚀 Procédure de mise à jour en PRODUCTION

### Méthode 1: Script Python automatique (RECOMMANDÉ)

Cette méthode est la plus sûre car elle:
- Crée automatiquement une sauvegarde
- Effectue des vérifications
- Peut restaurer en cas d'erreur

#### Étapes:

```bash
# 1. Se connecter au serveur de production
ssh user@votre-serveur

# 2. Aller dans le répertoire de l'application
cd /chemin/vers/tomatoplan-web

# 3. Activer l'environnement virtuel
source venv/bin/activate

# 4. Mettre à jour le code depuis Git
git pull origin main  # ou la branche appropriée

# 5. Arrêter l'application
sudo systemctl stop tomatoplan-web
# OU si vous utilisez un autre gestionnaire:
# supervisorctl stop tomatoplan-web

# 6. Exécuter le script de migration
python3 migrations/migrate_chauffeur_schema.py

# Le script va:
# - Créer une sauvegarde automatique
# - Migrer le schéma
# - Vérifier que tout s'est bien passé

# 7. Redémarrer l'application
sudo systemctl start tomatoplan-web
# OU
# supervisorctl start tomatoplan-web

# 8. Vérifier que l'application fonctionne
sudo systemctl status tomatoplan-web
# Tester l'accès web
curl http://localhost:5000/health  # ou l'URL appropriée
```

---

### Méthode 2: Migration SQL manuelle

Si vous préférez avoir un contrôle total sur la migration:

```bash
# 1. Se connecter au serveur
ssh user@votre-serveur

# 2. Aller dans le répertoire de l'application
cd /chemin/vers/tomatoplan-web

# 3. Arrêter l'application
sudo systemctl stop tomatoplan-web

# 4. Créer une sauvegarde manuelle
cp instance/tomatoplan.db instance/tomatoplan.db.backup_$(date +%Y%m%d_%H%M%S)

# 5. Exécuter le script SQL
sqlite3 instance/tomatoplan.db < migrations/001_update_chauffeur_schema.sql

# 6. Vérifier que la migration s'est bien passée
sqlite3 instance/tomatoplan.db "PRAGMA table_info(chauffeurs);"

# Vous devriez voir les colonnes:
# - id, nom, prenom, sst_id, telephone, actif, infos, created_at, updated_at

# 7. Mettre à jour le code
git pull origin main

# 8. Redémarrer l'application
sudo systemctl start tomatoplan-web
```

---

## 🔍 Vérification post-migration

Après la migration, vérifiez que tout fonctionne:

### 1. Vérifier la structure de la table

```bash
sqlite3 instance/tomatoplan.db "PRAGMA table_info(chauffeurs);"
```

Résultat attendu:
```
0|id|TEXT|0||1
1|nom|TEXT|1||0
2|prenom|TEXT|0||0
3|sst_id|INTEGER|0||0
4|telephone|TEXT|0||0
5|actif|INTEGER|0|1|0
6|infos|TEXT|0||0
7|created_at|TIMESTAMP|0||0
8|updated_at|TIMESTAMP|0||0
```

### 2. Vérifier les données

```bash
sqlite3 instance/tomatoplan.db "SELECT COUNT(*) FROM chauffeurs;"
sqlite3 instance/tomatoplan.db "SELECT COUNT(*) FROM chauffeurs WHERE sst_id IS NOT NULL;"
```

### 3. Tester l'application web

1. Ouvrir l'application dans un navigateur
2. Aller sur la page des chauffeurs
3. Vérifier que la liste s'affiche correctement
4. Créer un nouveau chauffeur pour tester
5. Modifier un chauffeur existant

---

## 🔧 Configuration serveur spécifique

### Si vous utilisez systemd

```bash
# Voir les logs
sudo journalctl -u tomatoplan-web -f

# Redémarrer
sudo systemctl restart tomatoplan-web

# Vérifier le statut
sudo systemctl status tomatoplan-web
```

### Si vous utilisez supervisor

```bash
# Voir les logs
tail -f /var/log/supervisor/tomatoplan-web.log

# Redémarrer
supervisorctl restart tomatoplan-web

# Vérifier le statut
supervisorctl status tomatoplan-web
```

### Si vous utilisez Docker

```bash
# Arrêter le conteneur
docker-compose down

# Mettre à jour le code
git pull origin main

# Reconstruire et redémarrer
docker-compose up -d --build

# Exécuter la migration dans le conteneur
docker-compose exec web python3 migrations/migrate_chauffeur_schema.py

# Voir les logs
docker-compose logs -f web
```

---

## 🆘 En cas de problème

### La migration échoue

```bash
# 1. Le script Python restaure automatiquement la sauvegarde
# Si ce n'est pas le cas, restaurez manuellement:

# Trouver la sauvegarde
ls -lh instance/*.backup_*

# Restaurer
cp instance/tomatoplan.db.backup_YYYYMMDD_HHMMSS instance/tomatoplan.db

# Redémarrer l'application
sudo systemctl start tomatoplan-web
```

### L'application ne démarre pas après la migration

```bash
# 1. Vérifier les logs
sudo journalctl -u tomatoplan-web -n 50

# 2. Vérifier que le schéma est correct
sqlite3 instance/tomatoplan.db "PRAGMA table_info(chauffeurs);"

# 3. Si le problème persiste, restaurer la sauvegarde
cp instance/tomatoplan.db.backup_YYYYMMDD_HHMMSS instance/tomatoplan.db
sudo systemctl restart tomatoplan-web
```

### Les chauffeurs n'ont plus de SST assigné

```bash
# Vérifier la conversion
sqlite3 instance/tomatoplan.db << EOF
SELECT
    c.nom,
    c.sst_id,
    s.nom as sst_nom
FROM chauffeurs c
LEFT JOIN sst s ON c.sst_id = s.id
WHERE c.sst_id IS NOT NULL;
EOF
```

Si des SST sont manquants, vérifiez que la table SST contient bien tous les sous-traitants.

---

## 📝 Checklist de migration

- [ ] J'ai lu ce guide en entier
- [ ] J'ai testé la migration sur une copie de la base de données
- [ ] J'ai prévenu les utilisateurs d'un temps d'arrêt
- [ ] J'ai créé une sauvegarde manuelle (en plus de celle automatique)
- [ ] L'application est arrêtée
- [ ] La migration est exécutée
- [ ] La migration s'est terminée sans erreur
- [ ] Le schéma de la table est correct
- [ ] Les données sont préservées
- [ ] L'application a été mise à jour (git pull)
- [ ] L'application est redémarrée
- [ ] L'application fonctionne correctement
- [ ] Les tests de vérification passent
- [ ] Les utilisateurs peuvent à nouveau accéder à l'application

---

## 📞 Support

En cas de problème, contactez l'équipe de développement avec:
- Les logs de la migration
- Les logs de l'application
- Le message d'erreur exact
- La version de Python et SQLite utilisée

```bash
# Informations système utiles pour le support
python3 --version
sqlite3 --version
cat /etc/os-release | grep PRETTY_NAME
```

---

## 🔄 Retour arrière (Rollback)

Si vous devez revenir à l'ancienne version:

```bash
# 1. Arrêter l'application
sudo systemctl stop tomatoplan-web

# 2. Restaurer la base de données
cp instance/tomatoplan.db.backup_YYYYMMDD_HHMMSS instance/tomatoplan.db

# 3. Revenir au code précédent
git checkout <commit-hash-précédent>

# 4. Redémarrer
sudo systemctl start tomatoplan-web
```

⚠️ **Attention** : Un retour arrière annulera toutes les données créées après la migration.
