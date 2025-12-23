import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

class AppConfig:
    _instance = None
    _config: Dict[str, Any] = {}
    _base_dir: Path = Path('.') # Default to current directory
    _config_file_name: str = "config.yaml"

    def __new__(cls, base_dir: Path = Path('.')):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            # Set base_dir and config_path immediately on the new instance
            cls._instance._base_dir = base_dir
            cls._instance._config_path = base_dir / "config" / cls._config_file_name
            cls._instance._load_config()
        # If instance already exists, ensure its base_dir matches or raise an error/warning
        # For this application, base_dir should be consistent once set.
        elif cls._instance._base_dir != base_dir:
            print(f"Warning: AppConfig already initialized with base_dir={cls._instance._base_dir}, "
                  f"ignoring new base_dir={base_dir}. Singleton must be initialized once.")
        return cls._instance

    def _load_config(self):
        if not self._config_path.exists():
            print(f"Warning: Configuration file not found at {self._config_path}. Using default settings.")
            self._config = self._get_default_config()
            self._save_config() # Save default config if not found
            return

        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {{}}
            # Merge with defaults to ensure all keys are present
            default_config = self._get_default_config()
            self._config = {{**default_config, **self._config}}
        except yaml.YAMLError as e:
            print(f"Error loading configuration from {self._config_path}: {{e}}. Using default settings.")
            self._config = self._get_default_config()
        except Exception as e:
            print(f"An unexpected error occurred while loading config: {{e}}. Using default settings.")
            self._config = self._get_default_config()

    def _save_config(self):
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self._config, f, indent=2)
        except Exception as e:
            print(f"Error saving default configuration to {self._config_path}: {{e}}.")

    def _get_default_config(self) -> Dict[str, Any]:
        """Define sensible default configuration settings."""
        return {
            "scanner": {
                "max_concurrent_requests": 10,
                "request_timeout": 30,
                "user_agents": [], # Will be populated by code for rotation
                "proxies": [], # Will be loaded from config
                "ssl_verify": True,
            },
            "database": {
                "path": "data/social_scan.db"
            },
            "logging": {
                "level": "INFO",
                "file": "logs/handyosint.log"
            },
            "ui": {
                "default_banner_scheme": "HEAT_WAVE",
                "default_menu_scheme": "GREEN_PLASMA"
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        parts = key.split('.')
        current = self._config
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        
        # Resolve paths relative to base_dir if they are config paths
        if key in ['database.path', 'logging.file'] and isinstance(current, str):
            # Ensure the path is relative to the config file's location, which is then relative to base_dir
            # The path in config.yaml is relative to the project root (where config.yaml is)
            return self._base_dir / Path(current)
        
        return current

    def set(self, key: str, value: Any):
        parts = key.split('.')
        current = self._config
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                current[part] = value
            elif part not in current or not isinstance(current[part], dict):
                current[part] = {{}}
            current = current[part]
        self._save_config() # Save changes immediately



# Example usage (for internal testing/demo)
if __name__ == "__main__":
    # Create a dummy config file for testing
    dummy_config_path = Path("config/test_config.yaml")
    with open(dummy_config_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump({
            "scanner": {
                "max_concurrent_requests": 5,
                "proxies": ["http://testproxy.com:8080"],
                "ssl_verify": False
            },
            "database": {
                "path": "data/test_db.db"
            }
        }, f)
    
    # Temporarily override config path for test
    AppConfig._config_path = dummy_config_path
    
    # Reload config from dummy file
    config = AppConfig()
    config._load_config()

    print(f"Max concurrent requests: {config.get('scanner.max_concurrent_requests')}")
    print(f"Proxies: {config.get('scanner.proxies')}")
    print(f"SSL Verify: {config.get('scanner.ssl_verify')}")
    print(f"DB Path: {config.get('database.path')}")

    # Clean up dummy file
    dummy_config_path.unlink()
    
    # Reset to original config path and reload
    AppConfig._config_path = Path("config/config.yaml")
    AppConfig._instance = None # Force recreation to load original config
    config = AppConfig()
    print("\n--- Loaded original config ---")
    print(f"Max concurrent requests: {config.get('scanner.max_concurrent_requests')}")
    print(f"Proxies: {config.get('scanner.proxies')}")
    print(f"SSL Verify: {config.get('scanner.ssl_verify')}")
    
    config.set('scanner.request_timeout', 60)
    print(f"Updated request timeout: {config.get('scanner.request_timeout')}")
    
    # Verify it was saved
    reloaded_config = AppConfig()
    reloaded_config._load_config()
    print(f"Reloaded config timeout: {reloaded_config.get('scanner.request_timeout')}")
