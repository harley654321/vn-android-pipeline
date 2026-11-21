# Extracción: absolutamente todo el texto

## Paso 0 — Detectar el motor

```bash
python3 - <<'PY'
import zipfile, collections
z=zipfile.ZipFile("juego.apk")
for n in z.namelist():
    if n.startswith("lib/") and n.endswith(".so"):
        print(n)
PY
```

| Señal | Motor | Camino |
|---|---|---|
| `librenpython.so` | Ren'Py | este documento |
| `assets/bin/Data`, `libunity.so` | Unity | otro proceso |
| `www/`, `index.html` | RPG Maker MV / web | Capacitor |
| `data.win` | GameMaker | otro proceso |

Comprobar también la versión: `assets/x-game/x-script_version.txt`.

## Paso 1 — Reconstruir el proyecto

El build de Android de Ren'Py renombra **todo** con prefijo `x-`. Hay que
quitarlo de cada componente de la ruta.

```
assets/x-game/x-story/x-main_events.rpyc  →  game/story/main_events.rpyc
```

**Dos exclusiones obligatorias:**

- `x-cache/` — bytecode viejo, no sirve y estorba.
- `x-tl/` — **las traducciones que ya trae el juego**. Si no se excluyen, se
  mezclan con el texto base y la extracción sale contaminada.

## Paso 2 — Descompilar TODOS los `.rpyc`, recursivamente

Este es el fallo más caro que hemos tenido. Un `glob` de primer nivel extrajo
16 de 199 archivos y produjo 568 cadenas en vez de 25.323.

```python
rpyc = []
for root, _dirs, files in os.walk(game):
    for f in files:
        if f.endswith(".rpyc"):
            rpyc.append(os.path.relpath(os.path.join(root, f), game))
```

## Paso 3 — Corregir los fallos del descompilador

unrpyc no es perfecto. Dos casos conocidos:

**a) Revierte displayables de screen language personalizados a su base.**
Un addon registra `zoom_viewport`; unrpyc lo escribe como `viewport`, y entonces
Ren'Py rechaza `start_zoom` al parsear. Hay que restaurar el nombre original.

**b) Genera archivos vacíos.** Si un `.rpy` descompilado queda vacío pero existe
su `.rpyc`, se borra el `.rpy` para que Ren'Py cargue el `.rpyc` original.

## Paso 4 — Plantilla oficial de traducción

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy renpy.sh proj translate es
```

Esto lo genera el motor enumerando sus propias cadenas: no hay filtro que se
pueda equivocar. Produce `game/tl/es/**/*.rpy` con bloques `translate es <id>:`.

**Importante:** el resultado tiene subcarpetas. Hay que recorrerlas todas.

## Paso 5 — Convertir a CSV

Dos formatos conviven en los archivos generados:

- Diálogo y narración: `translate es <id>:` seguido de `quien "texto"` o solo
  `"texto"` (narración sin personaje — fácil de olvidar).
- Interfaz: `translate es strings:` con pares `old "..."` / `new "..."`.

## Paso 6 — Auditoría de cobertura (obligatoria)

Antes de entregar, contar:

- Cadenas totales del juego.
- Cadenas en el CSV.
- Diferencia y motivo de cada una.

Referencia real: **xxxFiles 0.3.3 → 25.323 cadenas, 1.112.541 caracteres,
22.769 de diálogo y 2.554 de interfaz.**

Si el número sale mucho más bajo de lo esperado, casi siempre es un `glob` que
no recorre subcarpetas.

## Caso especial: el juego ya trae traducción

Muchos juegos de f95zone incluyen `tl/spanish/`. Antes de traducir nada,
**medir la cobertura oficial**: se comparan los identificadores de bloque
(`translate spanish <id>` frente a `translate es <id>`).

Si cubre el 100 %, no hay nada que traducir: basta con forzar el idioma
(ver `docs/03-COMPILACION.md`).

Referencia real: **xxxFiles 0.3.3 trae 8 idiomas oficiales y el español cubre
25.199 de 25.200 cadenas (100 %).**
