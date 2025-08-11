"""
Health check command for Automation Generator CLI
"""

import click
import os
import sys
import socket
from pathlib import Path

from ...core.config_manager import ConfigManager


@click.command('health')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed health information')
@click.pass_context
def health_command(ctx, verbose):
    """Perform system health checks"""
    
    config_manager = ctx.obj['config_manager']
    
    click.echo("🏥 Automation Generator Health Check")
    click.echo("=" * 50)
    
    checks = []
    
    # Configuration check
    config_status, config_msg = _check_configuration(config_manager, verbose)
    checks.append(("Configuration", config_status, config_msg))
    
    # Dependencies check  
    deps_status, deps_msg = _check_dependencies(verbose)
    checks.append(("Dependencies", deps_status, deps_msg))
    
    # API connectivity check
    api_status, api_msg = _check_api_connectivity(config_manager, verbose)
    checks.append(("API Connectivity", api_status, api_msg))
    
    # Database connectivity check
    db_status, db_msg = _check_database_connectivity(config_manager, verbose)
    checks.append(("Database Connectivity", db_status, db_msg))
    
    # Port availability check
    port_status, port_msg = _check_port_availability(config_manager, verbose)
    checks.append(("Port Availability", port_status, port_msg))
    
    # File permissions check
    perms_status, perms_msg = _check_file_permissions(config_manager, verbose)
    checks.append(("File Permissions", perms_status, perms_msg))
    
    # Display results
    passed = 0
    for name, status, message in checks:
        icon = "✅" if status else "❌"
        click.echo(f"{icon} {name}")
        
        if verbose or not status:
            click.echo(f"   {message}")
        
        if status:
            passed += 1
    
    click.echo()
    click.echo(f"Health Check Results: {passed}/{len(checks)} checks passed")
    
    if passed == len(checks):
        click.echo("🎉 All systems operational!")
        sys.exit(0)
    else:
        click.echo("⚠️  Some issues detected. Please address them before running the application.")
        sys.exit(1)


def _check_configuration(config_manager: ConfigManager, verbose: bool) -> tuple:
    """Check configuration validity"""
    try:
        if not config_manager.config_file.exists():
            return False, "Configuration file not found. Run 'automation-generator init'"
        
        is_valid, errors = config_manager.validate_config()
        
        if is_valid:
            config = config_manager.load_config()
            provider = config.get('llm', {}).get('provider', 'unknown')
            db_name = config.get('database', {}).get('database_name', 'unknown')
            return True, f"Valid configuration (Provider: {provider}, DB: {db_name})"
        else:
            error_summary = '; '.join(errors[:2])  # Show first 2 errors
            if len(errors) > 2:
                error_summary += f" (+{len(errors)-2} more)"
            return False, f"Configuration errors: {error_summary}"
        
    except Exception as e:
        return False, f"Configuration check failed: {str(e)}"


def _check_dependencies(verbose: bool) -> tuple:
    """Check required dependencies"""
    try:
        required_packages = [
            'streamlit',
            'pymongo', 
            'google-generativeai',
            'PyPDF2',
            'tenacity',
            'pyyaml',
            'click'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if not missing_packages:
            return True, f"All {len(required_packages)} required packages available"
        else:
            return False, f"Missing packages: {', '.join(missing_packages)}"
        
    except Exception as e:
        return False, f"Dependency check failed: {str(e)}"


def _check_api_connectivity(config_manager: ConfigManager, verbose: bool) -> tuple:
    """Check API connectivity"""
    try:
        from ...core.gemini_functions import GenerativeFunction
        
        # Try to initialize Gemini API
        try:
            gen_func = GenerativeFunction(config_manager)
            return True, "Gemini API connection successful"
        except ValueError as e:
            if "API key" in str(e):
                return False, "API key not configured or invalid"
            else:
                return False, f"API configuration error: {str(e)}"
        except Exception as e:
            return False, f"API connection failed: {str(e)}"
        
    except ImportError:
        return False, "Cannot test API connectivity (missing dependencies)"
    except Exception as e:
        return False, f"API check failed: {str(e)}"


def _check_database_connectivity(config_manager: ConfigManager, verbose: bool) -> tuple:
    """Check database connectivity"""
    try:
        from ...core.mongo_functions import MongoDB
        
        # Try to initialize MongoDB connection
        try:
            mongo_db = MongoDB(config_manager)
            stats = mongo_db.get_database_stats()
            
            if stats:
                db_name = stats.get('database_name', 'unknown')
                total_solutions = stats.get('total_solutions', 0)
                return True, f"MongoDB connection successful (DB: {db_name}, {total_solutions} solutions)"
            else:
                return False, "MongoDB connection established but stats unavailable"
                
        except ConnectionError as e:
            return False, f"MongoDB connection failed: {str(e)}"
        except ValueError as e:
            if "MongoDB URI" in str(e):
                return False, "MongoDB URI not configured"
            else:
                return False, f"MongoDB configuration error: {str(e)}"
        except Exception as e:
            return False, f"Database connection failed: {str(e)}"
        
    except ImportError:
        return False, "Cannot test database connectivity (missing dependencies)"
    except Exception as e:
        return False, f"Database check failed: {str(e)}"


def _check_port_availability(config_manager: ConfigManager, verbose: bool) -> tuple:
    """Check if configured port is available"""
    try:
        config = config_manager.load_config()
        port = config.get('app', {}).get('port', 8501)
        host = config.get('app', {}).get('host', 'localhost')
        
        # Try to bind to the port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            return True, f"Port {port} available on {host}"
        
    except OSError as e:
        if e.errno == 98:  # Address already in use
            return False, f"Port {port} already in use"
        else:
            return False, f"Port check failed: {str(e)}"
    except Exception as e:
        return False, f"Port availability check failed: {str(e)}"


def _check_file_permissions(config_manager: ConfigManager, verbose: bool) -> tuple:
    """Check file system permissions"""
    try:
        # Check if config directory is writable
        config_dir = config_manager.config_dir
        
        if not config_dir.exists():
            try:
                config_dir.mkdir(parents=True, exist_ok=True)
                return True, f"Config directory created successfully: {config_dir}"
            except PermissionError:
                return False, f"Cannot create config directory: {config_dir}"
        
        # Test write permissions
        test_file = config_dir / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
            return True, f"Config directory writable: {config_dir}"
        except PermissionError:
            return False, f"Config directory not writable: {config_dir}"
        
    except Exception as e:
        return False, f"File permission check failed: {str(e)}"