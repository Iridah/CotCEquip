#!/usr/bin/env python3
"""
ingest_accessories_lua.py - Importa accesorios desde módulo Lua del fandom
Uso: python ingest_accessories_lua.py accesories.json
"""
import re
import sys
from pathlib import Path

from ingest_common import get_connection, parse_stat, clean_text