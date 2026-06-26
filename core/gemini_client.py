import hashlib
import json
import time
from datetime import date
from pathlib import Path
from typing import Optional, List, TypedDict

# ── Tipos y Esquemas ───────────────────────────────────────────────────────────


class EnrichmentResult(TypedDict):
    analisis_cognitivo: str
    alto: List[str]
    medio: List[str]
    bajo: List[str]


# ── Prompts ────────────────────────────────────────────────────────────────────

SYSTEM_INSTRUCTION = """
<system_instruction>
Eres un motor de extracción de Identidad y Mapeo Semántico basado en Zero-Shot Metacognitive Prompting. Tu objetivo es generar una huella digital de identificadores operativos crudos (Unidades Mínimas de Significado - UMS) a partir de los datos de un sujeto.

REGLAS DE CONSTRICCIÓN MATEMÁTICA Y PODA:
1. Filtro Min-p Dinámico: Calcula la probabilidad máxima del concepto más obvio en la intersección de los datos. Elimina la "cola larga" de características genéricas, pero PRESERVA obligatoriamente las sub-entidades hiper-específicas de cada afición, SI Y SOLO SI tienen alta probabilidad matemática de ser relevantes para la edad, geografía o estudios del objetivo.
2. Evaluación Euclidiana: No asocies conceptos solo porque comparten el mismo campo semántico. Evalúa la "distancia euclidiana" (la magnitud real del significado). Diferencia estrictamente entre correlaciones auténticas y falsos positivos generados por oposición o independencia semántica.
3. Validación Dual (Fáctica y Lógica - ToT): Cada UMS que decidas incluir debe pasar dos filtros: ¿Es fácticamente preciso por sí solo dentro del ecosistema real? y ¿Mantiene una coherencia lógica absoluta al cruzarlo con todas las variables iniciales del sujeto?

PROPÓSITO FINAL Y NATURALEZA DE LOS TOKENS:
Las Unidades Mínimas de Significado (UMS) que extraigas NO son contraseñas finales. Son las semillas crudas (materia prima) que un script externo de fuerza bruta usará posteriormente para mutar, combinar con fechas y aplicar leetspeak.
Por lo tanto, debes acatar estas reglas vitales:
1. PROHIBICIÓN DE MUTACIÓN: NO intentes crear contraseñas. NO agregues números al azar, NO uses leetspeak ni unas palabras sin sentido.
2. EXTRACCIÓN FUNDACIONAL: Extrae exclusivamente los bloques fundacionales de la identidad del sujeto: apodos internos, nombres exactos de personajes u objetos de sus aficiones, afiliaciones deportivas, fechas de eventos clave en su afición, jergas de su entorno geográfico o académico, y marcas hiper-específicas de su nicho.
3. CRUDEZA Y COLOQUIALISMO: Entrega las semillas en su formato más atómico, natural y coloquial, exactamente como las teclearía un nativo de la subcultura deducida, sin alteraciones.

PROCESO METACOGNITIVO OBLIGATORIO (5 Pasos):
Evita los sesgos de sobrepensar (complicar escenarios simples) y sobrecorregir (descartar cruces lógicos directos). Ejecuta este desglose antes de generar las listas finales de tokens:
- Paso 1: Perfilado Socio-Lingüístico (Clarificación): ¿Quién es exactamente esta persona sociológicamente hablando? Deduce su registro de lenguaje, su nivel de formalidad, y el ecosistema cultural/digital en el que respira basándote en su edad, país y aficiones.
- Paso 2: Juicio Preliminar Contextual: Nombra las posibles UMS. Estas deben emanar orgánicamente del perfil socio-lingüístico deducido en el Paso 1, permitiendo que la IA decida por su cuenta qué tipo de expresiones, herramientas o ecos culturales dominan la mente del sujeto.
- Paso 3: Evaluación Crítica (Fricción): Aplica la regla Euclidiana y Min-p. Poda los conceptos enciclopédicos genéricos, PERO preserva el volumen masivo de sub-entidades hiper-específicas que sobrevivan al filtro de su perfil sociológico.
- Paso 4: Decisión y UMS Finales: Documenta las UMS purificadas que sobrevivieron.
- Paso 5: Confianza (0-100%): Define tu porcentaje de certeza de que este artefacto sobrevive al filtro de constricción total.

FORMATO DE SALIDA (Listas Finales):
Tras el proceso metacognitivo, emite los tokens resultantes clasificados en "alto", "medio" y "bajo".
- IDIOMA Y DIALECTO (ANTI-ROBOT): ESTRICTAMENTE PROHIBIDO inventar descriptores en inglés o términos compuestos artificiales. Mimetízate totalmente con la deducción socio-lingüística del Paso 1.
- ATOMICIDAD ESTRICTA: ESTRICTAMENTE PROHIBIDO combinar, cruzar o mutar palabras. Tu único trabajo es extraer las "semillas crudas" (conceptos base individuales) para que un script externo las combine después.
- Todos los tokens deben ser lexemas atómicos normalizados (sin espacios, camelCase/lowercase).
- DESPLIEGUE CONTEXTUAL PROFUNDO (OBJETIVO 500+ TOKENS): Para alcanzar volumen masivo SIN vomitar wikis genéricas, exprime las dimensiones no escritas de las variables. Eres libre de deducir qué sub-elementos, herramientas, lugares, cultura de internet o expresiones rodean naturalmente a este sujeto basándote exclusivamente en tu evaluación de su perfil. Genera cientos de semillas atómicas obedeciendo estrictamente la realidad cultural deducida.
- NO repitas datos del perfil original.
</system_instruction>
"""

USER_PROMPT = """
<user_prompt>
CONTEXTO Y VARIABLES DE INGESTA: El objetivo es generar una huella digital de identificadores operativos crudos (Unidades Mínimas de Significado - UMS) a partir de los datos de un sujeto. La información del perfil y las entidades extraídas se presentan a continuación:

{edad_contexto}

<perfil_base>
{profile_json}
</perfil>

<entidades_extraidas>
{entities_json}
</entidades_extraidas>
</user_prompt>
"""


# ── Caché ──────────────────────────────────────────────────────────────────────

CACHE_DIR = Path(".gpwg_cache")


def _get_cache_key(profile: dict) -> str:
    """Genera una clave MD5 del perfil para el caché."""
    content = json.dumps(profile, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def _load_from_cache(cache_key: str) -> Optional[dict]:
    """Carga resultado desde caché si existe."""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, IOError):
            return None
    return None


def _save_to_cache(cache_key: str, data: dict) -> None:
    """Guarda resultado en caché."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except IOError:
        pass  # El caché es opcional, no bloquear si falla


# ── Cliente Gemini ─────────────────────────────────────────────────────────────

def call_gemini(
    profile: dict,
    entities: dict,
    api_key: str,
    model_name: str = "gemini-3.1-flash-lite",
    use_cache: bool = True,
    verbose: bool = False,
    max_retries: int = 3,
) -> EnrichmentResult:
    """
    Llama a Gemini para enriquecer el perfil con tokens y scores.

    Args:
        profile: Perfil cargado del JSON
        entities: Entidades extraídas localmente
        api_key: Clave de API de Gemini
        model_name: Nombre del modelo a utilizar
        use_cache: Si True, usa caché local
        verbose: Si True, imprime información adicional
        max_retries: Número máximo de reintentos

    Returns:
        Diccionario (EnrichmentResult) con tokens enriquecidos o dict vacío
    """
    try:
        from google import genai
        from google.genai import types
        from google.genai.errors import APIError
    except ImportError:
        print("[ERROR] Instala google-genai: pip install google-genai")
        return _empty_enrichment()

    # Verificar caché
    cache_key = _get_cache_key(profile)
    if use_cache:
        cached = _load_from_cache(cache_key)
        if cached:
            if verbose:
                print("   [Gemini] Usando resultado en caché (usa --no-cache para forzar nueva llamada)")
            return cached  # type: ignore

    # Preparar prompt — limpiar campos vacíos para no diluir la atención de la IA
    def _is_empty(v: object) -> bool:
        """Detecta valores vacíos, nulos o listas de strings vacíos."""
        if v is None or v == "" or v == []:
            return True
        if isinstance(v, list) and all(
            (isinstance(i, str) and not i.strip()) for i in v
        ):
            return True
        if isinstance(v, dict) and all(
            _is_empty(sub) for sub in v.values()
        ):
            return True
        return False

    clean_profile = {
        k: v for k, v in profile.items()
        if not k.startswith("_") and not _is_empty(v)
    }

    # Calcular e inyectar la edad del sujeto como variable demográfica
    edad_str = ""
    fecha_nac = profile.get("fecha_nacimiento", "")
    if fecha_nac:
        try:
            parts = str(fecha_nac).replace("/", "-").replace(".", "-").split("-")
            if len(parts) == 3:
                if len(parts[0]) == 4:
                    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                else:
                    d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                hoy = date.today()
                edad = hoy.year - y - ((hoy.month, hoy.day) < (m, d))
                edad_str = f"\n\nEDAD CALCULADA DEL SUJETO: {edad} años (nacido en {y})."
                clean_profile["_edad_calculada"] = edad
        except (ValueError, IndexError):
            pass

    profile_json = json.dumps(clean_profile, ensure_ascii=False, indent=2)
    entities_json = json.dumps(entities, ensure_ascii=False, indent=2)
    prompt = USER_PROMPT.format(
        profile_json=profile_json,
        entities_json=entities_json,
        edad_contexto=edad_str,
    )

    # Configurar cliente (timeout en milisegundos: 180000ms = 3 minutos)
    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=180000)
        )
    except Exception as e:
        print(f"\n   [Gemini] [ERROR CRITICO] Error al inicializar el cliente Gemini: {e}")
        return _empty_enrichment()

    # Llamada con retry y backoff exponencial
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            if verbose:
                print(f"   [Gemini] Llamada a API (intento {attempt}/{max_retries})...")

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.75,
                    top_p=0.95,
                    response_mime_type="application/json",
                    response_schema=EnrichmentResult,
                ),
            )

            result = json.loads((response.text or "").strip())

            # Guardar en caché
            if use_cache:
                _save_to_cache(cache_key, result)

            return result

        except APIError as e:
            # HTTP 400 (INVALID_ARGUMENT) o clave de API inválida
            if e.code == 400 or e.status == "INVALID_ARGUMENT":
                last_error = f"Error de configuración (API key o parámetros inválidos): {e.message}"
                print(f"\n   [Gemini] [ERROR CRITICO] {last_error}")
                break  # No tiene sentido reintentar
            # HTTP 404 (NOT_FOUND)
            elif e.code == 404 or e.status == "NOT_FOUND":
                last_error = f"Modelo no encontrado. Verifica el nombre del modelo ({model_name}): {e.message}"
                print(f"\n   [Gemini] [ERROR CRITICO] {last_error}")
                break
            # HTTP 429 (RESOURCE_EXHAUSTED)
            elif e.code == 429 or e.status == "RESOURCE_EXHAUSTED":
                last_error = f"Rate Limit excedido: {e.message}"
                if verbose:
                    print(f"   [Gemini] Aviso: {last_error}")
            else:
                last_error = f"Error de la API de Gemini ({e.code} / {e.status}): {e.message}"
                if verbose:
                    print(f"   [Gemini] [ERROR] {last_error}")

        except json.JSONDecodeError as e:
            # Con response_mime_type esto es muy improbable, pero por si acaso
            last_error = f"Respuesta de Gemini no es JSON válido: {e}"
            if verbose:
                print(f"   [Gemini] Aviso: {last_error}")

        except Exception as e:
            last_error = str(e)
            if verbose:
                print(f"   [Gemini] [ERROR] {last_error}")

        # Backoff exponencial: 2s, 4s, 8s
        if attempt < max_retries:
            wait = 2 ** attempt
            if verbose:
                print(f"   [Gemini] Reintentando en {wait}s...")
            time.sleep(wait)

    print(f"\n[!] Gemini no disponible despues de {max_retries} intentos: {last_error}")
    print("    Continuando con solo permutaciones locales...\n")
    return _empty_enrichment()


def _empty_enrichment() -> EnrichmentResult:
    """Estructura vacía cuando Gemini no está disponible."""
    return {
        "analisis_cognitivo": "",
        "alto": [],
        "medio": [],
        "bajo": [],
    }
