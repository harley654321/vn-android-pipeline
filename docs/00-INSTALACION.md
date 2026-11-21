# Instalación del entorno

Todo esto lo automatiza `bash tools/bootstrap.sh`. Aquí está el detalle y el
motivo de cada pieza.

## 1. JDK 21 (obligatorio para compilar APK)

```bash
curl -L -o jdk21.tar.gz "https://api.adoptium.net/v3/binary/latest/21/ga/linux/x64/jdk/hotspot/normal/eclipse"
mkdir -p /opt/jdk21 && tar xzf jdk21.tar.gz -C /opt/jdk21 --strip-components=1
export JAVA_HOME=/opt/jdk21
export PATH=$JAVA_HOME/bin:$PATH
```

**Error típico:** `apksigner: exec: java: not found`. Es que `JAVA_HOME/bin` no
está en el `PATH` del proceso que firma. Cualquier script que firme debe
anteponerlo explícitamente.

## 2. Android SDK

```bash
curl -L -o cmdline.zip "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"
mkdir -p /opt/android-sdk/cmdline-tools
python3 -c "import zipfile;zipfile.ZipFile('cmdline.zip').extractall('/opt/android-sdk/cmdline-tools')"
mv /opt/android-sdk/cmdline-tools/cmdline-tools /opt/android-sdk/cmdline-tools/latest
chmod -R +x /opt/android-sdk/cmdline-tools/latest/bin
yes | sdkmanager --licenses
sdkmanager "platform-tools" "platforms;android-35" "build-tools;35.0.0"
```

**Error típico:** `sdkmanager: Permission denied`. Al descomprimir con Python se
pierden los bits de ejecución. Hay que hacer `chmod -R +x`.

## 3. Ren'Py SDK — la versión DEBE coincidir con el juego

Esto es crítico. Cada juego declara su versión en
`assets/x-game/x-script_version.txt`, por ejemplo `(8, 5, 2)`.

```bash
curl -L -o renpy.tar.bz2 "https://www.renpy.org/dl/8.5.2/renpy-8.5.2-sdk.tar.bz2"
mkdir -p tools/renpy-8.5.2
tar xjf renpy.tar.bz2 -C tools/renpy-8.5.2 --strip-components=1
```

**Error típico:** `Could not load file ... .rpyc`. Es un `.rpyc` compilado con
otra versión. Un SDK 8.3.7 no puede cargar un `.rpyc` de 8.5.2. Siempre se
descarga el SDK que diga `script_version.txt`.

## 4. unrpyc (descompilador de `.rpyc`)

```bash
curl -L -o unrpyc.zip "https://github.com/CensoredUsername/unrpyc/archive/refs/heads/master.zip"
python3 -c "import zipfile;zipfile.ZipFile('unrpyc.zip').extractall('tools')"
```

Se ejecuta con el Python del SDK, no con el del sistema:

```bash
PYTHONPATH=tools/renpy-8.5.2 tools/renpy-8.5.2/lib/py3-linux-x86_64/python \
  tools/unrpyc-master/unrpyc.py --clobber archivo.rpyc
```

**Error típico:** `ModuleNotFoundError: No module named 'decompiler'`. La versión
de un solo archivo no basta; hay que descargar el repositorio completo, que trae
la carpeta `decompiler/`.

## 5. Node 22 + Capacitor — SOLO para juegos WebGL

Los juegos de Ren'Py no lo necesitan. Para juegos web (three.js, RPG Maker MV)
hay que empaquetarlos con Capacitor porque `file://` rompe `fetch()` por CORS.

```bash
curl -L -o node.tar.xz "https://nodejs.org/dist/v22.23.5/node-v22.23.5-linux-x64.tar.xz"
mkdir -p /opt/node22 && tar xJf node.tar.xz -C /opt/node22 --strip-components=1
npm install @capacitor/core @capacitor/cli @capacitor/android
npx cap init "Juego" "com.autor.juego" --web-dir www
npx cap add android && npx cap sync android
cd android && ./gradlew assembleRelease
```

**Error típico:** `The Capacitor CLI requires NodeJS >=22.0.0`. Capacitor 8 no
funciona con Node 20.

## 6. Comprobación de núcleos

`nproc` **miente** en contenedores: puede devolver 1 cuando hay 4. Para saberlo
de verdad:

```bash
python3 -c "import os;print(len(os.sched_getaffinity(0)))"
```

Y si se mide con hilos, el GIL los serializa y parece que hay un núcleo. Hay que
medir con `multiprocessing`.

## Resumen de rutas

```
/opt/jdk21                          JDK 21
/opt/android-sdk                    Android SDK (build-tools 35.0.0)
/opt/node22                         Node 22 (solo WebGL)
tools/renpy-<version>               Ren'Py SDK (versión del juego)
tools/unrpyc-master/                descompilador
```
