# Ejemplos de simulación (ciclo por ciclo)

Cada fila es un flanco de reloj. Las columnas *antes* muestran el estado en el que estaba cada máquina, las columnas `CODIGO_OK` y `ALARMA` son las salidas Mealy (se calculan con el estado y la tecla pulsada) y las columnas *después* muestran el estado tras el flanco.

### Ejemplo 1: código correcto y ciclo completo de la barrera

Se teclea A, C, B. Después entra un carro (`SENSOR = 1`), la barrera espera, el carro sale y cierra.

| Ciclo | Tecla | SENSOR | Barrera (antes) | Verificador (antes) | `CODIGO_OK` | `ALARMA` | Barrera (después) | Verificador (después) | Qué pasa |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | – | 0 | CERRADA | SIN_TECLAS | – | – | CERRADA | SIN_TECLAS | – |
| 2 | A | 0 | CERRADA | SIN_TECLAS | – | – | CERRADA | PASO_1 | tecla correcta: avanza el código |
| 3 | A | 0 | CERRADA | PASO_1 | – | – | CERRADA | PASO_1 | se mantiene la tecla: no cambia nada |
| 4 | – | 0 | CERRADA | PASO_1 | – | – | CERRADA | PASO_1 | – |
| 5 | C | 0 | CERRADA | PASO_1 | – | – | CERRADA | PASO_2 | tecla correcta: avanza el código |
| 6 | – | 0 | CERRADA | PASO_2 | – | – | CERRADA | PASO_2 | – |
| 7 | B | 0 | CERRADA | PASO_2 | sí | – | ABRIENDO | SIN_TECLAS | **código correcto: `CODIGO_OK` abre la barrera**; la barrera empieza a abrir |
| 8 | – | 0 | ABRIENDO | SIN_TECLAS | – | – | ABIERTA | SIN_TECLAS | la barrera termina de abrir |
| 9 | – | 1 | ABIERTA | SIN_TECLAS | – | – | ABIERTA | SIN_TECLAS | hay un carro: la barrera se queda abierta |
| 10 | – | 1 | ABIERTA | SIN_TECLAS | – | – | ABIERTA | SIN_TECLAS | hay un carro: la barrera se queda abierta |
| 11 | – | 0 | ABIERTA | SIN_TECLAS | – | – | CERRANDO | SIN_TECLAS | ya no hay carro: empieza a cerrar |
| 12 | – | 0 | CERRANDO | SIN_TECLAS | – | – | CERRADA | SIN_TECLAS | la barrera queda cerrada |
| 13 | – | 0 | CERRADA | SIN_TECLAS | – | – | CERRADA | SIN_TECLAS | – |

### Ejemplo 2: código incorrecto

Se pulsa B sin haber pulsado antes A; luego A y B (falta la C). Los dos errores dan `ALARMA`.

| Ciclo | Tecla | SENSOR | Barrera (antes) | Verificador (antes) | `CODIGO_OK` | `ALARMA` | Barrera (después) | Verificador (después) | Qué pasa |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | B | 0 | CERRADA | SIN_TECLAS | – | sí | CERRADA | SIN_TECLAS | **tecla equivocada: `ALARMA`, el verificador se reinicia** |
| 2 | – | 0 | CERRADA | SIN_TECLAS | – | – | CERRADA | SIN_TECLAS | – |
| 3 | A | 0 | CERRADA | SIN_TECLAS | – | – | CERRADA | PASO_1 | tecla correcta: avanza el código |
| 4 | B | 0 | CERRADA | PASO_1 | – | sí | CERRADA | SIN_TECLAS | **tecla equivocada: `ALARMA`, el verificador se reinicia** |
| 5 | – | 0 | CERRADA | SIN_TECLAS | – | – | CERRADA | SIN_TECLAS | – |

### Ejemplo 3: sensor de seguridad al cerrar

Se abre la barrera con el código; cuando empieza a cerrar entra un carro y la barrera se reabre.

| Ciclo | Tecla | SENSOR | Barrera (antes) | Verificador (antes) | `CODIGO_OK` | `ALARMA` | Barrera (después) | Verificador (después) | Qué pasa |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | A | 0 | CERRADA | SIN_TECLAS | – | – | CERRADA | PASO_1 | tecla correcta: avanza el código |
| 2 | C | 0 | CERRADA | PASO_1 | – | – | CERRADA | PASO_2 | tecla correcta: avanza el código |
| 3 | B | 0 | CERRADA | PASO_2 | sí | – | ABRIENDO | SIN_TECLAS | **código correcto: `CODIGO_OK` abre la barrera**; la barrera empieza a abrir |
| 4 | – | 0 | ABRIENDO | SIN_TECLAS | – | – | ABIERTA | SIN_TECLAS | la barrera termina de abrir |
| 5 | – | 0 | ABIERTA | SIN_TECLAS | – | – | CERRANDO | SIN_TECLAS | ya no hay carro: empieza a cerrar |
| 6 | – | 1 | CERRANDO | SIN_TECLAS | – | – | ABIERTA | SIN_TECLAS | hay un carro: se vuelve a abrir (seguridad) |
| 7 | – | 0 | ABIERTA | SIN_TECLAS | – | – | CERRANDO | SIN_TECLAS | ya no hay carro: empieza a cerrar |
| 8 | – | 0 | CERRANDO | SIN_TECLAS | – | – | CERRADA | SIN_TECLAS | la barrera queda cerrada |
| 9 | – | 0 | CERRADA | SIN_TECLAS | – | – | CERRADA | SIN_TECLAS | – |
