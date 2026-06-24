"""
reporter.py — Resumen en consola y generación del archivo de auditoría.

Muestra estadísticas finales y opcionalmente guarda un reporte JSON
con todos los tokens, scores y métricas de la sesión.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any


# ── Banner ─────────────────────────────────────────────────────────────────────

BANNER = r"""
  ██████╗ ██████╗ ██╗    ██╗ ██████╗
 ██╔════╝ ██╔══██╗██║    ██║██╔════╝
 ██║  ███╗██████╔╝██║ █╗ ██║██║  ███╗
 ██║   ██║██╔═══╝ ██║███╗██║██║   ██║
 ╚██████╔╝██║     ╚███╔███╔╝╚██████╔╝
  ╚═════╝ ╚═╝      ╚══╝╚══╝  ╚═════╝
  Generative Password Wordlist Generator
  [!] Solo para auditorias de seguridad autorizadas
"""


def print_banner() -> None:
    """Imprime el banner de inicio."""
    print(BANNER)


def print_phase(phase: str) -> None:
    """Imprime el inicio de una fase del flujo."""
    print(f"\n[→] {phase}")


def print_summary(
    stats: Dict[str, Any],
    output_path: str,
    elapsed: float,
    dry_run: bool = False,
    gemini_used: bool = True,
    tokens_count: int = 0,
    report_path: str = None,
) -> None:
    """
    Imprime el resumen final en consola.

    Args:
        stats: Estadísticas calculadas por filters.get_stats()
        output_path: Ruta del archivo de salida
        elapsed: Tiempo total en segundos
        dry_run: Si True, mostrar mensaje de dry-run
        gemini_used: Si Gemini fue usado
        tokens_count: Cantidad de tokens extraídos
        report_path: Ruta del reporte de auditoría (si se generó)
    """
    print("\n" + "═" * 55)

    if dry_run:
        print("  [*] MODO DRY-RUN (sin escritura de archivo)")
    else:
        print(f"  [+] Wordlist generada exitosamente")

    print("═" * 55)
    print(f"  Contraseñas totales : {stats.get('total', 0):>10,}")
    print(f"  Tokens extraídos    : {tokens_count:>10,}")
    print(f"  Longitud promedio   : {stats.get('avg_length', 0):>10.1f} caracteres")
    print(f"  Longitud mínima     : {stats.get('min_length', 0):>10}")
    print(f"  Longitud máxima     : {stats.get('max_length', 0):>10}")
    print(f"  Prioridad alta      : {stats.get('high_priority_pct', 0):>9.1f}%")
    print(f"  Prioridad media     : {stats.get('medium_priority_pct', 0):>9.1f}%")
    print(f"  Prioridad baja      : {stats.get('low_priority_pct', 0):>9.1f}%")
    print(f"  Score promedio      : {stats.get('avg_score', 0):>10.2f}")
    print(f"  Gemini AI           : {'[ON]' if gemini_used else '[OFF]':>10}")
    print(f"  Tiempo total        : {elapsed:>9.1f}s")
    print("─" * 55)

    if not dry_run:
        print(f"  [>] Wordlist  -> {output_path}")
    if report_path:
        print(f"  [>] Reporte   -> {report_path}")

    print("═" * 55)
    print()
    print("  [!] AVISO LEGAL: Esta herramienta es exclusivamente para")
    print("      auditorias de seguridad autorizadas y pentesting etico.")
    print("      El uso no autorizado puede ser ilegal.")
    print()


def save_audit_report(
    output_path: str,
    profile_name: str,
    tokens: List[Dict[str, Any]],
    stats: Dict[str, Any],
    enrichment: Dict[str, Any],
    elapsed: float,
    gemini_used: bool,
) -> str:
    """
    Guarda un reporte de auditoría JSON con todos los detalles de la sesión.

    Args:
        output_path: Ruta base del archivo wordlist (se deriva la ruta del reporte)
        profile_name: Nombre del perfil procesado
        tokens: Lista de tokens extraídos con scores
        stats: Estadísticas de la wordlist final
        enrichment: Respuesta de Gemini
        elapsed: Tiempo total en segundos
        gemini_used: Si Gemini fue usado

    Returns:
        Ruta al archivo de reporte generado
    """
    report_path = output_path.replace(".txt", "_report.json")
    if not report_path.endswith("_report.json"):
        report_path = output_path + "_report.json"

    # Agrupar tokens por tipo para el reporte
    tokens_by_type: Dict[str, List] = {}
    for token in tokens:
        tipo = token.get("tipo", "otro")
        if tipo not in tokens_by_type:
            tokens_by_type[tipo] = []
        tokens_by_type[tipo].append({
            "valor": token["valor"],
            "score": token["score"],
            "fuente": token.get("fuente", "local"),
        })

    report = {
        "metadata": {
            "perfil": profile_name,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "elapsed_seconds": round(elapsed, 2),
            "gemini_usado": gemini_used,
        },
        "estadisticas": stats,
        "tokens_por_tipo": tokens_by_type,
        "tokens_total": len(tokens),
        "gemini_notas": enrichment.get("notas", ""),
        "gemini_patrones": enrichment.get("patrones_detectados", []),
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report_path
