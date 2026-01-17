# 🍅 TomatoPlan Web

Application web complète pour la gestion de planning de transport, avec base de données SQLite, système d'authentification, interface responsive et exports Excel/PDF.

## ✨ Fonctionnalités

### 📋 Gestion du Planning
- **Planning interactif** avec vue par jour
- **Création, édition et suppression** de missions
- **Assignation** de chauffeurs aux missions
- **Suivi en temps réel** des missions effectuées
- **Vue Gantt** chronologique des missions
- **Filtrage** par chauffeur, SST, voyage, statut

### 👥 Gestion des Chauffeurs
- **Base de données** complète des chauffeurs
- **Gestion des disponibilités** par date
- **Assignation** aux sous-traitants (SST)
- **Statut** actif/inactif

### 🚚 Gestion des Voyages/Tournées
- **Catalogue** des codes de voyage
- **Configuration** : type, durée, pays, statut
- **Intégration** avec le planning

### 💰 Finance
- **Dashboard financier** avec indicateurs clés
- **Gestion des tarifs** par SST et voyage
- **Revenus par palette** configurables
- **Calcul automatique** des marges (revenus - coûts)
- **Statistiques** par SST, voyage, période

### 📊 Analyse Avancée
- **Dashboard** avec graphiques interactifs
- **Analyse temporelle** des tendances
- **Comparaison de périodes**
- **Filtrage** multi-critères
- **Export** des données d'analyse

### 👁️ SAURON - Système de Surveillance
- **Logging complet** de toutes les actions
- **Historique détaillé** par utilisateur
- **Audit trail** : avant/après modifications
- **Statistiques** d'utilisation
- **Recherche** et filtrage avancés

### 🔐 Gestion des Droits
- **7 rôles prédéfinis** avec permissions granulaires :
  - **Viewer** : Consultation uniquement
  - **Planner** : Édition du planning
  - **Planner Advanced** : + historique + finance
  - **Driver Admin** : Gestion des chauffeurs
  - **Finance** : Gestion financière
  - **Analyse** : Accès à l'analyse
  - **Admin** : Accès complet
- **16 permissions** configurables
- **Authentification sécurisée** avec bcrypt
- **Sessions** persistantes

### 📤 Exports
- **Excel** : planning par chauffeur, par heure, par voyage
- **PDF** : génération de rapports formatés
- **Mise en page professionnelle**
- **Export personnalisable** par période

### 📱 Interface Moderne
- **Design responsive** : mobile, tablette, desktop
- **Bootstrap 5** pour une UI moderne
- **Drag & drop** pour réorganiser les missions
- **Filtres dynamiques** en temps réel
- **Notifications** et alertes
- **Mode sombre** (à venir)

### 📧 Annonces SST
- **Envoi d'emails** automatisés aux sous-traitants
- **Templates configurables** avec variables
- **Historique** des annonces envoyées
- **Gestion des listes** d'emails par SST

### ❓ Système d'Aide
- **Documentation intégrée**
- **Tooltips** contextuels
- **Guides** par fonctionnalité
- **FAQ**

## 🚀 Installation

### Prérequis

- **Python 3.8+**
- **pip** (gestionnaire de paquets Python)
- **Navigateur web moderne** (Chrome, Firefox, Edge, Safari)

### Installation Automatique

```bash
# 1. Cloner le projet
cd tomatoplan-web

# 2. Lancer le script d'installation
python install.py
```

Le script d'installation va :
- ✅ Vérifier Python
- ✅ Créer un environnement virtuel
- ✅ Installer les dépendances
- ✅ Configurer l'environnement (.env)
- ✅ Initialiser la base de données
- ✅ Créer les répertoires nécessaires
- ✅ Créer l'utilisateur admin par défaut

### Installation Manuelle

```bash
# 1. Créer l'environnement virtuel
python -m venv venv

# 2. Activer l'environnement
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Créer le fichier .env
cp .env.example .env
# Éditer .env avec vos paramètres

# 5. Initialiser la base de données
python -c "from app import create_app; from app.models import db; app=create_app(); app.app_context().push(); db.create_all()"
```

## 🎯 Démarrage

### Mode Développement

```bash
# Activer l'environnement virtuel
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Démarrer le serveur
python run.py
```

L'application sera accessible à : **http://127.0.0.1:5000**

### Mode Production

```bash
python run.py --production --host 0.0.0.0 --port 8080
```

### Options de Démarrage

```bash
python run.py --help

Options :
  --production     Démarrer en mode production
  --host HOST      Adresse d'écoute (défaut: 127.0.0.1)
  --port PORT      Port d'écoute (défaut: 5000)
  --debug          Activer le mode debug
```

## 📦 Migration des Données

Pour migrer vos données de l'ancienne application Tkinter (fichiers JSON) :

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer le script de migration
python migrations/migrate_from_json.py
```

Le script vous demandera le chemin vers le répertoire `_data` de l'ancienne application et importera :
- ✅ Chauffeurs
- ✅ Voyages
- ✅ SST et emails
- ✅ Tarifs SST
- ✅ Revenus par palette
- ✅ Missions
- ✅ Configuration des annonces

## 🔑 Connexion Initiale

**Utilisateur par défaut** :
- **Username** : `admin`
- **Password** : `admin`

⚠️ **IMPORTANT** : Changez ce mot de passe immédiatement après la première connexion !

## 📚 Structure du Projet

```
tomatoplan-web/
├── app/
│   ├── __init__.py          # Initialisation Flask
│   ├── models.py            # Modèles SQLAlchemy
│   ├── permissions.py       # Système de permissions
│   ├── routes/              # Routes (blueprints)
│   │   ├── auth.py          # Authentification
│   │   ├── main.py          # Pages principales
│   │   ├── planning.py      # Gestion du planning
│   │   ├── chauffeurs.py    # Gestion des chauffeurs
│   │   ├── voyages.py       # Gestion des voyages
│   │   ├── finance.py       # Finance
│   │   ├── analyse.py       # Analyse avancée
│   │   ├── admin.py         # Administration
│   │   ├── sauron.py        # Système de surveillance
│   │   └── api.py           # API REST
│   ├── templates/           # Templates HTML
│   ├── static/              # CSS, JS, images
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── utils/               # Utilitaires
│       └── exports.py       # Exports Excel/PDF
├── migrations/
│   └── migrate_from_json.py # Script de migration
├── config.py                # Configuration
├── run.py                   # Script de démarrage
├── install.py               # Script d'installation
├── requirements.txt         # Dépendances Python
├── .env                     # Configuration environnement
└── README.md                # Ce fichier
```

## 🔧 Configuration

Éditez le fichier `.env` pour configurer :

```env
# Clé secrète (générer une nouvelle en production!)
SECRET_KEY=votre-clé-secrète-très-longue

# Environnement
FLASK_ENV=development

# Base de données
DATABASE_URL=sqlite:///tomatoplan.db

# Email (optionnel)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=votre-email@gmail.com
MAIL_PASSWORD=votre-mot-de-passe-app
```

## 👥 Gestion des Utilisateurs

### Créer un Nouvel Utilisateur

1. Connectez-vous en tant qu'admin
2. Allez dans **Admin** → **Utilisateurs**
3. Cliquez sur **Nouveau utilisateur**
4. Remplissez le formulaire :
   - Username
   - Email (optionnel)
   - Nom complet
   - Rôle
   - Mot de passe initial
5. L'utilisateur peut ensuite changer son mot de passe

### Modifier les Droits

1. **Admin** → **Utilisateurs**
2. Sélectionnez l'utilisateur
3. Modifiez le **rôle**
4. Les permissions sont automatiquement mises à jour

## 📈 Utilisation

### Créer une Mission

1. Allez dans **Planning**
2. Sélectionnez la date
3. Cliquez sur **Nouvelle mission**
4. Remplissez les informations :
   - Heure, voyage, SST
   - Chauffeur (optionnel)
   - Palettes, pays, numéro
   - Revenus, coûts (calcul automatique de la marge)
5. **Enregistrer**

### Exporter le Planning

1. **Planning** → date souhaitée
2. Cliquez sur **Excel** ou **PDF**
3. Le fichier sera téléchargé automatiquement

### Analyser les Données

1. Allez dans **Analyse**
2. Sélectionnez la période
3. Choisissez le groupement (SST, voyage, chauffeur, date)
4. Consultez les graphiques et tableaux
5. Exportez si besoin

### Consulter l'Historique (SAURON)

1. Allez dans **SAURON**
2. Filtrez par :
   - Utilisateur
   - Action (CREATE, EDIT, DELETE, etc.)
   - Type d'entité
   - Période
3. Consultez les détails de chaque action

## 🛡️ Sécurité

### Bonnes Pratiques

- ✅ **Changez** le mot de passe admin par défaut
- ✅ **Générez** une nouvelle SECRET_KEY en production
- ✅ **Activez** HTTPS en production
- ✅ **Sauvegardez** régulièrement la base de données
- ✅ **Limitez** les permissions aux utilisateurs
- ✅ **Surveillez** les logs SAURON

### Sauvegarde de la Base de Données

```bash
# Créer une sauvegarde
cp tomatoplan.db tomatoplan_backup_$(date +%Y%m%d).db

# Ou avec un script automatisé (cron/tâche planifiée)
0 2 * * * cp /path/to/tomatoplan.db /path/to/backups/tomatoplan_$(date +\%Y\%m\%d).db
```

## 🐛 Dépannage

### Erreur "Module not found"

```bash
# Vérifier que l'environnement virtuel est activé
source venv/bin/activate

# Réinstaller les dépendances
pip install -r requirements.txt
```

### Erreur "Database locked"

SQLite peut avoir des problèmes de concurrence. Solutions :
- Redémarrer l'application
- Vérifier qu'aucune autre instance n'est en cours
- En production, envisager PostgreSQL ou MySQL

### Port déjà utilisé

```bash
# Utiliser un autre port
python run.py --port 8080
```

## 📞 Support

Pour toute question ou problème :
- Consultez la documentation intégrée (menu Aide)
- Vérifiez les logs dans le répertoire `logs/`
- Consultez l'historique SAURON pour debug

## 📄 Licence

© 2024 TomatoPlan Web - Tous droits réservés

## 🎉 Remerciements

Développé avec :
- Flask (Python web framework)
- SQLAlchemy (ORM)
- Bootstrap 5 (UI framework)
- Chart.js (Graphiques)
- SortableJS (Drag & drop)
- openpyxl (Excel)
- ReportLab (PDF)

---

**Version** : 1.0.0
**Dernière mise à jour** : 2024
