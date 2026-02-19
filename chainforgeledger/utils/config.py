"""
ChainForgeLedger Configuration Module

Configuration management for blockchain operations.
"""

import configparser
import json
import os
from typing import Any, Dict


class Config:
    """
    Configuration manager for ChainForgeLedger.
    
    Handles configuration loading, validation, and management.
    """
    
    DEFAULT_CONFIG = {
        "network": {
            "node_id": "chainforgeledger-node",
            "host": "localhost",
            "port": 8080,
            "peers": [],
            "network_id": "chainforgeledger-mainnet"
        },
        "blockchain": {
            "name": "ChainForgeLedger",
            "version": "1.0.0",
            "block_time": 60,
            "difficulty": 4,
            "max_blocks": 1000000,
            "block_size_limit": 1048576,
            "transaction_fee": 0.01
        },
        "consensus": {
            "algorithm": "pow",
            "difficulty_adjustment": 10,
            "target_block_time": 60
        },
        "storage": {
            "db_path": "chainforgeledger.db",
            "backup_path": "backups",
            "max_backups": 7,
            "auto_backup": False
        },
        "security": {
            "mining_reward": 50,
            "difficulty_adjustment_block": 100,
            "max_transaction_size": 1024
        },
        "api": {
            "enabled": True,
            "host": "0.0.0.0",
            "port": 8080,
            "cors": True,
            "debug": False
        },
        "logging": {
            "level": "INFO",
            "log_dir": "logs",
            "console_log": True,
            "file_log": True
        },
        "features": {
            "smart_contracts": False,
            "governance": False,
            "tokens": False,
            "stablecoins": False,
            "oracles": False
        }
    }
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_path:
            self.load(config_path)
    
    def load(self, config_path: str = None) -> bool:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            True if configuration loaded successfully
        """
        try:
            if not config_path:
                config_path = self.config_path
            
            if not config_path or not os.path.exists(config_path):
                return False
            
            config_ext = os.path.splitext(config_path)[1].lower()
            
            if config_ext == '.json':
                self._load_json(config_path)
            elif config_ext in ('.ini', '.cfg', '.config'):
                self._load_ini(config_path)
            elif config_ext == '.yaml' or config_ext == '.yml':
                self._load_yaml(config_path)
            else:
                raise ValueError(f"Unsupported configuration format: {config_ext}")
            
            return True
            
        except Exception as e:
            print(f"Failed to load configuration: {e}")
            return False
    
    def _load_json(self, config_path: str):
        """Load JSON configuration file."""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self._merge_config(config)
    
    def _load_ini(self, config_path: str):
        """Load INI configuration file."""
        config = configparser.ConfigParser()
        config.read(config_path)
        
        config_dict = {}
        for section in config.sections():
            config_dict[section] = dict(config[section])
        
        self._merge_config(config_dict)
    
    def _load_yaml(self, config_path: str):
        """Load YAML configuration file."""
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self._merge_config(config)
        
        except ImportError:
            print("PyYAML module not installed, cannot load YAML configuration")
            raise
    
    def _merge_config(self, config: Dict):
        """Merge loaded configuration into default configuration."""
        for section, settings in config.items():
            if section in self.config:
                self.config[section].update(settings)
            else:
                self.config[section] = settings
    
    def save(self, config_path: str = None):
        """
        Save configuration to file.
        
        Args:
            config_path: Path to configuration file
        """
        try:
            if not config_path:
                config_path = self.config_path
            
            if not config_path:
                raise ValueError("No configuration path specified")
            
            config_dir = os.path.dirname(config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            config_ext = os.path.splitext(config_path)[1].lower()
            
            if config_ext == '.json':
                self._save_json(config_path)
            elif config_ext in ('.ini', '.cfg', '.config'):
                self._save_ini(config_path)
            elif config_ext == '.yaml' or config_ext == '.yml':
                self._save_yaml(config_path)
            else:
                raise ValueError(f"Unsupported configuration format: {config_ext}")
            
        except Exception as e:
            print(f"Failed to save configuration: {e}")
            raise
    
    def _save_json(self, config_path: str):
        """Save configuration as JSON file."""
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)
    
    def _save_ini(self, config_path: str):
        """Save configuration as INI file."""
        config = configparser.ConfigParser()
        
        for section, settings in self.config.items():
            config[section] = {
                key: str(value) for key, value in settings.items()
            }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
    
    def _save_yaml(self, config_path: str):
        """Save configuration as YAML file."""
        try:
            import yaml
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False)
        
        except ImportError:
            print("PyYAML module not installed, cannot save YAML configuration")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key (can use dot notation like 'network.port')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        try:
            value = self.config
            
            for part in key.split('.'):
                value = value.get(part)
                if value is None:
                    return default
            
            return value
            
        except Exception as e:
            print(f"Failed to get configuration value: {e}")
            return default
    
    def set(self, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key: Configuration key (can use dot notation like 'network.port')
            value: Value to set
        """
        try:
            config = self.config
            
            parts = key.split('.')
            for part in parts[:-1]:
                if part not in config:
                    config[part] = {}
                config = config[part]
            
            config[parts[-1]] = value
            self.config_changed()
            
        except Exception as e:
            print(f"Failed to set configuration value: {e}")
            raise
    
    def has(self, key: str) -> bool:
        """
        Check if configuration key exists.
        
        Args:
            key: Configuration key (can use dot notation like 'network.port')
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            value = self.config
            
            for part in key.split('.'):
                value = value.get(part)
                if value is None:
                    return False
            
            return True
            
        except Exception as e:
            return False
    
    def get_section(self, section: str) -> Dict:
        """
        Get entire configuration section.
        
        Args:
            section: Section name
            
        Returns:
            Section configuration or empty dictionary
        """
        return self.config.get(section, {})
    
    def set_section(self, section: str, settings: Dict):
        """
        Set entire configuration section.
        
        Args:
            section: Section name
            settings: Section configuration
        """
        self.config[section] = settings
        self.config_changed()
    
    def validate(self) -> bool:
        """
        Validate configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Validate network settings
            if self.get('network.host', '') == '':
                return False
            
            if not isinstance(self.get('network.port', 0), int) or not (0 < self.get('network.port') < 65536):
                return False
            
            # Validate blockchain settings
            if self.get('blockchain.name', '') == '':
                return False
            
            if not isinstance(self.get('blockchain.block_time', 0), (int, float)) or self.get('blockchain.block_time') <= 0:
                return False
            
            # Validate consensus settings
            valid_algorithms = ['pow', 'pos', 'poa']
            if self.get('consensus.algorithm') not in valid_algorithms:
                return False
            
            # Validate security settings
            if not isinstance(self.get('security.mining_reward', 0), (int, float)) or self.get('security.mining_reward') < 0:
                return False
            
            return True
            
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False
    
    def reset(self):
        """Reset configuration to default values."""
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_changed()
    
    def config_changed(self):
        """Callback when configuration changes."""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return self.config.copy()
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.config, indent=2)
    
    def load_env_variables(self, prefix: str = 'CHAINFORGEL'):
        """
        Load configuration from environment variables.
        
        Args:
            prefix: Environment variable prefix
        """
        prefix = prefix.upper()
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix) + 1:].lower()
                self.set(config_key, self._parse_env_value(value))
    
    def _parse_env_value(self, value: str):
        """Parse environment variable value to appropriate type."""
        if value.lower() in ['true', 'yes', 'on']:
            return True
        if value.lower() in ['false', 'no', 'off']:
            return False
        
        try:
            return int(value)
        except ValueError:
            pass
        
        try:
            return float(value)
        except ValueError:
            pass
        
        return value
    
    def __getitem__(self, key: str):
        """Get configuration value using dictionary syntax."""
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any):
        """Set configuration value using dictionary syntax."""
        self.set(key, value)
    
    def __contains__(self, key: str):
        """Check if configuration key exists."""
        return self.has(key)
    
    def __str__(self):
        """String representation."""
        return self.to_json()
    
    def __repr__(self):
        """Debug representation."""
        return f"Config(path={self.config_path})"
    
    @classmethod
    def from_dict(cls, config: Dict) -> 'Config':
        """
        Create configuration from dictionary.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Config instance
        """
        instance = cls()
        instance._merge_config(config)
        return instance
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Config':
        """
        Create configuration from JSON string.
        
        Args:
            json_str: JSON string
            
        Returns:
            Config instance
        """
        return cls.from_dict(json.loads(json_str))
    
    @classmethod
    def create_default_config(cls, config_path: str) -> 'Config':
        """
        Create and save default configuration.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Config instance
        """
        config = cls(config_path)
        config.save(config_path)
        return config
