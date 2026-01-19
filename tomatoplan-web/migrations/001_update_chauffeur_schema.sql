-- Migration pour mettre à jour le schéma de la table chauffeurs
-- Date: 2026-01-19
-- Description: Ajoute les colonnes prenom, telephone et remplace sst par sst_id

-- ATTENTION: Faites une sauvegarde de votre base de données AVANT d'exécuter ce script!
-- Commande de sauvegarde: cp instance/tomatoplan.db instance/tomatoplan.db.backup_$(date +%Y%m%d_%H%M%S)

BEGIN TRANSACTION;

-- Étape 1: Créer une nouvelle table temporaire avec le nouveau schéma
CREATE TABLE chauffeurs_new (
    id TEXT PRIMARY KEY,
    nom TEXT NOT NULL UNIQUE,
    prenom TEXT,
    sst_id INTEGER,
    telephone TEXT,
    actif INTEGER DEFAULT 1,
    infos TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (sst_id) REFERENCES sst (id)
);

-- Étape 2: Copier les données existantes de l'ancienne table vers la nouvelle
-- Si vous avez déjà des données avec une colonne 'sst' (texte), il faut les convertir en sst_id
INSERT INTO chauffeurs_new (id, nom, prenom, sst_id, telephone, actif, infos, created_at, updated_at)
SELECT
    c.id,
    c.nom,
    NULL as prenom,  -- Les chauffeurs existants n'ont pas de prénom
    s.id as sst_id,  -- Convertir le nom SST en ID
    NULL as telephone,  -- Les chauffeurs existants n'ont pas de téléphone
    c.actif,
    c.infos,
    c.created_at,
    c.updated_at
FROM chauffeurs c
LEFT JOIN sst s ON c.sst = s.nom;  -- Joindre avec la table SST pour obtenir l'ID

-- Étape 3: Supprimer l'ancienne table
DROP TABLE chauffeurs;

-- Étape 4: Renommer la nouvelle table
ALTER TABLE chauffeurs_new RENAME TO chauffeurs;

-- Étape 5: Recréer les index
CREATE INDEX ix_chauffeurs_nom ON chauffeurs (nom);
CREATE INDEX ix_chauffeurs_sst_id ON chauffeurs (sst_id);
CREATE INDEX ix_chauffeurs_actif ON chauffeurs (actif);

COMMIT;

-- Vérification
SELECT 'Migration terminée. Vérification:' as message;
SELECT COUNT(*) as total_chauffeurs FROM chauffeurs;
SELECT COUNT(*) as chauffeurs_avec_sst FROM chauffeurs WHERE sst_id IS NOT NULL;
