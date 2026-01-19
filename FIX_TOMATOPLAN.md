# 🚨 CORRECTION RAPIDE TOMATOPLAN

## Votre problème: "Internal Server Error"

Votre site TomatoPlan est actuellement "mort" à cause d'une erreur de schéma de base de données.

**Erreur:** `no such column: chauffeurs.prenom`

## ✅ Solution en 3 étapes

### Étape 1: Sur votre ordinateur local

```bash
cd ~/tomatoplan/tomatoplan-web
scp migrations/migrate_chauffeur_schema.py ubuntu@VOTRE_SERVEUR:/tmp/
scp scripts/fix_production.sh ubuntu@VOTRE_SERVEUR:/tmp/
```

Remplacez `VOTRE_SERVEUR` par l'adresse IP ou le nom de domaine de votre serveur.

### Étape 2: Connexion au serveur

```bash
ssh ubuntu@VOTRE_SERVEUR
```

### Étape 3: Copier et exécuter le script de correction

```bash
# Copier les fichiers au bon endroit
sudo cp /tmp/migrate_chauffeur_schema.py /opt/tomatoplan/tomatoplan-web/migrations/
sudo cp /tmp/fix_production.sh /opt/tomatoplan/tomatoplan-web/scripts/
sudo chmod +x /opt/tomatoplan/tomatoplan-web/scripts/fix_production.sh

# Exécuter le script de correction
sudo /opt/tomatoplan/tomatoplan-web/scripts/fix_production.sh
```

## 🎯 Que fait le script?

Le script `fix_production.sh` fait TOUT automatiquement:

1. ✅ Arrête l'application
2. ✅ Nettoie le cache Python
3. ✅ **Crée une sauvegarde de sécurité** (aucune perte de données!)
4. ✅ Migre la base de données (ajoute `prenom`, `sst_id`, `telephone`)
5. ✅ Vérifie que tout est correct
6. ✅ Redémarre l'application

**Durée:** ~1 minute
**Temps d'arrêt:** ~1 minute
**Risque de perte de données:** AUCUN (sauvegarde automatique)

## 📊 Résultat attendu

Après l'exécution, vous verrez:

```
==================================================================
✓ Correction complète terminée avec succès!
==================================================================

Résumé:
  ✓ Application arrêtée
  ✓ Cache Python nettoyé
  ✓ Sauvegarde créée
  ✓ Migration de la base de données réussie
  ✓ Schéma vérifié (prenom, sst_id, telephone présents)
  ✓ Aucune perte de données
  ✓ Application redémarrée
  ✓ L'application répond correctement!
```

## 🌐 Vérification

Ouvrez votre navigateur et accédez à votre TomatoPlan:

```
http://VOTRE_SERVEUR
```

Tout devrait fonctionner! ✨

## 🆘 En cas de problème

Si le script échoue, il restaure automatiquement la sauvegarde. Vos données sont protégées.

Pour voir les logs:

```bash
sudo journalctl -u tomatoplan-web -f
```

## 📚 Documentation complète

Pour plus de détails, consultez:
- `tomatoplan-web/scripts/DEPLOY_FIX.md` - Guide complet de déploiement
- `tomatoplan-web/migrations/MIGRATION_GUIDE.md` - Guide de migration

---

## 🚀 COMMANDE RAPIDE (si vous êtes pressé)

Sur votre ordinateur local:
```bash
scp ~/tomatoplan/tomatoplan-web/migrations/migrate_chauffeur_schema.py ubuntu@VOTRE_SERVEUR:/tmp/ && \
scp ~/tomatoplan/tomatoplan-web/scripts/fix_production.sh ubuntu@VOTRE_SERVEUR:/tmp/ && \
ssh ubuntu@VOTRE_SERVEUR "sudo cp /tmp/migrate_chauffeur_schema.py /opt/tomatoplan/tomatoplan-web/migrations/ && \
sudo cp /tmp/fix_production.sh /opt/tomatoplan/tomatoplan-web/scripts/ && \
sudo chmod +x /opt/tomatoplan/tomatoplan-web/scripts/fix_production.sh && \
sudo /opt/tomatoplan/tomatoplan-web/scripts/fix_production.sh"
```

**Remplacez `VOTRE_SERVEUR` par votre adresse de serveur!**

Cette commande fait TOUT en une seule fois! 🎉

---

Bon courage! Votre site sera de nouveau opérationnel dans moins de 2 minutes! 💪
