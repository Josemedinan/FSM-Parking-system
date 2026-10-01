# Interaccion entre las dos FSM

| Senal | Sale de | Entra a | Para que sirve |
|---|---|---|---|
| `CODIGO_OK` | FSM 2 (Mealy) | FSM 1, entrada `OK` | ordena abrir la barrera |
| `CERRADA` | FSM 1 (Moore) | FSM 2, entrada `EN` | solo se acepta el codigo con la barrera cerrada |
| `CLK` | reloj del `top` | las dos FSM | un solo reloj para todo el sistema |
| `RST` | pin del `top` | las dos FSM | reset comun (asincrono en la FSM 1, sincronico en la FSM 2) |

Entradas del usuario: `A`, `B`, `C` (teclado, van a la FSM 2) y `SENSOR` (va a la FSM 1).
