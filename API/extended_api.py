# Fichier: API/extended_api.py
import requests
import re
import time
import hmac
import hashlib
import json
from urllib.parse import urlencode

# --- PARTIE 1 : Fonctions de Scan (CORRIGÉ) ---

def get_extended_funding_data():
    """
    [EXTENDED - APPEL UNIQUE] (Vrai code)
    Appelle /info/markets et parse la réponse pour le taux et le levier.
    """
    print("-> Appel API Extended (/api/v1/info/markets)...")
    url = "https://api.extended.exchange/api/v1/info/markets" # <-- L'URL CORRIGÉE
    headers = {"accept": "application/json"}
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # La structure est {"status":"OK","data":[...]}
        markets_list = data.get('data', []) 
        
        if not markets_list: 
            print("Erreur Extended (E1): clé 'data' vide ou introuvable.")
            return []

        funding_data = []
        for market_data in markets_list: 
            # On ne garde que les marchés actifs qui sont visibles
            if not market_data.get('active', False) or not market_data.get('visibleOnUi', False):
                continue
                
            pair_name_api = market_data.get('name') # Ex: 'ENA-USD'
            
            stats = market_data.get('marketStats', {})
            config = market_data.get('tradingConfig', {})
            
            hourly_funding_rate_str = stats.get('fundingRate')
            max_leverage_str = config.get('maxLeverage')

            # On s'assure que c'est un PERP en vérifiant que ces clés existent
            if hourly_funding_rate_str is not None and max_leverage_str is not None:
                try:
                    hourly_funding_rate = float(hourly_funding_rate_str)
                    max_leverage = int(float(max_leverage_str)) 
                    
                    match = re.match(r"^[A-Z0-9]+", pair_name_api)
                    pair_name_std = match.group(0) if match else pair_name_api
                    
                    funding_data.append({
                        "pair": pair_name_std, 
                        "rate_1h": hourly_funding_rate, # L'API le donne en 1h
                        "platform": "Extended",
                        "max_leverage": max_leverage
                    })
                except (ValueError, TypeError):
                    print(f"Skipping Extended pair {pair_name_api} due to invalid data.")
                    
        print(f"Extended: {len(funding_data)} paires trouvées.")
        return funding_data
    except Exception as e:
        print(f"Erreur Extended: {e}")
        return []

# --- PARTIE 2 : Classe de Trading (CORRIGÉ) ---

class ExtendedAPI:
    """
    Classe pour gérer la connexion et le trading sur Extended.
    (Implémentation réelle de la connexion)
    """
    def __init__(self, api_config):
        print("[Extended Trader] Initialisation...")
        self.base_url = "https://api.extended.exchange"
        self.api_key = api_config.get("key")
        self.api_secret = api_config.get("secret")
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Clé API ou Secret non trouvée pour Extended.")
        
        self.time_offset = 0 # Initialise à 0
        self.get_server_time_offset() # Synchronise l'heure
        
        print("[Extended Trader] Initialisation terminée.")

    # --- CORRIGÉ : Déplacé AVANT __init__ ---
    def get_server_time_offset(self):
        """
        Appelle l'endpoint PUBLIC /public/time pour synchroniser notre horloge
        avec celle du serveur.
        """
        try:
            print("[Extended Trader] Synchronisation de l'heure...")
            # --- CORRECTION : Utilise le bon endpoint public ---
            # L'ancien (/public/time) était faux (404)
            # Nous utilisons /api/v1/info/time (trouvé en cherchant)
            url = self.base_url + "/api/v1/info/time"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            server_time = int(response.json()['data']['serverTime'])
            local_time = int(time.time() * 1000)
            self.time_offset = server_time - local_time
            print(f"[Extended Trader] Décalage horaire calculé: {self.time_offset} ms")
        except Exception as e:
            print(f"[ERREUR Extended] Échec de la synchronisation de l'heure: {e}. On continue avec 0 offset.")
            self.time_offset = 0

    def _send_signed_request(self, method, endpoint, params={}):
        """
        Fonction privée pour créer une signature HMAC et envoyer la requête.
        (Version corrigée avec synchronisation de l'heure)
        """
        query_params = params.copy()
        
        # Utilise l'heure synchronisée
        timestamp = str(int(time.time() * 1000) + self.time_offset)
        query_params['timestamp'] = timestamp
        query_params['recvWindow'] = 5000 
        
        query_string = urlencode(query_params)
        
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        query_string += f"&signature={signature}"
        
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        url = self.base_url + endpoint + "?" + query_string
        
        try:
            if method == 'POST':
                response = requests.post(url, headers=headers, data="{}", timeout=10)
            else: # GET
                response = requests.get(url, headers=headers, timeout=10)
                
            response.raise_for_status() 
            return response.json()
            
        except requests.exceptions.HTTPError as http_err:
            print(f"[ERREUR API Extended] {http_err.response.status_code} - {http_err.response.text}")
            try:
                error_data = http_err.response.json()
                if error_data.get('code') == -1021:
                    print("[ERREUR SIGNATURE] Timestamp expiré. L'horloge de ton PC est peut-être désynchronisée.")
                    self.get_server_time_offset() # Tente de resynchroniser
            except:
                pass 
            return None
        except Exception as e:
            print(f"[ERREUR API Extended] {e}")
            return None

    def get_account_balance(self):
        """
        [TEST API] Récupère le solde du compte (réel).
        Appelle GET /api/v1/account/balance
        """
        print("[Extended Trader] Appel de get_account_balance (réel)...")
        
        data = self._send_signed_request('GET', '/api/v1/account/balance')
        
        if data and 'total_collateral_balance' in data:
            return float(data['total_collateral_balance'])
        elif data:
             print(f"[ERREUR Extended] Clé 'total_collateral_balance' non trouvée: {data}")
             return None
        else:
            return None