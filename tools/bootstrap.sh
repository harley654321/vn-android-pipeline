#!/usr/bin/env bash
# RENPY_VER: version del SDK de Ren'Py. DEBE coincidir con
# assets/x-game/x-script_version.txt del juego. Ej: 8.5.2
RENPY_VER="${RENPY_VER:-8.5.2}"
# bootstrap.sh - instala TODO lo necesario desde cero en un sandbox nuevo.
# Uso:  bash tools/bootstrap.sh
# Idempotente: si algo ya esta instalado, lo salta.
set -e

W="${W:-/app/conversations/$(ls /app/conversations | head -1)}"
TOOLS="$W/tools"
mkdir -p "$TOOLS"

say(){ printf "\n=== %s ===\n" "$1"; }

# ---------------------------------------------------------------- 1. JDK 21
say "JDK 21 (Adoptium Temurin)"
if [ ! -x /opt/jdk21/bin/java ]; then
  mkdir -p /opt/tools && cd /opt/tools
  curl -sL -o jdk21.tar.gz "https://api.adoptium.net/v3/binary/latest/21/ga/linux/x64/jdk/hotspot/normal/eclipse"
  mkdir -p /opt/jdk21 && tar xzf jdk21.tar.gz -C /opt/jdk21 --strip-components=1
fi
/opt/jdk21/bin/java -version 2>&1 | head -1

# ------------------------------------------------------- 2. Android SDK
say "Android SDK (cmdline-tools + platform 35 + build-tools 35)"
if [ ! -x /opt/android-sdk/cmdline-tools/latest/bin/sdkmanager ]; then
  mkdir -p /opt/tools /opt/android-sdk/cmdline-tools && cd /opt/tools
  curl -sL -o cmdline.zip "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"
  python3 -c "import zipfile;zipfile.ZipFile('/opt/tools/cmdline.zip').extractall('/opt/android-sdk/cmdline-tools')"
  mv /opt/android-sdk/cmdline-tools/cmdline-tools /opt/android-sdk/cmdline-tools/latest 2>/dev/null || true
  # OJO: extraer con Python NO conserva el bit de ejecucion. Sin esto: "Permission denied".
  chmod -R +x /opt/android-sdk/cmdline-tools/latest/bin
fi

# ------------------------------------------------------------- 3. Node 22
say "Node 22 (Capacitor 8 exige >=22; con Node 20 da EBADENGINE y aborta)"
if [ ! -x /opt/node22/bin/node ]; then
  cd /opt/tools
  V=$(curl -s https://nodejs.org/dist/index.json | python3 -c "import json,sys;d=json.load(sys.stdin);print([x['version'] for x in d if x['version'].startswith('v22.') and x.get('lts')][0].lstrip('v'))")
  curl -sL -o node22.tar.xz "https://nodejs.org/dist/v$V/node-v$V-linux-x64.tar.xz"
  mkdir -p /opt/node22 && tar xJf node22.tar.xz -C /opt/node22 --strip-components=1
fi

cat > /opt/env.sh <<'ENVEOF'
export JAVA_HOME=/opt/jdk21
export ANDROID_HOME=/opt/android-sdk
export ANDROID_SDK_ROOT=/opt/android-sdk
export PATH=/opt/node22/bin:$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH
ENVEOF
# shellcheck disable=SC1091
source /opt/env.sh
node -v; java -version 2>&1 | head -1

say "Licencias y paquetes del SDK"
if [ ! -d /opt/android-sdk/platforms/android-35 ]; then
  yes | sdkmanager --licenses >/dev/null 2>&1 || true
  sdkmanager "platform-tools" "platforms;android-35" "build-tools;35.0.0" >/dev/null
fi
ls /opt/android-sdk/build-tools /opt/android-sdk/platforms

# ---------------------------------------------------------- 4. Ren'Py SDK
say "Ren'Py SDK 8.3.7"
if [ ! -x "$TOOLS/renpy-${RENPY_VER}/renpy.sh" ]; then
  mkdir -p "$TOOLS" && cd "$TOOLS"
  curl -sL -o renpy-sdk.tar.bz2 "https://www.renpy.org/dl/${RENPY_VER}/renpy-${RENPY_VER}-sdk.tar.bz2"
  mkdir -p "$TOOLS/renpy-${RENPY_VER}"
  tar xjf renpy-sdk.tar.bz2 -C "$TOOLS/renpy-${RENPY_VER}" --strip-components=1
fi
ls "$TOOLS/renpy-${RENPY_VER}/renpy.sh"

# ------------------------------------------------------------ 5. unrpyc
say "unrpyc (descompilador de .rpyc)"
if [ ! -f "$TOOLS/unrpyc-master/unrpyc.py" ]; then
  cd "$TOOLS"
  curl -sL -o unrpyc.zip "https://github.com/CensoredUsername/unrpyc/archive/refs/heads/master.zip"
  python3 -c "import zipfile;zipfile.ZipFile('$TOOLS/unrpyc.zip').extractall('$TOOLS')"
fi
# OJO: hace falta el PAQUETE completo (carpeta decompiler/). El unrpyc.py suelto
# falla con ModuleNotFoundError: No module named 'decompiler'.
ls "$TOOLS/unrpyc-master" | head -3

say "LISTO"
echo "  source /opt/env.sh"
echo "  python3 tools/pipeline.py <apk> <salida.apk> --engine dry"
