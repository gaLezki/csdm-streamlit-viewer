import os
LABELS = {
    'HLTV2': 'HLTV 2.0',
    'ADR': 'adr',
    'KAST-%': 'kast',
    'Kills': 'kill_count'
}
PRECISIONS = {
    'HLTV2': 2,
    'ADR': 1,
    'KAST-%': 1,
    'Kills': 0
}

WEAPON_COLORS = {
    'AK-47': '#800000', 'AUG': '#8B4513', 'AWP': '#6B4226', 'CZ75 Auto': '#8B008B',
    'Decoy Grenade': '#404040', 'Desert Eagle': '#B8860B', 'Dual Berettas': '#8B4513',
    'FAMAS': '#8B0000', 'Five-SeveN': '#008080', 'Flashbang': '#006400', 'Galil AR': '#4B0082',
    'Glock-18': '#004d00', 'HE Grenade': '#404040', 'Incendiary Grenade': '#8B0000', 'Knife': '#004d00',
    'M4A1': '#006400', 'M4A4': '#00008B', 'MAC-10': '#8B4513', 'Molotov': '#8B0000', 'MP5-SD': '#556B2F',
    'MP7': '#00008B', 'MP9': '#404040', 'Nova': '#4B0082', 'P2000': '#006400', 'P250': '#8B4513',
    'P90': '#8B4513', 'SG 553': '#8B4513', 'Smoke Grenade': '#404040', 'SSG 08': '#004d00', 'Tec-9': '#8B4513',
    'UMP-45': '#8B4513', 'USP-S': '#404040', 'XM1014': '#4B0082', 'Zeus x27': '#8B0000'
}

# One would think that these should change in the future, until then, let's go with this
SIDE_ID = {
    'CT': 3,
    'T': 2
}

PLAYER_COLUMN_RENAMES = {'name': 'Player', 'match_count': 'GP', 'kill_count': 'K', 
                         'death_count': 'D', 'assist_count': 'A', 'HLTV 2.0': 'HLTV2', 
                         'kast': 'KAST-%', 'adr': 'ADR', 'first_kill_count': 'K (entry)', 'first_death_count': 'D (entry)'}
ALL_MATCHES_COLUMN_RENAMES = {'checksum': 'Match ID', 'name_team_a': 'Team A', 'name_team_b': 'Team B', 'score_team_a': 'A', 'score_team_b': 'B'}
EXCEL_FILE_PATH = os.path.dirname(os.path.abspath(__file__)) + "/import/demo.xlsx"