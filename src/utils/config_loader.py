"""
Configuration Loader Module
Handles loading and parsing YAML configuration files
"""

import yaml
from pathlib import Path
from typing import Dict, Any
import logging


class ConfigLoader:
    """Load and parse YAML configuration files"""

    def __init__(self, config_path: str):
        """
        Initialize config loader

        Args:
            config_path: Path to main config.yaml file
        """
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)

        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

    def load(self) -> Dict[str, Any]:
        """
        Load main configuration file

        Returns:
            Dictionary containing configuration
        """
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        self.logger.info(f"Loaded configuration from {self.config_path}")

        # Load medication mapping
        config['medication_mapping'] = self._load_medication_mapping()

        # Load data quality rules
        config['data_quality_rules'] = self._load_data_quality_rules()

        return config

    def _load_medication_mapping(self) -> Dict[str, Any]:
        """Load medication code mapping from YAML"""
        mapping_path = self.config_path.parent / 'medication_mapping.yaml'

        if not mapping_path.exists():
            self.logger.warning(f"Medication mapping file not found: {mapping_path}")
            return {}

        with open(mapping_path, 'r') as f:
            mapping_data = yaml.safe_load(f)

        self.logger.info(f"Loaded medication mapping: {len(mapping_data.get('medications', {}))} medications")

        return mapping_data.get('medications', {})

    def _load_data_quality_rules(self) -> Dict[str, Any]:
        """Load data quality validation rules from YAML"""
        rules_path = self.config_path.parent / 'data_quality_rules.yaml'

        if not rules_path.exists():
            self.logger.warning(f"Data quality rules file not found: {rules_path}")
            return {}

        with open(rules_path, 'r') as f:
            rules_data = yaml.safe_load(f)

        self.logger.info("Loaded data quality rules")

        return rules_data.get('validation_rules', {})

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key

        Args:
            key: Configuration key (supports dot notation, e.g., 'bigquery.project_id')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        config = self.load()

        keys = key.split('.')
        value = config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

            if value is None:
                return default

        return value
