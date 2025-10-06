"""Configuration management for AnyCRM."""
import json
import os
import secrets

CONFIG_FILE = "config.json"


def generate_api_key():
    """Generate a secure random API key."""
    return secrets.token_urlsafe(32)


DEFAULT_CONFIG = {
    "api_key": generate_api_key(),
    "base_url": "http://localhost:8000",
    "anyquest_api_key": "",
    "anyquest_api_url": "https://api.anyquest.ai"
}


def load_config():
    """Load configuration from file or create default."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        # Generate API key if missing or empty
        if not config.get("api_key"):
            config["api_key"] = generate_api_key()
            save_config(config)

        # Add base_url if missing (migration from webhook_base_url)
        if "base_url" not in config:
            config["base_url"] = config.get("webhook_base_url", "http://localhost:8000")
            save_config(config)

        return config
    else:
        default_config = DEFAULT_CONFIG.copy()
        default_config["api_key"] = generate_api_key()
        save_config(default_config)
        return default_config


def save_config(config):
    """Save configuration to file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def get_config():
    """Get current configuration."""
    return load_config()


def update_config(updates):
    """Update configuration with new values."""
    config = load_config()
    config.update(updates)
    save_config(config)
    return config
