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

1. Abstracción del Dato Crudo y Expansión de Vectores de Identidad:
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

- Ejes de Expresión y Frontera (Mecánicas de Emisión y Proyección):
  * Dimensión Cognitivo-Lingüística: Densidad léxica, sintaxis dominante, asimilación de múltiples idiomas/sistemas de códigos, y recurrencias fonéticas o tipográficas.
  * Barreras Ético-Ideológicas: Límites infranqueables (tabúes), alineación con dogmas o sistemas de creencias rígidos, y brújula moral implícita que restringe su marco de acción.
  * Proyección de Identidad (La Persona): Disonancia entre su realidad estructural y el rastro que decide emitir voluntariamente, identidades aspiracionales, y gestión de su máscara social/digital.

REGLA DE TRAZABILIDAD FORENSE (CERO ASUNCIONES): Prohibido analizar datos de forma aislada o generar deducciones abstractas sin respaldo empírico. Todo punto de información tiene consecuencias interseccionales inmediatas. Cada variable, parámetro o dimensión perfilada debe estar estrictamente anclada a una pieza de evidencia explícita presente en los datos crudos. Si detectas una dimensión que no puedes justificar con un dato real, descártala. Si durante el análisis detectas una nueva dimensión conceptual respaldada por evidencia que no esté listada aquí, es tu obligación extraerla e incorporarla al perfil.

2. Triangulación Contextual (Matriz de Colisión Dinámica):
Prohibido realizar cruces lineales simples o basarse en plantillas de intersección predefinidas. La triangulación debe ser estrictamente algorítmica y adaptativa a la naturaleza del conjunto de datos proporcionado.

Ejecuta el siguiente motor de inferencia para procesar los datos de la Fase 1:

- Identificación de Nodos Dominantes (Señal vs. Ruido): Analiza todas las dimensiones extraídas previamente. Aísla y selecciona únicamente los vectores que presenten la mayor "carga de anomalía" o el peso definitorio más alto para este individuo en particular. Descarta las dimensiones que presenten datos genéricos o de bajo impacto.
- Generación de Colisiones por Fricción: Fuerza la intersección cruzada de los Nodos Dominantes identificados, asegurándote de chocar variables que pertenezcan a ejes distintos (ej. cruzar una variable predominante del Eje Estructural con una del Eje Conductual o de Expresión).
- Eje de Deducción Universal: Por cada colisión generada, evalúa la intersección bajo la siguiente heurística: ¿Qué fricciones, limitaciones operativas, vulnerabilidades o necesidades absolutas se materializan cuando la realidad del [Nodo Dominante A] interactúa con las restricciones del [Nodo Dominante B]?
- Extracción de Anclajes de Identidad: Identifica cómo el individuo resuelve o gestiona las fricciones detectadas. Las soluciones a estas fricciones (herramientas, conceptos, afiliaciones, dogmas, lugares de refugio) constituyen sus "Anclas de Identidad".

El resultado de este cruce dinámico definirá el mapa topológico exacto de la mente del objetivo y su verdadera Cohorte Cultural, revelando los conceptos de alta entropía que utiliza como base de su seguridad personal.

3. Activación de Conocimiento Latente (Materialización Empírica de Entidades):
Utiliza tu red de conocimiento global para traducir las "Anclas de Identidad" abstractas (obtenidas en la Fase 2) en entidades tangibles, hiper-específicas y localizadas. Prohibido utilizar taxonomías, categorías o esferas predefinidas. El dominio de búsqueda debe ser completamente abierto, agnóstico y dictado de forma exclusiva por la naturaleza del perfil procesado.

Ejecuta el siguiente protocolo de materialización dinámica:

- Derivación de Dominios Relevantes: Basándote en las fricciones y anclas descubiertas en la Fase 2, identifica cuáles son las áreas específicas de la realidad (física, digital, conceptual, social, ocupacional, etc.) donde este individuo interactúa con mayor intensidad. Genera dinámicamente las categorías de extracción pertinentes para este caso único.
- Extracción de Sustantivos Propios: Para cada dominio generado, sumérgete en tu espacio latente y extrae los elementos empíricos exactos que conforman el ecosistema del individuo. Debes materializar abstracciones en nomenclaturas reales, hitos geográficos locales, marcas indispensables, herramientas específicas, dialectos, acrónimos o dogmas exactos.

REGLA DE REDUCCIÓN ONTOLÓGICA (ESPECIFICIDAD EXTREMA): Prohibido emitir Nodos Padre (categorías, familias, clases o conceptos plurales). Por cada entidad generada, es obligatorio aplicar un algoritmo de descenso semántico hasta aislar el Nodo Terminal (la instancia única e indivisible).

Mecánica de pensamiento requerida:
1. Nivel de Abstracción: Identifica el concepto o necesidad derivada de las colisiones anteriores.
2. Descenso de Manifestación: Desciende a la manifestación física, digital, social o teórica exacta de ese concepto.
3. Aislamiento del Identificador: Destila la manifestación hasta obtener su identificador único (nomenclaturas exactas, códigos de versión, coordenadas crudas, jergas atómicas, acrónimos indivisibles).

Heurística de validación: Someta su token final a esta prueba lógica: ¿El término generado admite subtipos, variaciones o modelos derivados? 
- Si la respuesta es SÍ, el nivel de resolución es insuficiente y el token es inválido. Debes descender un nivel más.
- Si la respuesta es NO (es indivisible y atómico), el token es válido.

4. Síntesis de Tokens (Motor de Fuzzing Semántico y Estructural):
Transforma los Nodos Terminales (obtenidos en la Fase 3) en lexemas atómicos. Tu objetivo es ejecutar saltos lógicos de nivel pragmático que un algoritmo de permutación tradicional (fuzzing de código) no puede realizar. Prohibido usar ejemplos predefinidos o anclarse a categorías humanas, técnicas o espaciales. El procesamiento debe ser puramente matemático-lingüístico.

Ejecuta el siguiente pipeline de transformación secuencial:

- Eje de Derivación Pragmática (Desplazamiento Semántico): Somete el Nodo Terminal a su heurística de uso real. Evalúa la disonancia entre la [Nomenclatura Oficial del Nodo] y el [Uso Pragmático en la Cohorte del Objetivo]. Deriva obligatoriamente el lexema equivalente que el individuo utilizaría en su entorno nativo (reducciones operativas, designaciones gremiales, hipocorísticos estructurales o sinónimos de aislamiento).
- Eje de Fusión Sintáctica: Fusiona el lexema derivado con anclajes secundarios extraídos de las colisiones previas (ej. hitos temporales o espaciales). La regla de concatenación (ej. camelCase, snake_case, unión plana, delimitadores) debe ser dictada exclusivamente por el nivel de [Sofisticación Técnica] y el [Ecosistema Operativo] del perfil.
- Eje de Degradación Lingüística: Aplica un truncamiento o compresión al lexema fusionado basándote estrictamente en la [Densidad Léxica] y el estrés ambiental del sujeto. Extrae las contracciones, acrónimos orgánicos o vicios de asimilación propios de su cohorte, sin inventar sustituciones aleatorias de caracteres.

HEURÍSTICA DE VALIDACIÓN (UMBRAL DE CARGA COGNITIVA): Somete el token resultante a una validación final contra el Eje Conductual del sujeto. Si la estructura generada exige una retención de memoria o un esfuerzo de tipado superior a la disciplina operativa o tolerancia al estrés del individuo, el token es lógicamente inválido y su entropía debe reducirse orgánicamente.
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
            return cached  # type: ignore

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
        model_name=model_name,
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
