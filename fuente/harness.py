# -*- coding: utf-8 -*-
"""Utilidades de verificacion con Logisim-evolution REAL (modo sin ventana)."""
import re
import sys
sys.path.insert(0, '.')
from lg import write_project
from lgrun import run


def write_vec(path, header, rows, seq=False):
    with open(path, 'w') as f:
        if seq:
            f.write('<set> <seq> ' + ' '.join(header) + '\n')
            for i, r in enumerate(rows):
                f.write('1 %d ' % (i + 1) + ' '.join(str(int(v)) for v in r) + '\n')
        else:
            f.write(' '.join(header) + '\n')
            for r in rows:
                f.write(' '.join(str(int(v)) for v in r) + '\n')


def check(circ_file, circuit, header, rows, seq=False, tag=None, verbose=True):
    """Corre un vector de prueba contra `circuit` del archivo .circ.

    header : nombres de pines (entradas y salidas) tal como estan rotulados.
    rows   : filas de valores 0/1 en el mismo orden que header.
    seq=False: circuito combinacional; cada fila se evalua desde cero.
    seq=True : circuito secuencial; el estado se conserva entre filas. Si el
               circuito tiene un pin CLK (entrada), pongalo como columna y
               genere DOS filas por ciclo (CLK=0 y CLK=1) con las mismas
               entradas; si el circuito contiene un componente Clock, cada
               fila alterna el reloj sola (medio periodo por fila; el flanco
               de subida ocurre ANTES de aplicar las entradas de las filas
               pares 2,4,6...).
    Devuelve True si todas las filas coinciden."""
    tag = tag or circuit
    vec = 'vec_%s.txt' % tag
    write_vec(vec, header, rows, seq)
    rc, out, err = run(['-w', circuit, vec, circ_file])
    m = re.search(r'Correctos: (\d+), Fallidos: (\d+)', out)
    if not m:
        if verbose:
            print('ERROR al correr Logisim:', out[-800:], err[-400:])
        return False
    ok = int(m.group(2)) == 0
    if verbose:
        print(('PASS ' if ok else 'FAIL ') + '%s: %s correctos, %s fallidos' % (
            circuit, m.group(1), m.group(2)))
        if not ok:
            print(out[-1500:])
    return ok


def load_ok(circ_file):
    """Carga el .circ y lo regraba con Logisim (detecta archivos corruptos)."""
    rc, out, err = run(['-n', circ_file, circ_file + '.resaved'])
    return rc == 0 and not err.strip()
