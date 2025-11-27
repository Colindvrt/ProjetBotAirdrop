import requests
import pandas as pd
from datetime import datetime

def get_aster_funding():
    """
    Récupère les taux de financement (funding rates) actuels de Aster
    via l'endpoint /markPrice.
    """
    print("Tentative de connexion à l'API d'Aster...")
    
    # 1. L'URL de base et l'endpoint trouvés dans la documentation
    # (https://docs.asterdex.com/product/aster-perpetual-pro/api/api-documentation)
    url = "https://fapi.asterdex.com/fapi/v1/markPrice"
    
    try:
        # 2. Exécuter la requête GET (endpoint public)
        response = requests.get(url)
        response.raise_for_status() 
        
        data = response.json()
        
        # 3. La réponse est une LISTE d'objets (un par paire)
        markets_list = data
        
        if not markets_list:
            print("Aucune donnée de marché trouvée dans la réponse d'Aster.")
            return

        funding_data = []
        
        # 4. Boucler sur chaque marché (paire)
        for market_data in markets_list:
            
            pair_name = market_data.get('symbol')
            
            # 5. Extraire le taux de funding
            # Sur les API de type Binance, le taux de funding 8h
            # s'appelle 'lastFundingRate'
            funding_8h_rate = float(market_data.get('lastFundingRate', 0))
            
            # 6. Calculer les autres métriques
            # Le taux est déjà pour 8h, on le convertit en 1h et en APR
            hourly_funding_rate = funding_8h_rate / 8
            apr = funding_8h_rate * 3 * 365 # 3 périodes de 8h par jour
            
            funding_data.append({
                "Paire": pair_name,
                "Funding (1h) %": hourly_funding_rate * 100,
                "Funding (8h) %": funding_8h_rate * 100,
                "APR (Annualisé) %": apr * 100
            })

        # 7. Afficher les données avec Pandas
        df = pd.DataFrame(funding_data)
        
        if df.empty:
            print("Aucune donnée de funding n'a été trouvée.")
            return

        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        
        print(f"--- Taux de Funding Aster --- (au {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        
        print("\nTOP Funding (Positif - bon pour short) :")
        print(df.sort_values(by="Funding (8h) %", ascending=False).head(10))
        
        print("\nTOP Funding (Négatif - bon pour long) :")
        print(df.sort_values(by="Funding (8h) %", ascending=True).head(10))

    except requests.exceptions.HTTPError as http_err:
        print(f"Erreur HTTP: {http_err} - {http_err.response.text}")
    except Exception as err:
        print(f"Une erreur est survenue: {err}")

# --- Point d'entrée du script ---
if __name__ == "__main__":
    get_aster_funding()