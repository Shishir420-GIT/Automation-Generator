"""
Migration command for Automation Generator CLI
"""

import click
from typing import Optional

from ...core.config_manager import ConfigManager
from ...migrations.base_migration import MigrationManager


@click.command('migrate')
@click.option('--direction', type=click.Choice(['up', 'down']), default='up', 
              help='Migration direction')
@click.option('--version', help='Target migration version')
@click.option('--dry-run', is_flag=True, help='Show what would be migrated without executing')
@click.option('--force', is_flag=True, help='Force migration even if already applied')
@click.pass_context
def migrate_command(ctx, direction: str, version: Optional[str], dry_run: bool, force: bool):
    """Database migration and schema management"""
    
    config_manager = ctx.obj['config_manager']
    
    # Validate configuration first
    click.echo("🔍 Validating configuration...")
    is_valid, errors = config_manager.validate_config()
    
    if not is_valid:
        click.echo("❌ Configuration validation failed:")
        for error in errors:
            click.echo(f"   • {error}")
        click.echo("💡 Run 'automation-generator config validate' for more details")
        return
    
    try:
        # Initialize migration manager
        migration_manager = MigrationManager(config_manager)
        
        click.echo("📊 Database Migration Tool")
        click.echo("=" * 40)
        
        if dry_run:
            click.echo("🔍 DRY RUN MODE - No changes will be made")
            click.echo()
        
        # Show current migration status
        current_version = migration_manager.get_current_version()
        available_migrations = migration_manager.get_available_migrations()
        
        click.echo(f"Current database version: {current_version or 'None (fresh database)'}")
        click.echo(f"Available migrations: {len(available_migrations)}")
        
        if not available_migrations:
            click.echo("❌ No migration files found")
            return
        
        # Determine target version
        if version:
            target_version = version
        else:
            if direction == 'up':
                # Default to latest version
                target_version = max(available_migrations.keys())
            else:
                # Default to previous version  
                target_version = migration_manager.get_previous_version(current_version)
        
        click.echo(f"Target version: {target_version}")
        click.echo()
        
        # Get migration plan
        if direction == 'up':
            migrations_to_run = migration_manager.get_pending_migrations(target_version)
            action = "apply"
        else:
            migrations_to_run = migration_manager.get_rollback_migrations(current_version, target_version)
            action = "rollback"
        
        if not migrations_to_run:
            click.echo(f"✅ Database is already at target version {target_version}")
            return
        
        click.echo(f"📋 Migrations to {action}:")
        for migration_version in migrations_to_run:
            migration = available_migrations.get(migration_version)
            if migration:
                click.echo(f"   • {migration_version}: {migration.description}")
        
        click.echo()
        
        if dry_run:
            click.echo("🔍 DRY RUN - Migration plan shown above")
            return
        
        # Confirm migration
        if not force:
            if not click.confirm(f"Proceed with {action}ing {len(migrations_to_run)} migration(s)?"):
                click.echo("Migration cancelled.")
                return
        
        # Execute migrations
        click.echo(f"🚀 Starting database migration...")
        
        success_count = 0
        for migration_version in migrations_to_run:
            click.echo(f"   Executing {migration_version}...")
            
            try:
                if direction == 'up':
                    result = migration_manager.apply_migration(migration_version)
                else:
                    result = migration_manager.rollback_migration(migration_version)
                
                if result:
                    click.echo(f"   ✅ {migration_version} completed")
                    success_count += 1
                else:
                    click.echo(f"   ❌ {migration_version} failed")
                    break
                    
            except Exception as e:
                click.echo(f"   ❌ {migration_version} failed: {str(e)}")
                break
        
        if success_count == len(migrations_to_run):
            click.echo(f"🎉 Migration completed successfully! ({success_count}/{len(migrations_to_run)} migrations)")
            
            # Show final status
            final_version = migration_manager.get_current_version()
            click.echo(f"   Database version: {final_version}")
            
        else:
            click.echo(f"⚠️  Migration partially completed ({success_count}/{len(migrations_to_run)} migrations)")
            click.echo("   Database may be in an inconsistent state")
            click.echo("   Review logs and consider rolling back")
        
    except Exception as e:
        click.echo(f"❌ Migration failed: {str(e)}")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()


@click.command('migration-status')
@click.pass_context
def migration_status_command(ctx):
    """Show current migration status"""
    
    config_manager = ctx.obj['config_manager']
    
    try:
        migration_manager = MigrationManager(config_manager)
        
        current_version = migration_manager.get_current_version()
        available_migrations = migration_manager.get_available_migrations()
        pending_migrations = migration_manager.get_pending_migrations()
        
        click.echo("📊 Migration Status")
        click.echo("=" * 30)
        click.echo(f"Current Version: {current_version or 'None'}")
        click.echo(f"Available Migrations: {len(available_migrations)}")
        click.echo(f"Pending Migrations: {len(pending_migrations)}")
        
        if pending_migrations:
            click.echo()
            click.echo("Pending migrations:")
            for version in pending_migrations:
                migration = available_migrations.get(version)
                desc = migration.description if migration else "Unknown"
                click.echo(f"   • {version}: {desc}")
        else:
            click.echo()
            click.echo("✅ Database is up to date")
        
    except Exception as e:
        click.echo(f"❌ Failed to get migration status: {str(e)}")


# Migration status command will be added in main.py to avoid circular imports