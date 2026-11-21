#!/usr/bin/env python3
"""
renpy_extract.py - APK de Ren'Py -> CSV de traduccion.

Uso:
    python3 renpy_extract.py <apk> <salida.csv> [--sdk DIR] [--unrpyc DIR] [--lang es]

Hace todo el proceso sin intervencion:
  1. Descomprime assets/x-game/ y quita el prefijo x- que mete el build de Android
  2. Descompila los .rpyc con unrpyc
  3. Lanza el comando oficial `translate` de Ren'Py (enumera TODAS las cadenas)
  4. Convierte la plantilla a CSV de 8 columnas
  5. Auditoria de cobertura y aviso si algo queda fuera
"""
import argparse, ast, csv, os, re, shutil, subprocess, sys, zipfile

DEFAULT_SDK = "/app/conversations/6afe678da538e484fb909e80/tools/renpy-8.3.7"
DEFAULT_UNRPYC = "/app/conversations/6afe678da538e484fb909e80/tools/unrpyc-master/unrpyc.py"

CODE = re.compile(r"^(screen|label|if|elif|else|jump|call|show|hide|play|stop|scene|with|"
                  r"define|default|python|init|style|image|transform|menu|while|return|pass|"
                  r"pause|voice|window|nvl|at|as|expression|translate)\b")
PH = [(r"\$\{[^}]+\}", "var"), (r"\[[^\]\[]+\]", "interp"), (r"%[sd]", "var"),
      (r"\{[^}]*\}", "tag"), (r"\\n", "nl")]


def placeholders(s):
    out = []
    for pat, label in PH:
        for m in re.findall(pat, s):
            if (label, m) not in out:
                out.append((label, m))
    return " ".join(f"{a}:{b}" for a, b in out)


def unq(lit):
    try:
        return ast.literal_eval(lit)
    except Exception:
        return lit[1:-1]


def run(cmd, cwd=None, env=None, timeout=600):
    r = subprocess.run(cmd, cwd=cwd, env=env, timeout=timeout,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("apk")
    ap.add_argument("out")
    ap.add_argument("--sdk", default=DEFAULT_SDK)
    ap.add_argument("--unrpyc", default=DEFAULT_UNRPYC)
    ap.add_argument("--lang", default="es")
    ap.add_argument("--work", default=None)
    a = ap.parse_args()

    work = a.work or (os.path.splitext(a.out)[0] + "_work")
    if os.path.exists(work):
        shutil.rmtree(work)
    game = os.path.join(work, "proj", "game")
    os.makedirs(game, exist_ok=True)

    # 1. descomprimir
    z = zipfile.ZipFile(a.apk)
    names = z.namelist()
    prefix = None
    for cand in ("assets/x-game/", "assets/game/"):
        if any(n.startswith(cand) for n in names):
            prefix = cand
            break
    if prefix is None:
        print("ERROR: no encuentro assets/x-game/ ni assets/game/ en el APK.")
        print("No parece un build de Ren'Py. Archivos de primer nivel:")
        for n in sorted({x.split('/')[0] for x in names})[:15]:
            print("   ", n)
        return 2
    print(f"[1/5] extrayendo desde {prefix}")

    strip = lambda s: "/".join(c[2:] if c.startswith("x-") else c for c in s.split("/"))
    n = 0
    for i in z.infolist():
        if not i.filename.startswith(prefix) or i.is_dir():
            continue
        rel = i.filename[len(prefix):]
        if rel.startswith(("cache/", "tl/", "x-cache/", "x-tl/")):
            continue
        out = os.path.join(game, strip(rel))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as f:
            f.write(z.read(i))
        n += 1
    print(f"      {n} archivos copiados")

    # 2. descompilar
    rpyc = []
    for root, _dirs, files in os.walk(game):
        for f in files:
            if f.endswith(".rpyc"):
                rpyc.append(os.path.relpath(os.path.join(root, f), game))
    if not rpyc:
        print("ERROR: no hay .rpyc en el juego.")
        return 2
    print(f"[2/5] descompilando {len(rpyc)} .rpyc")
    env = dict(os.environ)
    env["PYTHONPATH"] = a.sdk
    sdkpy = os.path.join(a.sdk, "lib", "py3-linux-x86_64", "python")
    rc, out = run([sdkpy, a.unrpyc, "--clobber"] + rpyc, cwd=game, env=env)
    ok = sum(1 for l in out.splitlines() if "successfully decompiled" in l)
    print("      " + (out.strip().splitlines()[-1] if out.strip() else "sin salida"))
    if ok == 0 and "Traceback" in out:
        print(out[-1500:])
        return 2

    # ---- FIXUPS: unrpyc revierte displayables SL personalizados a su base ----
    # Caso conocido: `zoom_viewport` (addon 01_zoom_viewport) sale como `viewport`
    # y Ren'Py entonces rechaza `start_zoom` al parsear.
    CUSTOM = {"zoom_viewport": ("start_zoom", "zoom_min", "zoom_max", "zoom_amount")}
    arreglados = 0
    for root, _d, files in os.walk(game):
        for f in files:
            if not f.endswith(".rpy"):
                continue
            fp = os.path.join(root, f)
            lines = open(fp, encoding="utf-8", errors="ignore").read().split("\n")
            changed = False
            for i, ln in enumerate(lines):
                m = re.match(r"^(\s*)viewport(\b.*)$", ln)
                if not m:
                    continue
                ventana = "\n".join(lines[i + 1:i + 18])
                for nombre, props in CUSTOM.items():
                    if any(re.search(r"^\s*" + pr + r"\b", ventana, re.M) for pr in props):
                        lines[i] = m.group(1) + nombre + m.group(2)
                        changed = True
                        break
            if changed:
                open(fp, "w", encoding="utf-8").write("\n".join(lines))
                arreglados += 1
    if arreglados:
        print(f"      fixups: {arreglados} archivo(s) con displayables SL restaurados")

    # 3. translate oficial
    print(f"[3/5] generando plantilla con el comando oficial de Ren'Py")
    tl = os.path.join(game, "tl")
    if os.path.exists(tl):
        shutil.rmtree(tl)
    env2 = dict(os.environ)
    env2["SDL_VIDEODRIVER"] = "dummy"
    env2["SDL_AUDIODRIVER"] = "dummy"
    rc, out = run([os.path.join(a.sdk, "renpy.sh"), "proj", "translate", a.lang],
                  cwd=work, env=env2, timeout=900)
    tldir = os.path.join(tl, a.lang)
    if not os.path.isdir(tldir):
        print("ERROR: Ren'Py no genero la carpeta de traduccion.")
        print(out[-2000:])
        return 2
    files = []
    for _root, _dirs, _fs in os.walk(tldir):
        for _f in _fs:
            if _f.endswith(".rpy"):
                files.append(os.path.relpath(os.path.join(_root, _f), tldir))
    files.sort()
    print(f"      generados: {', '.join(files)}")

    # 4. parsear a CSV
    print("[4/5] convirtiendo a CSV")
    rows = []
    for fn in files:
        path = os.path.join(tldir, fn)
        base = fn[:-4]
        lines = open(path, encoding="utf-8-sig", errors="replace").read().splitlines()
        cur = None
        for i, line in enumerate(lines):
            m = re.match(r"^translate\s+\S+\s+(\S+)\s*:", line)
            if m:
                cur = m.group(1)
                continue
            if line.strip() == "translate %s strings:" % a.lang:
                cur = "strings"
                continue
            m = re.match(r'^\s*(?:(\w+)\s+)?("(?:[^"\\]|\\.)*")\s*(?:with\s+\w+)?\s*$', line)
            if m and cur and cur != "strings" and (m.group(1) or "") not in ("old", "new") \
                    and not CODE.match((m.group(1) or "").strip()):
                txt = unq(m.group(2))
                if not txt or not txt.strip():
                    continue
                ctx = ""
                for j in range(max(0, i - 4), i):
                    if lines[j].strip().startswith("#"):
                        ctx = lines[j].strip().lstrip("# ").strip()
                rows.append({"id": cur, "tabla": base, "tipo": "dialogo",
                             "original": txt, "contexto": ((m.group(1) or "(narracion)") + " | " + ctx).strip(" |")})
                continue
            mo = re.match(r'^\s*old\s+("(?:[^"\\]|\\.)*")\s*$', line)
            if mo:
                txt = unq(mo.group(1))
                if not txt or not txt.strip():
                    continue
                ctx = ""
                for j in range(max(0, i - 3), i):
                    if lines[j].strip().startswith("#"):
                        ctx = lines[j].strip().lstrip("# ").strip()
                rows.append({"id": "s_" + str(len(rows) + 1), "tabla": base, "tipo": "interfaz",
                             "original": txt, "contexto": ctx})
                continue
            if re.match(r'^translate\s', line):
                cur = None

    seen = set()
    final = []
    for r in rows:
        k = (r["original"], r["tabla"])
        if k in seen:
            continue
        seen.add(k)
        final.append(r)

    with open(a.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(["n", "id", "tabla", "tipo", "original", "traduccion",
                    "contexto", "placeholders_obligatorios"])
        for i, r in enumerate(final, 1):
            w.writerow([i, r["id"], r["tabla"], r["tipo"], r["original"], "",
                        r["contexto"], placeholders(r["original"])])

    # 5. auditoria
    print("[5/5] auditoria de cobertura")
    dlg = sum(1 for r in final if r["tipo"] == "dialogo")
    ui = len(final) - dlg
    chars = sum(len(r["original"]) for r in final)
    print(f"      cadenas: {len(final)}  (dialogo {dlg} / interfaz {ui})")
    print(f"      caracteres: {chars}")
    print(f"      con placeholders: {sum(1 for r in final if placeholders(r['original']))}")
    print(f"      CSV: {os.path.abspath(a.out)}")
    print("\n      Muestra:")
    for r in final[:5]:
        print(f"        [{r['tipo']}] {r['original'][:80]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
