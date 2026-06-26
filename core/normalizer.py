"""
normalizer.py — Normalización de texto y extracción de entidades locales.

Quita acentos, genera variantes de nombres y pre-procesa el texto libre
de descripcion_persona antes de enviarlo a Gemini.
"""

import re
import unicodedata
from typing import List


def remove_accents(text: str) -> str:
    """Convierte caracteres acentuados a ASCII equivalente."""
    if not isinstance(text, str):
        return str(text)
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


def normalize_text(text: str) -> str:
    """Normaliza un texto: quita acentos y caracteres extraños."""
    text = remove_accents(text)
    # Conservar solo alfanuméricos, espacios y guiones
    text = re.sub(r"[^\w\s\-]", "", text)
    return text.strip()


def name_variants(name: str) -> List[str]:
    """
    Genera variantes básicas de un nombre:
    original, sin acentos, partes individuales.

    Ejemplo: 'María José' → ['María José', 'Maria Jose', 'María', 'José', 'Maria', 'Jose']
    """
    variants = set()
    name = name.strip()

    # Original
    variants.add(name)
    # Sin acentos
    no_accent = remove_accents(name)
    variants.add(no_accent)

    # Partes individuales (nombre y apellidos por separado)
    parts = name.split()
    for part in parts:
        if len(part) > 1:
            variants.add(part)
            variants.add(remove_accents(part))

    return [v for v in variants if v]


def normalize_profile(profile: dict) -> dict:
    """
    Normaliza los campos del perfil para facilitar el procesamiento.
    Agrega el campo '_normalized' con variantes sin acentos para campos clave.
    """
    normalized = dict(profile)

    # Normalizar nombre completo
    nombre = profile.get("nombre_completo", "")
    normalized["_nombre_variants"] = name_variants(nombre)

    # Normalizar apodos
    apodos_raw = profile.get("apodos", [])
    if isinstance(apodos_raw, str):
        apodos_raw = [a.strip() for a in apodos_raw.split(",")]
    apodos_norm = []
    for apodo in apodos_raw:
        apodos_norm.extend(name_variants(apodo))
    normalized["_apodos_variants"] = list(set(apodos_norm))

    # Normalizar mascotas
    mascotas_raw = profile.get("mascotas", [])
    if isinstance(mascotas_raw, str):
        mascotas_raw = [m.strip() for m in mascotas_raw.split(",")]
    normalized["_mascotas_variants"] = []
    for m in mascotas_raw:
        normalized["_mascotas_variants"].extend(name_variants(m))

    # Normalizar familiares
    familiares_raw = profile.get("familiares", [])
    familiares_list = []
    if isinstance(familiares_raw, dict):
        for val in familiares_raw.values():
            if isinstance(val, list):
                for v in val:
                    if isinstance(v, str) and v.strip():
                        familiares_list.append(v)
            elif isinstance(val, str) and val.strip():
                familiares_list.append(val)
    elif isinstance(familiares_raw, list):
        for val in familiares_raw:
            if isinstance(val, str) and val.strip():
                familiares_list.append(val)
    elif isinstance(familiares_raw, str):
        familiares_list = [f.strip() for f in familiares_raw.split(",") if f.strip()]

    normalized["_familiares_variants"] = []
    for f in familiares_list:
        normalized["_familiares_variants"].extend(name_variants(f))

    return normalized


# ── Formatos de fecha ──────────────────────────────────────────────────────────

def generate_date_formats(fecha: str) -> List[str]:
    """
    Genera múltiples formatos de fecha a partir de una cadena YYYY-MM-DD.

    Ejemplo input: '1987-05-12'
    Outputs: ['19870512', '12051987', '870512', '120587', '1987', '05', '12', ...]
    """
    formats = []
    fecha = fecha.strip()

    # Intentar parsear varios formatos de entrada
    parts = None
    for sep in ["-", "/", "."]:
        if sep in fecha:
            parts = fecha.split(sep)
            break

    if not parts or len(parts) != 3:
        # Si no tiene separadores, asumir YYYYMMDD o DDMMYYYY
        if len(fecha) == 8 and fecha.isdigit():
            parts = [fecha[:4], fecha[4:6], fecha[6:]]
        else:
            formats.append(fecha)
            return formats

    # Determinar si el primer componente es año (4 dígitos)
    if len(parts[0]) == 4:
        yyyy, mm, dd = parts[0], parts[1].zfill(2), parts[2].zfill(2)
    elif len(parts[2]) == 4:
        dd, mm, yyyy = parts[0].zfill(2), parts[1].zfill(2), parts[2]
    else:
        # Ambiguo, asumir DD-MM-YYYY
        dd, mm, yyyy = parts[0].zfill(2), parts[1].zfill(2), "20" + parts[2]

    yy = yyyy[2:]  # Año corto

    # Combinaciones comunes en contraseñas
    combos = [
        f"{yyyy}{mm}{dd}",   # 19870512
        f"{dd}{mm}{yyyy}",   # 12051987
        f"{mm}{dd}{yyyy}",   # 05121987
        f"{dd}{mm}{yy}",     # 120587
        f"{yy}{mm}{dd}",     # 870512
        f"{mm}{dd}{yy}",     # 051287
        f"{yyyy}",           # 1987
        f"{dd}{mm}",         # 1205
        f"{mm}{dd}",         # 0512
        f"{dd}",             # 12
        f"{mm}",             # 05
        f"{yy}",             # 87
        f"{dd}-{mm}-{yyyy}", # 12-05-1987
        f"{yyyy}-{mm}-{dd}", # 1987-05-12
        f"{dd}/{mm}/{yyyy}", # 12/05/1987
        f"{dd}.{mm}.{yyyy}", # 12.05.1987
    ]

    # Deduplicar manteniendo orden
    seen = set()
    for c in combos:
        if c not in seen:
            seen.add(c)
            formats.append(c)

    return formats


# ── Extracción NLP local de descripcion_persona ───────────────────────────────

def extract_entities_from_description(text: str) -> dict:
    """
    Extrae entidades relevantes de texto libre usando regex y heurísticas.
    Es un pre-procesamiento local antes de enviar a Gemini.

    Returns:
        Dict con listas de: years, numbers, keywords, acronyms, proper_nouns
    """
    if not text:
        return {
            "years": [], "numbers": [], "keywords": [],
            "acronyms": [], "proper_nouns": [],
        }

    entities: dict[str, list[str]] = {
        "years": [],
        "numbers": [],
        "keywords": [],
        "acronyms": [],
        "proper_nouns": [],
    }

    # Años (1940-2030)
    years = re.findall(r"\b(19[4-9]\d|20[0-3]\d)\b", text)
    entities["years"] = list(set(years))

    # Números de 2-6 dígitos (posibles años cortos, días especiales, etc.)
    numbers = re.findall(r"\b\d{2,6}\b", text)
    entities["numbers"] = list(set(numbers))[:20]  # Limitar

    # Acrónimos (2-6 letras mayúsculas, ej. PUCP, TCG, LAN)
    acronyms = re.findall(r"\b([A-Z]{2,6})\b", text)
    entities["acronyms"] = list(set(acronyms))

    # Palabras en mayúscula que probablemente son nombres propios o lugares
    # (Excluir inicio de oración para reducir falsos positivos)
    sentences = re.split(r"[.!?]", text)
    keywords = []
    for sentence in sentences:
        words = sentence.split()
        for i, word in enumerate(words):
            if i == 0:
                continue  # Saltar primera palabra de oración
            clean_word = re.sub(r"[^\w]", "", word)
            if clean_word and clean_word[0].isupper() and len(clean_word) > 2:
                keywords.append(clean_word)

    # Nombres propios multi-palabra (ej. "Alianza Lima", "Dragon Ball")
    proper_nouns = re.findall(
        r"\b([A-Z][a-záéíóúñ]+(?:\s+[A-Z][a-záéíóúñ]+)+)\b", text
    )
    entities["proper_nouns"] = list(set(proper_nouns))[:20]

    # Extraer palabras clave significativas incluso en minúsculas
    # (nombres de juegos, plataformas, tecnologías comunes)
    known_patterns = re.findall(
        r"\b(valorant|dota|fortnite|minecraft|league|legends|overwatch|"
        r"csgo|counter|strike|apex|genshin|pokemon|yugioh|digimon|"
        r"naruto|dragon\s*ball|one\s*piece|bleach|jujutsu|"
        r"steam|discord|twitch|tiktok|instagram|youtube|reddit|"
        r"bitcoin|ethereum|crypto|blockchain|binance|"
        r"arduino|raspberry|python|javascript|java|react|"
        r"anime|manga|otaku|cosplay|k-?pop|j-?pop|"
        r"mecatronica|mecatrónica|electronica|electrónica|"
        r"ingenieria|ingeniería|sistemas|software|"
        r"futbol|fútbol|basket|voley|"
        r"apuestas|casino|poker|ruleta|"
        r"criptomonedas?|trading|nft)\b",
        text, re.IGNORECASE
    )
    known_unique = list(set(p.strip().lower() for p in known_patterns))

    entities["keywords"] = list(set(keywords + known_unique))[:50]

    return entities

