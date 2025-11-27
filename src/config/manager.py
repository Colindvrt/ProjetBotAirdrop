"""
Configuration manager for the Funding Farming Bot.

Handles loading, saving, and validation of configuration data (API keys, etc.).
"""

import json
import os
import shutil
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime


class ConfigManager:
    """
    Manages application configuration, including API keys and settings.

    The configuration is stored in config.json in the project root directory.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_path: Path to config.json. If None, uses default path in project root.
        """
        if config_path is None:
            # Default to config.json in project root (2 levels up from this file)
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config.json"

        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from config.json.

        Returns:
            Dictionary containing configuration data.
        """
        if not self.config_path.exists():
            # Create empty config if it doesn't exist
            return self._create_default_config()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except json.JSONDecodeError as e:
            print(f"Error loading config.json: {e}")
            print("Creating backup and using default config...")
            self._backup_config()
            return self._create_default_config()
        except Exception as e:
            print(f"Unexpected error loading config: {e}")
            return self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """
        Create default configuration structure.

        Returns:
            Default configuration dictionary.
        """
        default_config = {
            "hyperliquid": {
                "secret": ""
            },
            "paradex": {
                "key": "",
                "secret": ""
            },
            "lighter": {
                "key": "",
                "account_index": "0",
                "api_key_index": "2"
            },
            "extended": {
                "api_key": "",
                "public_key": "",
                "private_key": "",
                "vault_id": ""
            }
        }

        # Save default config
        self.save_config(default_config)
        return default_config

    def _backup_config(self):
        """
        Create a backup of the current config file.
        """
        if self.config_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.config_path.parent / f"config.json.bak.{timestamp}"
            try:
                shutil.copy2(self.config_path, backup_path)
                print(f"Config backup created: {backup_path}")
            except Exception as e:
                print(f"Failed to create backup: {e}")

    def save_config(self, config: Optional[Dict[str, Any]] = None):
        """
        Save configuration to config.json.

        Args:
            config: Configuration to save. If None, saves current self.config.
        """
        if config is not None:
            self.config = config

        # Create backup before saving
        if self.config_path.exists():
            self._backup_config()

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print(f"Configuration saved to {self.config_path}")
        except Exception as e:
            print(f"Error saving config: {e}")
            raise

    def get_platform_config(self, platform_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific platform.

        Args:
            platform_name: Name of the platform (e.g., "hyperliquid", "paradex")

        Returns:
            Platform-specific configuration dictionary.
        """
        platform_key = platform_name.lower()
        return self.config.get(platform_key, {})

    def set_platform_config(self, platform_name: str, config: Dict[str, Any]):
        """
        Set configuration for a specific platform.

        Args:
            platform_name: Name of the platform
            config: Configuration dictionary for the platform
        """
        platform_key = platform_name.lower()
        self.config[platform_key] = config

    def update_platform_field(self, platform_name: str, field: str, value: str):
        """
        Update a specific field in a platform's configuration.

        Args:
            platform_name: Name of the platform
            field: Field to update (e.g., "secret", "key")
            value: New value for the field
        """
        platform_key = platform_name.lower()
        if platform_key not in self.config:
            self.config[platform_key] = {}
        self.config[platform_key][field] = value

    def validate_platform_config(self, platform_name: str) -> tuple[bool, Optional[str]]:
        """
        Validate configuration for a specific platform.

        Args:
            platform_name: Name of the platform

        Returns:
            Tuple of (is_valid, error_message)
        """
        platform_key = platform_name.lower()
        platform_config = self.config.get(platform_key, {})

        if not platform_config:
            return False, f"No configuration found for {platform_name}"

        # Platform-specific validation
        if platform_key == "hyperliquid":
            if not platform_config.get("secret"):
                return False, "Hyperliquid: missing 'secret' (private key)"
            if len(platform_config.get("secret", "")) < 10:
                return False, "Hyperliquid: 'secret' appears invalid"

        elif platform_key == "paradex":
            if not platform_config.get("key"):
                return False, "Paradex: missing 'key' (wallet address)"
            if not platform_config.get("secret"):
                return False, "Paradex: missing 'secret' (JWT token)"

        elif platform_key == "lighter":
            if not platform_config.get("key"):
                return False, "Lighter: missing 'key' (API private key)"
            if not platform_config.get("account_index"):
                return False, "Lighter: missing 'account_index'"
            if not platform_config.get("api_key_index"):
                return False, "Lighter: missing 'api_key_index'"

        elif platform_key == "extended":
            required_fields = ["api_key", "public_key", "private_key", "vault_id"]
            for field in required_fields:
                if not platform_config.get(field):
                    return False, f"Extended: missing '{field}'"

        else:
            return False, f"Unknown platform: {platform_name}"

        return True, None

    def is_platform_configured(self, platform_name: str) -> bool:
        """
        Check if a platform has valid configuration.

        Args:
            platform_name: Name of the platform

        Returns:
            True if platform is properly configured, False otherwise.
        """
        is_valid, _ = self.validate_platform_config(platform_name)
        return is_valid

    def get_configured_platforms(self) -> list[str]:
        """
        Get list of all properly configured platforms.

        Returns:
            List of platform names that are configured.
        """
        platforms = ["hyperliquid", "paradex", "lighter", "extended"]
        return [p for p in platforms if self.is_platform_configured(p)]

    def clear_platform_config(self, platform_name: str):
        """
        Clear configuration for a specific platform.

        Args:
            platform_name: Name of the platform
        """
        platform_key = platform_name.lower()
        if platform_key in self.config:
            # Reset to empty structure
            if platform_key == "hyperliquid":
                self.config[platform_key] = {"secret": ""}
            elif platform_key == "paradex":
                self.config[platform_key] = {"key": "", "secret": ""}
            elif platform_key == "lighter":
                self.config[platform_key] = {
                    "key": "",
                    "account_index": "0",
                    "api_key_index": "2"
                }
            elif platform_key == "extended":
                self.config[platform_key] = {
                    "api_key": "",
                    "public_key": "",
                    "private_key": "",
                    "vault_id": ""
                }

    def export_config(self, export_path: str, include_secrets: bool = False):
        """
        Export configuration to a file.

        Args:
            export_path: Path to export config
            include_secrets: If False, redacts sensitive information
        """
        export_data = self.config.copy()

        if not include_secrets:
            # Redact sensitive fields
            for platform in export_data.values():
                for key in platform:
                    if key in ["secret", "key", "private_key", "api_key"]:
                        platform[key] = "***REDACTED***"

        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=4, ensure_ascii=False)

    def __repr__(self) -> str:
        """String representation of the config manager."""
        configured = self.get_configured_platforms()
        return f"ConfigManager(path={self.config_path}, configured_platforms={configured})"


# Global instance for easy access
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """
    Get the global configuration manager instance.

    Returns:
        Global ConfigManager instance.
    """
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager


def reset_config_manager():
    """
    Reset the global configuration manager.

    Useful for testing or when config file location changes.
    """
    global _global_config_manager
    _global_config_manager = None
