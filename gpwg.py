#!/usr/bin/env python3
"""
gpwg.py — Generative Password Wordlist Generator

Genera wordlists personalizadas y priorizadas usando IA (Gemini) + permutaciones inteligentes.

USO:
    python gpwg.py --profile target_profile.json --api-key TU_CLAVE --max 30000

EJEMPLOS:
    python gpwg.py --profile perfil.json --api-key sk-... --max 10000
    python gpwg.py --profile perfil.json --no-gemini --dry-run
    python gpwg.py --template objetivo.json
    python gpwg.py --profile perfil.json --api-key sk-... --format json --verbose

AVISO LEGAL:
    Esta herramienta es exclusivamente para auditorías de seguridad autorizadas
    y pentesting ético. El uso no autorizado puede ser ilegal.
"""

import argparse
import io
import json
import os
import sys
import time
from pathlib import Path

# Forzar UTF-8 en stdout/stderr para Windows (evita errores con emojis/unicode)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Verificar versión de Python ────────────────────────────────────────────────
if sys.version_info < (3, 8):
    print("[ERROR] Se requiere Python 3.8 o superior.")
    sys.exit(1)


# ── Plantilla de perfil de ejemplo ────────────────────────────────────────────

EXAMPLE_PROFILE = {
    "nombre_completo": "Juan Carlos Pérez García",
    "fecha_nacimiento": "1987-05-12",
    "apodos": ["Juanca", "JC", "Carlitos"],
    "mascotas": ["Max", "Luna"],
    "familiares": {
        "pareja": "María López",
        "hijos": ["Santiago", "Valentina"],
        "madre": "Rosa García",
        "padre": "Pedro Pérez"
    },
    "ciudad_nacimiento": "Guadalajara",
    "ciudad_residencia": "Ciudad de México",
    "equipos_favoritos": ["Chivas", "Barcelona"],
    "redes_sociales": {
        "instagram": "juanca87",
        "twitter": "jcperez",
        "steam": "juanca_gaming"
    },
    "empresa": "TechCorp México",
    "intereses": ["fútbol", "gaming", "música rock", "viajes", "fotografía"],
    "palabras_clave_extra": ["mexico", "guadalajara", "2019"],
    "descripcion_persona": (
        "Juan Carlos es fanático del equipo Chivas desde niño. Su mascota más querida "
        "fue un perro llamado Toby que tuvo de 2010 a 2020. Le encanta el grupo Metallica "
        "y su canción favorita es Enter Sandman. Viajó a Europa en 2015 y quedó enamorado "
        "de Barcelona. Su número de la suerte es el 7. Usa frecuentemente la palabra 'dragon' "
        "en sus contraseñas porque es su animal favorito. Trabaja en TechCorp desde 2018. "
        "Su apodo en el trabajo es 'el Juanca'. Nació en el Hospital Civil de Guadalajara."
    )
}


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser de argumentos CLI."""
    parser = argparse.ArgumentParser(
        prog="gpwg",
        description="GPWG — Generative Password Wordlist Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ejemplos:
  python gpwg.py --profile perfil.json --api-key TU_CLAVE
  python gpwg.py --profile perfil.json --no-gemini --dry-run
  python gpwg.py --template objetivo.json
  python gpwg.py --profile perfil.json --api-key TU_CLAVE --format json --verbose

[!] Solo para auditorias de seguridad autorizadas y pentesting etico.
        """,
    )

    # ── Grupo: Entrada ─────────────────────────────────────────────────────────
    input_group = parser.add_argument_group("entrada")
    input_group.add_argument(
        "--profile", "-p",
        metavar="RUTA_JSON",
        help="Ruta al archivo JSON del perfil objetivo (requerido a menos que uses --template)",
    )
    input_group.add_argument(
        "--template",
        metavar="RUTA_SALIDA",
        help="Genera un archivo JSON de ejemplo en la ruta indicada y termina",
    )

    # ── Grupo: API ─────────────────────────────────────────────────────────────
    api_group = parser.add_argument_group("api")
    api_group.add_argument(
        "--api-key", "-k",
        metavar="CLAVE",
        default=os.environ.get("GEMINI_API_KEY", ""),
        help="Clave de API de Gemini (también: variable de entorno GEMINI_API_KEY)",
    )
    api_group.add_argument(
        "--model",
        metavar="MODELO",
        default="gemini-3.1-flash-lite",
        help="Modelo de Gemini a utilizar (por defecto: gemini-3.1-flash-lite)",
    )
    api_group.add_argument(
        "--no-gemini",
        action="store_true",
        help="Ejecutar sin IA: solo permutaciones locales (más rápido, menos calidad)",
    )
    api_group.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignorar caché local y forzar nueva llamada a Gemini",
    )

    # ── Grupo: Salida ─────────────────────────────────────────────────────────
    output_group = parser.add_argument_group("salida")
    output_group.add_argument(
        "--output", "-o",
        metavar="ARCHIVO",
        default="",
        help="Nombre del archivo de salida (por defecto: wordlist_[nombre].txt)",
    )
    output_group.add_argument(
        "--format", "-f",
        choices=["txt", "json", "hashcat"],
        default="txt",
        help="Formato de salida: txt (default), json (con metadata), hashcat",
    )
    output_group.add_argument(
        "--no-report",
        action="store_true",
        help="No generar el archivo de reporte de auditoría JSON",
    )

    # ── Grupo: Filtros ────────────────────────────────────────────────────────
    filter_group = parser.add_argument_group("filtros")
    filter_group.add_argument(
        "--max", "-m",
        type=int,
        default=30000,
        metavar="N",
        help="Cantidad máxima de contraseñas (default: 30000)",
    )
    filter_group.add_argument(
        "--min-length",
        type=int,
        default=6,
        metavar="N",
        help="Longitud mínima de contraseña (default: 6)",
    )
    filter_group.add_argument(
        "--max-length",
        type=int,
        default=32,
        metavar="N",
        help="Longitud máxima de contraseña (default: 32)",
    )

    # ── Grupo: Comportamiento ─────────────────────────────────────────────────
    behavior_group = parser.add_argument_group("comportamiento")
    behavior_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Ejecutar todo el flujo sin escribir el archivo de salida",
    )
    behavior_group.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar tokens y scores durante la generación",
    )

    return parser


def handle_template(output_path: str) -> None:
    """Genera un archivo JSON de ejemplo en la ruta indicada."""
    path = Path(output_path)
    if path.exists():
        print(f"⚠️  El archivo ya existe: {output_path}")
        resp = input("   ¿Sobreescribir? [s/N]: ").strip().lower()
        if resp not in ("s", "si", "sí", "y", "yes"):
            print("   Cancelado.")
            sys.exit(0)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(EXAMPLE_PROFILE, f, ensure_ascii=False, indent=2)

    print(f"\n[+] Plantilla generada en: {output_path}")
    print("    Edita los campos con los datos reales del objetivo.")
    print("    El campo 'descripcion_persona' es el mas importante para Gemini.\n")
    sys.exit(0)


def main() -> None:
    """Punto de entrada principal del programa."""
    # Imports aquí para que --help funcione sin dependencias instaladas
    try:
        from tqdm import tqdm
    except ImportError:
        tqdm = None

    from core.loader import load_profile, get_display_name
    from core.normalizer import normalize_profile, extract_entities_from_description
    from core.gemini_client import call_gemini
    from core.token_extractor import extract_tokens
    from core.permutator import generate_wordlist
    from core.filters import apply_filters, get_stats, save_wordlist
    from core.reporter import (
        print_banner, print_phase, print_summary, save_audit_report
    )

    parser = build_parser()
    args = parser.parse_args()

    # ── Modo template ──────────────────────────────────────────────────────────
    if args.template:
        handle_template(args.template)
        return  # No alcanzará aquí (sys.exit en handle_template)

    # ── Validar que --profile está dado ───────────────────────────────────────
    if not args.profile:
        parser.print_help()
        print("\n[ERROR] Debes indicar --profile o usar --template para generar una plantilla.\n")
        sys.exit(1)

    # ── Validar API key si se va a usar Gemini ─────────────────────────────────
    if not args.no_gemini and not args.api_key:
        print("\n[ERROR] Se requiere --api-key o la variable de entorno GEMINI_API_KEY.")
        print("        Usa --no-gemini para ejecutar sin IA.\n")
        sys.exit(1)

    start_time = time.time()

    # ── Banner ─────────────────────────────────────────────────────────────────
    print_banner()

    # ── Fase 1: Carga y validación ─────────────────────────────────────────────
    print_phase("Cargando perfil...")
    profile = load_profile(args.profile)
    display_name = get_display_name(profile)
    print(f"   Perfil cargado: {profile['nombre_completo']}")

    # ── Fase 2: Normalización ──────────────────────────────────────────────────
    print_phase("Normalizando datos...")
    normalized_profile = normalize_profile(profile)
    entities = extract_entities_from_description(
        profile.get("descripcion_persona", "")
    )
    if args.verbose and entities:
        print(f"   Entidades locales detectadas: {sum(len(v) for v in entities.values())} elementos")

    # ── Fase 3: Enrichment con Gemini ─────────────────────────────────────────
    enrichment: dict = {}
    gemini_used = False

    if not args.no_gemini:
        print_phase("Enriqueciendo con Gemini AI...")
        enrichment = call_gemini(
            profile=normalized_profile,
            entities=entities,
            api_key=args.api_key,
            model_name=args.model,
            use_cache=not args.no_cache,
            verbose=args.verbose,
        )
        if enrichment.get("tokens"):
            gemini_used = True
            print(f"   {len(enrichment['tokens'])} tokens recibidos de Gemini")
            if args.verbose and enrichment.get("notas"):
                print(f"   Notas: {enrichment['notas']}")
    else:
        print_phase("Modo sin Gemini (--no-gemini activado)")

    # ── Fase 4: Extracción de tokens ──────────────────────────────────────────
    print_phase("Extrayendo tokens...")
    tokens = extract_tokens(normalized_profile, enrichment)
    print(f"   {len(tokens)} tokens únicos extraídos")

    if args.verbose:
        print("\n   Top 15 tokens por score:")
        sorted_tokens = sorted(tokens, key=lambda t: t["score"], reverse=True)
        for t in sorted_tokens[:15]:
            print(f"   [{t['score']:>2}] {t['tipo']:<15} → {t['valor']}")
        print()

    # ── Fase 5: Generación de permutaciones ───────────────────────────────────
    print_phase("Generando permutaciones...")

    # Con barra de progreso si tqdm está disponible
    if tqdm is not None:
        with tqdm(
            total=args.max,
            desc="   Generando",
            unit=" pwd",
            ncols=65,
            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}",
        ) as pbar:
            raw_wordlist = generate_wordlist(
                tokens=tokens,
                max_passwords=args.max,
                min_length=args.min_length,
                max_length=args.max_length,
                verbose=args.verbose,
            )
            pbar.update(len(raw_wordlist))
    else:
        raw_wordlist = generate_wordlist(
            tokens=tokens,
            max_passwords=args.max,
            min_length=args.min_length,
            max_length=args.max_length,
            verbose=args.verbose,
        )

    # ── Fase 6: Filtros y ordenamiento ────────────────────────────────────────
    print_phase("Aplicando filtros y ordenando...")
    final_wordlist = apply_filters(
        wordlist=raw_wordlist,
        min_length=args.min_length,
        max_length=args.max_length,
        max_passwords=args.max,
    )
    stats = get_stats(final_wordlist)

    # ── Fase 7: Guardar salida ─────────────────────────────────────────────────
    # Determinar extensión según formato
    ext_map = {"txt": ".txt", "json": ".json", "hashcat": ".txt"}
    ext = ext_map.get(args.format, ".txt")

    output_path = args.output or f"wordlist_{display_name}{ext}"
    if args.format == "json" and not output_path.endswith(".json"):
        output_path = output_path.rsplit(".", 1)[0] + ".json"

    report_path = None

    if not args.dry_run:
        print_phase("Guardando wordlist...")
        save_wordlist(
            wordlist=final_wordlist,
            output_path=output_path,
            fmt=args.format,
            stats=stats,
        )

        if not args.no_report:
            report_path = save_audit_report(
                output_path=output_path,
                profile_name=profile["nombre_completo"],
                tokens=tokens,
                stats=stats,
                enrichment=enrichment,
                elapsed=time.time() - start_time,
                gemini_used=gemini_used,
            )

    # ── Resumen final ──────────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    print_summary(
        stats=stats,
        output_path=output_path,
        elapsed=elapsed,
        dry_run=args.dry_run,
        gemini_used=gemini_used,
        tokens_count=len(tokens),
        report_path=report_path,
    )


if __name__ == "__main__":
    main()
