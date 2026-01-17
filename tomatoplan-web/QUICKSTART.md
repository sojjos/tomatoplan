# 🚀 Guide de Démarrage Rapide - TomatoPlan Web

## Installation en 3 étapes

### 1️⃣ Installer

```bash
cd tomatoplan-web
python install.py
```

### 2️⃣ Démarrer

```bash
# Windows
venv\Scripts\activate
python run.py

# Linux/Mac
source venv/bin/activate
python run.py
```

### 3️⃣ Utiliser

Ouvrez votre navigateur : **http://127.0.0.1:5000**

**Connexion initiale** :
- Username: `admin`
- Password: `admin`

⚠️ **Changez ce mot de passe immédiatement !**

---

## 📦 Migration des Données (optionnel)

Si vous avez des données de l'ancienne application :

```bash
source venv/bin/activate
python migrations/migrate_from_json.py
```

Indiquez le chemin vers votre dossier `_data`.

---

## 🎯 Premières Actions

1. **Changer le mot de passe admin**
   - Cliquez sur votre nom (en haut à droite) → Changer mot de passe

2. **Créer des utilisateurs**
   - Admin → Utilisateurs → Nouveau utilisateur

3. **Ajouter des chauffeurs**
   - Chauffeurs → Nouveau chauffeur

4. **Créer une mission**
   - Planning → Nouvelle mission

5. **Consulter les stats**
   - Accueil (tableau de bord)

---

## 📚 Documentation Complète

Consultez le fichier [README.md](README.md) pour la documentation complète.

---

## ❓ Besoin d'Aide ?

- **Dans l'application** : Menu Aide
- **Documentation** : README.md
- **Support** : Contactez votre administrateur
