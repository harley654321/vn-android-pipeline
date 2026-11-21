#!/usr/bin/env python3
"""
renpy_build.py - CSV traducido + APK original -> APK en espanol firmado.

Uso:
    python3 renpy_build.py <apk_original> <csv_traducido> <salida.apk>
                            [--work DIR] [--keystore F] [--pass PASS] [--alias A]

Reutiliza la carpeta de trabajo de renpy_extract.py (misma ruta por defecto).
Pasos: rellena tl/es, fuerza el idioma, compila, reempaqueta y firma.
"""
import argparse, ast, csv, os, re, shutil, subprocess, sys, zipfile

SDK = "/app/conversations/6afe678da538e484fb909e80/tools/renpy-8.3.7"
BT = "/opt/android-sdk/build-tools/35.0.0"
LANG = "es"


def unq(l):
    try:
        return ast.literal_eval(l)
    except Exception:
        return l[1:-1]


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def run(cmd, cwd=None, env=None, timeout=900):
    env = dict(env or os.environ)
    jh = "/opt/jdk21/bin"
    if os.path.isdir(jh) and jh not in env.get("PATH", ""):
        env["PATH"] = jh + ":" + env.get("PATH", "")
    r = subprocess.run(cmd, cwd=cwd, env=env, timeout=timeout,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("apk")
    ap.add_argument("csv")
    ap.add_argument("out")
    ap.add_argument("--work", default=None)
    ap.add_argument("--keystore", default=None)
    ap.add_argument("--pass", dest="pw", default="Sunmeadow2026!")
    ap.add_argument("--alias", default=None)
    a = ap.parse_args()

    work = a.work or (os.path.splitext(a.csv)[0] + "_work")
    game = os.path.join(work, "proj", "game")
    tldir = os.path.join(game, "tl", LANG)
    if not os.path.isdir(tldir):
        print(f"ERROR: no existe {tldir}. Corre antes renpy_extract.py.")
        return 2

    # 1. mapa original -> traduccion
    with open(a.csv, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    tr = {}
    vacias = 0
    for r in rows:
        t = (r.get("traduccion") or "").strip()
        if not t:
            vacias += 1
            continue
        tr[r["original"]] = t
    print(f"[1/6] traducciones: {len(tr)} | vacias (se quedan en ingles): {vacias}")
    if not tr:
        print("ERROR: el CSV no tiene ninguna traduccion.")
        return 2

    # 2. rellenar los .rpy de tl/es
    print(f"[2/6] rellenando tl/{LANG}")
    n_dlg = n_str = 0
    for fn in os.listdir(tldir):
        if not fn.endswith(".rpy"):
            continue
        p = os.path.join(tldir, fn)
        out = []
        in_strings = False
        pending_old = None
        for line in open(p, encoding="utf-8-sig", errors="replace").read().splitlines():
            if re.match(rf"^translate\s+\S+\s+strings\s*:", line):
                in_strings = True
                out.append(line)
                continue
            if re.match(r"^translate\s", line):
                in_strings = False
            if in_strings:
                mo = re.match(r'^(\s*)old\s+("(?:[^"\\]|\\.)*")\s*$', line)
                if mo:
                    pending_old = unq(mo.group(2))
                    out.append(line)
                    continue
                mn = re.match(r'^(\s*)new\s+("(?:[^"\\]|\\.)*")\s*$', line)
                if mn and pending_old is not None and pending_old in tr:
                    out.append(f'{mn.group(1)}new "{esc(tr[pending_old])}"')
                    n_str += 1
                    pending_old = None
                    continue
                out.append(line)
                continue
            m = re.match(r'^(\s*)(\w+)\s+("(?:[^"\\]|\\.)*")(\s+with\s+\w+)?\s*$', line)
            if m and m.group(2) not in ("old", "new"):
                orig = unq(m.group(3))
                if orig in tr:
                    out.append(f'{m.group(1)}{m.group(2)} "{esc(tr[orig])}"{m.group(4) or ""}')
                    n_dlg += 1
                    continue
            out.append(line)
        open(p, "w", encoding="utf-8-sig").write("\n".join(out) + "\n")
    print(f"      dialogo: {n_dlg} | interfaz: {n_str}")

    # 3. forzar el idioma
    print(f"[3/6] forzando config.language = {LANG}")
    with open(os.path.join(game, "zzz_spanish.rpy"), "w", encoding="utf-8") as f:
        f.write(f'define config.language = "{LANG}"\n')

    # 4. compilar
    print("[4/6] compilando con Ren'Py")
    env = dict(os.environ)
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SDL_AUDIODRIVER"] = "dummy"
    rc, out = run([os.path.join(SDK, "renpy.sh"), "proj", "compile"], cwd=work, env=env)
    if not os.path.exists(os.path.join(game, "zzz_spanish.rpyc")):
        rc, out = run([os.path.join(SDK, "renpy.sh"), "proj", "lint"], cwd=work, env=env)
    if not os.path.exists(os.path.join(game, "zzz_spanish.rpyc")):
        print("ERROR: Ren'Py no compilo. Ultimas lineas:")
        print(out[-1500:])
        return 2
    print("      compilado")

    # 5. reempaquetar
    print("[5/6] reempaquetando APK")
    z = zipfile.ZipFile(a.apk)
    prefix = "assets/x-game/" if any(n.startswith("assets/x-game/") for n in z.namelist()) else "assets/game/"
    nuevos = {}
    for fn in os.listdir(tldir):
        if fn.endswith(".rpyc"):
            nuevos[prefix + "x-tl/x-" + LANG + "/x-" + fn] = os.path.join(tldir, fn)
    zp = os.path.join(game, "zzz_spanish.rpyc")
    if os.path.exists(zp):
        nuevos[prefix + "x-zzz_spanish.rpyc"] = zp

    tmp = a.out + ".tmp"
    with zipfile.ZipFile(tmp, "w") as zo:
        for i in z.infolist():
            data = z.read(i) if i.filename not in nuevos else open(nuevos[i.filename], "rb").read()
            zi = zipfile.ZipInfo(i.filename, date_time=i.date_time)
            zi.compress_type = zipfile.ZIP_DEFLATED if i.compress_type == zipfile.ZIP_DEFLATED else zipfile.ZIP_STORED
            zi.external_attr = i.external_attr
            zo.writestr(zi, data)
        for name, path in nuevos.items():
            if name in z.namelist():
                continue
            zo.writestr(name, open(path, "rb").read())
    print(f"      {len(nuevos)} archivos nuevos/reemplazados")

    # 6. alinear y firmar
    print("[6/6] firmando")
    ks = a.keystore or os.path.join("/app/conversations/6afe678da538e484fb909e80", "apk", "sunmeadow.keystore")
    al = a.out + ".aligned"
    run([os.path.join(BT, "zipalign"), "-p", "-f", "4", tmp, al])
    rc, out = run([os.path.join(BT, "apksigner"), "sign", "--ks", ks,
                   "--ks-key-alias", a.alias or "sunmeadow",
                   "--ks-pass", f"pass:{a.pw}", "--key-pass", f"pass:{a.pw}",
                   "--out", a.out, al])
    if rc != 0:
        print("ERROR firmando (se entrega sin firmar):")
        print(out[-800:])
        shutil.move(al, a.out)
    else:
        print("      firma OK")
    for f in (tmp, al):
        if os.path.exists(f):
            os.remove(f)
    print(f"\nAPK: {os.path.abspath(a.out)}  ({os.path.getsize(a.out)/1024/1024:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
