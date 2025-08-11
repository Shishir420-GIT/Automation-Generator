"""
Config command for Automation Generator CLI
"""

import click
import yaml
from pathlib import Path

from ...core.config_manager import ConfigManager


@click.group('config')
@click.pass_context
def config_command(ctx):
    """Configuration management commands"""
    pass


@config_command.command('show')
@click.option('--key', help='Show specific configuration key (supports dot notation)')
@click.option('--format', type=click.Choice(['yaml', 'json']), default='yaml', help='Output format')
@click.pass_context
def show_config(ctx, key, format):
    """Display current configuration"""
    
    config_manager = ctx.obj['config_manager']
    
    if not config_manager.config_file.exists():
        click.echo("❌ Configuration file not found. Run 'automation-generator init' first.")
        return
    
    config = config_manager.load_config()
    
    if key:
        value = config_manager.get(key)
        if value is None:
            click.echo(f"❌ Configuration key '{key}' not found")
            return
        
        click.echo(f"{key}: {value}")
    else:
        if format == 'yaml':
            click.echo(yaml.dump(config, default_flow_style=False, indent=2))
        else:
            import json
            click.echo(json.dumps(config, indent=2))


@config_command.command('set')
@click.argument('key')
@click.argument('value')
@click.pass_context
def set_config(ctx, key, value):
    """Set configuration value (supports dot notation)"""
    
    config_manager = ctx.obj['config_manager']
    
    # Try to parse value as appropriate type
    parsed_value = _parse_value(value)
    
    if config_manager.set(key, parsed_value):
        click.echo(f"✅ Set {key} = {parsed_value}")
    else:
        click.echo(f"❌ Failed to set configuration key: {key}")


@config_command.command('get')
@click.argument('key')
@click.pass_context
def get_config(ctx, key):
    """Get configuration value (supports dot notation)"""
    
    config_manager = ctx.obj['config_manager']
    
    value = config_manager.get(key)
    if value is None:
        click.echo(f"❌ Configuration key '{key}' not found")
        return
    
    click.echo(f"{key}: {value}")


@config_command.command('validate')
@click.pass_context
def validate_config(ctx):
    """Validate current configuration"""
    
    config_manager = ctx.obj['config_manager']
    
    if not config_manager.config_file.exists():
        click.echo("❌ Configuration file not found. Run 'automation-generator init' first.")
        return
    
    click.echo("🔍 Validating configuration...")
    
    is_valid, errors = config_manager.validate_config()
    
    if is_valid:
        click.echo("✅ Configuration is valid")
        
        # Show configuration summary
        config = config_manager.load_config()
        click.echo()
        click.echo("📋 Configuration Summary:")
        click.echo(f"   Config file: {config_manager.config_file}")
        click.echo(f"   LLM Provider: {config.get('llm', {}).get('provider', 'Not set')}")
        click.echo(f"   Database: {config.get('database', {}).get('database_name', 'Not set')}")
        click.echo(f"   App Port: {config.get('app', {}).get('port', 'Not set')}")
        
    else:
        click.echo("❌ Configuration validation failed:")
        for error in errors:
            click.echo(f"   • {error}")
        
        click.echo()
        click.echo("💡 Common fixes:")
        click.echo("   • Set API keys in environment variables")
        click.echo("   • Verify MongoDB URI format")
        click.echo("   • Check port availability")


@config_command.command('edit')
@click.pass_context
def edit_config(ctx):
    """Open configuration file in default editor"""
    
    config_manager = ctx.obj['config_manager']
    
    if not config_manager.config_file.exists():
        click.echo("❌ Configuration file not found. Run 'automation-generator init' first.")
        return
    
    try:
        import os
        os.system(f'"{os.environ.get("EDITOR", "nano")}" "{config_manager.config_file}"')
    except Exception as e:
        click.echo(f"❌ Failed to open editor: {str(e)}")
        click.echo(f"💡 You can manually edit: {config_manager.config_file}")


@config_command.command('reset')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def reset_config(ctx, confirm):
    """Reset configuration to defaults"""
    
    config_manager = ctx.obj['config_manager']
    
    if not confirm:
        if not click.confirm("⚠️  This will reset your configuration to defaults. Continue?"):
            click.echo("Reset cancelled.")
            return
    
    if config_manager.config_file.exists():
        config_manager.config_file.unlink()
    
    # Recreate default configuration
    if config_manager.create_config_template():
        click.echo("✅ Configuration reset to defaults")
        click.echo(f"📝 Edit configuration at: {config_manager.config_file}")
    else:
        click.echo("❌ Failed to reset configuration")


@config_command.command('path')
@click.pass_context
def show_config_path(ctx):
    """Show configuration file path"""
    
    config_manager = ctx.obj['config_manager']
    
    click.echo(f"Configuration directory: {config_manager.config_dir}")
    click.echo(f"Configuration file: {config_manager.config_file}")
    click.echo(f"Log directory: {config_manager.log_dir}")
    
    if config_manager.config_file.exists():
        click.echo("✅ Configuration file exists")
    else:
        click.echo("❌ Configuration file not found")


def _parse_value(value_str: str):
    """Parse string value to appropriate Python type"""
    
    # Boolean values
    if value_str.lower() in ('true', 'yes', 'on', '1'):
        return True
    elif value_str.lower() in ('false', 'no', 'off', '0'):
        return False
    
    # Numeric values
    try:
        # Try integer first
        if '.' not in value_str:
            return int(value_str)
        else:
            return float(value_str)
    except ValueError:
        pass
    
    # JSON-like values
    if value_str.startswith(('[', '{')):
        try:
            import json
            return json.loads(value_str)
        except json.JSONDecodeError:
            pass
    
    # String value (default)
    return value_str