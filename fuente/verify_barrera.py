# -*- coding: utf-8 -*-
import itertools, random, sys
sys.path.insert(0, '.')
import harness
from lg import write_project
import barrera

F = 'barrera_test.circ'
KEYS = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]      # una tecla a la vez


def m1_next(s, sensor, ok):
    if s == 0:
        return 1 if ok else 0
    if s == 1:
        return 2
    if s == 2:
        return 2 if sensor else 3
    return 2 if sensor else 0


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


def main():
    write_project(F, barrera.build_all(test=True), 'top')
    ok = harness.load_ok(F)
    print('carga ok', ok)
    rows = []
    for s in range(4):
        for se, okk in itertools.product((0, 1), repeat=2):
            n = m1_next(s, se, okk)
            rows.append([se, okk, s >> 1, s & 1, n >> 1, n & 1])
    ok &= harness.check(F, 'M1_next_state_logic', ['SENSOR', 'OK', 'Q1', 'Q0', 'D1', 'D0'], rows)
    rows = [[s >> 1, s & 1] + [int(s == k) for k in range(4)] for s in range(4)]
    ok &= harness.check(F, 'M1_output_logic', ['Q1', 'Q0', 'CERRADA', 'ABRIENDO', 'ABIERTA', 'CERRANDO'], rows)
    rows = []
    for p in range(4):
        for (a, b, c), en, rst in itertools.product(KEYS, (0, 1), (0, 1)):
            n = m2_next(p, en, a, b, c, rst)
            rows.append([a, b, c, en, rst, p >> 1, p & 1, n >> 1, n & 1])
    ok &= harness.check(F, 'M2_next_state_logic', ['A', 'B', 'C', 'EN', 'RST', 'P1', 'P0', 'D1', 'D0'], rows)
    rows = []
    for p in range(4):
        for (a, b, c), en in itertools.product(KEYS, (0, 1)):
            okk, al = m2_out(p, en, a, b, c)
            rows.append([a, b, c, en, p >> 1, p & 1, okk, al, int(p == 1), int(p == 2)])
    ok &= harness.check(F, 'M2_output_logic',
                        ['A', 'B', 'C', 'EN', 'P1', 'P0', 'CODIGO_OK', 'ALARMA', 'PASO_1', 'PASO_2'], rows)
    hdr = ['RST', 'SENSOR', 'A', 'B', 'C', 'CERRADA', 'ABRIENDO', 'ABIERTA', 'CERRANDO', 'Q1', 'Q0',
           'CODIGO_OK', 'ALARMA', 'PASO_1', 'PASO_2']
    for seed, pk, ps in ((1, 0.5, 0.5), (2, 0.7, 0.3), (3, 0.35, 0.7)):
        rnd = random.Random(seed)
        s, p = 0, 0
        cur = dict(RST=0, SENSOR=0, A=0, B=0, C=0)
        rows, vis = [], set()
        # secuencias guiadas: con frecuencia se teclea el codigo correcto A, C, B
        script = []
        for k in range(3000):
            if (k + 1) % 2 == 0:
                st = 0 if cur['RST'] else s
                en = int(st == 0)
                okk, al = m2_out(p, en, cur['A'], cur['B'], cur['C'])
                ns = 0 if cur['RST'] else m1_next(st, cur['SENSOR'], okk)
                np_ = m2_next(p, en, cur['A'], cur['B'], cur['C'], cur['RST'])
                s, p = ns, np_
            if k < 6:
                cur = dict(RST=int(k < 3), SENSOR=0, A=0, B=0, C=0)
            else:
                if rnd.random() < 0.3:
                    key = rnd.random()
                    if not script and rnd.random() < 0.4:
                        script = ['A', 'A', None, 'C', 'C', None, 'B', 'B', None]
                    if script:
                        kk = script.pop(0)
                    else:
                        kk = rnd.choice(['A', 'B', 'C', None]) if rnd.random() < pk else None
                    cur['A'], cur['B'], cur['C'] = int(kk == 'A'), int(kk == 'B'), int(kk == 'C')
                if rnd.random() < 0.15:
                    cur['SENSOR'] = int(rnd.random() < ps)
                cur['RST'] = int(rnd.random() < 0.01)
            if cur['RST']:
                s = 0
            okk, al = m2_out(p, int(s == 0), cur['A'], cur['B'], cur['C'])
            vis.add((s, p, okk, al))
            rows.append([cur['RST'], cur['SENSOR'], cur['A'], cur['B'], cur['C'], int(s == 0), int(s == 1),
                         int(s == 2), int(s == 3), s >> 1, s & 1, okk, al, int(p == 1), int(p == 2)])
        print('cobertura: M1', sorted({v[0] for v in vis}), 'M2 p', sorted({v[1] for v in vis}),
              'OK/ALARMA', sorted({v[2:] for v in vis}))
        ok &= harness.check(F, 'top', hdr, rows, seq=True, tag='top%d' % seed)
    print('TODO OK' if ok else 'HAY FALLAS')


main()
