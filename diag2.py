"""
Diagnóstico de unidades de timeout en google-genai.
Ejecutar con: python diag2.py --api-key TU_CLAVE
"""
import argparse
import time

from google import genai
from google.genai import types

parser = argparse.ArgumentParser()
parser.add_argument("--api-key", required=True)
args = parser.parse_args()

# ── Test A: Sin timeout explícito (default del SDK) ────────────────────────────
print("=" * 60)
print("TEST A: generate_content SIN timeout explícito...")
print("=" * 60)
try:
    client_default = genai.Client(api_key=args.api_key)
    t0 = time.time()
    resp = client_default.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents="Di 'hola' y nada mas.",
    )
    elapsed = time.time() - t0
    print(f"  OK en {elapsed:.2f}s: {resp.text}")
except Exception as e:
    elapsed = time.time() - t0
    print(f"  FAIL en {elapsed:.2f}s: {type(e).__name__}: {e}")

# ── Test B: timeout=120000 (120 segundos si es milisegundos) ───────────────────
print("\n" + "=" * 60)
print("TEST B: generate_content con timeout=120000 (120s si es ms)...")
print("=" * 60)
try:
    client_ms = genai.Client(
        api_key=args.api_key,
        http_options=types.HttpOptions(timeout=120000)
    )
    t0 = time.time()
    resp = client_ms.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents="Di 'hola' y nada mas.",
    )
    elapsed = time.time() - t0
    print(f"  OK en {elapsed:.2f}s: {resp.text}")
except Exception as e:
    elapsed = time.time() - t0
    print(f"  FAIL en {elapsed:.2f}s: {type(e).__name__}: {e}")

# ── Test C: gemini-3.1-flash-lite con timeout=120000 ──────────────────────────
print("\n" + "=" * 60)
print("TEST C: gemini-3.1-flash-lite con timeout=120000...")
print("=" * 60)
try:
    t0 = time.time()
    resp = client_ms.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents="Di 'hola' y nada mas.",
    )
    elapsed = time.time() - t0
    print(f"  OK en {elapsed:.2f}s: {resp.text}")
except Exception as e:
    elapsed = time.time() - t0
    print(f"  FAIL en {elapsed:.2f}s: {type(e).__name__}: {e}")

# ── Test D: Structured Output con timeout=120000 ──────────────────────────────
print("\n" + "=" * 60)
print("TEST D: Structured Output con timeout=120000...")
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

    t0 = time.time()
    resp = client_ms.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents="Genera 3 tokens de ejemplo para 'Juan Carlos' de Lima, 30 anios.",
        config=types.GenerateContentConfig(
            system_instruction="Eres un motor analitico. Genera tokens.",
            temperature=0.3,
            response_mime_type="application/json",
            response_schema=Result,
        ),
    )
    elapsed = time.time() - t0
    print(f"  OK en {elapsed:.2f}s:")
    print(f"    {resp.text}")
except Exception as e:
    elapsed = time.time() - t0
    print(f"  FAIL en {elapsed:.2f}s: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("DIAGNOSTICO COMPLETO")
print("=" * 60)
