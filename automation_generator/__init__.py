"""
Automation Generator - AI-powered automation script generator from SOPs

A pip-installable package that transforms Standard Operating Procedures (SOPs)
into executable automation scripts using AI.
"""

__version__ = "1.0.0"
__author__ = "Automation Generator Team"
__email__ = "support@automation-generator.com"

from .core.config_manager import ConfigManager
from .utils.validators import InputValidator

__all__ = [
    "ConfigManager",
    "InputValidator",
    "__version__"
]