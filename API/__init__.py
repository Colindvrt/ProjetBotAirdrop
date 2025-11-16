# Fichier: API/__init__.py

# --- Rend les fonctions de scan (funding) accessibles ---
try:
    from .hyperliquid_api import get_hyperliquid_funding_data
except ImportError:
    print("Avertissement: hyperliquid_api.py non trouvé")
    def get_hyperliquid_funding_data(): return []

try:
    from .paradex_api import get_paradex_funding_data
except ImportError:
    print("Avertissement: paradex_api.py non trouvé")
    def get_paradex_funding_data(): return []

try:
    from .lighter_api import get_lighter_funding_data
except ImportError:
    print("Avertissement: lighter_api.py non trouvé")
    def get_lighter_funding_data(): return []

try:
    from .extended_api import get_extended_funding_data
except ImportError:
    print("Avertissement: extended_api.py non trouvé")
    def get_extended_funding_data(): return []


# --- Rend les classes de trading (API) accessibles ---
try:
    from .hyperliquid_api import HyperliquidAPI
except ImportError:
    class HyperliquidAPI:
        def __init__(self, cfg): print("Erreur: Classe HyperliquidAPI non chargée")
        def get_account_balance(self): return None

try:
    from .paradex_api import ParadexAPI
except ImportError:
    class ParadexAPI:
        def __init__(self, cfg): print("Erreur: Classe ParadexAPI non chargée")
        def get_account_balance(self): return None

try:
    from .lighter_api import LighterAPI
except ImportError:
    class LighterAPI:
        def __init__(self, cfg): print("Erreur: Classe LighterAPI non chargée")
        def get_account_balance(self): return None

try:
    from .extended_api import ExtendedAPI
except ImportError:
    class ExtendedAPI:
        def __init__(self, cfg): print("Erreur: Classe ExtendedAPI non chargée")
        def get_account_balance(self): return None

print("Paquet API chargé.")