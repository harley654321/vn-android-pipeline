# Fallos conocidos — checklist obligatoria

Recorrer esta lista **antes** de entregar cualquier cosa.

## Extracción

| Fallo | Síntoma | Arreglo |
|---|---|---|
| Filtro que descarta `${...}` | Cientos de frases de narrativa en inglés | Nunca filtrar por caracteres especiales. Comparar contra el texto final, no contra patrones |
| `glob` no recursivo | Cadenas extraídas muy por debajo de lo esperado | `os.walk`, nunca `listdir` |
| Incluir `x-tl/` como base | Traducciones mezcladas con el original | Excluir `x-tl/` y `x-cache/` |
| No quitar el prefijo `x-` | Ren'Py no encuentra los archivos | Quitarlo de cada componente de la ruta |
| Narración sin personaje | Solo se extraen diálogos con hablante | Aceptar líneas que son solo `"texto"` |
| SDK de versión distinta | `Could not load file ... .rpyc` | Descargar el SDK de `script_version.txt` |
| unrpyc revierte displayables SL | `X is not a valid child of ...` | Restaurar el nombre original del displayable |
| unrpyc genera `.rpy` vacío | Error de parseo o pérdida de funciones | Borrar el `.rpy` y dejar que use el `.rpyc` |

## Traducción

| Fallo | Síntoma | Arreglo |
|---|---|---|
| Llaves añadidas | Líneas en blanco en el juego | Enmascarar antes de traducir, nunca corregir después |
| Deduplicar por id | Cadenas perdidas al reinsertar | Emparejar también por texto original |
| Traducir dentro de `{...}` | Variable rota | Lista de marcadores por fila en el CSV |

## Compilación y entrega

| Fallo | Síntoma | Arreglo |
|---|---|---|
| `java: not found` al firmar | Firma falla | Añadir `JAVA_HOME/bin` al `PATH` |
| `sdkmanager: Permission denied` | No se instala el SDK | `chmod -R +x` tras descomprimir con Python |
| Capacitor con Node 20 | `requires NodeJS >=22` | Instalar Node 22 |
| APK mayor de 200 MB | Subida rechazada | Comprimir a `.zip` o reducir assets |
| `.apk` bloqueado por el alojador | Subida rechazada | Entregar en `.zip` |
| `file://` rompe `fetch()` | Juego en blanco | Empaquetar con Capacitor (servidor local) |

## Entorno

| Fallo | Síntoma | Arreglo |
|---|---|---|
| `nproc` devuelve 1 | Se cree que hay un núcleo | `os.sched_getaffinity(0)` o benchmark con `multiprocessing` |
| Medir con hilos | Parece que no hay paralelismo | El GIL los serializa; usar procesos |
| Google Translate | Captcha desde IP de servidor | No es usable; usar otra vía |

## Antes de entregar — lista corta

- [ ] Conté las cadenas del juego y las del CSV
- [ ] La diferencia es cero o está justificada fila por fila
- [ ] No hay placeholders alterados
- [ ] No hay filas con el inglés dentro de `traduccion`
- [ ] El APK abre y arranca en el idioma correcto
- [ ] Verifiqué el contenido dentro del APK, no solo la firma
- [ ] Subí a gofile y anoté el enlace
