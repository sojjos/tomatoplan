# Migrations TomatoPlan Web

Ce répertoire contient les scripts de migration de base de données pour TomatoPlan Web.

## 📁 Fichiers

### Scripts de migration

- **`migrate_chauffeur_schema.py`** (✅ RECOMMANDÉ)
  - Script Python automatique pour migrer le schéma de la table chauffeurs
  - Crée automatiquement une sauvegarde
  - Gère les erreurs et peut restaurer en cas de problème
  - Usage: `python3 migrations/migrate_chauffeur_schema.py`

- **`001_update_chauffeur_schema.sql`**
  - Script SQL manuel pour la migration
  - Pour les utilisateurs avancés qui préfèrent SQLite directement
  - Usage: `sqlite3 instance/tomatoplan.db < migrations/001_update_chauffeur_schema.sql`

- **`migrate_from_json.py`**
  - Script de migration initial depuis les fichiers JSON
  - Utilisé lors de la première installation

### Documentation

- **`MIGRATION_GUIDE.md`** (📖 À LIRE EN PREMIER)
  - Guide complet de migration pour la production
  - Procédures pas-à-pas
  - Gestion des erreurs
  - Checklist de vérification

- **`README.md`** (ce fichier)
  - Vue d'ensemble du répertoire migrations

## 🚀 Mise à jour rapide en production

Pour mettre à jour votre serveur de production rapidement:

```bash
# Utiliser le script automatique (recommandé)
./update_production.sh

# OU en mode automatique sans confirmation
./update_production.sh --auto
```

## 📋 Changements de cette migration

### Version: 001 - Mise à jour schéma Chauffeur
**Date:** 2026-01-19

**Modifications:**
- ✅ Ajout de la colonne `prenom` (prénom du chauffeur)
- ✅ Ajout de la colonne `telephone` (numéro de téléphone)
- ✅ Remplacement de `sst` (texte) par `sst_id` (clé étrangère vers table SST)
- ✅ Amélioration de l'intégrité référentielle

**Impact:**
- Modification de la structure de la table `chauffeurs`
- Les données existantes sont préservées
- Les SST sont automatiquement convertis en relations

## ⚠️ Important

1. **Toujours faire une sauvegarde avant une migration**
2. **Tester la migration sur une copie avant de l'appliquer en production**
3. **Arrêter l'application pendant la migration**
4. **Lire le MIGRATION_GUIDE.md avant de commencer**

## 🆘 En cas de problème

Consultez le fichier `MIGRATION_GUIDE.md` pour:
- Procédures de dépannage
- Restauration de sauvegarde
- Retour arrière (rollback)
- Contact support

## 📝 Historique des migrations

| Version | Date | Description | Fichiers |
|---------|------|-------------|----------|
| 001 | 2026-01-19 | Mise à jour schéma Chauffeur | `migrate_chauffeur_schema.py`, `001_update_chauffeur_schema.sql` |

## 🔗 Liens utiles

- [Guide de migration](./MIGRATION_GUIDE.md)
- [Documentation principale](../README.md)
