"""
Init command for Automation Generator CLI
"""

import click
import os
from pathlib import Path
from typing import Optional

from ...core.config_manager import ConfigManager


@click.command('init')
@click.option('--config-dir', type=click.Path(), help='Configuration directory path')
@click.option('--force', is_flag=True, help='Overwrite existing configuration')
@click.option('--interactive', '-i', is_flag=True, default=True, help='Interactive setup')
@click.pass_context
def init_command(ctx, config_dir: Optional[str], force: bool, interactive: bool):
    """Initialize new Automation Generator installation"""
    
    config_manager = ctx.obj['config_manager']
    if config_dir:
        config_manager.config_dir = Path(config_dir)
    
    click.echo("🚀 Welcome to Automation Generator Setup!")
    click.echo()
    
    # Check if config already exists
    if config_manager.config_file.exists() and not force:
        click.echo(f"⚠️  Configuration already exists at: {config_manager.config_file}")
        if not click.confirm("Do you want to overwrite it?"):
            click.echo("Setup cancelled.")
            return
    
    # Create config directory
    click.echo(f"📁 Configuration directory: {config_manager.config_dir}")
    if config_manager.ensure_config_dir():
        click.echo("✅ Created configuration directory")
    else:
        click.echo("❌ Failed to create configuration directory")
        return
    
    if interactive:
        # Interactive setup
        config = _interactive_setup()
    else:
        # Non-interactive setup with defaults
        config = _default_setup()
    
    # Save configuration
    if config_manager.save_config(config):
        click.echo(f"✅ Configuration saved to {config_manager.config_file}")
        
        # Validate configuration
        is_valid, errors = config_manager.validate_config()
        if is_valid:
            click.echo("✅ Configuration validation passed")
        else:
            click.echo("⚠️  Configuration validation warnings:")
            for error in errors:
                click.echo(f"   • {error}")
        
        click.echo()
        click.echo("🚀 You're all set! Next steps:")
        click.echo("   1. Set your API keys in environment variables or config file")
        click.echo("   2. Run 'automation-generator migrate' to set up database")
        click.echo("   3. Run 'automation-generator run' to start the application")
        
    else:
        click.echo("❌ Failed to save configuration")


def _interactive_setup() -> dict:
    """Interactive configuration setup"""
    config = {
        "version": "1.0",
        "llm": {},
        "database": {},
        "app": {},
        "features": {},
        "security": {},
        "advanced": {}
    }
    
    click.echo("🔑 LLM Provider Setup:")
    providers = ["gemini", "openai", "claude"]
    provider = click.prompt(
        "Select your preferred LLM provider",
        type=click.Choice(providers),
        default="gemini"
    )
    config["llm"]["provider"] = provider
    
    if provider == "gemini":
        api_key_env = "GEMINI_API_KEY"
        default_model = "gemini-1.5-flash"
    elif provider == "openai":
        api_key_env = "OPENAI_API_KEY"
        default_model = "gpt-4"
    else:  # claude
        api_key_env = "CLAUDE_API_KEY"
        default_model = "claude-3-sonnet"
    
    # Check if environment variable exists
    api_key = os.environ.get(api_key_env)
    if api_key:
        click.echo(f"✅ Found {api_key_env} in environment")
        config["llm"]["api_key"] = f"${{{api_key_env}}}"
    else:
        click.echo(f"⚠️  {api_key_env} not found in environment")
        if click.confirm(f"Do you want to set {api_key_env} now?"):
            api_key = click.prompt(f"Enter your {provider} API key", hide_input=True)
            config["llm"]["api_key"] = api_key
        else:
            config["llm"]["api_key"] = f"${{{api_key_env}}}"
            click.echo(f"💡 Remember to set {api_key_env} environment variable later")
    
    config["llm"]["model"] = default_model
    
    click.echo()
    click.echo("💾 Database Setup:")
    mongodb_uri = os.environ.get("MONGODB_URI")
    if mongodb_uri:
        click.echo("✅ Found MONGODB_URI in environment")
        config["database"]["mongodb_uri"] = "${MONGODB_URI}"
    else:
        click.echo("⚠️  MONGODB_URI not found in environment")
        if click.confirm("Do you want to set MongoDB URI now?"):
            mongodb_uri = click.prompt("Enter your MongoDB URI")
            config["database"]["mongodb_uri"] = mongodb_uri
        else:
            config["database"]["mongodb_uri"] = "${MONGODB_URI}"
            click.echo("💡 Remember to set MONGODB_URI environment variable later")
    
    config["database"]["database_name"] = click.prompt(
        "Database name", default="automation_generator"
    )
    config["database"]["collections"] = {
        "solutions": "solutions",
        "ratings": "ratings",
        "users": "users",
        "analytics": "analytics"
    }
    
    click.echo()
    click.echo("🎨 Application Preferences:")
    config["app"]["host"] = click.prompt("Host", default="localhost")
    config["app"]["port"] = click.prompt("Port", type=int, default=8501)
    config["app"]["theme"] = click.prompt(
        "Theme", type=click.Choice(["light", "dark", "auto"]), default="light"
    )
    config["app"]["debug"] = click.confirm("Enable debug mode?", default=False)
    config["app"]["log_level"] = "DEBUG" if config["app"]["debug"] else "INFO"
    config["app"]["max_file_size_mb"] = 20
    config["app"]["session_timeout_hours"] = 24
    
    click.echo()
    click.echo("🚀 Feature Configuration:")
    config["features"]["enable_community"] = click.confirm("Enable community features?", default=True)
    config["features"]["enable_ratings"] = click.confirm("Enable ratings?", default=True)
    config["features"]["enable_analytics"] = click.confirm("Enable analytics?", default=True)
    config["features"]["enable_multi_language"] = click.confirm("Enable multi-language support?", default=True)
    config["features"]["enable_visualizations"] = click.confirm("Enable visualizations?", default=True)
    config["features"]["enable_api"] = click.confirm("Enable REST API?", default=False)
    
    # Security settings
    config["security"]["require_auth"] = False
    config["security"]["allowed_domains"] = []
    config["security"]["rate_limiting"] = True
    config["security"]["max_requests_per_hour"] = 100
    
    # Advanced settings
    config["advanced"]["cache_enabled"] = True
    config["advanced"]["cache_ttl_hours"] = 24
    config["advanced"]["background_tasks"] = True
    config["advanced"]["telemetry_enabled"] = click.confirm("Enable anonymous telemetry?", default=True)
    
    return config


def _default_setup() -> dict:
    """Default configuration setup without interaction"""
    return {
        "version": "1.0",
        "llm": {
            "provider": "gemini",
            "api_key": "${GEMINI_API_KEY}",
            "model": "gemini-1.5-flash",
            "backup_providers": []
        },
        "database": {
            "mongodb_uri": "${MONGODB_URI}",
            "database_name": "automation_generator",
            "collections": {
                "solutions": "solutions",
                "ratings": "ratings",
                "users": "users",
                "analytics": "analytics"
            }
        },
        "app": {
            "host": "localhost",
            "port": 8501,
            "theme": "light",
            "debug": False,
            "log_level": "INFO",
            "max_file_size_mb": 20,
            "session_timeout_hours": 24
        },
        "features": {
            "enable_community": True,
            "enable_ratings": True,
            "enable_analytics": True,
            "enable_multi_language": True,
            "enable_visualizations": True,
            "enable_api": False
        },
        "security": {
            "require_auth": False,
            "allowed_domains": [],
            "rate_limiting": True,
            "max_requests_per_hour": 100
        },
        "advanced": {
            "cache_enabled": True,
            "cache_ttl_hours": 24,
            "background_tasks": True,
            "telemetry_enabled": True
        }
    }