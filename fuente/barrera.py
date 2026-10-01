# -*- coding: utf-8 -*-
"""Barrera de estacionamiento con codigo de acceso - dos FSM que interactuan.

 FSM 1 (Moore, 4 estados)  = CONTROLADOR DE LA BARRERA
      CERRADA -> ABRIENDO -> ABIERTA -> CERRANDO -> CERRADA   (con sensor de seguridad)
 FSM 2 (Mealy, 2 estados)  = VERIFICADOR DEL CODIGO (hay que pulsar A y luego B)
      salidas: CODIGO_OK, ALARMA (dependen del estado Y de los botones)
"""
import sys
sys.path.insert(0, '.')
from lg import *
from sop import sop_circuit

EXT1 = ['SENSOR', 'OK']
OUT1 = ['CERRADA', 'ABRIENDO', 'ABIERTA', 'CERRANDO']
COL = {'CERRADA': '#e00000', 'ABRIENDO': '#f2c200', 'ABIERTA': '#00b020', 'CERRANDO': '#ff7a00',
       'CODIGO_OK': '#00c8d2', 'ALARMA': '#e0007a', 'PASO_1': '#2f7bff', 'PASO_2': '#8a4bff'}


# ------------------------------------------------------------------ FSM 1
def c_reg1():
    c = Circuit('M1_registro_estado')
    c.text(60, 50, 'FSM 1 (Moore) - State register (2 FF D, reset asincrono)', size=16, bold=True)
    c.text(60, 76, 'Guarda el estado Q1 Q0.  RST = 1 lo lleva a 00 (CERRADA) sin esperar el flanco.', size=12)
    ys = {1: 140, 0: 240}
    d = {k: c.pin_in('D%d' % k, 100, ys[k] + 10) for k in (1, 0)}
    ck = c.pin_in('CLK', 100, 370)
    rs = c.pin_in('RST', 100, 420)
    ff = {k: c.dff(300, ys[k], 'Q%d' % k) for k in (1, 0)}
    q = {k: c.pin_out('Q%d' % k, 480, ys[k] + 10) for k in (1, 0)}
    for k in (1, 0):
        c.net('d%d' % k, d[k].o, ff[k].D)
        c.net('q%d' % k, ff[k].Q, q[k].i)
    c.wire_net('clk', [ck.o, ff[1].CLK, ff[0].CLK],
               [[(100, 370), (230, 370), (230, 190), (290, 190)], [(230, 290), (290, 290)]])
    c.wire_net('rst', [rs.o, ff[1].R, ff[0].R],
               [[(100, 420), (400, 420), (400, 220), (320, 220), (320, 200)],
                [(400, 320), (320, 320), (320, 300)]])
    c.route()
    c.make_appearance(title='State register')
    return c


def c_nsl1():
    d1 = ["Q1' Q0", "Q1 Q0'", "Q1 Q0 SENSOR"]
    d0 = ["Q1' Q0' OK", "Q1 Q0' SENSOR'"]
    notes = ("D1 = Q1'Q0 + Q1Q0' + Q1Q0.SENSOR\n"
             "D0 = Q1'Q0'.OK + Q1Q0'.SENSOR'\n"
             "Un termino AND por cada flecha del diagrama de estados.")
    return sop_circuit('M1_next_state_logic', 'FSM 1 (Moore) - Next state logic',
                       'D1 D0 = estado siguiente = f(estado actual Q1 Q0, SENSOR, OK del verificador de codigo)',
                       EXT1 + ['Q1', 'Q0'], [('D1', d1), ('D0', d0)], notes=notes,
                       box_title='Next state logic')


def c_ol1():
    notes = ("CERRADA = Q1'Q0'   ABRIENDO = Q1'Q0   ABIERTA = Q1Q0'   CERRANDO = Q1Q0\n"
             "Moore: las salidas dependen SOLO del estado (un LED por estado).")
    return sop_circuit('M1_output_logic', 'FSM 1 (Moore) - Output logic',
                       'Salidas = f(estado actual)', ['Q1', 'Q0'],
                       [('CERRADA', ["Q1' Q0'"]), ('ABRIENDO', ["Q1' Q0"]),
                        ('ABIERTA', ["Q1 Q0'"]), ('CERRANDO', ["Q1 Q0"])],
                       notes=notes, box_title='Output logic')


def c_fsm1(reg, nsl, ol):
    c = Circuit('M1_FSM_Moore')
    c.text(60, 40, 'FSM 1 (Moore) - Controlador de la barrera', size=16, bold=True)
    c.text(60, 66, 'Next state logic -> State register (Q1 Q0) -> Output logic.  Q realimenta a la Next state logic.',
           size=11)
    T, XP, XN = 260, 100, 360
    wN, wR, wO = (x.appearance['w'] for x in (nsl, reg, ol))
    XR = XN + wN + 120
    XO = XR + wR + 120
    XPO = XO + wO + 60
    pin = {'CLK': c.pin_in('CLK', XP, 140), 'RST': c.pin_in('RST', XP, 180)}
    for k, n in enumerate(EXT1):
        pin[n] = c.pin_in(n, XP, T + 20 + 20 * k)
    N, R, O = c.sub(nsl, XN, T), c.sub(reg, XR, T), c.sub(ol, XO, T)
    po = {n: c.pin_out(n, XPO, T + 20 + 20 * k) for k, n in enumerate(OUT1)}
    hN = nsl.appearance['h']
    yl = {1: T + hN + 40, 0: T + hN + 60}
    for k in (1, 0):
        po['Q%d' % k] = c.pin_out('Q%d' % k, XPO, yl[k])
    for x, w, s in ((XN, wN, 'Next state logic'), (XR, wR, 'State register'), (XO, wO, 'Output logic')):
        c.text(x + w // 2, T - 34, s, size=13, bold=True, align='center')
    for k, n in enumerate(EXT1):
        y = T + 20 + 20 * k
        c.wire_net(n, [pin[n].o, N.p[n]], [[(XP, y), (XN, y)]])
    for k, n in enumerate(('D1', 'D0')):
        y = T + 20 + 20 * k
        c.wire_net(n, [N.p[n], R.p[n]], [[(XN + wN, y), (XR, y)]])
    xg_r, xg_c = XN + wN + 40, XN + wN + 80
    c.wire_net('CLK', [pin['CLK'].o, R.p['CLK']],
               [[(XP, 140), (xg_c, 140), (xg_c, T + 60), (XR, T + 60)]])
    c.wire_net('RST', [pin['RST'].o, R.p['RST']],
               [[(XP, 180), (xg_r, 180), (xg_r, T + 80), (XR, T + 80)]])
    xq = {1: XR + wR + 30, 0: XR + wR + 50}
    xv = {1: XN - 30, 0: XN - 20}
    for j, k in enumerate((1, 0)):
        yq, yin, n = T + 20 + 20 * j, T + 20 + 20 * (len(EXT1) + j), 'Q%d' % k
        c.wire_net(n, [R.p[n], O.p[n], N.p[n], po[n].i],
                   [[(XR + wR, yq), (XO, yq)], [(xq[k], yq), (xq[k], yl[k])],
                    [(xv[k], yl[k]), (xq[k], yl[k]), (XPO, yl[k])],
                    [(xv[k], yl[k]), (xv[k], yin), (XN, yin)]])
    for k, n in enumerate(OUT1):
        y = T + 20 + 20 * k
        c.wire_net(n, [O.p[n], po[n].i], [[(XO + wO, y), (XPO, y)]])
    c.text(xv[1], yl[0] + 24, 'Q1 Q0 (estado actual) realimentan a la Next state logic', size=10)
    c.route()
    c.make_appearance(in_labels=['CLK', 'RST'] + EXT1, out_labels=OUT1 + ['Q1', 'Q0'], title='FSM 1 (Moore)')
    return c


# ------------------------------------------------------------------ FSM 2
def c_reg2():
    c = Circuit('M2_registro_estado')
    c.text(60, 50, 'FSM 2 (Mealy) - State register (2 FF D)', size=16, bold=True)
    c.text(60, 76, 'P1 P0 = cuantas teclas del codigo van bien:  00 ninguna,  01 va la 1a (A),  10 van 2 (A, C).  '
                   '(Reset sincronico en la next state logic.)', size=12)
    ys = {1: 140, 0: 240}
    d = {k: c.pin_in('D%d' % k, 100, ys[k] + 10) for k in (1, 0)}
    ck = c.pin_in('CLK', 100, 370)
    ff = {k: c.dff(300, ys[k], 'P%d' % k) for k in (1, 0)}
    q = {k: c.pin_out('P%d' % k, 480, ys[k] + 10) for k in (1, 0)}
    for k in (1, 0):
        c.net('d%d' % k, d[k].o, ff[k].D)
        c.net('q%d' % k, ff[k].Q, q[k].i)
    c.wire_net('clk', [ck.o, ff[1].CLK, ff[0].CLK],
               [[(100, 370), (230, 370), (230, 190), (290, 190)], [(230, 290), (290, 290)]])
    c.route()
    c.make_appearance(title='State register')
    return c


def c_nsl2():
    d1 = ["RST' EN P1' P0 C", "RST' EN P1 P0' A' B'"]
    d0 = ["RST' EN P1' P0' A", "RST' EN P1' P0 B' C'"]
    notes = ("D1 = RST'.EN.P1'.P0.C + RST'.EN.P1.P0'.A'.B'\n"
             "D0 = RST'.EN.P1'.P0'.A + RST'.EN.P1'.P0.B'.C'\n"
             "Codigo secreto A -> C -> B: la tecla correcta avanza, mantenerla no cambia nada, una equivocada regresa a 00.\n"
             "EN = 0 (barrera no cerrada) o RST = 1: vuelve a 00.")
    return sop_circuit('M2_next_state_logic', 'FSM 2 (Mealy) - Next state logic',
                       'D1 D0 = estado siguiente = f(P1 P0, teclas A B C, EN, RST)   (se pulsa una tecla a la vez)',
                       ['A', 'B', 'C', 'EN', 'RST', 'P1', 'P0'],
                       [('D1', d1), ('D0', d0)], notes=notes, box_title='Next state logic')


def c_ol2():
    ok = ["EN P1 P0' B A' C'"]
    al = ["EN P1' P0' B", "EN P1' P0' C", "EN P1' P0 B", "EN P1 P0' A"]
    notes = ("CODIGO_OK = EN.P1.P0'.B.A'.C'   (van A y C bien y ahora B)\n"
             "ALARMA = EN.(P1'P0'.B + P1'P0'.C + P1'P0.B + P1P0'.A)   (tecla equivocada en cada paso)\n"
             "PASO_1 = P1'P0   PASO_2 = P1P0'\n"
             "Mealy: CODIGO_OK y ALARMA cambian en cuanto pulsas la tecla (dependen de las teclas Y del estado).")
    return sop_circuit('M2_output_logic', 'FSM 2 (Mealy) - Output logic',
                       'Salidas = f(estado P1 P0, teclas A B C, EN)', ['A', 'B', 'C', 'EN', 'P1', 'P0'],
                       [('CODIGO_OK', ok), ('ALARMA', al), ('PASO_1', ["P1' P0"]), ('PASO_2', ["P1 P0'"])],
                       notes=notes, box_title='Output logic')


def c_fsm2(reg, nsl, ol):
    c = Circuit('M2_FSM_Mealy')
    c.text(60, 40, 'FSM 2 (Mealy) - Verificador del codigo secreto (A, luego C, luego B)', size=16, bold=True)
    c.text(60, 66, 'Mealy: las teclas y EN llegan a la Next state logic Y a la Output logic; las salidas reaccionan sin esperar el reloj.',
           size=11)
    T, XN = 380, 380
    wN, wR, wO = (x.appearance['w'] for x in (nsl, reg, ol))
    XR = XN + wN + 100
    XO = XR + wR + 190
    YO = T - 80                 # las filas P1, P0 de la OL quedan a la altura de Q del registro
    XPO = XO + wO + 60
    keys = ['A', 'B', 'C', 'EN']
    P = {n: c.pin_in(n, 100, T + 20 + 20 * k) for k, n in enumerate(keys)}
    P['RST'] = c.pin_in('RST', 100, T + 100)
    P['CLK'] = c.pin_in('CLK', 100, T + 180)
    N, R, O = c.sub(nsl, XN, T), c.sub(reg, XR, T), c.sub(ol, XO, YO)
    for x, y, w, s in ((XN, T, wN, 'Next state logic'), (XR, T, wR, 'State register'),
                       (XO, YO, wO, 'Output logic')):
        c.text(x + w // 2, y - 34, s, size=13, bold=True, align='center')
    outs = ['CODIGO_OK', 'ALARMA', 'PASO_1', 'PASO_2']
    op = {n: c.pin_out(n, XPO, O.p[n].y) for n in outs}
    for n in outs:
        c.wire_net(n, [O.p[n], op[n].i], [[(XO + wO, O.p[n].y), (XPO, O.p[n].y)]])
    c.wire_net('RST', [P['RST'].o, N.p['RST']], [[(100, T + 100), (XN, T + 100)]])
    rail = {'A': T - 150, 'B': T - 130, 'C': T - 110, 'EN': T - 90}
    xb = {'A': 140, 'B': 160, 'C': 180, 'EN': 200}
    xd = {'A': XR + wR + 80, 'B': XR + wR + 60, 'C': XR + wR + 40, 'EN': XR + wR + 20}
    for k, n in enumerate(keys):
        yp = T + 20 + 20 * k
        c.wire_net(n, [P[n].o, N.p[n], O.p[n]],
                   [[(100, yp), (XN, yp)],
                    [(xb[n], yp), (xb[n], rail[n]), (xd[n], rail[n]), (xd[n], O.p[n].y), (XO, O.p[n].y)]])
    for k, n in enumerate(('D1', 'D0')):
        y = T + 20 + 20 * k
        c.wire_net(n, [N.p[n], R.p[n]], [[(XN + wN, y), (XR, y)]])
    xc = XN + wN + 40
    c.wire_net('CLK', [P['CLK'].o, R.p['CLK']],
               [[(100, T + 180), (xc, T + 180), (xc, T + 60), (XR, T + 60)]])
    yl = {1: T + 220, 0: T + 240}
    xq = {1: XR + wR + 110, 0: XR + wR + 130}
    xl = {1: XN - 40, 0: XN - 20}
    for j, k in enumerate((1, 0)):
        n = 'P%d' % k
        yq = T + 20 + 20 * j
        yin = T + 20 + 20 * (5 + j) + 0
        c.wire_net(n, [R.p[n], O.p[n], N.p[n]],
                   [[(XR + wR, yq), (XO, O.p[n].y)], [(xq[k], yq), (xq[k], yl[k])],
                    [(xl[k], yl[k]), (xq[k], yl[k])], [(xl[k], yl[k]), (xl[k], yin), (XN, yin)]])
    c.text(XN - 40, T + 264, 'P1 P0 (estado actual) realimentan a la Next state logic', size=10)
    c.route()
    c.make_appearance(in_labels=['CLK', 'RST'] + keys, out_labels=outs, title='FSM 2 (Mealy)')
    return c


# ------------------------------------------------------------------ top
def build_top(cs, test=False):
    m1c, m2c = cs['M1_FSM_Moore'], cs['M2_FSM_Mealy']
    c = Circuit('top')
    c.text(60, 30, 'Barrera de estacionamiento con código secreto: dos FSM que interactúan', size=18, bold=True)
    c.text(60, 60, 'FSM 2 (Mealy) verifica el código secreto A, C, B.   FSM 1 (Moore) mueve la barrera.   '
                   'Un solo CLK y un solo RST.', size=11)
    X, Y1 = 540, 240
    w1, h1 = m1c.appearance['w'], m1c.appearance['h']
    w2, h2 = m2c.appearance['w'], m2c.appearance['h']
    G = [Y1 + h1 + 30 + 20 * k for k in range(2)]
    Y2 = G[-1] + 60
    m1, m2 = c.sub(m1c, X, Y1), c.sub(m2c, X, Y2)
    Xr = X + max(w1, w2)
    xd = Xr + 170
    P1, P2 = m1.p, m2.p
    ck = c.clock('CLK', 100, P1['CLK'].y)
    rst = c.pin_in('RST', 100, P1['RST'].y)
    sensor = c.pin_in('SENSOR', 100, P1['SENSOR'].y)
    mk = (lambda n, y: c.pin_in(n, 100, y)) if test else (lambda n, y: c.button(n, 100, y))
    keys = {n: mk(n, P2[n].y) for n in ('A', 'B', 'C')}
    c.text(100, Y1 - 60, 'ENTRADAS (clic)', size=12, bold=True)
    c.text(100, Y1 - 40, 'SENSOR = hay un carro bajo la barrera', size=10)
    c.text(100, P2['A'].y - 40, 'TECLADO A B C (mantén el clic)', size=10)
    xk, xs_ = X - 140, X - 120
    c.wire_net('CLK', [ck.o, P1['CLK'], P2['CLK']],
               [[(100, P1['CLK'].y), (X, P1['CLK'].y)], [(xk, P1['CLK'].y), (xk, P2['CLK'].y), (X, P2['CLK'].y)]])
    c.wire_net('RST', [rst.o, P1['RST'], P2['RST']],
               [[(100, P1['RST'].y), (X, P1['RST'].y)], [(xs_, P1['RST'].y), (xs_, P2['RST'].y), (X, P2['RST'].y)]])
    c.wire_net('SENSOR', [sensor.o, P1['SENSOR']], [[(100, P1['SENSOR'].y), (X, P1['SENSOR'].y)]])
    for n, b in keys.items():
        c.wire_net(n, [b.o, P2[n]], [[(100, P2[n].y), (X, P2[n].y)]])

    def dev(label, y):
        if label in COL and not test:
            return c.led(label, xd, y, COL[label])
        return c.pin_out(label, xd, y)
    o1 = {n: dev(n, P1[n].y) for n in OUT1 + ['Q1', 'Q0']}
    o2 = {n: dev(n, P2[n].y) for n in ('CODIGO_OK', 'ALARMA', 'PASO_1', 'PASO_2')}
    c.text(xd - 10, Y1 - 40, 'FSM 1 (Moore): estado de la barrera', size=12, bold=True)
    c.text(xd - 10, Y2 - 40, 'FSM 2 (Mealy): verificador de código', size=12, bold=True)
    for n in ('ABRIENDO', 'ABIERTA', 'CERRANDO', 'Q1', 'Q0'):
        y = P1[n].y
        c.wire_net('o_' + n, [P1[n], o1[n].i], [[(X + w1, y), (xd, y)]])
    for n in ('ALARMA', 'PASO_1', 'PASO_2'):
        y = P2[n].y
        c.wire_net('o_' + n, [P2[n], o2[n].i], [[(X + w2, y), (xd, y)]])
    # FSM 1 -> FSM 2 : CERRADA (= EN)
    y1p, y2p = P1['CERRADA'].y, P2['EN'].y
    xb, xl = Xr + 30, X - 100
    c.wire_net('CERRADA', [P1['CERRADA'], P2['EN'], o1['CERRADA'].i],
               [[(X + w1, y1p), (xd, y1p)], [(xb, y1p), (xb, G[0]), (xl, G[0]), (xl, y2p), (X, y2p)]])
    # FSM 2 -> FSM 1 : CODIGO_OK (= OK)
    ya, yb = P2['CODIGO_OK'].y, P1['OK'].y
    xr, xf = Xr + 60, X - 80
    c.wire_net('CODIGO_OK', [P2['CODIGO_OK'], P1['OK'], o2['CODIGO_OK'].i],
               [[(X + w2, ya), (xd, ya)], [(xr, ya), (xr, G[1]), (xf, G[1]), (xf, yb), (X, yb)]])
    c.text(X, Y2 + h2 + 10, 'FSM 1 -> FSM 2: CERRADA (EN: solo acepta código con la barrera cerrada)      '
                            'FSM 2 -> FSM 1: CODIGO_OK (OK: abre la barrera)', size=10)
    y0 = Y2 + h2 + 60
    c.text(60, y0, 'Cómo probarlo', size=13, bold=True)
    c.text(60, y0 + 24, chr(10).join([
        '0) Simulate > Ticks Enabled (Ctrl+K).  Para ir paso a paso: desactívalo y haz clic sobre CLK.',
        '1) RST = 1 un momento y luego 0.  Se enciende CERRADA (rojo).',
        '2) CÓDIGO SECRETO = A, luego C, luego B.  Mantén pulsada cada tecla hasta que el LED de progreso',
        '   se encienda y suéltala:  A -> PASO_1 (azul),  C -> PASO_2 (violeta),  B -> CODIGO_OK (cian, al instante,',
        '   Mealy) y la barrera hace ABRIENDO (amarillo) -> ABIERTA (verde).',
        '3) Con SENSOR = 1 (hay un carro debajo) la barrera se queda ABIERTA.  Con SENSOR = 0 pasa a CERRANDO',
        '   (naranja) -> CERRADA.  Si pones SENSOR = 1 mientras cierra, vuelve a ABIERTA (seguridad).',
        '4) CÓDIGO INCORRECTO: pulsa una tecla equivocada (p. ej. B primero, o A luego B) y se enciende',
        '   ALARMA (morado); el progreso se borra y hay que empezar de nuevo.']),
        size=11, mono=True)
    c.route()
    return c


def build_all(test=False):
    reg1, nsl1, ol1 = c_reg1(), c_nsl1(), c_ol1()
    fsm1 = c_fsm1(reg1, nsl1, ol1)
    reg2, nsl2, ol2 = c_reg2(), c_nsl2(), c_ol2()
    fsm2 = c_fsm2(reg2, nsl2, ol2)
    cs = [reg1, nsl1, ol1, fsm1, reg2, nsl2, ol2, fsm2]
    top = build_top({c.name: c for c in cs}, test)
    return cs + [top]


if __name__ == '__main__':
    # Reconstruye el circuito:   python barrera.py [salida.circ]
    out = sys.argv[1] if len(sys.argv) > 1 else 'barrera_codigo.circ'
    write_project(out, build_all(), 'top')
    print('Circuito escrito en', out)
