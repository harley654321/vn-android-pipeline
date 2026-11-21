# Reglas no negociables

Estas reglas existen porque cada una se rompió al menos una vez y costó horas.

## 1. Cobertura medida, nunca supuesta

Antes de decir "extraje todo": contar cuántas cadenas tiene el juego y cuántas
están en el CSV. Si la diferencia no es cero, hay que explicar cada una.

El caso que lo provocó: un filtro descartaba toda frase que contuviera `${...}`
porque la trataba como código. Eran **298 frases de narrativa**, incluida la
primera línea del juego. Se entregó un APK mezclado y hubo que rehacerlo.

## 2. Un solo CSV final

Nunca varios CSV parciales. El traductor rellena una columna y devuelve un
archivo. Cualquier otra cosa genera desalineación.

## 3. Todo el texto, no solo la historia

Es fácil extraer los diálogos y olvidar que el jugador también ve:

- Menú de opciones y ajustes
- Pantallas de guardar / cargar
- Accesibilidad (lectura por voz, alto contraste, tamaño de texto)
- Nombres de fuentes y de idiomas
- Cheats, updater, minijuegos
- Texto de interfaz del motor Ren'Py (`common.rpy`, ~310 cadenas)
- Globos de ayuda, tooltips, mensajes de error del juego

Traducir la historia y dejar los ajustes en inglés es una mala experiencia.

## 4. Los placeholders no se tocan

Se enmascaran **antes** de enviar el texto a traducir y se restauran después.
Nunca se corrige a posteriori.

En Ren'Py los marcadores son `[variable]`, `{b}...{/b}`, `{color=#fff}`,
`{#weekday}`, `%s` y `\n`. En otros motores: `${item}`, `{P}`, `{Esc}`.

Añadir llaves donde no las había deja líneas en blanco en el juego.

## 5. Verificar el APK, no la intención

Que la firma diga OK no prueba nada. Hay que abrir los `.rpyc` de la traducción
dentro del APK, descomprimir el pickle y comprobar que cada cadena traducida
está presente.

## 6. Entorno reproducible

Todo lo que se instala queda en `tools/bootstrap.sh` y en
`docs/00-INSTALACION.md`, con versiones exactas y los errores ya resueltos.
Un chat nuevo debe poder continuar leyendo este repo.

## 7. Escenas explícitas

Si la IA traductora no puede o no le permiten traducir contenido explícito:

1. Traduce todo lo que sí pueda.
2. **No** deja las escenas en inglés ni las suaviza.
3. Devuelve la lista exacta de los números de fila que no tradujo.
4. Esas filas las traduce otra IA o el usuario.

El objetivo es que ninguna escena quede a medias sin que quede registrado.
