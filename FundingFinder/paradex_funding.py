import requests
import pandas as pd
from datetime import datetime

def get_paradex_period_map():
    """
    [APPEL 1 - STATIQUE]
    Appelle /markets (SANS paramètre) pour créer une carte : 
    Symbole -> Période de funding
    Ex: {'ETH-USD-PERP': 8, 'FF-USD-PERP': 1}
    """
    print("Étape 1: Appel de /markets (pour les périodes)...")
    
    url = "https://api.prod.paradex.trade/v1/markets"
    headers = {"accept": "application/json"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        markets_list = data.get('results', []) 
        
        period_map = {}
        if not markets_list:
            print("Erreur Paradex: n'a pas pu récupérer la carte des périodes (clé 'results' vide).")
            return None

        # Boucler sur la LISTE
        for market_data in markets_list: 
            pair_name = market_data.get('symbol')
            
            # --- LA CORRECTION EST ICI ---
            # La clé est 'asset_kind', pas 'market_type'
            if market_data.get('asset_kind') == 'PERP':
                
                period = int(market_data.get('funding_period_hours', 1))
                if period == 0: period = 1 # Sécurité
                period_map[pair_name] = period
        
        print(f"Étape 1: OK. Carte de {len(period_map)} périodes créée.")
        return period_map
        
    except requests.exceptions.HTTPError as http_err:
        print(f"Erreur HTTP Étape 1: {http_err} - {http_err.response.text}")
        return None
    except Exception as err:
        print(f"Erreur Étape 1: {err}")
        return None

def get_paradex_rates(period_map):
    """
    [APPEL 2 - DYNAMIQUE]
    Appelle /markets/summary (AVEC paramètre) pour obtenir les taux actuels
    et les combine avec la carte des périodes.
    """
    print("Étape 2: Appel de /markets/summary (pour les taux)...")
    
    url = "https://api.prod.paradex.trade/v1/markets/summary"
    params = {"market": "ALL"}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status() 
        data = response.json()
        
        markets_list = data.get('results', [])
        if not markets_list:
            print("Erreur Étape 2: n'a pas pu récupérer les taux (clé 'results' vide).")
            return None
            
        print("Étape 2: OK. Taux récupérés.")
        funding_data = []
        
        for market_data in markets_list:
            pair_name = market_data.get('symbol', '')
            
            # Utiliser la carte pour trouver la période de cette paire
            funding_period = period_map.get(pair_name)
            
            if funding_period: # Si la paire est dans notre carte (donc c'est un PERP)
                
                rate_for_period = float(market_data.get('funding_rate', 0))
                
                # Normaliser en taux 1h
                hourly_funding_rate = rate_for_period / funding_period
                
                funding_data.append({
                    "Paire": pair_name,
                    "Taux (API)": rate_for_period,
                    "Période (h)": funding_period,
                    "Funding (1h) %": hourly_funding_rate * 100,
                    "Funding (8h) %": (hourly_funding_rate * 8) * 100
                })
        
        return pd.DataFrame(funding_data)

    except requests.exceptions.HTTPError as http_err:
        print(f"Erreur HTTP Étape 2: {http_err} - {http_err.response.text}")
        return None
    except Exception as err:
        print(f"Erreur Étape 2: {err}")
        return None

# --- Point d'entrée du script ---
if __name__ == "__main__":
    
    # Étape 1: Construire la carte
    period_map = get_paradex_period_map()
    
    if period_map:
        # Étape 2: Récupérer les taux et calculer
        df = get_paradex_rates(period_map)
        
        if df is not None and not df.empty:
            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 1000)
            
            print(f"\n--- Taux de Funding Paradex (Corrigés) --- (au {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
            
            print("\nTOP Funding (Positif - bon pour short) :")
            print(df.sort_values(by="Funding (8h) %", ascending=False).head(10))
            
            print("\nTOP Funding (Négatif - bon pour long) :")
            print(df.sort_values(by="Funding (8h) %", ascending=True).head(10))
        else:
            print("Échec du calcul des taux.")