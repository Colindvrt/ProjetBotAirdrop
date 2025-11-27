"""
Funding Farming Bot - Main entry point.

A modern funding arbitrage bot with delta-neutral strategies.
Version 2.0 - Complete refactored architecture.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.app import FundingFarmingApp


def main():
    """Main entry point."""
    try:
        app = FundingFarmingApp()
        app.run()
    except ImportError as e:
        print(f"ERROR: Missing dependency - {e}")
        print("\nPlease install required packages:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
