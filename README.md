# Pipeline de ports Android (Ren'Py → español)

Todo lo necesario para tomar un APK de un juego de PC, extraer **el 100 % de su
texto**, traducirlo y devolver un APK firmado y funcional.

## Regla de oro

> **Nunca se da un texto por completo sin medir el total del juego.**
> Si no has contado cuántas cadenas tiene el juego y cuántas extrajiste, no has
> terminado. Todos los fallos graves de este proyecto han sido de cobertura.

## Arranque rápido en un entorno vacío

```bash
bash tools/bootstrap.sh          # instala JDK, Android SDK, Ren'Py SDK y unrpyc
python3 tools/renpy_extract.py juego.apk salida.csv --sdk tools/renpy-X.Y.Z
```

## El ciclo de trabajo

1. **Detectar el motor** (ver `docs/01-EXTRACCION.md`).
2. **Extraer todo** a un CSV de 8 columnas.
3. **Traducir** la columna `traduccion` (ver `docs/02-TRADUCCION.md`).
4. **Construir** el APK traducido y firmado (ver `docs/03-COMPILACION.md`).
5. **Auditar** y subir a gofile.

## Documentos

| Documento | Qué contiene |
|---|---|
| [docs/00-INSTALACION.md](docs/00-INSTALACION.md) | Qué instalar, cómo y por qué, según el entorno |
| [docs/01-EXTRACCION.md](docs/01-EXTRACCION.md) | Cómo extraer absolutamente todo el texto |
| [docs/02-TRADUCCION.md](docs/02-TRADUCCION.md) | El CSV, las reglas y el caso de las escenas explícitas |
| [docs/03-COMPILACION.md](docs/03-COMPILACION.md) | Compilar, empaquetar, firmar y entregar |
| [docs/04-FALLOS-CONOCIDOS.md](docs/04-FALLOS-CONOCIDOS.md) | **Checklist obligatoria**: cada fallo y su arreglo |
| [docs/05-REGLAS.md](docs/05-REGLAS.md) | Las reglas no negociables del proyecto |

## Herramientas

| Script | Para qué |
|---|---|
| `tools/bootstrap.sh` | Instala el entorno completo desde cero |
| `tools/renpy_extract.py` | APK → CSV con auditoría de cobertura |
| `tools/translate_csv.py` | Rellena la columna `traduccion` con un motor (o `dry` para probar) |
| `tools/renpy_build.py` | CSV traducido + APK → APK firmado |
| `tools/pipeline.py` | Los tres pasos en un solo comando |
