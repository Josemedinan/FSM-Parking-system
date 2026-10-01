# -*- coding: utf-8 -*-
"""Genera las tablas de las dos FSM (Markdown y CSV) en ../tablas

Las tablas salen de los MODELOS de las maquinas y se comprueban contra las
ECUACIONES booleanas que implementa el circuito (si alguna no coincide, el script falla).

Uso:   python generar_tablas.py
"""
import csv
import itertools
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tablas')
os.makedirs(OUT, exist_ok=True)

# ===================================================================== FSM 1 (Moore)
S1 = ['CERRADA', 'ABRIENDO', 'ABIERTA', 'CERRANDO']      # codigo = indice (Q1 Q0)


def m1_next(s, sensor, ok):
    if s == 0:
        return 1 if ok else 0
    if s == 1:
        return 2
    if s == 2:
        return 2 if sensor else 3
    return 2 if sensor else 0


def m1_eq(q1, q0, sensor, ok):
    """Ecuaciones del circuito M1_next_state_logic (suma de productos)."""
    nq1, nq0 = 1 - q1, 1 - q0
    d1 = (nq1 & q0) | (q1 & nq0) | (q1 & q0 & sensor)
    d0 = (nq1 & nq0 & ok) | (q1 & nq0 & (1 - sensor))
    return d1, d0


def m1_out_eq(q1, q0):
    nq1, nq0 = 1 - q1, 1 - q0
    return nq1 & nq0, nq1 & q0, q1 & nq0, q1 & q0


# ===================================================================== FSM 2 (Mealy)
S2 = ['SIN_TECLAS', 'PASO_1 (A ok)', 'PASO_2 (A,C ok)']   # codigo = indice (P1 P0); 11 no se usa
KEYS = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]
KNAME = {(0, 0, 0): 'ninguna', (1, 0, 0): 'A', (0, 1, 0): 'B', (0, 0, 1): 'C'}


def m2_next(p, en, a, b, c, rst):
    if rst or not en:
        return 0
    if p == 0:
        return 1 if a else 0
    if p == 1:
        return 2 if c else (0 if b else 1)
    if p == 2:
        return 0 if (a or b) else 2
    return 0


def m2_out(p, en, a, b, c):
    ok = int(en and p == 2 and b)
    al = int(en and ((p == 0 and (b or c)) or (p == 1 and b) or (p == 2 and a)))
    return ok, al


def m2_eq(p1, p0, en, a, b, c, rst):
    n = lambda v: 1 - v
    d1 = (n(rst) & en & n(p1) & p0 & c) | (n(rst) & en & p1 & n(p0) & n(a) & n(b))
    d0 = (n(rst) & en & n(p1) & n(p0) & a) | (n(rst) & en & n(p1) & p0 & n(b) & n(c))
    return d1, d0


def m2_out_eq(p1, p0, en, a, b, c):
    n = lambda v: 1 - v
    ok = en & p1 & n(p0) & b & n(a) & n(c)
    al = (en & n(p1) & n(p0) & b) | (en & n(p1) & n(p0) & c) | (en & n(p1) & p0 & b) | (en & p1 & n(p0) & a)
    return ok, al


# ===================================================================== utilidades
def md_table(header, rows):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '|'.join([':---:'] * len(header)) + '|']
    for r in rows:
        out.append('| ' + ' | '.join(str(x) for x in r) + ' |')
    return '\n'.join(out)


def write_csv(name, header, rows):
    with open(os.path.join(OUT, name), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main():
    # ------------------------------------------------------------ FSM 1
    t_rows, csv_rows = [], []
    for s in range(4):
        for sensor, ok in itertools.product((0, 1), repeat=2):
            n = m1_next(s, sensor, ok)
            assert m1_eq(s >> 1, s & 1, sensor, ok) == (n >> 1, n & 1), ('FSM1 NSL', s, sensor, ok)
            row = [S1[s], s >> 1, s & 1, sensor, ok, n >> 1, n & 1, S1[n]]
            t_rows.append(row)
            csv_rows.append(row)
    h1 = ['Estado actual', 'Q1', 'Q0', 'SENSOR', 'OK', "D1 (=Q1')", "D0 (=Q0')", 'Estado siguiente']
    write_csv('fsm1_moore_transiciones.csv', h1, csv_rows)
    o_rows = []
    for s in range(4):
        o = m1_out_eq(s >> 1, s & 1)
        assert o == tuple(int(s == k) for k in range(4))
        o_rows.append([S1[s], s >> 1, s & 1] + list(o))
    ho = ['Estado', 'Q1', 'Q0'] + S1
    write_csv('fsm1_moore_salidas.csv', ho, o_rows)

    md1 = f"""# FSM 1 (Moore) - Controlador de la barrera

4 estados, codificacion binaria (2 flip-flops D, reset asincrono). Las salidas dependen **solo del estado**.

## Entradas y salidas
| Senal | Tipo | Significado |
|---|---|---|
| `CLK` | entrada | reloj comun a las dos FSM |
| `RST` | entrada | reset asincrono (estado 00 = CERRADA) |
| `SENSOR` | entrada | 1 = hay un carro bajo la barrera |
| `OK` | entrada (viene de la FSM 2) | 1 = el codigo secreto fue correcto (`CODIGO_OK`) |
| `CERRADA`, `ABRIENDO`, `ABIERTA`, `CERRANDO` | salidas (Moore) | un LED por estado |

## Codificacion de estados
{md_table(['Estado', 'Q1', 'Q0'], [[S1[s], s >> 1, s & 1] for s in range(4)])}

## Diagrama de estados
```mermaid
stateDiagram-v2
    [*] --> CERRADA
    CERRADA --> ABRIENDO: OK = 1
    CERRADA --> CERRADA: OK = 0
    ABRIENDO --> ABIERTA
    ABIERTA --> ABIERTA: SENSOR = 1
    ABIERTA --> CERRANDO: SENSOR = 0
    CERRANDO --> ABIERTA: SENSOR = 1 (seguridad)
    CERRANDO --> CERRADA: SENSOR = 0
```

## Tabla de transicion de estados (con la codificacion)
{md_table(h1, t_rows)}

## Tabla de salidas (Moore)
{md_table(ho, o_rows)}

## Ecuaciones (suma de productos, un termino AND por flecha del diagrama)
```
D1 = Q1'.Q0 + Q1.Q0' + Q1.Q0.SENSOR
D0 = Q1'.Q0'.OK + Q1.Q0'.SENSOR'

CERRADA  = Q1'.Q0'      ABRIENDO = Q1'.Q0
ABIERTA  = Q1.Q0'       CERRANDO = Q1.Q0
```
"""
    open(os.path.join(OUT, '01_FSM1_Moore_barrera.md'), 'w', encoding='utf-8').write(md1)

    # ------------------------------------------------------------ FSM 2
    t_rows, csv_rows = [], []
    for p in range(4):
        for k, en, rst in itertools.product(KEYS, (0, 1), (0, 1)):
            a, b, c = k
            n = m2_next(p, en, a, b, c, rst)
            assert m2_eq(p >> 1, p & 1, en, a, b, c, rst) == (n >> 1, n & 1), ('FSM2 NSL', p, k, en, rst)
            ok, al = m2_out(p, en, a, b, c)
            assert m2_out_eq(p >> 1, p & 1, en, a, b, c) == (ok, al), ('FSM2 OL', p, k, en)
            csv_rows.append([p >> 1, p & 1, a, b, c, en, rst, n >> 1, n & 1, ok, al])
    h2 = ['P1', 'P0', 'A', 'B', 'C', 'EN', 'RST', "D1 (=P1')", "D0 (=P0')", 'CODIGO_OK', 'ALARMA']
    write_csv('fsm2_mealy_transiciones_y_salidas.csv', h2, csv_rows)
    # tabla "legible": EN = 1, RST = 0
    leg = []
    for p in range(3):
        for k in KEYS:
            a, b, c = k
            n = m2_next(p, 1, a, b, c, 0)
            ok, al = m2_out(p, 1, a, b, c)
            leg.append([S2[p], p >> 1, p & 1, KNAME[k], S2[n], n >> 1, n & 1,
                        'CODIGO_OK' if ok else ('ALARMA' if al else '-')])
    hl = ['Estado actual', 'P1', 'P0', 'Tecla', 'Estado siguiente', "P1'", "P0'", 'Salida (Mealy)']
    write_csv('fsm2_mealy_tabla_legible.csv', hl, leg)

    md2 = f"""# FSM 2 (Mealy) - Verificador del codigo secreto (A, luego C, luego B)

Detector de secuencia con 2 flip-flops D (reset sincronico). Las salidas dependen del **estado y de las entradas**
(por eso `CODIGO_OK` y `ALARMA` cambian en cuanto se pulsa la tecla, sin esperar el reloj).
Se asume que se pulsa **una tecla a la vez**.

## Entradas y salidas
| Senal | Tipo | Significado |
|---|---|---|
| `A`, `B`, `C` | entradas | teclas del teclado (botones) |
| `EN` | entrada (viene de la FSM 1) | 1 = la barrera esta CERRADA (solo entonces se acepta codigo) |
| `RST` | entrada | reset sincronico |
| `CODIGO_OK` | salida (Mealy, va a la FSM 1) | se pulso B con A y C ya correctas |
| `ALARMA` | salida (Mealy) | tecla equivocada en cualquier paso |
| `PASO_1`, `PASO_2` | salidas (de estado) | progreso del codigo (LEDs) |

## Codificacion de estados
{md_table(['Estado', 'P1', 'P0', 'Significado'],
          [[S2[0], 0, 0, 'ninguna tecla correcta todavia'], [S2[1], 0, 1, 'la A ya se pulso'],
           [S2[2], 1, 0, 'A y C ya se pulsaron'], ['(no usado)', 1, 1, 'se trata como 00']])}

## Diagrama de estados (Mealy: tecla / salida), con EN = 1
```mermaid
stateDiagram-v2
    [*] --> SIN_TECLAS
    SIN_TECLAS --> PASO_1: A / -
    SIN_TECLAS --> SIN_TECLAS: B o C / ALARMA
    PASO_1 --> PASO_1: A (se mantiene) / -
    PASO_1 --> PASO_2: C / -
    PASO_1 --> SIN_TECLAS: B / ALARMA
    PASO_2 --> PASO_2: C (se mantiene) / -
    PASO_2 --> SIN_TECLAS: B / CODIGO_OK
    PASO_2 --> SIN_TECLAS: A / ALARMA
```
Si `EN = 0` (barrera no cerrada) o `RST = 1`, de cualquier estado se vuelve a SIN_TECLAS.

## Tabla de transicion y salidas (EN = 1, RST = 0)
{md_table(hl, leg)}

La tabla completa (todas las combinaciones de P1, P0, A, B, C, EN, RST con una tecla a la vez) esta en
`fsm2_mealy_transiciones_y_salidas.csv`.

## Ecuaciones
```
Next state logic:
D1 = RST'.EN.P1'.P0.C + RST'.EN.P1.P0'.A'.B'
D0 = RST'.EN.P1'.P0'.A + RST'.EN.P1'.P0.B'.C'

Output logic (Mealy):
CODIGO_OK = EN.P1.P0'.B.A'.C'
ALARMA    = EN.(P1'.P0'.B + P1'.P0'.C + P1'.P0.B + P1.P0'.A)
PASO_1 = P1'.P0        PASO_2 = P1.P0'
```
"""
    open(os.path.join(OUT, '02_FSM2_Mealy_codigo.md'), 'w', encoding='utf-8').write(md2)

    md3 = """# Interaccion entre las dos FSM

| Senal | Sale de | Entra a | Para que sirve |
|---|---|---|---|
| `CODIGO_OK` | FSM 2 (Mealy) | FSM 1, entrada `OK` | ordena abrir la barrera |
| `CERRADA` | FSM 1 (Moore) | FSM 2, entrada `EN` | solo se acepta el codigo con la barrera cerrada |
| `CLK` | reloj del `top` | las dos FSM | un solo reloj para todo el sistema |
| `RST` | pin del `top` | las dos FSM | reset comun (asincrono en la FSM 1, sincronico en la FSM 2) |

Entradas del usuario: `A`, `B`, `C` (teclado, van a la FSM 2) y `SENSOR` (va a la FSM 1).
"""
    open(os.path.join(OUT, '03_Interaccion.md'), 'w', encoding='utf-8').write(md3)
    print('Tablas generadas en', os.path.abspath(OUT))


def paso(s, p, key, sensor, rst=0):
    a, b, c = key
    en = int(s == 0)
    ok, al = m2_out(p, en, a, b, c)
    ns = 0 if rst else m1_next(s, sensor, ok)
    np_ = m2_next(p, en, a, b, c, rst)
    return ok, al, ns, np_


NOTA_BARRERA = {(0, 1): 'la barrera empieza a abrir', (1, 2): 'la barrera termina de abrir',
                (2, 3): 'ya no hay carro: empieza a cerrar', (3, 0): 'la barrera queda cerrada',
                (3, 2): 'hay un carro: se vuelve a abrir (seguridad)'}


def traza(titulo, descripcion, secuencia):
    """secuencia: lista de (tecla 'A'/'B'/'C'/None, sensor)."""
    s = p = 0
    filas = []
    for i, (t, sensor) in enumerate(secuencia, 1):
        key = (int(t == 'A'), int(t == 'B'), int(t == 'C'))
        ok, al, ns, np_ = paso(s, p, key, sensor)
        notas = []
        if ok:
            notas.append('**código correcto: `CODIGO_OK` abre la barrera**')
        elif al:
            notas.append('**tecla equivocada: `ALARMA`, el verificador se reinicia**')
        elif t and np_ != p:
            notas.append('tecla correcta: avanza el código')
        elif t:
            notas.append('se mantiene la tecla: no cambia nada')
        if (s, ns) in NOTA_BARRERA:
            notas.append(NOTA_BARRERA[(s, ns)])
        elif s == 2 and ns == 2 and sensor:
            notas.append('hay un carro: la barrera se queda abierta')
        filas.append([i, t or '–', sensor, S1[s], S2[p].split(' ')[0], 'sí' if ok else '–', 'sí' if al else '–',
                      S1[ns], S2[np_].split(' ')[0], '; '.join(notas) or '–'])
        s, p = ns, np_
    h = ['Ciclo', 'Tecla', 'SENSOR', 'Barrera (antes)', 'Verificador (antes)', '`CODIGO_OK`', '`ALARMA`',
         'Barrera (después)', 'Verificador (después)', 'Qué pasa']
    return f"### {titulo}\n\n{descripcion}\n\n{md_table(h, filas)}\n"


def trazas():
    ok_seq = [(None, 0), ('A', 0), ('A', 0), (None, 0), ('C', 0), (None, 0), ('B', 0), (None, 0), (None, 1),
              (None, 1), (None, 0), (None, 0), (None, 0)]
    mal_seq = [('B', 0), (None, 0), ('A', 0), ('B', 0), (None, 0)]
    seg_seq = [('A', 0), ('C', 0), ('B', 0), (None, 0), (None, 0), (None, 1), (None, 0), (None, 0), (None, 0)]
    texto = ("# Ejemplos de simulación (ciclo por ciclo)\n\n"
             "Cada fila es un flanco de reloj. Las columnas *antes* muestran el estado en el que estaba cada máquina, "
             "las columnas `CODIGO_OK` y `ALARMA` son las salidas Mealy (se calculan con el estado y la tecla pulsada) "
             "y las columnas *después* muestran el estado tras el flanco.\n\n"
             + traza('Ejemplo 1: código correcto y ciclo completo de la barrera',
                     'Se teclea A, C, B. Después entra un carro (`SENSOR = 1`), la barrera espera, el carro sale y cierra.',
                     ok_seq)
             + '\n' + traza('Ejemplo 2: código incorrecto',
                            'Se pulsa B sin haber pulsado antes A; luego A y B (falta la C). Los dos errores dan `ALARMA`.',
                            mal_seq)
             + '\n' + traza('Ejemplo 3: sensor de seguridad al cerrar',
                            'Se abre la barrera con el código; cuando empieza a cerrar entra un carro y la barrera se reabre.',
                            seg_seq))
    open(os.path.join(OUT, '04_Ejemplos_de_simulacion.md'), 'w', encoding='utf-8').write(texto)
    return texto


if __name__ == '__main__':
    main()
    trazas()
