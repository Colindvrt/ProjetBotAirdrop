import requests
import pandas as pd
from datetime import datetime

def get_hyperliquid_funding():
    """
    Récupère les taux de financement (funding rates) de Hyperliquid
    pour tous les actifs et les affiche.
    """
    print("Tentative de connexion à l'API d'Hyperliquid...")
    
    url = "https://api.hyperliquid.xyz/info"
    payload = {
        "type": "metaAndAssetCtxs"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() 
        data = response.json()
        
        # 4. Extraire les données pertinentes
        # data[0]['universe'] contient la liste des métadonnées (avec les noms)
        # data[1] contient la liste des contextes (avec le funding)
        
        if not data or len(data) < 2 or 'universe' not in data[0] or not data[1]:
            print("Structure de réponse API inattendue.")
            return

        asset_metadata = data[0]['universe'] # Liste des métadonnées (avec les noms)
        asset_contexts = data[1]             # Liste des contextes (avec le funding)
        
        # S'assurer que les listes ont la même taille
        if len(asset_metadata) != len(asset_contexts):
            print("Erreur : Les listes de métadonnées et de contextes ne correspondent pas.")
            return

        funding_data = []
        
        # 5. Boucler sur les contextes en utilisant 'enumerate' pour obtenir l'index
        for i, asset_context in enumerate(asset_contexts):
            
            # Utiliser l'index 'i' pour récupérer le nom depuis la liste de métadonnées
            pair_name = asset_metadata[i].get('name')
            
            # Récupérer le funding depuis le contexte (asset_context)
            hourly_funding_rate = float(asset_context.get('funding', 0))
            
            # 6. Calculer des métriques utiles
            funding_8h = hourly_funding_rate * 8
            apr = hourly_funding_rate * 24 * 365
            
            funding_data.append({
                "Paire": pair_name,
                "Funding (1h) %": hourly_funding_rate * 100,
                "Funding (8h) %": funding_8h * 100,
                "APR (Annualisé) %": apr * 100
            })

        # 7. Afficher les données avec Pandas
        df = pd.DataFrame(funding_data)
        
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        
        print(f"--- Taux de Funding Hyperliquid --- (au {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        
        # Filtrer les paires qui n'ont pas de nom (devrait plus arriver)
        df = df.dropna(subset=['Paire'])
        
        print("\nTOP Funding (Positif - bon pour short) :")
        print(df.sort_values(by="Funding (8h) %", ascending=False).head(10))
        
        print("\nTOP Funding (Négatif - bon pour long) :")
        print(df.sort_values(by="Funding (8h) %", ascending=True).head(10))

    except requests.exceptions.HTTPError as http_err:
        print(f"Erreur HTTP: {http_err} - {response.text}")
    except Exception as err:
        print(f"Une erreur est survenue: {err}")

# --- Point d'entrée du script ---
if __name__ == "__main__":
    get_hyperliquid_funding()