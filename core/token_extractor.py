"""
token_extractor.py — Extrae y estructura tokens con scores desde el perfil y el enrichment de Gemini.

Combina: datos del perfil + respuesta de Gemini + variantes locales de fecha.
Produce una lista unificada de tokens con score de importancia.
"""

from typing import List, Dict, Any
from core.normalizer import (
    name_variants,
    generate_date_formats,
)


# Tipo interno para un token
# { "valor": str, "tipo": str, "score": int, "fuente": str }

def extract_tokens(profile: dict, enrichment: dict) -> List[Dict[str, Any]]:
    """
    Extrae todos los tokens posibles combinando el perfil local con el enrichment de Gemini.

    Args:
        profile: Perfil normalizado (con claves _nombre_variants, etc.)
        enrichment: Respuesta de Gemini (puede ser dict vacío si --no-gemini)

    Returns:
        Lista de tokens únicos con score y tipo.
    """
    tokens: List[Dict[str, Any]] = []
    seen_values = set()

    def add_token(valor: str, tipo: str, score: int, fuente: str = "local") -> None:
        """Agrega un token si no está duplicado y tiene contenido."""
        valor = str(valor).strip()
        key = valor.lower()
        if not valor or key in seen_values or len(valor) < 2:
            return
        seen_values.add(key)
        tokens.append({
            "valor": valor,
            "tipo": tipo,
            "score": max(1, min(10, score)),  # Clamp 1-10
            "fuente": fuente,
        })

    # ── 1. Nombre y variantes ──────────────────────────────────────────────────
    nombre = profile.get("nombre_completo", "")
    for variant in profile.get("_nombre_variants", name_variants(nombre)):
        # Primera parte del nombre (primer nombre) tiene más peso
        parts = variant.split()
        if parts:
            add_token(parts[0], "nombre", 9)   # Primer nombre
        if len(parts) > 1:
            add_token(parts[-1], "apellido", 7)  # Último apellido
        add_token(variant, "nombre_completo", 8)

    # ── 2. Apodos ──────────────────────────────────────────────────────────────
    for variant in profile.get("_apodos_variants", []):
        add_token(variant, "apodo", 9)

    # ── 3. Fecha de nacimiento ─────────────────────────────────────────────────
    fecha = profile.get("fecha_nacimiento", "")
    if fecha:
        for fmt in generate_date_formats(str(fecha)):
            add_token(fmt, "fecha", 8)

    # ── 4. Mascotas ────────────────────────────────────────────────────────────
    for variant in profile.get("_mascotas_variants", []):
        add_token(variant, "mascota", 8)

    # ── 5. Familiares ──────────────────────────────────────────────────────────
    for variant in profile.get("_familiares_variants", []):
        add_token(variant, "familiar", 6)

    # ── 6. Ciudades ────────────────────────────────────────────────────────────
    ciudad_nac = profile.get("ciudad_nacimiento", "")
    ciudad_res = profile.get("ciudad_residencia", "")
    if ciudad_nac:
        for v in name_variants(str(ciudad_nac)):
            add_token(v, "ciudad", 5)
    if ciudad_res:
        for v in name_variants(str(ciudad_res)):
            add_token(v, "ciudad", 6)

    # ── 7. Equipos favoritos ───────────────────────────────────────────────────
    equipos = profile.get("equipos_favoritos", [])
    if isinstance(equipos, str):
        equipos = [e.strip() for e in equipos.split(",")]
    for equipo in equipos:
        for v in name_variants(str(equipo)):
            add_token(v, "equipo", 5)

    # ── 8. Redes sociales / usernames ─────────────────────────────────────────
    redes = profile.get("redes_sociales", {})
    if isinstance(redes, dict):
        for platform, username in redes.items():
            if username:
                add_token(str(username), "username", 7)
    elif isinstance(redes, list):
        for item in redes:
            if isinstance(item, str):
                add_token(item, "username", 7)

    # ── 9. Empresa ────────────────────────────────────────────────────────────
    empresa = profile.get("empresa", "")
    if empresa:
        for v in name_variants(str(empresa)):
            add_token(v, "empresa", 4)

    # ── 10. Intereses ─────────────────────────────────────────────────────────
    intereses = profile.get("intereses", [])
    if isinstance(intereses, str):
        intereses = [i.strip() for i in intereses.split(",")]
    for interes in intereses:
        for v in name_variants(str(interes)):
            add_token(v, "keyword", 7)

    # ── 11. Palabras clave extra ──────────────────────────────────────────────
    extras = profile.get("palabras_clave_extra", [])
    if isinstance(extras, str):
        extras = [e.strip() for e in extras.split(",")]
    for extra in extras:
        add_token(str(extra), "keyword", 6)

    # ── 12. Tokens de Gemini ──────────────────────────────────────────────────
    tier_scores = {"alto": 9, "medio": 6, "bajo": 3}
    for tier, score in tier_scores.items():
        for token_value in enrichment.get(tier, []):
            val = str(token_value).strip()
            add_token(val, "gemini", score, fuente="gemini")
            # Para tokens multi-palabra, generar variante unida (camelCase)
            # ej. "Dragon Ball" → "DragonBall", "dragonball"
            if " " in val:
                parts = val.split()
                joined = "".join(parts)
                camel = "".join(p.capitalize() for p in parts)
                add_token(joined, "gemini", score, fuente="gemini")
                if camel != joined:
                    add_token(camel, "gemini", score, fuente="gemini")

    return tokens


def get_score_tiers(tokens: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Agrupa tokens por tier de importancia.

    Returns:
        Dict con listas: 'high' (8-10), 'medium' (5-7), 'low' (1-4)
    """
    high = [t for t in tokens if t["score"] >= 8]
    medium = [t for t in tokens if 5 <= t["score"] <= 7]
    low = [t for t in tokens if t["score"] < 5]

    return {"high": high, "medium": medium, "low": low}
