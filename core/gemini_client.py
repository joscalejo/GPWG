"""
gemini_client.py — Cliente para Gemini AI con caché y retry.

Envía el perfil a Gemini para obtener tokens enriquecidos con scores.
Implementa caché local (evita llamadas repetidas), retry con backoff exponencial,
y Structured Outputs (JSON Schema) para mayor robustez.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Optional, List, TypedDict

# ── Tipos y Esquemas ───────────────────────────────────────────────────────────

class Token(TypedDict):
    valor: str
    tipo: str
    score: int
    razon: str

class EnrichmentResult(TypedDict):
    tokens: List[Token]
    apodos_sugeridos: List[str]
    patrones_detectados: List[str]
    notas: str

# ── Prompts ────────────────────────────────────────────────────────────────────

SYSTEM_INSTRUCTION = """
<system_instruction>
Eres un motor analítico avanzado diseñado para la deducción contextual profunda, el perfilado psicológico y la generación de inteligencia. Tu objetivo es procesar conjuntos de datos aislados, reconstruir el tejido sociológico y cultural del individuo objetivo, y extraer tokens de alta entropía semántica para la generación de wordlists de seguridad.

<marco_cognitivo>
Debes procesar la información ejecutando estrictamente el siguiente flujo secuencial:

1. Abstracción del Dato Crudo:
Extrae las meta-propiedades de cada dato operando bajo un espectro analítico multidimensional. Para mantener un perfilado de alcance universal y evitar el anclaje categórico, es obligatorio categorizar la información evaluando amplias dimensiones conceptuales. Utiliza, de manera obligatoria pero no excluyente, los siguientes vectores:

- Ejes Estructurales (Realidad Físico-Temporal):
  * Temporalidad y Ritmos Vitales: Cohorte generacional, frecuencias de actividad cíclica, exposición histórica a macro-eventos y etapas de desarrollo formativo.
  * Geografía y Movilidad: Densidad y escala de su entorno operativo (físico y digital), vectores de desplazamiento habituales y fronteras de su ecosistema de interacción.
  * Demografía Aplicada: Esfera de formación e instrucción, rol estructural/productivo dentro de su entorno social, y dinámicas de vinculación interpersonal.

- Ejes Conductuales (Mecánicas Psicológicas, Económicas y Sociales):
  * Patrones de Consumo y Adopción: Umbrales de asimilación ante nuevos estímulos o herramientas, criterios de selección de recursos, y nivel de dependencia hacia agentes externos.
  * Economía Implícita: Flujos de gestión de recursos, prioridades de inversión vital (tiempo/capital), y marcadores estructurales de su estrato de supervivencia o comodidad.
  * Perfilado Psicológico Latente: Esquemas de mitigación de riesgos y amenazas, anclajes de estabilidad emocional, motores primarios de motivación, y heurísticas o sesgos en la toma de decisiones.
  * Adhesión Tribal y Cultura: Códigos de pertenencia colectiva, sistemas de validación grupal, dialectos o jergas de aislamiento tribal, y arquetipos de influencia que guían su conducta.

Prohibido analizar datos de forma aislada. Todo punto de información tiene consecuencias interseccionales inmediatas. Si durante el análisis detectas una nueva dimensión conceptual subyacente que no esté listada aquí, es tu obligación extraerla e incorporarla al perfil.

2. Triangulación Contextual:
Intersecta las coordenadas espacio-temporales con los intereses explícitos.
Eje analítico: ¿Qué implicaciones sociológicas tiene poseer [Interés A] dentro de [Coordenada Geográfica B] durante [Periodo de Vida C]?
El resultado de esta intersección define el "Nicho Específico" o "Cohorte Cultural" del objetivo.

3. Activación de Conocimiento Latente (Derivación de Entidades):
Utiliza tu red de conocimiento global para extraer entidades tangibles, específicas y localizadas asociadas al Nicho Específico. Genera ramificaciones obligatorias hacia:
- Vectores de Entretenimiento: Figuras de autoridad, creadores, medios consumidos o ecosistemas digitales intrínsecos a la cohorte.
- Vectores Lingüísticos: Dialectos de subculturas, coloquialismos regionales, o modismos propios de su demografía.
- Vectores Histórico-Nostálgicos: Hitos culturales, eventos o productos que definieron sus etapas formativas críticas en su región particular.

4. Síntesis de Tokens (Formato de Wordlist):
Traduce estas entidades en cadenas de caracteres atómicas. 
Regla de mutación: Genera variantes lingüísticas naturales, abreviaturas, concatenaciones sin espacios, y modificaciones fonéticas o sustituciones de caracteres comunes (ej. leet speak básico) que el individuo utilizaría instintivamente.
</marco_cognitivo>

<reglas_puntuacion>
Asigna un valor numérico (SCORE 1-10) de probabilidad de adopción por parte del usuario:
- 9-10: Datos primarios inmutables y deducciones de primer grado de extrema precisión, estadísticamente ineludibles al triangular el perfil.
- 7-8: Deducciones altamente probables derivadas de la triangulación de dos o más variables fuertes.
- 5-6: Elementos de ecosistemas más amplios y consumo masivo relacionado a su demografía.
- 1-4: Elementos periféricos o tangenciales de baja probabilidad de adopción personal.
</reglas_puntuacion>

<restricciones_salida>
1. Genera entre 60 y 150 tokens.
2. La salida debe ser estrictamente un objeto JSON válido. No es necesario añadir bloques de código markdown (```json), solo el JSON crudo.
3. El esquema a utilizar está predefinido en la API, pero asegúrate de llenar correctamente los campos basándote en esta estructura lógica:

{
  "tokens": [
    {
      "valor": "cadena_generada",
      "tipo": "categoria_del_token_ej_interes_o_jerga",
      "score": 8,
      "razon": "Justificación explícita de CÓMO interactuaron los datos (triangulación temporal, local y demográfica) para derivar esta entidad."
    }
  ],
  "apodos_sugeridos": ["variantes", "deducidas"],
  "patrones_detectados": ["patron_psicologico_1"],
  "notas": "Explicación general de tu deducción sociológica"
}
</restricciones_salida>
</system_instruction>
"""

USER_PROMPT = """
<user_prompt>
Inicia el proceso de deducción contextual profunda.
Aplica el marco cognitivo sobre los siguientes conjuntos de datos. Triangula las variables disponibles, deriva las entidades latentes de la cohorte cultural del individuo y genera los tokens resultantes, justificando exhaustivamente la cadena lógica utilizada en cada derivación dentro de la estructura JSON requerida.

<datos_base_estructurados>
{profile_json}
</datos_base_estructurados>

<entidades_locales_extraidas>
{entities_json}
</entidades_locales_extraidas>
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
        use_cache: Si True, usa caché local
        verbose: Si True, imprime información adicional
        max_retries: Número máximo de reintentos

    Returns:
        Diccionario (EnrichmentResult) con tokens enriquecidos o dict vacío
    """
    try:
        import google.generativeai as genai
        from google.api_core import exceptions as google_exceptions
    except ImportError:
        print("[ERROR] Instala google-generativeai: pip install google-generativeai")
        return _empty_enrichment()

    # Verificar caché
    cache_key = _get_cache_key(profile)
    if use_cache:
        cached = _load_from_cache(cache_key)
        if cached:
            if verbose:
                print("   [Gemini] Usando resultado en caché (usa --no-cache para forzar nueva llamada)")
            return cached

    # Preparar prompt
    clean_profile = {k: v for k, v in profile.items() if not k.startswith("_")}
    profile_json = json.dumps(clean_profile, ensure_ascii=False, indent=2)
    entities_json = json.dumps(entities, ensure_ascii=False, indent=2)
    prompt = USER_PROMPT.format(
        profile_json=profile_json,
        entities_json=entities_json,
    )

    # Configurar cliente
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=SYSTEM_INSTRUCTION,
    )

    # Llamada con retry y backoff exponencial
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            if verbose:
                print(f"   [Gemini] Llamada a API (intento {attempt}/{max_retries})...")

            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    response_mime_type="application/json",
                    response_schema=EnrichmentResult,
                ),
            )

            result = json.loads(response.text.strip())

            # Guardar en caché
            if use_cache:
                _save_to_cache(cache_key, result)

            return result

        except google_exceptions.InvalidArgument as e:
            # Errores en la clave de API o esquema
            last_error = f"Error de configuración (API key inválida o esquema): {e}"
            if verbose: print(f"   [Gemini] [ERROR] {last_error}")
            break # No tiene sentido reintentar

        except google_exceptions.ResourceExhausted as e:
            last_error = f"Rate Limit excedido: {e}"
            if verbose: print(f"   [Gemini] Aviso: {last_error}")

        except json.JSONDecodeError as e:
            # Con response_mime_type esto es muy improbable, pero por si acaso
            last_error = f"Respuesta de Gemini no es JSON válido: {e}"
            if verbose: print(f"   [Gemini] Aviso: {last_error}")
            
        except Exception as e:
            last_error = str(e)
            if verbose: print(f"   [Gemini] [ERROR] {last_error}")

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
        "tokens": [],
        "apodos_sugeridos": [],
        "patrones_detectados": [],
        "notas": "Enrichment de Gemini no disponible.",
    }
