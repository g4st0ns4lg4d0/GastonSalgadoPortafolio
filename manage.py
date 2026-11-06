#!/usr/bin/env python
"""CLI del proyecto. Desarrollo usa SQLite salvo configuración explícita."""
import os
import sys
from pathlib import Path

import environ

if __name__ == "__main__":
    environ.Env.read_env(Path(__file__).resolve().parent / ".env", overwrite=False)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
