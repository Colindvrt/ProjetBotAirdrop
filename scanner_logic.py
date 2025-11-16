# Fichier: scanner_logic.py
import pandas as pd
import re
from datetime import datetime

# --- IMPORTS CORRIGÉS ---
# On dit à Python de regarder dans le paquet 'API'
from API import (
    get_hyperliquid_funding_data,
    get_paradex_funding_data,
    get_lighter_funding_data,
    get_extended_funding_data
)
# --- FIN DES CORRECTIONS ---


# --- FONCTION STANDARDISATION (Inchangée) ---
def standardize_pair_name(pair_str):
    if pair_str is None: return None
    match = re.match(r"^[A-Z0-9]+", pair_str)
    if match: return match.group(0)
    return pair_str

# --- FONCTION CALCUL DES SPREADS (Inchangée) ---
def find_funding_opportunities(all_data):
    if not all_data:
        print("Aucune donnée fournie à la fonction de calcul.")
        return pd.DataFrame() 
    print(f"Total: {len(all_data)} points de données. Calcul des spreads...")
    df = pd.DataFrame(all_data)
    if df.empty:
        return pd.DataFrame()
    df['pair_std'] = df['pair'].apply(standardize_pair_name)
    df = df.drop_duplicates(subset=['pair_std', 'platform'])
    df_pivot_rates = df.pivot(index='pair_std', columns='platform', values='rate_1h')
    df_pivot_leverage = df.pivot(index='pair_std', columns='platform', values='max_leverage').fillna(1)
    min_rates = df_pivot_rates.min(axis=1)
    max_rates = df_pivot_rates.max(axis=1)
    min_platforms = df_pivot_rates.idxmin(axis=1)
    max_platforms = df_pivot_rates.idxmax(axis=1)
    df_final = pd.DataFrame({
        'long_platform': min_platforms,
        'long_rate': min_rates,
        'short_platform': max_platforms,
        'short_rate': max_rates
    }).reset_index()
    leverage_lookup = df_pivot_leverage.to_dict('index')
    df_final['Levier Long'] = df_final.apply(
        lambda row: int(leverage_lookup.get(row['pair_std'], {}).get(row['long_platform'], 1)), axis=1
    )
    df_final['Levier Short'] = df_final.apply(
        lambda row: int(leverage_lookup.get(row['pair_std'], {}).get(row['short_platform'], 1)), axis=1
    )
    df_final['spread_1h'] = df_final['short_rate'] - df_final['long_rate']
    df_final = df_final[df_final['long_platform'] != df_final['short_platform']]
    df_final = df_final[df_final['spread_1h'] > 0]
    df_final['spread_1h_%'] = df_final['spread_1h'] * 100
    df_final['spread_8h_%'] = df_final['spread_1h_%'] * 8
    df_final['Min Levier'] = df_final[['Levier Long', 'Levier Short']].min(axis=1)
    df_final['Score (1h)'] = df_final['spread_1h_%'] * df_final['Min Levier']
    df_final['Score (8h)'] = df_final['spread_8h_%'] * df_final['Min Levier']
    df_final = df_final.sort_values(by='Score (1h)', ascending=False)
    df_final['long_rate_%'] = df_final['long_rate'] * 100
    df_final['short_rate_%'] = df_final['short_rate'] * 100
    df_final = df_final.rename(columns={
        'pair_std': 'Paire', 'long_platform': 'Long Sur', 'short_platform': 'Short Sur',
        'long_rate_%': 'Taux Long (1h)', 'short_rate_%': 'Taux Short (1h)',
        'spread_1h_%': 'Spread (1h)', 'spread_8h_%': 'Spread (8h)'
    })
    print("Calcul des spreads terminé.")
    return df_final[[
        'Paire', 'Score (1h)', 'Spread (1h)', 'Min Levier',
        'Long Sur', 'Levier Long', 'Taux Long (1h)', 
        'Short Sur', 'Levier Short', 'Taux Short (1h)',
        'Score (8h)', 'Spread (8h)' 
    ]].head(25)