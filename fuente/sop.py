# -*- coding: utf-8 -*-
"""Constructor de logica combinacional en forma suma-de-productos (SOP),
dibujada como en la presentacion (Harris & Harris, cap. 3):

    entradas a la izquierda -> cada variable con su riel vertical y su riel
    complementado (compuerta NOT) -> una compuerta AND por termino producto ->
    una compuerta OR por salida -> pines de salida a la derecha.

TODO el cableado es explicito (sin tuneles, sin autorruteo): cada cable esta
calculado, y Circuit.route() lo valida (sin cortos, sin T accidentales).

Uso:
    c = sop_circuit(
        name='M1_output_logic',
        title='FSM 1 (Moore) - Output logic',
        subtitle='Salidas = f(estado)',
        inputs=['Q2', 'Q1', 'Q0'],
        outputs=[('MIC', ["Q2' Q1' Q0", "Q2' Q1 Q0'"]),
                 ('NPU', ["Q2' Q1 Q0"])],
        notes='MIC = Q2\'(Q1 xor Q0)   NPU = Q2\'Q1Q0')

  * una salida = (nombre, [termino, ...]); un termino = string con literales
    separados por espacio ("A B' C") o lista ['A', "B'", 'C'].
  * literal negado: A'   (tambien ~A o !A)
  * un termino de 1 literal se cablea directo a la OR (sin AND); si la salida
    tiene un unico termino no lleva OR.
"""
from lg import *

X_PIN = 100
Y0 = 150
ROW = 40


def _lit(l):
    l = l.strip()
    if l.endswith("'"):
        return l[:-1], True
    if l[0] in '~!':
        return l[1:], True
    return l, False


def _terms(ts):
    out = []
    for t in ts:
        lits = t.split() if isinstance(t, str) else list(t)
        out.append([_lit(l) for l in lits])
    return out


def sop_circuit(name, title, subtitle, inputs, outputs, notes=None, box_title=None,
                and_size=50):
    c = Circuit(name)
    c.text(60, 50, title, size=16, bold=True)
    if subtitle:
        c.text(60, 76, subtitle, size=12)
    outs = [(n, _terms(ts)) for n, ts in outputs]
    used = {}                                   # (var, neg) -> True
    for _, ts in outs:
        for t in ts:
            for v, neg in t:
                if v not in inputs:
                    raise ValueError('%s: variable %s no declarada' % (name, v))
                used[(v, neg)] = True
    for v in inputs:
        if (v, False) not in used and (v, True) not in used:
            raise ValueError('%s: la entrada %s no se usa en ningun termino' % (name, v))
    need_comp = {v: (v, True) in used for v in inputs}
    n_in = len(inputs)

    # ---------------------------------------------------- filas de las entradas
    yv = {v: Y0 + ROW * i for i, v in enumerate(inputs)}
    xt, xc = {}, {}
    x = 230
    for v in inputs:
        xt[v] = x
        if need_comp[v]:
            xc[v] = x + 50
            x += 80
        else:
            x += 30
    x_last = x

    # ------------------------------------------------ filas de las compuertas
    Y_A = Y0 + ROW * n_in + 50
    term_rows = []                               # [(out_idx, term_idx, y, n)]
    y = Y_A
    and_terms = []                               # terminos con >=2 literales
    direct = {}                                  # literal -> lista de (out_idx)
    for oi, (oname, ts) in enumerate(outs):
        for ti, t in enumerate(ts):
            if len(t) >= 2:
                and_terms.append((oi, ti, y))
                y += 80
            else:
                direct.setdefault(t[0], []).append(oi)
    y_and_end = y
    y_d = {}
    yy = y_and_end + 20
    for lit in direct:
        y_d[lit] = yy
        yy += 30
    y_bottom = max([y_and_end] + list(y_d.values()) + [Y_A])

    x_and = x_last + 60 + and_size            # salida de las AND
    x_pin_and = x_and - and_size
    n_tracks = len(and_terms) + len(direct)
    x_trk0 = x_and + 30
    x_or_in = x_trk0 + 10 * n_tracks + 40
    x_or_out = x_or_in + and_size
    x_out_pin = x_or_out + 40

    # ------------------------------------------------ compuertas AND
    ands = {}                                    # (oi,ti) -> gate
    lit_taps = {}                                # (var,neg) -> [(y_pin)]
    for (oi, ti, y) in and_terms:
        t = outs[oi][1][ti]
        g = c.gate('AND', x_and, y, len(t), size=and_size)
        ands[(oi, ti)] = g
        for k, (v, neg) in enumerate(t):
            lit_taps.setdefault((v, neg), []).append((g.i[k], g.i[k].y))
    for lit, ois in direct.items():
        lit_taps.setdefault(lit, []).append((None, y_d[lit]))

    # ------------------------------------------------ pines y NOT
    pins, nots = {}, {}
    for v in inputs:
        pins[v] = c.pin_in(v, X_PIN, yv[v])
        if need_comp[v]:
            nots[v] = c.not_(xt[v] + 40, yv[v])
    # etiquetas de los rieles
    for v in inputs:
        c.text(xt[v] + 4, yv[v] - 22, v, size=9)
        if need_comp[v]:
            c.text(xc[v] + 4, yv[v] - 22, v + "'", size=9)

    # ------------------------------------------------ redes de las variables
    for v in inputs:
        refs = [pins[v].o]
        polys = [[(X_PIN, yv[v]), (xt[v], yv[v])]]
        taps_t = lit_taps.get((v, False), [])
        taps_c = lit_taps.get((v, True), [])
        if need_comp[v]:
            refs.append(nots[v].i[0])
            polys.append([(xt[v], yv[v]), (xt[v] + 10, yv[v])])
        ys_t = [yy_ for _, yy_ in taps_t]
        if ys_t:
            polys.append([(xt[v], yv[v]), (xt[v], max(ys_t))])
            for ref, yy_ in taps_t:
                polys.append([(xt[v], yy_), (x_pin_and, yy_)] if ref is not None else [(xt[v], yy_)])
                if ref is not None:
                    refs.append(ref)
        c.wire_net(v, refs, polys)
        if need_comp[v]:
            refs = [nots[v].o]
            polys = [[(xt[v] + 40, yv[v]), (xc[v], yv[v])]]
            ys_c = [yy_ for _, yy_ in taps_c]
            polys.append([(xc[v], yv[v]), (xc[v], max(ys_c))])
            for ref, yy_ in taps_c:
                if ref is not None:
                    polys.append([(xc[v], yy_), (x_pin_and, yy_)])
                    refs.append(ref)
                else:
                    polys.append([(xc[v], yy_)])
            c.wire_net(v + "'", refs, polys)

    # ------------------------------------------------ OR de cada salida
    used_rows = set([y for _, _, y in and_terms] + list(y_d.values()))
    or_ranges = []
    track_x = {}
    tk = 0
    for (oi, ti, y) in and_terms:
        track_x[(oi, ti)] = x_trk0 + 10 * tk
        tk += 1
    for lit in direct:
        track_x[lit] = x_trk0 + 10 * tk
        tk += 1

    out_pins = []
    direct_paths = {lit: [] for lit in direct}
    # reservar las filas de las salidas de un solo termino (cable recto que
    # cruza la zona de las OR)
    for oi, (oname, ts) in enumerate(outs):
        if len(ts) == 1:
            t = ts[0]
            yrow = ands[(oi, 0)].o.y if len(t) >= 2 else y_d[t[0]]
            or_ranges.append((yrow - 10, yrow + 10))
    for oi, (oname, ts) in enumerate(outs):
        srcs = []                                   # (fila_fuente, clave, tipo)
        for ti, t in enumerate(ts):
            if len(t) >= 2:
                srcs.append((ands[(oi, ti)].o.y, (oi, ti), 'and'))
            else:
                srcs.append((y_d[t[0]], t[0], 'dir'))
        srcs.sort(key=lambda s: s[0])
        n = len(srcs)
        if n == 1:
            src = srcs[0]
            yrow = src[0]
            pin = c.pin_out(oname, x_out_pin, yrow)
            if src[2] == 'and':
                g = ands[src[1]]
                c.wire_net(oname, [g.o, pin.i], [[(x_and, yrow), (x_out_pin, yrow)]])
            else:
                lit = src[1]
                direct_paths[lit].append(('pin', pin, yrow))
                c.wire_net('__dummy%d' % oi, [], [])
            out_pins.append(oname)
            continue
        dys = gate_dy(n, and_size)
        half = 10 * ((max(max(abs(d) for d in dys), and_size // 2) + 9) // 10)
        ymean = sum(s[0] for s in srcs) / n
        base = int(round(ymean / 10.0)) * 10
        shift = 0
        for cand in [0, 10, -10, 20, -20, 30, -30, 40, -40, 50, -50, 60, -60]:
            yo = base + cand
            rows = [yo + d for d in dys]
            if any(r in used_rows for r in rows):
                continue
            if any(not (yo + half < a or yo - half > b) for (a, b) in or_ranges):
                continue
            break
        else:
            raise RuntimeError('%s: no encontre lugar para la OR de %s' % (name, oname))
        used_rows.update(rows)
        or_ranges.append((yo - half - 10, yo + half + 10))
        og = c.gate('OR', x_or_out, yo, n, size=and_size)
        pin = c.pin_out(oname, x_out_pin, yo)
        c.wire_net(oname + '_or', [og.o, pin.i], [[(x_or_out, yo), (x_out_pin, yo)]])
        for k, (ysrc, key, kind) in enumerate(srcs):
            yq = rows[k]
            if kind == 'and':
                g = ands[key]
                xk = track_x[key]
                c.wire_net('%s_t%d' % (oname, k), [g.o, og.i[k]],
                           [[(x_and, ysrc), (xk, ysrc), (xk, yq), (x_or_in, yq)]])
            else:
                direct_paths[key].append(('or', og.i[k], yq))
        out_pins.append(oname)

    # --- terminos directos (literal solo) -> hacia sus OR / pines
    for lit, targets in direct_paths.items():
        v, neg = lit
        xr = xc[v] if neg else xt[v]
        yd = y_d[lit]
        xk = track_x[lit]
        polys = [[(xr, yd), (xk, yd)]]
        ys = [yd] + [t[2] for t in targets]
        polys.append([(xk, min(ys)), (xk, max(ys))])
        refs = []
        for kind, ref, yq in targets:
            if kind == 'or':
                polys.append([(xk, yq), (x_or_in, yq)])
                refs.append(ref)
            else:
                polys.append([(xk, yq), (x_out_pin, yq)])
                refs.append(ref.i)
        # la red de la variable ya existe (v o v'); sumamos estas ramas a ella
        for i_, (nm, rr, pp) in enumerate(c.nets):
            if nm == (v + "'" if neg else v):
                rr.extend(refs)
                pp.extend(polys)
                break
    c.nets = [n for n in c.nets if not n[0].startswith('__dummy')]

    # ------------------------------------------------ notas al pie
    y_txt = max(list(used_rows) + [y_bottom]) + 80
    if notes:
        c.text(60, y_txt, notes, size=11, mono=True)
    c.route()
    c.make_appearance(in_labels=list(inputs), out_labels=[o[0] for o in outs],
                      title=box_title or name)
    return c
