"""
config.py — Configurações centrais e cliente Airtable compartilhado
"""
import os
import logging
from functools import wraps
from flask import request, jsonify
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("centro_comando")

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY", "")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID", "")
WEBHOOK_SECRET   = os.environ.get("WEBHOOK_SECRET", "")

airtable = Api(AIRTABLE_API_KEY)

def get_table(nome: str):
    return airtable.table(AIRTABLE_BASE_ID, nome)

def requer_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Webhook-Secret", "")
        if WEBHOOK_SECRET and token != WEBHOOK_SECRET:
            return jsonify({"status": "error", "message": "Não autorizado"}), 401
        return f(*args, **kwargs)
    return wrapper

def resposta(data=None, message="ok", status="ok", code=200):
    return jsonify({"status": status, "message": message, "data": data or {}}), code

def erro(message: str, code: int = 500):
    logger.error(message)
    return jsonify({"status": "error", "message": message, "data": {}}), code
