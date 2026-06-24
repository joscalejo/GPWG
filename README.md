# GPWG — Generative Password Wordlist Generator

Herramienta CLI en Python que genera wordlists personalizadas y priorizadas combinando **permutaciones inteligentes locales** con **enriquecimiento de Gemini AI**.

> [!WARNING]
> Esta herramienta es exclusivamente para auditorias de seguridad autorizadas y pentesting etico. El uso no autorizado puede ser ilegal y esta estrictamente prohibido.

---

## Características

- **Enriquecimiento con Gemini AI** — Analiza el perfil y asigna scores de importancia (1–10) a cada token
- **Permutaciones priorizadas** — Genera mas combinaciones para tokens con score alto
- **Cache local** — No repite llamadas a Gemini si el perfil no cambio
- **Retry con backoff** — 3 reintentos automaticos si Gemini falla
- **Multiples formatos** — `txt`, `json` (con metadata), `hashcat`
- **Reporte de auditoria** — JSON con todos los tokens, scores y metricas
- **Modo dry-run** — Simula sin escribir archivos
- **Fechas inteligentes** — 16+ formatos por cada fecha
- **Normalizacion** — Quita acentos, genera variantes de nombres automaticamente

---

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/GPWG.git
cd GPWG

# Instalar dependencias
pip install -r requirements.txt
```

### Dependencias

| Paquete | Versión | Uso |
|---|---|---|
| `google-generativeai` | ≥0.8.0 | Cliente de Gemini AI |
| `tqdm` | ≥4.66.0 | Barras de progreso |
| `unidecode` | ≥1.3.8 | Normalización de texto |

---

## Uso Rápido

### 1. Generar una plantilla de perfil

```bash
python gpwg.py --template objetivo.json
```

### 2. Editar el perfil

Abre `mi_perfil.json` y llena los datos. El campo `descripcion_persona` es el más importante — escribe un texto natural y detallado.

### 3. Ejecutar

```bash
python gpwg.py --profile mi_perfil.json --api-key TU_CLAVE_GEMINI --max 30000
```

La clave también puede estar en la variable de entorno:
```bash
$env:GEMINI_API_KEY = "TU_CLAVE"   # PowerShell
python gpwg.py --profile mi_perfil.json
```

---

## Flags de la CLI

| Flag | Default | Descripción |
|---|---|---|
| `--profile` / `-p` | requerido | Ruta al archivo JSON del perfil |
| `--api-key` / `-k` | `$GEMINI_API_KEY` | Clave de API de Gemini |
| `--output` / `-o` | `wordlist_[nombre].txt` | Archivo de salida |
| `--format` / `-f` | `txt` | Formato: `txt`, `json`, `hashcat` |
| `--max` / `-m` | `30000` | Máximo de contraseñas |
| `--min-length` | `6` | Longitud mínima |
| `--max-length` | `32` | Longitud máxima |
| `--no-gemini` | `false` | Solo permutaciones locales |
| `--no-cache` | `false` | Forzar nueva llamada a Gemini |
| `--dry-run` | `false` | Simular sin escribir archivo |
| `--verbose` / `-v` | `false` | Mostrar tokens y scores |
| `--no-report` | `false` | No generar reporte de auditoría |
| `--template` | — | Generar JSON de ejemplo |

---

## Estructura del Perfil JSON

```json
{
  "nombre_completo": "Juan Carlos Pérez García",
  "fecha_nacimiento": "1987-05-12",
  "apodos": ["Juanca", "JC"],
  "mascotas": ["Max", "Luna"],
  "familiares": {
    "pareja": "María López",
    "hijos": ["Santiago"]
  },
  "ciudad_nacimiento": "Guadalajara",
  "ciudad_residencia": "Ciudad de México",
  "equipos_favoritos": ["Chivas"],
  "redes_sociales": {
    "instagram": "juanca87"
  },
  "empresa": "TechCorp",
  "intereses": ["fútbol", "gaming", "Metallica"],
  "palabras_clave_extra": ["dragon", "7"],
  "descripcion_persona": "Texto detallado y natural sobre la persona..."
}
```

### Campos requeridos
- `nombre_completo`
- `fecha_nacimiento` (formato: `YYYY-MM-DD`)

### Consejos para `descripcion_persona`
- Menciona mascotas pasadas, frases favoritas, eventos importantes
- Incluye apodos de infancia o en el trabajo
- Nombra películas, músicos, personajes que admira
- Fechas especiales distintas al cumpleaños (aniversario, logros, etc.)

---

## Flujo de Ejecución

```
Usuario → Crea JSON con descripción detallada
    ↓
Carga y validación del JSON (con calidad %)
    ↓
Normalización + extracción NLP local
    ↓
Gemini AI analiza y asigna scores (con caché)
    ↓
Motor extrae todos los tokens con scores 1-10
    ↓
Permutaciones inteligentes (más para score alto)
    ↓
Filtros + ordenamiento por probabilidad
    ↓
wordlist_[nombre].txt  +  _report.json
```

---

## Ejemplos de Uso

### Solo local (sin API)
```bash
python gpwg.py --profile perfil.json --no-gemini
```

### Modo verbose (ver tokens y scores)
```bash
python gpwg.py --profile perfil.json --api-key TU_CLAVE --verbose
```

### Salida en formato JSON con metadata
```bash
python gpwg.py --profile perfil.json --api-key TU_CLAVE --format json
```

### Probar sin escribir archivos
```bash
python gpwg.py --profile perfil.json --api-key TU_CLAVE --dry-run --verbose
```

### Contraseñas más largas, máximo 5000
```bash
python gpwg.py --profile perfil.json --api-key TU_CLAVE --max 5000 --min-length 8 --max-length 20
```

### Forzar re-análisis de Gemini (ignorar caché)
```bash
python gpwg.py --profile perfil.json --api-key TU_CLAVE --no-cache
```

---

## Estructura del Proyecto

```
GPWG/
├── gpwg.py                       # CLI principal
├── requirements.txt
├── target_profile.example.json   # Plantilla documentada
├── README.md
└── core/
    ├── loader.py          # Carga y validación del JSON
    ├── normalizer.py      # Normalización, fechas, NLP local
    ├── gemini_client.py   # Cliente Gemini + caché + retry
    ├── token_extractor.py # Tokens con scores
    ├── permutator.py      # Motor de permutaciones
    ├── filters.py         # Filtros, formatos de salida
    └── reporter.py        # Resumen en consola + reporte JSON
```

---

## Caché

Las respuestas de Gemini se guardan en `.gpwg_cache/` (en el directorio actual).
El nombre del archivo es el hash MD5 del perfil JSON, por lo que:
- Si el perfil no cambia → se reutiliza la respuesta anterior
- Si cambias cualquier campo → se hace una nueva llamada

Usa `--no-cache` para forzar siempre una nueva llamada.

---

## Licencia

MIT — Uso libre para fines legales y autorizados.

**Disclaimer**: El autor no se hace responsable por el uso indebido de esta herramienta.
