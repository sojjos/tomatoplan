# Guide de déploiement du fix pour TomatoPlan

## 🚨 Problème

Votre application TomatoPlan affiche "Internal Server Error" à cause d'un problème de schéma de base de données. La table `chauffeurs` est incompatible avec le code.

**Erreur:** `no such column: chauffeurs.prenom`

## ✅ Solution

Le script `fix_production.sh` va tout réparer automatiquement en:

1. ✅ Arrêtant l'application proprement
2. ✅ Nettoyant le cache Python
3. ✅ Créant une sauvegarde de sécurité
4. ✅ Migrant le schéma de la base de données
5. ✅ Vérifiant qu'aucune donnée n'est perdue
6. ✅ Redémarrant l'application

## 📋 Instructions de déploiement

### Depuis votre ordinateur local:

```bash
# 1. Transférer les fichiers vers le serveur
cd tomatoplan-web
scp migrations/migrate_chauffeur_schema.py ubuntu@VOTRE_SERVEUR:/tmp/
scp scripts/fix_production.sh ubuntu@VOTRE_SERVEUR:/tmp/
```

### Sur votre serveur de production:

```bash
# 2. Se connecter au serveur
ssh ubuntu@VOTRE_SERVEUR

# 3. Copier les fichiers dans le bon répertoire
sudo cp /tmp/migrate_chauffeur_schema.py /opt/tomatoplan/tomatoplan-web/migrations/
sudo cp /tmp/fix_production.sh /opt/tomatoplan/tomatoplan-web/scripts/
sudo chmod +x /opt/tomatoplan/tomatoplan-web/scripts/fix_production.sh

# 4. Exécuter le script de correction
cd /opt/tomatoplan/tomatoplan-web
sudo ./scripts/fix_production.sh
```

## ⚡ Exécution rapide (une seule commande)

Si vous êtes pressé, depuis votre serveur:

```bash
sudo /opt/tomatoplan/tomatoplan-web/scripts/fix_production.sh
```

## 🔍 Que fait le script exactement?

### Étape 1: Arrêt de l'application
- Arrête le service `tomatoplan-web`
- Tue les processus gunicorn qui restent

### Étape 2: Nettoyage du cache
- Supprime tous les `__pycache__`
- Supprime tous les fichiers `.pyc`

### Étape 3: Vérification de la base actuelle
- Affiche le schéma actuel
- Compte le nombre de chauffeurs

### Étape 4: Sauvegarde de sécurité
- Crée `tomatoplan.db.backup_fix_YYYYMMDD_HHMMSS`
- Vérifie l'intégrité de la sauvegarde

### Étape 5: Migration du schéma
- Exécute le script `migrate_chauffeur_schema.py`
- Ajoute les colonnes: `prenom`, `telephone`
- Convertit `sst` (texte) en `sst_id` (clé étrangère)
- Préserve TOUTES les données existantes

### Étape 6: Vérification
- Vérifie que les colonnes sont présentes
- Vérifie qu'aucune donnée n'a été perdue
- Si problème, restaure automatiquement la sauvegarde

### Étape 7: Redémarrage
- Redémarre `tomatoplan-web`
- Vérifie que l'application répond

## ✅ Après l'exécution

Le script affichera:

```
==================================================================
✓ Correction complète terminée avec succès!
==================================================================

Résumé:
  ✓ Application arrêtée
  ✓ Cache Python nettoyé
  ✓ Sauvegarde créée: /opt/tomatoplan/tomatoplan-web/tomatoplan.db.backup_fix_20260119_XXXXXX
  ✓ Migration de la base de données réussie
  ✓ Schéma vérifié (prenom, sst_id, telephone présents)
  ✓ Aucune perte de données (X chauffeurs préservés)
  ✓ Application redémarrée
```

## 🧪 Vérification manuelle

Après l'exécution du script, testez:

```bash
# 1. Vérifier que le service tourne
sudo systemctl status tomatoplan-web

# 2. Vérifier que l'application répond
curl http://localhost:5000

# 3. Voir les logs en direct
sudo journalctl -u tomatoplan-web -f

# 4. Vérifier le schéma de la base
sqlite3 /opt/tomatoplan/tomatoplan-web/tomatoplan.db "PRAGMA table_info(chauffeurs);"
```

Vous devriez voir:
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

## 🌐 Tester l'application web

Ouvrez votre navigateur et accédez à votre TomatoPlan. Tout devrait fonctionner!

## 🆘 En cas de problème

### Le script échoue pendant la migration

Le script restaurera automatiquement la sauvegarde. Vos données sont en sécurité.

### L'application ne démarre pas après le script

```bash
# Voir les logs d'erreur
sudo journalctl -u tomatoplan-web -n 50

# Restaurer manuellement la sauvegarde
sudo cp /opt/tomatoplan/tomatoplan-web/tomatoplan.db.backup_fix_* /opt/tomatoplan/tomatoplan-web/tomatoplan.db

# Redémarrer
sudo systemctl restart tomatoplan-web
```

### Erreur "script not found"

Vérifiez que vous avez bien copié les fichiers:

```bash
ls -la /opt/tomatoplan/tomatoplan-web/migrations/migrate_chauffeur_schema.py
ls -la /opt/tomatoplan/tomatoplan-web/scripts/fix_production.sh
```

## 📊 Sauvegardes disponibles

Après l'exécution, vous aurez:

- `tomatoplan.db` - Base de données migrée (en production)
- `tomatoplan.db.backup_fix_YYYYMMDD_HHMMSS` - Sauvegarde de sécurité
- `tomatoplan.db.backup_YYYYMMDD_HHMMSS` - Sauvegardes précédentes (si existantes)

Pour restaurer une sauvegarde:

```bash
sudo systemctl stop tomatoplan-web
sudo cp /opt/tomatoplan/tomatoplan-web/tomatoplan.db.backup_fix_XXXXXX /opt/tomatoplan/tomatoplan-web/tomatoplan.db
sudo systemctl start tomatoplan-web
```

## 🔐 Sécurité

Le script:
- ✅ Demande confirmation avant de continuer
- ✅ Crée une sauvegarde avant toute modification
- ✅ Vérifie l'intégrité des données
- ✅ Restaure automatiquement en cas d'erreur
- ✅ Ne supprime jamais les données

## ⏱️ Durée estimée

Le script prend environ **30-60 secondes** pour s'exécuter, selon la taille de votre base de données.

Temps d'arrêt de l'application: **~1 minute**

## 📞 Support

Si vous rencontrez des problèmes:

1. Vérifiez les logs: `sudo journalctl -u tomatoplan-web -f`
2. Vérifiez que sqlite3 est installé: `which sqlite3`
3. Vérifiez les permissions: `ls -la /opt/tomatoplan/tomatoplan-web/`

---

## ✨ C'est tout!

Le script est conçu pour être **sûr**, **rapide** et **automatique**. Il corrige tous les problèmes de schéma sans perte de données.

**Bonne chance! 🚀**
