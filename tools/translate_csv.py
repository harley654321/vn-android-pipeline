#!/usr/bin/env python3
"""
translate_csv.py v2 - traduce la columna `original` y rellena `traduccion`.

Novedades v2: traduccion por LOTES con contexto de escena y glosario fijado.
Pensado para un LLM local (llama-server) o cualquier endpoint compatible OpenAI.

  python3 translate_csv.py entrada.csv salida.csv --engine openai \
      --base http://localhost:8080/v1 --model local --batch 20 --context 6 \
      --glossary glosario.md

Motores: openai | mymemory | dry

Por que por lotes y con contexto: una MT frase a frase no ve la escena y produce
calcos. Mandando 20 lineas seguidas de la misma tabla, mas las 6 anteriores ya
traducidas como referencia, el modelo mantiene el hilo y el tono. Si el lote
devuelve un numero de lineas distinto, se reintenta linea a linea.
"""
import csv, re, sys, json, time, sqlite3, argparse, os, urllib.request, urllib.parse

PH = re.compile(r"(\[[A-Za-z_][\w.]*\]|\{[^{}]*\}|%[sd]|\$\{[^}]+\})")
TOK = "\u3010{}\u3011"

def mask(s):
    items = []
    def rep(m):
        items.append(m.group(1)); return TOK.format(len(items)-1)
    return PH.sub(rep, s), items

def unmask(s, items):
    for i, v in enumerate(items): s = s.replace(TOK.format(i), v)
    return s

class Cache:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS t (k TEXT PRIMARY KEY, v TEXT)")
    def get(self, k):
        r = self.db.execute("SELECT v FROM t WHERE k=?", (k,)).fetchone()
        return json.loads(r[0]) if r else None
    def put(self, k, v):
        self.db.execute("INSERT OR REPLACE INTO t VALUES (?,?)", (k, json.dumps(v, ensure_ascii=False)))
        self.db.commit()

SYS = """Eres traductor profesional de videojuegos del ingles al espanol latino.
Traduce SOLO el texto que se te da. No anadas, no resumas, no expliques.

REGLAS OBLIGATORIAS:
1. Espanol latino neutro. Nunca "vosotros", nunca "coger" con sentido sexual.
2. Natural y con emocion. Nunca literal ni robotico. Si una palabra hace dudar,
   usa una cotidiana ("desvan" -> "el piso de arriba").
3. Nombres de personas y lugares: se quedan en el original.
   Objetos, comidas y oficios comunes: se traducen.
4. Contenido adulto: traduce tal cual, sin suavizar, sin eufemismos, sin omitir.
5. Los marcadores 【0】,【1】... son variables del motor. Se copian EXACTOS y en la
   misma posicion relativa. Nunca se traducen ni se eliminan.
6. Respeta los saltos de linea \\n y las etiquetas {b}{/b}{i}{/i}.

FORMATO DE SALIDA: un objeto JSON con la clave "t" cuyo valor es una lista de
cadenas, en el mismo orden y con la misma cantidad que la entrada. Nada mas."""

def oai_batch(lines, ctx, base, model, key, glossary):
    user = []
    if glossary: user.append("GLOSARIO (usa estas formas siempre):\n" + glossary.strip()[:4000])
    if ctx: user.append("CONTEXTO ANTERIOR YA TRADUCIDO:\n" + "\n".join(ctx))
    user.append("LINEAS A TRADUCIR (JSON, mismo orden):\n" + json.dumps(lines, ensure_ascii=False))
    body = json.dumps({"model": model, "temperature": 0.3, "max_tokens": 4096,
        "response_format": {"type": "json_object"},
        "messages": [{"role":"system","content":SYS},
                     {"role":"user","content":"\n\n".join(user)}]}).encode()
    req = urllib.request.Request(base.rstrip("/")+"/chat/completions", data=body,
        headers={"Content-Type":"application/json","Authorization":"Bearer "+(key or "sk-local")})
    d = json.load(urllib.request.urlopen(req, timeout=300))
    txt = d["choices"][0]["message"]["content"].strip()
    txt = re.sub(r"^```(?:json)?|```$", "", txt, flags=re.M).strip()
    obj = json.loads(txt)
    out = obj.get("t") or obj.get("translations") or obj.get("traducciones")
    if not isinstance(out, list): raise ValueError("sin lista 't'")
    return out

def mm(text, email=""):
    url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text[:480])}&langpair=en|es"
    if email: url += "&de=" + urllib.parse.quote(email)
    d = json.load(urllib.request.urlopen(url, timeout=30))
    if d.get("responseStatus") != 200: raise RuntimeError(d.get("responseDetails","error"))
    return d["responseData"]["translatedText"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--engine", default="dry", choices=["openai","mymemory","dry"])
    ap.add_argument("--base", default="http://localhost:8080/v1")
    ap.add_argument("--model", default="local")
    ap.add_argument("--key", default=os.environ.get("API_KEY",""))
    ap.add_argument("--email", default="")
    ap.add_argument("--batch", type=int, default=20, help="lineas por peticion")
    ap.add_argument("--context", type=int, default=6, help="lineas previas como referencia")
    ap.add_argument("--glossary", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--cache", default="")
    a = ap.parse_args()

    rows = list(csv.DictReader(open(a.src, encoding="utf-8-sig")))
    fields = list(rows[0].keys())
    cache = Cache(a.cache or a.dst + ".cache.db")
    glossary = open(a.glossary, encoding="utf-8").read() if a.glossary and os.path.exists(a.glossary) else ""

    pend = [i for i,r in enumerate(rows) if not r.get("traduccion","").strip() and r["original"].strip()]
    if a.limit: pend = pend[:a.limit]
    print(f"pendientes: {len(pend)} | lote {a.batch} | contexto {a.context}", flush=True)

    done = fail = 0
    i = 0
    while i < len(pend):
        chunk = pend[i:i+a.batch]
        raw = [rows[j]["original"] for j in chunk]
        masked = [mask(x)[0] for x in raw]
        items = [mask(x)[1] for x in raw]
        key = a.engine + "\x00" + "\x00".join(raw)
        got = cache.get(key)

        if got is None:
            try:
                if a.engine == "dry":
                    got = masked
                elif a.engine == "mymemory":
                    got = []
                    for m in masked:
                        got.append(mm(m, a.email)); time.sleep(0.25)
                else:
                    ctx = [rows[j]["traduccion"] for j in pend[max(0,i-a.context):i]
                           if rows[j].get("traduccion","").strip()]
                    got = oai_batch(masked, ctx, a.base, a.model, a.key, glossary)
                if len(got) != len(chunk): raise ValueError(f"devolvio {len(got)} de {len(chunk)}")
                cache.put(key, got)
            except Exception as e:
                # reintento linea a linea antes de rendirse
                if a.engine == "openai" and len(chunk) > 1:
                    for j, m in zip(chunk, masked):
                        try:
                            g = oai_batch([m], [], a.base, a.model, a.key, glossary)
                            rows[j]["traduccion"] = unmask(g[0], mask(rows[j]["original"])[1]); done += 1
                        except Exception as e2:
                            fail += 1; print(f"   fila {rows[j]['n']}: {str(e2)[:70]}", flush=True)
                    i += len(chunk); continue
                fail += len(chunk); print(f"   lote fallido: {str(e)[:70]}", flush=True)
                i += len(chunk); continue

        for j, g, it in zip(chunk, got, items):
            rows[j]["traduccion"] = unmask(g, it)
            done += 1
        i += len(chunk)
        if done % 100 < a.batch: print(f"   {done}/{len(pend)}", flush=True)

    with open(a.dst, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
        w.writeheader(); w.writerows(rows)

    bad = [r["n"] for r in rows if r.get("traduccion","").strip()
           and sorted(PH.findall(r["original"])) != sorted(PH.findall(r["traduccion"]))]
    print(f"\ntraducidas: {done} | fallos: {fail} | placeholders rotos: {len(bad)} {bad[:6]}")
    print("salida:", a.dst)

if __name__ == "__main__": main()
