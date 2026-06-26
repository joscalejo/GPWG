"""
Diagnóstico de timeout y conectividad con google-genai SDK.
Ejecutar con: python diag.py --api-key TU_CLAVE
"""
import argparse
import time

from google import genai
from google.genai import types
from google.genai.errors import APIError

parser = argparse.ArgumentParser()
parser.add_argument("--api-key", required=True)
args = parser.parse_args()

# ── Test 1: Verificar qué modelos existen ──────────────────────────────────────
print("=" * 60)
print("TEST 1: Listando modelos disponibles (flash/lite)...")
print("=" * 60)
try:
    client = genai.Client(api_key=args.api_key)
    for model in client.models.list():
        name = model.name or ""
        if "flash" in name.lower() or "lite" in name.lower():
            print(f"  + {name}")
except APIError as e:
    print(f"  ERROR listando modelos: {e.code} / {e.status} - {e.message}")
except Exception as e:
    print(f"  ERROR: {type(e).__name__}: {e}")

# ── Test 2: Llamada simple con timeout=60 a gemini-2.0-flash-lite ──────────────
print("\n" + "=" * 60)
print("TEST 2: Llamada simple con timeout=60 a gemini-2.0-flash-lite...")
print("=" * 60)
try:
    client60 = genai.Client(
        api_key=args.api_key,
        http_options=types.HttpOptions(timeout=60)
    )
    t0 = time.time()
    resp = client60.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents="Di 'hola' y nada mas.",
    )
    elapsed = time.time() - t0
    print(f"  OK Respuesta en {elapsed:.2f}s: {resp.text}")
except Exception as e:
    elapsed = time.time() - t0
    print(f"  FAIL Error tras {elapsed:.2f}s: {type(e).__name__}: {e}")

# ── Test 3: Llamada simple con timeout=60 a gemini-3.1-flash-lite ──────────────
print("\n" + "=" * 60)
print("TEST 3: Llamada simple con timeout=60 a gemini-3.1-flash-lite...")
print("=" * 60)
try:
    t0 = time.time()
    resp = client60.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents="Di 'hola' y nada mas.",
    )
    elapsed = time.time() - t0
    print(f"  OK Respuesta en {elapsed:.2f}s: {resp.text}")
except Exception as e:
    elapsed = time.time() - t0
    print(f"  FAIL Error tras {elapsed:.2f}s: {type(e).__name__}: {e}")

# ── Test 4: Llamada con response_schema a gemini-3.1-flash-lite ────────────────
print("\n" + "=" * 60)
print("TEST 4: Llamada con response_schema + system_instruction...")
print("=" * 60)
try:
    from typing import List, TypedDict

    class Token(TypedDict):
        valor: str
        tipo: str
        score: int
        razon: str

    class Result(TypedDict):
        tokens: List[Token]

    client300 = genai.Client(
        api_key=args.api_key,
        http_options=types.HttpOptions(timeout=300)
    )
    t0 = time.time()
    resp = client300.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents="Genera 3 tokens de ejemplo para el nombre 'Juan Carlos Perez' de Lima, Peru, edad 30.",
        config=types.GenerateContentConfig(
            system_instruction="Eres un motor analitico. Genera tokens de seguridad.",
            temperature=0.3,
            response_mime_type="application/json",
            response_schema=Result,
        ),
    )
    elapsed = time.time() - t0
    print(f"  OK Respuesta en {elapsed:.2f}s:")
    print(f"    {resp.text}")
except Exception as e:
    elapsed = time.time() - t0
    print(f"  FAIL Error tras {elapsed:.2f}s: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("DIAGNOSTICO COMPLETO")
print("=" * 60)
