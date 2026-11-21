# Traducción

## Formato del CSV

Ocho columnas, una fila por cadena, UTF-8 con BOM, comillas dobles.

| Columna | Contenido |
|---|---|
| `n` | Número de fila |
| `id` | Identificador del bloque de traducción |
| `tabla` | Archivo de origen (da la escena) |
| `tipo` | `dialogo` o `interfaz` |
| `original` | Texto en inglés — **no se toca** |
| `traduccion` | **La única columna que se rellena** |
| `contexto` | Personaje y línea de origen |
| `placeholders_obligatorios` | Marcadores que deben sobrevivir |

## Reglas para quien traduce

1. Rellenar solo `traduccion`. No tocar `original`, `id` ni `n`.
2. No borrar, añadir ni reordenar filas.
3. Si una fila no se traduce, se deja **vacía**. Nunca copiar el inglés.
4. Copiar los marcadores exactamente igual.
5. Español latino, natural y con emoción. Nada de `vosotros`.
6. Nombres propios de personas y lugares se quedan; objetos comunes se traducen.
7. Contenido explícito crudo, sin suavizar ni añadir eufemismos.
8. Traducir por escena: `tabla` y `contexto` dan la escena y el personaje.

## Escenas explícitas — protocolo obligatorio

Si la IA traductora no puede o no le permiten traducir contenido explícito:

1. Traduce **todo lo que sí pueda**.
2. Deja esas filas **vacías**. No las dejes en inglés dentro de `traduccion`,
   no las suavices y no las resumas.
3. Al terminar, entrega **la lista exacta de los números de fila** que no
   tradujo.
4. Esas filas las traduce otra IA o el usuario.

Así ninguna escena queda a medias sin que quede registrado, y el trabajo se
puede repartir entre varias sesiones sin perder la cuenta.

## Verificación automática

```bash
python3 tools/translate_csv.py entrada.csv salida.csv --engine dry
```

`dry` no traduce: comprueba el enmascarado de marcadores y reporta los rotos.
Sirve para validar un CSV recibido antes de construir.

## Glosario

Los nombres de personajes, lugares y términos de marca se fijan una vez y se
respetan en todo el archivo. Se pasan al traductor como lista cerrada.

Ejemplo de la regla: `Golden Ox` se traduce siempre igual (`Buey Dorado`) o se
deja siempre igual, pero nunca de dos formas distintas.
