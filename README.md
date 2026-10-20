# Reels Studio 🎬

Agente **local** (en tu computador, sin nube y sin login) que crea reels verticales
1080×1920 con un **avatar que habla**, a partir de:

1. Una **foto** del presentador.
2. Un **texto de contexto**: el agente escribe el guion con IA local (Gemma 4).
3. Un **fondo de Pexels** (video o foto) que eliges de una galería.

Resultado: presentador hablando, textos en pantalla, captura de apoyo en marco de
celular y un cierre con tu logo y tu Instagram.

## ¿Cómo funciona?

```
Contexto ──► Gemma 4 (llama-server) ──► Guion JSON validado ──► (lo editas)
Guion    ──► Kokoro TTS (voz en español) ──► voz.wav
Foto+voz ──► ComfyUI: RMBG (fondo → verde) ──► SadTalker (cara que habla) ──► avatar.mp4
Pexels   ──► fondo descargado (solo *.pexels.com, https)
Todo     ──► ffmpeg: fondo + avatar (chroma key) + textos + mockup + cierre ──► reel.mp4
         ──► verificación (1080×1920, audio, duración) ──► ✅ listo / ❌ error claro
```

**Regla de oro:** el LLM solo redacta un JSON; orden, validación y render son código
determinista. El reel solo se marca "listo" si pasa la verificación.

## Instalación (una vez)

```bash
cp .env.example .env      # pega tu llave gratis de https://www.pexels.com/api/
make install              # backend, frontend, ComfyUI, SadTalker y modelos (~6 GB)
```

## Uso

```bash
make run                  # ComfyUI + API + editor
```

Abre http://localhost:5173 y sigue la barra derecha:

1. **Avatar**: sube la foto (de frente, buena luz) y elige la voz.
2. **Guion**: describe el reel → "Generar guion con IA". Edita cada escena.
3. **Fondo**: búsquedas sugeridas o la tuya (en inglés funciona mejor).
4. **Marca**: tu @usuario, el logo del cierre y (opcional) una captura de apoyo.
5. **🎬 Generar reel**: progreso por etapas; al final lo ves y descargas el MP4.

## Arquitectura limpia

| Capa | Carpeta | Contenido |
|---|---|---|
| Dominio | `backend/src/reels_studio/domain` | Entidades puras y errores |
| Aplicación | `.../application` | Puertos y casos de uso (`RenderReel`, `GenerateScript`…) |
| Infraestructura | `.../infrastructure` | llama.cpp, Pexels, Kokoro, ComfyUI, ffmpeg, SQLite |
| Interfaz | `.../interfaces/http` | FastAPI: DTOs, routers, seguridad |
| Nodo ComfyUI | `comfyui_nodes/reels_studio` | `ReelsSadTalker` (SadTalker en su propio venv) |
| Workflow | `workflows/avatar_talking_head.json` | LoadImage → RMBG → ReelsSadTalker |
| Editor | `frontend/src/features` | Tipo Google Vids: escenas · lienzo 9:16 · herramientas · línea de tiempo |

**Patrones usados:**
- *Ports & Adapters*: cambiar de motor sin tocar los casos de uso.
- *Strategy*: animador del avatar.
- *Template Method*: pipeline de render.
- *Builder*: filtergraph de ffmpeg.
- *Repository*: SQLite.
- *Observer* (SSE): progreso.
- Mapa de manejadores en el reducer.

## Seguridad (OWASP) → prueba

| Control | Prueba |
|---|---|
| Subidas: magic bytes, límites, re-codificación PNG (sin EXIF ni cargas ocultas) | `tests/security/test_owasp_controls.py` |
| Path traversal: archivos solo por UUID | `test_file_store_only_resolves_uuid_names`, `test_files_endpoint_rejects_traversal` |
| SSRF: descargas solo `*.pexels.com` por https, redirecciones validadas | `test_downloader_blocks_non_pexels_urls` |
| Inyección de comandos: lista de argumentos; texto renderizado como imagen | `test_filtergraph_builds_argument_list_without_shell` |
| LLM01/LLM02: contexto delimitado, salida validada por esquema | `test_user_context_cannot_escape_data_block`, `test_script_writer_rejects_malformed_json` |
| Exposición: solo 127.0.0.1, CORS, cabeceras, rate limit, sin trazas | `test_security_headers_present`, `test_unexpected_error_does_not_leak_internals` |
| Secretos: llave de Pexels solo en `.env`, nunca llega al navegador | `make lint` (gitleaks) |

## Comandos

```bash
make test   # pruebas backend (sin modelos ni red)
make lint   # ruff + mypy --strict + eslint + tsc + gitleaks
```
