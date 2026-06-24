"""
filters.py — Filtros y ordenamiento final de la wordlist.

Aplica filtros de longitud, ordena por score y limita al máximo indicado.
También maneja la generación de salida en múltiples formatos.
"""

from typing import List, Dict, Any
import statistics


def apply_filters(
    wordlist: List[Dict[str, Any]],
    min_length: int = 6,
    max_length: int = 32,
    max_passwords: int = 30000,
) -> List[Dict[str, Any]]:
    """
    Aplica filtros finales y ordena la wordlist por score descendente.

    Args:
        wordlist: Lista de dicts con password, score, tokens_used
        min_length: Longitud mínima de contraseña
        max_length: Longitud máxima de contraseña
        max_passwords: Límite final de contraseñas

    Returns:
        Lista filtrada, ordenada y limitada
    """
    # Filtrar por longitud (el permutador ya filtra, pero por si acaso)
    filtered = [
        entry for entry in wordlist
        if min_length <= len(entry["password"]) <= max_length
    ]

    # Ordenar por score descendente (mayor probabilidad primero)
    filtered.sort(key=lambda e: e["score"], reverse=True)

    # Limitar al máximo
    return filtered[:max_passwords]


def get_stats(wordlist: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcula estadísticas de la wordlist final.

    Returns:
        Dict con estadísticas de cantidad, longitud y distribución de scores
    """
    if not wordlist:
        return {
            "total": 0,
            "avg_length": 0,
            "min_length": 0,
            "max_length": 0,
            "high_priority_pct": 0,
            "medium_priority_pct": 0,
            "low_priority_pct": 0,
        }

    passwords = [e["password"] for e in wordlist]
    scores = [e["score"] for e in wordlist]
    lengths = [len(p) for p in passwords]

    high = sum(1 for s in scores if s >= 8)
    medium = sum(1 for s in scores if 5 <= s < 8)
    low = sum(1 for s in scores if s < 5)
    total = len(wordlist)

    return {
        "total": total,
        "avg_length": round(statistics.mean(lengths), 1),
        "min_length": min(lengths),
        "max_length": max(lengths),
        "high_priority_pct": round(high / total * 100, 1),
        "medium_priority_pct": round(medium / total * 100, 1),
        "low_priority_pct": round(low / total * 100, 1),
        "avg_score": round(statistics.mean(scores), 2),
    }


# ── Formatos de salida ─────────────────────────────────────────────────────────

def format_txt(wordlist: List[Dict[str, Any]]) -> str:
    """Formato plano: una contraseña por línea."""
    return "\n".join(entry["password"] for entry in wordlist)


def format_json(wordlist: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
    """Formato JSON con metadata de cada contraseña."""
    import json
    output = {
        "stats": stats,
        "wordlist": [
            {
                "password": e["password"],
                "score": e["score"],
                "tokens_used": e.get("tokens_used", []),
            }
            for e in wordlist
        ],
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


def format_hashcat(wordlist: List[Dict[str, Any]]) -> str:
    """
    Formato compatible con Hashcat: lista plana de contraseñas.
    (Idéntico al TXT, incluido por compatibilidad y claridad semántica)
    """
    return format_txt(wordlist)


def save_wordlist(
    wordlist: List[Dict[str, Any]],
    output_path: str,
    fmt: str = "txt",
    stats: Dict[str, Any] = None,
) -> None:
    """
    Guarda la wordlist en el archivo de salida.

    Args:
        wordlist: Lista procesada de contraseñas
        output_path: Ruta del archivo de salida
        fmt: 'txt', 'json' o 'hashcat'
        stats: Estadísticas calculadas (requerido para formato json)
    """
    stats = stats or {}

    if fmt == "json":
        content = format_json(wordlist, stats)
    elif fmt == "hashcat":
        content = format_hashcat(wordlist)
    else:
        content = format_txt(wordlist)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
