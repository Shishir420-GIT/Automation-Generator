"""
Run command for Automation Generator CLI
"""

import click
import subprocess
import sys
import os
import time
from pathlib import Path

from ...core.config_manager import ConfigManager


@click.command('run')
@click.option('--host', help='Host to bind to')
@click.option('--port', type=int, help='Port to bind to')
@click.option('--config', type=click.Path(exists=True), help='Config file path')
@click.option('--no-browser', is_flag=True, help='Don\'t open browser automatically')
@click.option('--dev', is_flag=True, help='Development mode (auto-reload)')
@click.pass_context
def run_command(ctx, host, port, config, no_browser, dev):
    """Start the Automation Generator application"""
    
    config_manager = ctx.obj['config_manager']
    
    # Load configuration
    if config:
        # Use specified config file
        config_manager.config_file = Path(config)
    
    app_config = config_manager.load_config()
    
    # Validate configuration first
    click.echo("🔍 Validating configuration...")
    is_valid, errors = config_manager.validate_config()
    
    if not is_valid:
        click.echo("❌ Configuration validation failed:")
        for error in errors:
            click.echo(f"   • {error}")
        click.echo()
        click.echo("💡 Fix these issues or run 'automation-generator config validate' for details")
        return
    
    click.echo("✅ Configuration validation passed")
    
    # Override config with command line options
    final_host = host or app_config.get('app', {}).get('host', 'localhost')
    final_port = port or app_config.get('app', {}).get('port', 8501)
    
    # Prepare Streamlit secrets
    streamlit_secrets = config_manager.get_streamlit_config()
    
    # Create temporary secrets file
    secrets_dir = config_manager.config_dir / ".streamlit"
    secrets_dir.mkdir(exist_ok=True)
    secrets_file = secrets_dir / "secrets.toml"
    
    try:
        with open(secrets_file, 'w') as f:
            for key, value in streamlit_secrets.items():
                if value:  # Only write non-empty values
                    f.write(f'{key} = "{value}"\n')
        
        click.echo(f"📝 Created Streamlit secrets at: {secrets_file}")
        
        # Find the app file location
        package_dir = Path(__file__).parent.parent.parent
        app_file = package_dir / "core" / "app.py"
        
        if not app_file.exists():
            click.echo(f"❌ Application file not found: {app_file}")
            click.echo(f"   Looked in: {package_dir}")
            click.echo(f"   Package dir contents: {list(package_dir.iterdir()) if package_dir.exists() else 'Directory not found'}")
            return
        
        # Prepare Streamlit command
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            str(app_file),
            "--server.headless", "true", 
            "--server.port", str(final_port),
            "--server.address", final_host
        ]
        
        if no_browser:
            cmd.extend(["--server.runOnSave", "false"])
        
        # Set environment variables
        env = os.environ.copy()
        env['AUTOMATION_GENERATOR_CONFIG_DIR'] = str(config_manager.config_dir)
        
        # Development mode
        if dev:
            cmd.extend(["--server.runOnSave", "true"])
            env['AUTOMATION_GENERATOR_DEV'] = "1"
        
        click.echo(f"🚀 Starting Automation Generator on http://{final_host}:{final_port}")
        click.echo("   Press Ctrl+C to stop the server")
        click.echo()
        
        # Start the application
        try:
            process = subprocess.run(cmd, env=env, cwd=str(package_dir))
            if process.returncode != 0:
                click.echo(f"❌ Application exited with code: {process.returncode}")
        except KeyboardInterrupt:
            click.echo("\n🛑 Stopping application...")
        except Exception as e:
            click.echo(f"❌ Failed to start application: {str(e)}")
        
    finally:
        # Clean up secrets file
        try:
            if secrets_file.exists():
                secrets_file.unlink()
                click.echo("🧹 Cleaned up temporary secrets file")
        except Exception as e:
            click.echo(f"⚠️  Warning: Could not clean up secrets file: {e}")


@click.command('dev')
@click.pass_context  
def dev_command(ctx):
    """Start in development mode with auto-reload"""
    ctx.invoke(run_command, dev=True)