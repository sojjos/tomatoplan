"""
Fonctions utilitaires pour les calculs financiers des missions
"""
from app.models import db, RevenuPalette, TarifSST, Voyage


def calculer_revenu(voyage_code, palettes):
    """
    Calcule le revenu d'une mission basé sur le voyage et le nombre de palettes

    Args:
        voyage_code: Code du voyage
        palettes: Nombre de palettes

    Returns:
        float: Revenu calculé
    """
    if not voyage_code or palettes is None:
        return 0.0

    # Rechercher le tarif correspondant dans la table revenus_palettes
    revenu_palette = RevenuPalette.query.filter(
        RevenuPalette.voyage == voyage_code,
        RevenuPalette.palettes_min <= palettes,
        RevenuPalette.palettes_max >= palettes
    ).first()

    if revenu_palette:
        return float(revenu_palette.revenu)

    return 0.0


def calculer_cout(sst_nom, voyage_code):
    """
    Calcule le coût d'une mission basé sur le SST et le voyage

    Args:
        sst_nom: Nom du SST
        voyage_code: Code du voyage

    Returns:
        float: Coût calculé
    """
    if not sst_nom or not voyage_code:
        return 0.0

    # Importer ici pour éviter les imports circulaires
    from app.models import SST

    # Trouver le SST
    sst = SST.query.filter_by(nom=sst_nom).first()
    if not sst:
        return 0.0

    # Rechercher le tarif pour ce SST et ce voyage
    tarif = TarifSST.query.filter_by(
        sst_id=sst.id,
        voyage=voyage_code
    ).first()

    if tarif:
        return float(tarif.tarif)

    return 0.0


def get_type_voyage(voyage_code):
    """
    Récupère le type du voyage (LIVRAISON, RAMASSE, etc.)

    Args:
        voyage_code: Code du voyage

    Returns:
        str: Type du voyage ou 'LIVRAISON' par défaut
    """
    if not voyage_code:
        return 'LIVRAISON'

    voyage = Voyage.query.filter_by(code=voyage_code).first()
    if voyage and voyage.type:
        return voyage.type

    return 'LIVRAISON'


def get_pays_voyage(voyage_code):
    """
    Récupère le pays du voyage

    Args:
        voyage_code: Code du voyage

    Returns:
        str: Pays du voyage ou 'Belgique' par défaut
    """
    if not voyage_code:
        return 'Belgique'

    voyage = Voyage.query.filter_by(code=voyage_code).first()
    if voyage and voyage.country:
        return voyage.country

    return 'Belgique'


def calculer_mission_complete(voyage_code, palettes, sst_nom):
    """
    Calcule tous les paramètres financiers d'une mission

    Args:
        voyage_code: Code du voyage
        palettes: Nombre de palettes
        sst_nom: Nom du SST

    Returns:
        dict: {
            'type': str,
            'pays': str,
            'revenus': float,
            'couts': float,
            'marge': float
        }
    """
    type_mission = get_type_voyage(voyage_code)
    pays = get_pays_voyage(voyage_code)
    revenus = calculer_revenu(voyage_code, palettes)
    couts = calculer_cout(sst_nom, voyage_code)
    marge = revenus - couts

    return {
        'type': type_mission,
        'pays': pays,
        'revenus': round(revenus, 2),
        'couts': round(couts, 2),
        'marge': round(marge, 2)
    }
