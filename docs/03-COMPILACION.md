# Compilación y entrega

Hay dos situaciones distintas. Identificarlas antes de empezar ahorra días.

## Caso A — el juego ya trae traducción oficial

Comprobado con la auditoría de identificadores de `docs/01-EXTRACCION.md`.
No hay que traducir nada: solo activar el idioma.

```bash
# 1. mini proyecto solo con el override
mkdir -p /tmp/miniproj/game
cat > /tmp/miniproj/game/zzz_lang_es.rpy <<'R'
define config.language = "spanish"
R

# 2. compilar con el SDK de la MISMA version del juego
SDL_VIDEODRIVER=dummy renpy.sh /tmp/miniproj compile
# -> /tmp/miniproj/game/zzz_lang_es.rpyc

# 3. meter el .rpyc en el APK (con prefijo x-)
# 4. zipalign + apksigner
```

El nombre del idioma es el de la carpeta: `tl/spanish` → `"spanish"`.

## Caso B — traducimos nosotros

```bash
python3 tools/renpy_build.py juego.apk traducido.csv salida.apk --work <dir>
```

El script hace, en orden:

1. Rellena los bloques de `game/tl/es/**/*.rpy` con la columna `traduccion`.
2. Crea `game/zzz_lang_es.rpy` con `define config.language = "es"`.
3. Compila con el SDK.
4. Reempaqueta el APK **conservando todos los `.rpyc` originales** y añadiendo
   solo los nuevos.
5. Firma.

## Reempaquetar sin romper nada

- Se copian **todas** las entradas del APK original.
- Se añade la traducción como `assets/x-game/x-tl/x-es/x-*.rpyc` (prefijo `x-`).
- Los `.rpyc` del juego base **no se tocan**: si se sustituyen por los
  descompilados, se corre el riesgo de romper el juego.
- Para un APK de 1 GB conviene `ZIP_STORED`: recomprimir tarda muchísimo y no
  aporta nada.

## Firmar

```bash
zipalign -p -f 4 entrada.apk alineado.apk
apksigner sign --ks clave.keystore --ks-key-alias <alias> \
  --ks-pass pass:<clave> --key-pass pass:<clave> \
  --out final.apk alineado.apk
apksigner verify final.apk
```

**La clave de firma hay que conservarla.** Sin ella no se pueden publicar
actualizaciones del mismo paquete: Android las rechaza por firma distinta y el
usuario tiene que desinstalar.

## Verificar de verdad

Que `apksigner verify` diga OK solo prueba la firma. Falta comprobar que la
traducción está dentro:

```python
# abrir assets/x-game/x-tl/x-es/*.rpyc, descomprimir el pickle
# y comprobar que cada cadena traducida aparece en el blob
```

Referencia real: My Summer Job → **631 de 631 traducciones presentes**.

## Entrega

- Subir a **gofile.io**:

```bash
SRV=$(curl -s https://api.gofile.io/servers | python3 -c "import json,sys;print(json.load(sys.stdin)['data']['servers'][0]['name'])")
curl -F "file=@final.apk" "https://$SRV.gofile.io/contents/uploadfile"
```

- Los `.apk` están bloqueados en algunos alojadores por seguridad y el límite
  suele ser 200 MB. Si el APK pesa más, se entrega en `.zip`.
- gofile borra por inactividad: es un puente de entrega, no un archivo.
