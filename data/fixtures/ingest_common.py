#!/usr/bin/env python3
from pathlib import Path

import environ
import psycopg2


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def get_env_path() -> Path:
    return get_project_root() / 'CotcEquip' / '.env'


def load_env():
    env = environ.Env()
    env_path = get_env_path()

    if not env_path.exists():
        raise FileNotFoundError(f"No se encontró el .env en: {env_path}")

    environ.Env.read_env(env_path)
    return env


def get_db_config():
    env = load_env()
    return {
        'dbname': env('DB_NAME'),
        'user': env('DB_USER'),
        'password': env('DB_PASSWORD'),
        'host': env('DB_HOST'),
        'port': int(env('DB_PORT', default=5432)),
    }


def get_connection():
    return psycopg2.connect(**get_db_config())


def parse_stat(val):
    if val is None:
        return 0

    val = str(val).strip().strip('"').replace('+', '').replace(',', '').strip()
    if not val:
        return 0

    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def clean_text(val):
    if not val:
        return ''
    return (
        str(val)
        .replace('<br>', '\n')
        .replace('br', '\n')
        .strip()
    )