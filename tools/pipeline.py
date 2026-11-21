#!/usr/bin/env python3
"""
pipeline.py - UN solo comando: APK -> extraer -> traducir -> APK traducido firmado.

    python3 pipeline.py <apk> <salida.apk> --engine dry|mymemory|openai [opciones]

Opciones de motor:
    --engine mymemory                      gratis, sin clave, cuota diaria baja
    --engine openai --base URL --model M --key K   cualquier endpoint compatible OpenAI
    --engine dry                           no traduce (prueba de cadena completa)

Todo el texto vive en archivos, nunca en la respuesta del chat, asi que el
volumen no depende de ningun limite de mensaje.
"""
import argparse, subprocess, sys, os, time, csv, shutil

TOOLS = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

def step(n, total, txt):
    print(f"[{n}/{total}] {txt}", flush=True)

def run(cmd, **kw):
    r = subprocess.run(cmd, **kw)
    if r.returncode != 0:
        sys.exit(f"FALLO: {' '.join(map(str,cmd))}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("apk"); ap.add_argument("salida")
    ap.add_argument("--engine", default="dry")
    ap.add_argument("--base", default=""); ap.add_argument("--model", default="")
    ap.add_argument("--key", default=""); ap.add_argument("--email", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--work", default="")
    ap.add_argument("--keep-csv", default="")
    a = ap.parse_args()

    work = a.work or os.path.splitext(a.salida)[0] + "_work"
    csv_out = a.keep_csv or os.path.join(work, "traduccion.csv")
    os.makedirs(work, exist_ok=True)

    t0 = time.time()
    step(1, 4, "extrayendo texto del APK")
    run([PY, os.path.join(TOOLS, "renpy_extract.py"), a.apk, csv_out, "--work", work])

    step(2, 4, f"traduciendo con motor '{a.engine}'")
    csv_tr = os.path.join(work, "traduccion_es.csv")
    tcmd = [PY, os.path.join(TOOLS, "translate_csv.py"), csv_out, csv_tr, "--engine", a.engine]
    if a.base:  tcmd += ["--base", a.base]
    if a.model: tcmd += ["--model", a.model]
    if a.key:   tcmd += ["--key", a.key]
    if a.email: tcmd += ["--email", a.email]
    if a.limit: tcmd += ["--limit", str(a.limit)]
    run(tcmd)

    step(3, 4, "compilando y firmando el APK")
    run([PY, os.path.join(TOOLS, "renpy_build.py"), a.apk, csv_tr, a.salida, "--work", work])

    step(4, 4, "verificando")
    rows = list(csv.DictReader(open(csv_tr, encoding="utf-8-sig")))
    trad = sum(1 for r in rows if r.get("traduccion", "").strip())
    size = os.path.getsize(a.salida) / 1024 / 1024
    print(f"      cadenas: {len(rows)} | traducidas: {trad} | APK: {size:.1f} MB")
    print(f"      tiempo total: {time.time()-t0:.1f}s")
    print(f"\nAPK: {os.path.abspath(a.salida)}")

if __name__ == "__main__":
    main()
