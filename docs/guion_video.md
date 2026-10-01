# Guion del video (máx. 5 min)

Sugerencia: grabar la pantalla con Logisim abierto (`circuito/barrera_codigo.circ`) y las tablas en `tablas/`.

| Tiempo | Qué mostrar | Qué decir |
|---|---|---|
| 0:00 – 0:30 | `top` completo | "Es una barrera de estacionamiento con código secreto. Son dos FSM que interactúan y comparten un solo reloj: una Moore que controla la barrera y una Mealy que verifica el código." |
| 0:30 – 1:15 | `tablas/01_FSM1_Moore_barrera.md` (diagrama y tablas) | FSM 1 Moore: 4 estados (CERRADA, ABRIENDO, ABIERTA, CERRANDO), codificación binaria de 2 bits. Las salidas dependen solo del estado. Sensor de seguridad: si hay un carro, no cierra. Ecuaciones D1 y D0 sacadas de la tabla de transición. |
| 1:15 – 2:15 | `tablas/02_FSM2_Mealy_codigo.md` | FSM 2 Mealy: detector de secuencia A → C → B. Estados SIN_TECLAS, PASO_1, PASO_2. Las salidas `CODIGO_OK` y `ALARMA` dependen de la tecla y del estado. Mantener una tecla no avanza; una equivocada da alarma y reinicia. |
| 2:15 – 3:00 | Doble clic en una FSM → bloques | Topología del libro: *Next state logic*, *State register* (flip-flops D con CLK y reset) y *Output logic*; la realimentación de Q. Mostrar la Next state logic (un AND por flecha) y la Output logic. Moore: solo Q; Mealy: Q y entradas. |
| 3:00 – 3:30 | `top`, los cables entre cajas | Interacción: `CODIGO_OK` → `OK` (abre la barrera) y `CERRADA` → `EN` (solo acepta código con la barrera cerrada). Un solo `CLK` y un solo `RST` para las dos. |
| 3:30 – 4:30 | **Demostración** (Ticks Enabled) | RST. Pulsar A (PASO_1), C (PASO_2), B → `CODIGO_OK` al instante y la barrera ABRIENDO → ABIERTA. `SENSOR = 1`: se queda abierta. `SENSOR = 0`: CERRANDO → CERRADA. Luego pulsar B primero → ALARMA. |
| 4:30 – 5:00 | `fuente/` y verificación | Decisiones: factorizar en dos FSM, Moore vs Mealy, reset asíncrono y síncrono, estados no usados regresan a 00. Se comprobó con pruebas automáticas contra un modelo (exhaustivo en cada bloque y miles de ciclos en el sistema completo). |
