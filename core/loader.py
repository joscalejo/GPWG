"""
loader.py — Carga y validación del perfil JSON.

Valida campos requeridos y opcionales, provee mensajes claros
de qué falta y cómo mejorar la calidad del perfil.
"""

import json
import sys
from pathlib import Path


# Campos absolutamente requeridos para que el programa funcione
REQUIRED_FIELDS = ["nombre_completo", "fecha_nacimiento"]

# Campos opcionales que mejoran mucho la calidad de la wordlist
RECOMMENDED_FIELDS = [
    "apodos",
    "mascotas",
    "familiares",
    "ciudad_nacimiento",
    "ciudad_residencia",
    "equipos_favoritos",
    "descripcion_persona",
    "redes_sociales",
    "intereses",
    "empresa",
    "palabras_clave_extra",
]

QUALITY_TIPS = {
    "apodos":              "Agrega apodos o diminutivos usados por amigos/familia.",
    "mascotas":            "Nombre(s) de mascotas actuales o pasadas.",
    "familiares":          "Nombres de pareja, hijos, padres, hermanos.",
    "ciudad_nacimiento":   "Ciudad donde nació la persona.",
    "ciudad_residencia":   "Ciudad donde vive actualmente.",
    "equipos_favoritos":   "Equipos de fútbol, béisbol, etc.",
    "descripcion_persona": "Texto libre DETALLADO sobre la persona: hobbies, frases favoritas, lugares especiales, etc.",
    "redes_sociales":      "Usernames de Instagram, Twitter, Steam, etc.",
    "intereses":           "Hobbies, series, música, videojuegos favoritos.",
    "empresa":             "Empresa donde trabaja o trabajó.",
    "palabras_clave_extra":"Cualquier palabra/número especial que uses en contraseñas.",
}


def load_profile(path: str) -> dict:
    """
    Carga y valida el archivo JSON del perfil.

    Args:
        path: Ruta al archivo JSON.

    Returns:
        Diccionario con el perfil cargado.

    Raises:
        SystemExit si hay errores críticos.
    """
    profile_path = Path(path)

    # ── Verificar que el archivo existe ────────────────────────────────────────
    if not profile_path.exists():
        print(f"\n[ERROR] Archivo no encontrado: {path}")
        print(f"        Tip: Usa --template {path} para generar una plantilla.\n")
        sys.exit(1)

    if not profile_path.is_file():
        print(f"\n[ERROR] La ruta no es un archivo: {path}\n")
        sys.exit(1)

    # ── Cargar el JSON ─────────────────────────────────────────────────────────
    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)
    except json.JSONDecodeError as e:
        print(f"\n[ERROR] Error de formato en el JSON: {e}")
        print(f"        Verifica que el archivo sea JSON valido en: {path}\n")
        sys.exit(1)
    except UnicodeDecodeError:
        print(f"\n[ERROR] Error de codificacion. Guarda el archivo como UTF-8.\n")
        sys.exit(1)

    if not isinstance(profile, dict):
        print(f"\n[ERROR] El JSON debe ser un objeto ({{...}}), no una lista.\n")
        sys.exit(1)

    # ── Validar campos requeridos ──────────────────────────────────────────────
    missing_required = [f for f in REQUIRED_FIELDS if not profile.get(f)]
    if missing_required:
        print("\n[ERROR] Faltan campos requeridos en el perfil:")
        for field in missing_required:
            print(f"        * {field}")
        print(f"\n        Tip: Usa --template {path} para ver la plantilla completa.\n")
        sys.exit(1)

    # ── Advertir sobre campos opcionales faltantes ────────────────────────────
    missing_recommended = [f for f in RECOMMENDED_FIELDS if not profile.get(f)]
    if missing_recommended:
        quality_score = round(
            (len(RECOMMENDED_FIELDS) - len(missing_recommended)) / len(RECOMMENDED_FIELDS) * 100
        )
        print(f"\n[!] Calidad del perfil: {quality_score}%")
        if quality_score < 50:
            print("    Para mejores resultados, considera agregar:")
            for field in missing_recommended[:4]:
                print(f"    * {field}: {QUALITY_TIPS[field]}")
        print()

    return profile


def get_display_name(profile: dict) -> str:
    """Extrae un nombre limpio para usar en nombres de archivos."""
    name = profile.get("nombre_completo", "target")
    # Reemplazar espacios y caracteres especiales por guión bajo
    safe = "".join(c if c.isalnum() else "_" for c in name)
    return safe.strip("_")
