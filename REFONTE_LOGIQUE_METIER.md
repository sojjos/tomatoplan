# Refonte de la logique métier TomatoPlan

## Problèmes identifiés

L'application actuelle permet à l'utilisateur de saisir manuellement des valeurs qui devraient être calculées automatiquement selon les règles métier.

### Erreurs dans le formulaire de mission actuel:

1. **Type (LIVRAISON/RAMASSE)**: Champ manuel → Devrait venir automatiquement du code voyage
2. **Revenus**: Champ manuel → Doit être calculé depuis RevenuPalette (voyage + nb palettes)
3. **Coûts**: Champ manuel → Doit être calculé depuis TarifSST (SST + voyage)
4. **Marge**: Champ manuel → Calcul automatique (Revenus - Coûts)
5. **Pays**: Champ manuel → Devrait venir du code voyage
6. **Checkbox "Ramasse"**: Redondant avec le type (déjà indiqué par le code voyage)

### Filtrage manquant:

- Les chauffeurs ne sont PAS filtrés par SST
- Quand un SST est sélectionné, SEULS les chauffeurs liés à ce SST doivent apparaître

### Pages manquantes:

- Gestion des disponibilités des chauffeurs (calendrier travail/repos)

---

## ✅ Solutions implémentées

### 1. Fonctions de calcul automatique

**Fichier:** `app/utils/calculs.py`

Fonctions créées:
- `calculer_revenu(voyage_code, palettes)` → Cherche dans RevenuPalette
- `calculer_cout(sst_nom, voyage_code)` → Cherche dans TarifSST
- `get_type_voyage(voyage_code)` → Récupère le type depuis la table Voyage
- `get_pays_voyage(voyage_code)` → Récupère le pays depuis la table Voyage
- `calculer_mission_complete()` → Calcule tout en une fois

### 2. Routes API ajoutées

**Fichier:** `app/routes/api.py`

Nouvelles routes:
- `GET /api/calcul-mission?voyage=XXX&sst=YYY&palettes=ZZ` → Retourne calculs automatiques
- `GET /api/chauffeurs-par-sst?sst=XXX` → Retourne chauffeurs filtrés par SST

---

## 🔧 Modifications nécessaires

### Template `planning/index.html` à modifier

#### Formulaire mission (lignes 235-328)

**RETIRER:**
```html
<!-- Type manuel -->
<div class="col-md-6 mb-3">
    <label class="form-label">Type</label>
    <select class="form-select" id="missionType" required>
        <option value="LIVRAISON">LIVRAISON</option>
        <option value="RAMASSE">RAMASSE</option>
    </select>
</div>

<!-- Revenus manuels -->
<div class="col-md-4 mb-3">
    <label class="form-label">Revenus (€)</label>
    <input type="number" class="form-control" id="missionRevenus" step="0.01" value="0">
</div>

<!-- Coûts manuels -->
<div class="col-md-4 mb-3">
    <label class="form-label">Coûts (€)</label>
    <input type="number" class="form-control" id="missionCouts" step="0.01" value="0">
</div>

<!-- Checkbox Ramasse redondante -->
<div class="form-check mb-3">
    <input class="form-check-input" type="checkbox" id="missionRamasse">
    <label class="form-check-label" for="missionRamasse">
        Ramasse
    </label>
</div>
```

**REMPLACER PAR:**
```html
<!-- Type en lecture seule (automatique) -->
<div class="col-md-6 mb-3">
    <label class="form-label">Type <small class="text-muted">(automatique)</small></label>
    <input type="text" class="form-control" id="missionType" readonly style="background-color: #e9ecef;">
</div>

<!-- Pays en lecture seule (automatique) -->
<div class="col-md-4 mb-3">
    <label class="form-label">Pays <small class="text-muted">(automatique)</small></label>
    <input type="text" class="form-control" id="missionPays" readonly style="background-color: #e9ecef;">
</div>

<!-- Affichage des calculs automatiques -->
<div class="alert alert-info mb-3">
    <strong>💰 Calculs automatiques:</strong>
    <div class="row mt-2">
        <div class="col-md-4">
            <label class="form-label small">Revenus</label>
            <div class="fs-5"><strong id="displayRevenus">0.00 €</strong></div>
            <input type="hidden" id="missionRevenus" value="0">
        </div>
        <div class="col-md-4">
            <label class="form-label small">Coûts SST</label>
            <div class="fs-5"><strong id="displayCouts">0.00 €</strong></div>
            <input type="hidden" id="missionCouts" value="0">
        </div>
        <div class="col-md-4">
            <label class="form-label small">Marge</label>
            <div class="fs-5"><strong id="displayMarge" class="text-success">0.00 €</strong></div>
            <input type="hidden" id="missionMarge" value="0">
        </div>
    </div>
    <small class="text-muted">
        <i class="bi bi-info-circle"></i>
        Les tarifs sont définis dans Finance > Tarifs SST et Finance > Revenus Palettes
    </small>
</div>
```

#### JavaScript à ajouter (après ligne 340)

```javascript
// Événements pour calcul automatique
document.getElementById('missionVoyage').addEventListener('change', function() {
    const select = this;
    const selectedOption = select.options[select.selectedIndex];

    // Mettre à jour type et pays automatiquement
    const type = selectedOption.dataset.type || '';
    const pays = selectedOption.dataset.pays || '';

    document.getElementById('missionType').value = type;
    document.getElementById('missionPays').value = pays;

    // Recalculer les montants
    calculerMontantsAutomatiques();
});

document.getElementById('missionSST').addEventListener('change', function() {
    // Filtrer les chauffeurs
    chargerChauffeursPar SST(this.value);

    // Recalculer les coûts
    calculerMontantsAutomatiques();
});

document.getElementById('missionPalettes').addEventListener('change', function() {
    // Recalculer les revenus
    calculerMontantsAutomatiques();
});

// Fonction pour calculer automatiquement
async function calculerMontantsAutomatiques() {
    const voyage = document.getElementById('missionVoyage').value;
    const sst = document.getElementById('missionSST').value;
    const palettes = document.getElementById('missionPalettes').value || 0;

    if (!voyage || !sst) {
        // Réinitialiser
        document.getElementById('displayRevenus').textContent = '0.00 €';
        document.getElementById('displayCouts').textContent = '0.00 €';
        document.getElementById('displayMarge').textContent = '0.00 €';
        document.getElementById('missionRevenus').value = 0;
        document.getElementById('missionCouts').value = 0;
        document.getElementById('missionMarge').value = 0;
        return;
    }

    try {
        const response = await fetch('/api/calcul-mission?voyage=' + voyage + '&sst=' + sst + '&palettes=' + palettes);
        const data = await response.json();

        if (data.error) {
            console.error('Erreur calcul:', data.error);
            return;
        }

        // Mettre à jour l'affichage
        document.getElementById('displayRevenus').textContent = data.revenus.toFixed(2) + ' €';
        document.getElementById('displayCouts').textContent = data.couts.toFixed(2) + ' €';
        document.getElementById('displayMarge').textContent = data.marge.toFixed(2) + ' €';

        // Mettre à jour les champs cachés
        document.getElementById('missionRevenus').value = data.revenus;
        document.getElementById('missionCouts').value = data.couts;
        document.getElementById('missionMarge').value = data.marge;

        // Colorer la marge
        const margeElement = document.getElementById('displayMarge');
        if (data.marge > 0) {
            margeElement.className = 'text-success';
        } else if (data.marge < 0) {
            margeElement.className = 'text-danger';
        } else {
            margeElement.className = 'text-secondary';
        }

    } catch (error) {
        console.error('Erreur:', error);
    }
}

// Fonction pour charger les chauffeurs par SST
async function chargerChauffeursPar SST(sstNom) {
    const selectChauffeur = document.getElementById('missionChauffeur');

    try {
        const url = sstNom ? '/api/chauffeurs-par-sst?sst=' + encodeURIComponent(sstNom) : '/api/chauffeurs-par-sst';
        const response = await fetch(url);
        const data = await response.json();

        // Vider et recréer la liste
        selectChauffeur.innerHTML = '<option value="">Non assigné</option>';

        data.chauffeurs.forEach(function(chauffeur) {
            const option = document.createElement('option');
            option.value = chauffeur.nom;
            option.textContent = chauffeur.nom + (chauffeur.prenom ? ' ' + chauffeur.prenom : '');
            selectChauffeur.appendChild(option);
        });

    } catch (error) {
        console.error('Erreur chargement chauffeurs:', error);
    }
}
```

#### Modifier saveMission() (ligne 400+)

Retirer le champ `ramasse` de l'envoi:

**AVANT:**
```javascript
ramasse: document.getElementById('missionRamasse').checked,
```

**APRÈS:**
```javascript
// ramasse est déterminé par le type (automatique depuis le voyage)
ramasse: document.getElementById('missionType').value === 'RAMASSE',
```

---

## 🆕 Page manquante: Disponibilités chauffeurs

### Créer `app/templates/chauffeurs/disponibilites.html`

Cette page doit permettre de:
- Voir un calendrier des disponibilités par chauffeur
- Marquer un chauffeur comme indisponible (congé, maladie, etc.)
- Voir visuellement qui est disponible pour une date donnée

**Route à ajouter:** `GET /chauffeurs/disponibilites`

---

## 📊 Données nécessaires en base

Pour que le système fonctionne, il faut configurer:

### 1. Table `voyages`
```sql
INSERT INTO voyages (code, type, country, duree, actif) VALUES
('BXL-01', 'LIVRAISON', 'Belgique', 60, 1),
('BXL-02', 'RAMASSE', 'Belgique', 45, 1),
...
```

### 2. Table `revenus_palettes`
```sql
INSERT INTO revenus_palettes (voyage, palettes_min, palettes_max, revenu) VALUES
('BXL-01', 0, 10, 150.00),
('BXL-01', 11, 20, 280.00),
('BXL-01', 21, 999, 400.00),
...
```

### 3. Table `tarifs_sst`
```sql
INSERT INTO tarifs_sst (sst_id, voyage, tarif) VALUES
(1, 'BXL-01', 120.00),  -- SST "Transport A" pour voyage BXL-01
(1, 'BXL-02', 95.00),
(2, 'BXL-01', 130.00),  -- SST "Transport B" pour voyage BXL-01
...
```

---

## 🧪 Tests à effectuer

Après modifications:

1. ✅ Créer une mission en sélectionnant un voyage → Le type et pays doivent s'afficher automatiquement
2. ✅ Sélectionner un SST → Seuls les chauffeurs de ce SST apparaissent
3. ✅ Changer le nombre de palettes → Les revenus se recalculent
4. ✅ Changer le SST → Les coûts se recalculent
5. ✅ Vérifier que la marge = revenus - coûts
6. ✅ Vérifier qu'on ne peut pas éditer manuellement les montants

---

## ⚡ Script de migration des données

Si des missions existent déjà avec des valeurs manuelles, créer un script pour recalculer:

```python
# migrations/recalculer_missions.py
from app.models import db, Mission
from app.utils.calculs import calculer_mission_complete

missions = Mission.query.all()
for mission in missions:
    if mission.voyage and mission.sst:
        calculs = calculer_mission_complete(
            mission.voyage,
            mission.palettes or 0,
            mission.sst
        )

        mission.type = calculs['type']
        mission.pays = calculs['pays']
        mission.revenus = calculs['revenus']
        mission.couts = calculs['couts']
        mission.marge = calculs['marge']
        mission.ramasse = (calculs['type'] == 'RAMASSE')

db.session.commit()
print(f"✓ {len(missions)} missions recalculées")
```

---

## 📝 Résumé des fichiers modifiés

1. ✅ **app/utils/calculs.py** - Créé (fonctions de calcul)
2. ✅ **app/routes/api.py** - Modifié (nouvelles routes API)
3. ⏳ **app/templates/planning/index.html** - À modifier (formulaire)
4. ⏳ **app/templates/chauffeurs/disponibilites.html** - À créer
5. ⏳ **app/routes/chauffeurs.py** - À modifier (route disponibilités)
6. ⏳ **migrations/recalculer_missions.py** - À créer (migration données)

---

## 🎯 Prochaines étapes

1. Modifier le template `planning/index.html` selon ce document
2. Créer la page de gestion des disponibilités
3. Tester sur le serveur de développement
4. Créer un script de migration pour recalculer les missions existantes
5. Déployer en production
