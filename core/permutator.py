"""
permutator.py — Motor de permutaciones inteligente.

Genera contraseñas combinando tokens con:
- Capitalización (normal, UPPER, Capitalized, camelCase)
- Leet speak
- Sufijos numéricos y especiales comunes
- Combinación de tokens entre sí
- Separadores

La cantidad de combinaciones generadas por token es proporcional a su score.
"""

from typing import List, Dict, Any, Set, Iterator


# ── Tablas de sustitución leet ─────────────────────────────────────────────────

LEET_MAP = {
    "a": "4", "e": "3", "i": "1", "o": "0",
    "s": "5", "t": "7", "l": "1", "g": "9",
    "b": "8", "z": "2",
}

# ── Sufijos más comunes en contraseñas ─────────────────────────────────────────

COMMON_SUFFIXES = [
    "1", "12", "123", "1234", "12345", "123456",
    "!", "!!", ".", "*",
    "01", "99", "00", "2024", "2023", "2025", "2026",
    "#1", "@1",
]

COMMON_PREFIXES = [
    "!", "@", "#", ".", "*",
]

SEPARATORS = ["", ".", "_", "-", "@"]


# ── Funciones de transformación ────────────────────────────────────────────────

def to_leet(word: str) -> str:
    """Convierte un string a leet speak."""
    return "".join(LEET_MAP.get(c.lower(), c) for c in word)


def capitalizations(word: str) -> List[str]:
    """Genera variantes de capitalización de una palabra."""
    variants = set()
    variants.add(word)                     # Original
    variants.add(word.lower())             # todo minúsculas
    variants.add(word.upper())             # TODO MAYÚSCULAS
    variants.add(word.capitalize())        # Primera mayúscula
    # Alternar mayúsculas (aLtErNaDo)
    alt = "".join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(word))
    variants.add(alt)
    return list(variants)


def with_suffixes(base: str, suffixes: List[str]) -> List[str]:
    """Combina una base con sufijos."""
    return [base + s for s in suffixes]


def with_prefixes(base: str, prefixes: List[str]) -> List[str]:
    """Combina una base con prefijos."""
    return [p + base for p in prefixes]


# ── Motor principal ────────────────────────────────────────────────────────────

def _generate_single_token(token: Dict[str, Any], max_per_token: int) -> Iterator[str]:
    """
    Genera contraseñas a partir de un único token.

    La cantidad de transformaciones depende del score del token.
    """
    valor = token["valor"]
    score = token["score"]
    count = 0

    # Todas las caps del valor original
    caps = capitalizations(valor)
    for cap in caps:
        if count >= max_per_token:
            return
        yield cap
        count += 1

    # Con sufijos (cantidad proporcional al score)
    num_suffixes = min(len(COMMON_SUFFIXES), max(2, score))
    for cap in caps[:2]:  # Solo las 2 primeras variantes de cap
        for suffix in COMMON_SUFFIXES[:num_suffixes]:
            if count >= max_per_token:
                return
            yield cap + suffix
            count += 1

    # Con prefijos (solo para scores altos)
    if score >= 7:
        for cap in caps[:2]:
            for prefix in COMMON_PREFIXES[:3]:
                if count >= max_per_token:
                    return
                yield prefix + cap
                count += 1

    # Leet speak (solo scores medios y altos)
    if score >= 5:
        leet = to_leet(valor)
        if leet != valor:  # Solo si hay diferencia
            for cap in capitalizations(leet)[:2]:
                if count >= max_per_token:
                    return
                yield cap
                count += 1
            for suffix in COMMON_SUFFIXES[:3]:
                if count >= max_per_token:
                    return
                yield leet + suffix
                count += 1


def _generate_two_token_combos(
    token_a: Dict[str, Any],
    token_b: Dict[str, Any],
    max_combos: int,
    seen: Set[str],
) -> Iterator[str]:
    """
    Genera combinaciones de dos tokens con separadores.
    """
    score_avg = (token_a["score"] + token_b["score"]) / 2
    caps_a = capitalizations(token_a["valor"])[:2]
    caps_b = capitalizations(token_b["valor"])[:2]

    num_seps = min(len(SEPARATORS), max(1, int(score_avg / 3)))
    count = 0

    for a in caps_a:
        for b in caps_b:
            for sep in SEPARATORS[:num_seps]:
                if count >= max_combos:
                    return
                combo = a + sep + b
                key = combo.lower()
                if key not in seen and len(combo) >= 4:
                    seen.add(key)
                    yield combo
                    count += 1
            # Con sufijos
            for suffix in COMMON_SUFFIXES[:3]:
                if count >= max_combos:
                    return
                combo = a + b + suffix
                key = combo.lower()
                if key not in seen:
                    seen.add(key)
                    yield combo
                    count += 1


def generate_wordlist(
    tokens: List[Dict[str, Any]],
    max_passwords: int = 30000,
    min_length: int = 6,
    max_length: int = 32,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """
    Motor principal de generación de contraseñas.

    Genera permutaciones priorizando tokens con score alto.
    Usa un set() interno para deduplicar durante la generación.

    Args:
        tokens: Lista de tokens con score
        max_passwords: Límite máximo de contraseñas
        min_length: Longitud mínima
        max_length: Longitud máxima
        verbose: Si True, muestra progreso por tier

    Returns:
        Lista de dicts: { "password": str, "score": float, "tokens_used": list }
    """
    seen: Set[str] = set()
    wordlist: List[Dict[str, Any]] = []

    # Ordenar por score descendente para priorizar los más importantes
    sorted_tokens = sorted(tokens, key=lambda t: t["score"], reverse=True)

    # Separar por tier
    high_tokens = [t for t in sorted_tokens if t["score"] >= 8]
    medium_tokens = [t for t in sorted_tokens if 5 <= t["score"] <= 7]
    low_tokens = [t for t in sorted_tokens if t["score"] < 5]

    if verbose:
        print(f"   Tokens: {len(high_tokens)} altos | {len(medium_tokens)} medios | {len(low_tokens)} bajos")

    def add_password(pwd: str, score: float, token_vals: list) -> bool:
        """Agrega una contraseña si cumple los filtros."""
        key = pwd.lower()
        if key in seen:
            return False
        if len(pwd) < min_length or len(pwd) > max_length:
            seen.add(key)  # Marcar como vista aunque no se agregue
            return False
        seen.add(key)
        wordlist.append({
            "password": pwd,
            "score": score,
            "tokens_used": token_vals,
        })
        return True

    # ── Fase 1: Tokens individuales (score alto → muchas combinaciones) ─────────
    for token in sorted_tokens:
        if len(wordlist) >= max_passwords:
            break
        score = token["score"]
        # Cuántas contraseñas generar por token (proporcional al score)
        max_per_token = int(10 + score * 15)  # Alto: ~250, Medio: ~100, Bajo: ~25

        for pwd in _generate_single_token(token, max_per_token):
            if len(wordlist) >= max_passwords:
                break
            add_password(pwd, float(score), [token["valor"]])

    # ── Fase 2: Combinaciones de 2 tokens (priorizar high + cualquier tier) ───
    remaining = max_passwords - len(wordlist)
    if remaining > 0:
        # Combinar high con medium
        combo_pairs = []
        for i, ta in enumerate(high_tokens[:10]):  # Top 10 high
            for tb in medium_tokens[:10]:           # Top 10 medium
                combo_pairs.append((ta, tb))
        # Combinar high entre sí
        for i, ta in enumerate(high_tokens[:-1]):
            for tb in high_tokens[i+1:]:
                combo_pairs.append((ta, tb))
        # Combinar medium entre sí
        for i, ta in enumerate(medium_tokens[:8]):
            for tb in medium_tokens[i+1:min(i+5, len(medium_tokens))]:
                combo_pairs.append((ta, tb))

        # Ordenar pares por score combinado
        combo_pairs.sort(key=lambda p: p[0]["score"] + p[1]["score"], reverse=True)

        max_per_combo = max(5, remaining // max(1, len(combo_pairs)))
        max_per_combo = min(max_per_combo, 30)  # Cap razonable por par

        for ta, tb in combo_pairs:
            if len(wordlist) >= max_passwords:
                break
            score_avg = (ta["score"] + tb["score"]) / 2
            for pwd in _generate_two_token_combos(ta, tb, max_per_combo, seen):
                if len(wordlist) >= max_passwords:
                    break
                add_password(pwd, score_avg, [ta["valor"], tb["valor"]])

    # ── Fase 3: Completar con tokens bajos si hay espacio ──────────────────────
    remaining = max_passwords - len(wordlist)
    if remaining > 0 and low_tokens:
        for token in low_tokens:
            if len(wordlist) >= max_passwords:
                break
            for pwd in _generate_single_token(token, 5):
                if len(wordlist) >= max_passwords:
                    break
                add_password(pwd, float(token["score"]), [token["valor"]])

    return wordlist
