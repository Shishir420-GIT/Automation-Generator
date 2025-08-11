"""
Main CLI entry point for Automation Generator
"""

import click
import logging
import sys
from pathlib import Path

from ..core.config_manager import ConfigManager
from .commands import init, run, migrate, config, health


@click.group()
@click.version_option()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config-dir', type=click.Path(), help='Configuration directory path')
@click.pass_context
def cli(ctx, verbose, config_dir):
    """Automation Generator - AI-powered automation from SOPs"""
    
    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize context
    ctx.ensure_object(dict)
    ctx.obj['config_manager'] = ConfigManager(Path(config_dir) if config_dir else None)
    ctx.obj['verbose'] = verbose


# Register all commands
cli.add_command(init.init_command)
cli.add_command(run.run_command)
cli.add_command(migrate.migrate_command)
cli.add_command(migrate.migration_status_command)
cli.add_command(config.config_command)
cli.add_command(health.health_command)


def main():
    """Main entry point for CLI"""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n❌ Interrupted by user", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()