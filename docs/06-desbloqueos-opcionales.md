# Desbloqueos opcionales: galería y salto rápido

Fecha: **2026-11-21**. Probado en xxxFiles 0.3.3 (Ren'Py 8.5.2).

## Regla de oro: busca la bandera del desarrollador antes de inventar nada

Muchos juegos ya traen su propio desbloqueo, escondido en un menú de cheats o
en una opción de debug. Antes de escribir código nuevo, grep:

```bash
grep -rn "unlocked_all\|unlock_all\|gallery_unlock\|cheat" game --include="*.rpy"
```

En xxxFiles existía `default persistent.gallery_unlocked_all = False` y
`cheat.rpy` ya lo ponía a `True`. No hizo falta inventar la lógica: solo
hacerla accesible desde la galería.

## Galería: qué la bloquea de verdad

```python
def is_replay_unlocked(item):
    return persistent.gallery_unlocked_all or renpy.seen_label(item.replay)
```

La galería se abre por **label visto**, no por partida guardada. La galería de
imágenes (`GalleryItem`) usa `renpy.seen_image()` y en este juego estaba vacía
(`gallery_items = []`), así que no había nada que desbloquear ahí.

## Por qué NO meter una partida guardada

Un save de Ren'Py no guarda solo "he jugado". Guarda el estado completo:
variables, inventario, stats de personajes, banderas de eventos, posición,
versión del guion. Meterlo tiene tres problemas:

1. **Se rompe entre versiones.** Al actualizar el juego cambian labels y
   variables; un save viejo puede lanzar `AttributeError` o saltar a un label
   que ya no existe.
2. **Pisa el progreso del jugador.** Al cargar, sobrescribe su partida real.
3. **No es lo que hace el juego.** El "avance rápido" del segundo playthrough
   no viene del save, viene de `preferences.skip_unseen`.

Las banderas persistentes son independientes de los saves y sobreviven a las
actualizaciones. Es la vía correcta.

## Salto rápido: la pieza real

Ren'Py solo salta texto ya leído por defecto. La preferencia `skip_unseen`
elimina esa restricción, y es exactamente el comportamiento de "ya jugué esto".

```python
config.label_callbacks.append(_port_skip_cb)   # se activa una sola vez
```

Se hace una sola vez con un guard (`persistent._port_skip_set`) para no pisar
la elección del jugador si luego lo desactiva en Preferencias.

## El parche completo (2 archivos, ~30 líneas)

`game/zz_extra_unlocks.rpy` — la función de alternancia y el hook del salto.
`game/gallery/replay.rpy` — un `textbutton` de 6 líneas dentro de la pantalla.

Ambas zonas van marcadas con `# PORT:` para poder revertirlas.

## Riesgos reales, y cómo se acotan

| Riesgo | Mitigación |
|---|---|
| El botón rompe la pantalla | Se compila y se verifica el `.rpyc` antes de empaquetar |
| La bandera no cubre otra galería | Se comprobó que `is_replay_unlocked` es la única puerta |
| El jugador no quiere el salto | Es una preferencia normal, se puede desactivar |
| El autor cambia la galería en otra versión | El parche está aislado; si falla, se borran 2 archivos |

## Verificación obligatoria antes de entregar

```bash
# 1. el .rpyc compila
renpy.sh <proj> compile
# 2. el APK no tiene entradas duplicadas (rompe apksigner)
python3 -c "import zipfile;n=zipfile.ZipFile('x.apk').namelist();print(len(n)-len(set(n)))"
# 3. la traducción original sigue intacta
python3 -c "import zipfile;print(len([n for n in zipfile.ZipFile('x.apk').namelist() if '/x-tl/' in n]))"
```
