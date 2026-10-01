# -*- coding: utf-8 -*-
"""Mini-libreria para generar archivos .circ de Logisim-evolution 5.x.

Geometria de pines tomada del codigo fuente de Logisim-evolution
(AbstractGate, AbstractFlipFlop, NotGate, Pin, ...).
"""
from router import Router, DIRS, OPP
import xml.etree.ElementTree as ET

DIRS = {'E': (10, 0), 'W': (-10, 0), 'N': (0, -10), 'S': (0, 10)}
OPP = {'E': 'W', 'W': 'E', 'N': 'S', 'S': 'N'}


class Ref:
    """Punto de conexion de un componente. d = lado por donde sale el cable."""
    def __init__(self, x, y, d, kind=None):
        self.x, self.y, self.d = x, y, d
        self.kind = kind          # 'out' (maneja la red), 'in' (recibe), 'aux' o None

    @property
    def pt(self):
        return (self.x, self.y)

    @property
    def stub(self):
        dx, dy = DIRS[self.d]
        return (self.x + dx, self.y + dy)


def gate_dy(n, size=50):
    """Desplazamientos verticales de las entradas (AbstractGate.getInputOffset)."""
    if n <= 3:
        if size < 40:
            sk, sd, sl = -5, 10, 10
        elif size < 60 or n <= 2:
            sk, sd, sl = -10, 20, 20
        else:
            sk, sd, sl = -15, 30, 30
    else:
        sk, sd, sl = -5, 10, 10
    out = []
    for i in range(n):
        if n % 2 == 1:
            dy = sk * (n - 1) + sd * i
        else:
            dy = sk * n + sd * i
            if i >= n // 2:
                dy += sl
        out.append(dy)
    return out


class Obj:
    pass


class Circuit:
    def __init__(self, name, note=None):
        self.name = name
        self.comps = []          # (lib, name, (x,y), [(k,v),...])
        self.nets = []           # (netname, [Ref...])
        self.blocks = []         # rectangulos (x1,y1,x2,y2) ocupados
        self.in_pins = []        # (label, x, y)  entradas en orden
        self.out_pins = []
        self.wires = []          # segmentos ((x1,y1),(x2,y2)) ya ruteados
        self.appearance = None
        self.terminals = {}      # pt -> Ref (todos los pines conectables)
        self.extra_wires = []

    # ------------------------------------------------------------ util
    def _add(self, lib, name, loc, attrs=None):
        self.comps.append((lib, name, loc, attrs or []))

    def block(self, x1, y1, x2, y2):
        self.blocks.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))

    def term(self, x, y, d, kind=None):
        r = Ref(x, y, d, kind)
        self.terminals[(x, y)] = r
        return r

    # ------------------------------------------------- componentes I/O
    def pin_in(self, label, x, y):
        """Pin de entrada. (x,y) = punto de conexion (lado derecho del pin)."""
        self._add('0', 'Pin', (x, y), [('appearance', 'classic'), ('label', label)])
        self.block(x - 20, y - 10, x, y + 10)
        self.in_pins.append((label, x, y))
        o = Obj()
        o.o = self.term(x, y, 'E', 'out')
        return o

    def pin_out(self, label, x, y):
        """Pin de salida. (x,y) = punto de conexion (lado izquierdo del pin)."""
        self._add('0', 'Pin', (x, y),
                  [('appearance', 'classic'), ('facing', 'west'), ('label', label),
                   ('type', 'output')])
        self.block(x, y - 10, x + 20, y + 10)
        self.out_pins.append((label, x, y))
        o = Obj()
        o.i = self.term(x, y, 'W', 'in')
        return o

    def clock(self, label, x, y):
        self._add('0', 'Clock', (x, y), [('appearance', 'classic'), ('label', label)])
        self.block(x - 20, y - 10, x, y + 10)
        o = Obj()
        o.o = self.term(x, y, 'E', 'out')
        return o

    def button(self, label, x, y):
        """Boton pulsador (Button de Logisim); (x,y) = salida, cuerpo a la izquierda."""
        self._add('5', 'Button', (x, y), [('label', label)])
        self.block(x - 20, y - 10, x, y + 10)
        o = Obj()
        o.o = self.term(x, y, 'E', 'out')
        return o

    def led(self, label, x, y, color=None):
        attrs = [('facing', 'west'), ('label', label), ('labelloc', 'east')]
        if color:
            attrs.append(('color', color))
        self._add('5', 'LED', (x, y), attrs)
        self.block(x, y - 10, x + 20, y + 10)
        o = Obj()
        o.i = self.term(x, y, 'W', 'in')
        return o

    def text(self, x, y, s, size=12, bold=False, align='left', mono=False):
        """Texto anclado por arriba-izquierda (valign=top)."""
        fam = 'Monospaced' if mono else 'SansSerif'
        st = 'bold' if bold else 'plain'
        self._add('8', 'Text', (x, y),
                  [('font', '%s %s %d' % (fam, st, size)), ('halign', align),
                   ('text', s), ('valign', 'top')])
        lines = s.split(chr(10))
        w = int(max(len(l) for l in lines) * size * 0.62)
        h = int(len(lines) * (size + 4))
        if align == 'left':
            self.block(x, y, x + w, y + h)
        elif align == 'center':
            self.block(x - w // 2, y, x + w // 2, y + h)

    # ----------------------------------------------------- compuertas
    def gate(self, kind, x, y, n=2, label=None, size=50):
        """kind: AND OR NAND NOR XOR.  (x,y) = salida."""
        names = {'AND': 'AND Gate', 'OR': 'OR Gate', 'NAND': 'NAND Gate',
                 'NOR': 'NOR Gate', 'XOR': 'XOR Gate'}
        attrs = [('inputs', str(n)), ('size', str(size))]
        if label:
            attrs.append(('label', label))
        self._add('1', names[kind], (x, y), attrs)
        w = size + (10 if kind in ('NAND', 'NOR', 'XOR') else 0)
        dys = gate_dy(n, size)
        half = max(max(abs(d) for d in dys), size // 2)
        half = 10 * ((half + 9) // 10)
        self.block(x - w, y - half, x, y + half)
        g = Obj()
        g.o = self.term(x, y, 'E', 'out')
        g.i = [self.term(x - w, y + dy, 'W', 'in') for dy in dys]
        return g

    def not_(self, x, y, label=None):
        attrs = [('size', '30')]
        if label:
            attrs.append(('label', label))
        self._add('1', 'NOT Gate', (x, y), attrs)
        self.block(x - 30, y - 10, x, y + 10)
        g = Obj()
        g.o = self.term(x, y, 'E', 'out')
        g.i = [self.term(x - 30, y, 'W', 'in')]
        return g

    # ------------------------------------------------------- tuneles
    def tunnel(self, x, y, label, d):
        """d = lado por el que llega el cable (punta del tunel)."""
        fac = {'E': 'east', 'W': 'west', 'N': 'north', 'S': 'south'}[d]
        self._add('0', 'Tunnel', (x, y), [('facing', fac), ('label', label),
                                          ('labelfont', 'SansSerif plain 11')])
        bw = 7 * len(label) + 18
        if d == 'W':
            self.block(x, y, x + bw, y)
        elif d == 'E':
            self.block(x - bw, y, x, y)
        elif d == 'S':
            self.block(x - bw // 2, y - 20, x + bw // 2, y)
        else:
            self.block(x - bw // 2, y, x + bw // 2, y + 20)
        self.term(x, y, d)
        return Ref(x, y, d)

    def tun(self, name, *refs, dx=30):
        """Conecta cada ref con un tunel llamado `name` (cable corto)."""
        flat = []
        for r in refs:
            if isinstance(r, (list, tuple)):
                flat.extend(r)
            else:
                flat.append(r)
        for k, r in enumerate(flat):
            vx, vy = DIRS[r.d]
            tx, ty = r.x + vx * dx // 10, r.y + vy * dx // 10
            t = self.tunnel(tx, ty, name, OPP[r.d])
            self.nets.append(('%s.t%d' % (name, k), [r, t], None))
        return None

    # ------------------------------------------------------ flip-flop
    def dff(self, x, y, label=None):
        attrs = [('appearance', 'logisim_evolution')]
        if label:
            attrs.append(('label', label))
        self._add('4', 'D Flip-Flop', (x, y), attrs)
        self.block(x - 10, y, x + 50, y + 60)
        f = Obj()
        f.D = self.term(x - 10, y + 10, 'W', 'in')
        f.CLK = self.term(x - 10, y + 50, 'W', 'in')
        f.Q = self.term(x + 50, y + 10, 'E', 'out')
        f.QN = self.term(x + 50, y + 50, 'E', 'out')
        f.R = self.term(x + 20, y + 60, 'S', 'aux')
        f.S = self.term(x + 20, y, 'N', 'aux')
        # los pines R/S sin usar quedan bloqueados por el rectangulo
        f.x, f.y = x, y
        return f

    # ------------------------------------------------ subcircuitos
    def sub(self, circ, x, y):
        """Instancia de otro circuito con apariencia personalizada.
        (x,y) = esquina superior izquierda de la caja."""
        ap = circ.appearance
        self._add(None, circ.name, (x, y), [])
        self.block(x, y, x + ap['w'], y + ap['h'])
        s = Obj()
        s.box = (x, y, x + ap['w'], y + ap['h'])
        s.p = {}
        for k, (lab, dy) in enumerate(ap['ins']):
            s.p[lab] = self.term(x, y + dy, 'W', 'in')
        for k, (lab, dy) in enumerate(ap['outs']):
            s.p[lab] = self.term(x + ap['w'], y + dy, 'E', 'out')
        return s

    # --------------------------------------------------------- redes
    def net(self, name, *refs):
        flat = []
        for r in refs:
            if isinstance(r, (list, tuple)):
                flat.extend(r)
            else:
                flat.append(r)
        self.nets.append((name, self._order(name, flat), None))

    def _order(self, name, refs):
        outs = [r for r in refs if r.kind == 'out']
        if len(outs) > 1:
            raise RuntimeError('red %s: hay %d salidas conectadas entre si (cortocircuito)' % (name, len(outs)))
        return outs + [r for r in refs if r.kind != 'out']

    def wire_net(self, name, refs, polylines):
        """Red con cableado dibujado a mano (lista de polilineas)."""
        self.nets.append((name, self._order(name, list(refs)), polylines))

    def check_complete(self):
        """Devuelve lista de terminales de entrada sin cablear (serian entradas
        flotantes = cables azules) y redes sin fuente."""
        used = set()
        problems = []
        for name, refs, poly in self.nets:
            if len(refs) >= 2:
                for r in refs:
                    used.add(r.pt)
                if not any(r.kind == 'out' for r in refs) and not any(r.kind is None for r in refs):
                    problems.append('red %s sin fuente' % name)
        for pt, r in self.terminals.items():
            if r.kind == 'in' and pt not in used:
                problems.append('entrada sin conectar en %s' % (pt,))
        return problems

    # ------------------------------------------------- apariencia
    def make_appearance(self, in_labels=None, out_labels=None, title=None):
        """Caja rectangular con pines cada 20 px (entradas izq, salidas der)."""
        ins = in_labels if in_labels is not None else [l for l, _, _ in self.in_pins]
        outs = out_labels if out_labels is not None else [l for l, _, _ in self.out_pins]
        title = title or self.name
        maxin = max([len(l) for l in ins] + [1])
        maxout = max([len(l) for l in outs] + [1])
        w = max(100, 10 * ((int((maxin + maxout) * 7.2 + 30) + 9) // 10),
                10 * ((int(len(title) * 7.2 + 30) + 9) // 10))
        n = max(len(ins), len(outs))
        h = 20 * n + 20
        self.appearance = {
            'w': w, 'h': h, 'title': title,
            'ins': [(l, 20 + 20 * k) for k, l in enumerate(ins)],
            'outs': [(l, 20 + 20 * k) for k, l in enumerate(outs)],
        }

    # ---------------------------------------------------- ruteo
    def route(self, margin=120, verbose=False, strict=True):
        R = Router(self, margin)
        R.run()
        R.validate()
        self.wires = R.segments()
        if strict:
            pr = self.check_complete()
            if pr:
                raise RuntimeError('circuito %s: ' % self.name + '; '.join(pr))

    # ------------------------------------------------------ XML
    def to_xml(self, parent):
        ce = ET.SubElement(parent, 'circuit', {'name': self.name})
        ET.SubElement(ce, 'a', {'name': 'appearance', 'val': 'custom'})
        ET.SubElement(ce, 'a', {'name': 'circuit', 'val': self.name})
        ET.SubElement(ce, 'a', {'name': 'circuitnamedboxfixedsize', 'val': 'true'})
        ET.SubElement(ce, 'a', {'name': 'simulationFrequency', 'val': '1.0'})
        ap = self.appearance
        if ap is not None:
            ae = ET.SubElement(ce, 'appear')
            X0, Y0 = 50, 50
            ET.SubElement(ae, 'rect', {'fill': 'none', 'height': str(ap['h']),
                                       'stroke': '#000000', 'stroke-width': '2',
                                       'width': str(ap['w']), 'x': str(X0), 'y': str(Y0)})
            t = ET.SubElement(ae, 'text', {
                'dominant-baseline': 'central', 'fill': '#000000',
                'font-family': 'SansSerif', 'font-size': '12', 'font-weight': 'bold',
                'text-anchor': 'middle', 'x': str(X0 + ap['w'] // 2),
                'y': str(Y0 + ap['h'] // 2)})
            t.text = ap['title']
            pinpos = {}
            for (lab, x, y) in self.in_pins:
                pinpos[('in', lab)] = (x, y)
            for (lab, x, y) in self.out_pins:
                pinpos[('out', lab)] = (x, y)
            for lab, dy in ap['ins']:
                tt = ET.SubElement(ae, 'text', {
                    'dominant-baseline': 'central', 'fill': '#404040',
                    'font-family': 'SansSerif', 'font-size': '10',
                    'text-anchor': 'start', 'x': str(X0 + 6), 'y': str(Y0 + dy)})
                tt.text = lab
            for lab, dy in ap['outs']:
                tt = ET.SubElement(ae, 'text', {
                    'dominant-baseline': 'central', 'fill': '#404040',
                    'font-family': 'SansSerif', 'font-size': '10',
                    'text-anchor': 'end', 'x': str(X0 + ap['w'] - 6), 'y': str(Y0 + dy)})
                tt.text = lab
            for lab, dy in ap['ins']:
                x, y = pinpos[('in', lab)]
                ET.SubElement(ae, 'circ-port', {'dir': 'in', 'pin': '%d,%d' % (x, y),
                                                'x': str(X0), 'y': str(Y0 + dy)})
            for lab, dy in ap['outs']:
                x, y = pinpos[('out', lab)]
                ET.SubElement(ae, 'circ-port', {'dir': 'out', 'pin': '%d,%d' % (x, y),
                                                'x': str(X0 + ap['w']), 'y': str(Y0 + dy)})
            ET.SubElement(ae, 'circ-anchor', {'facing': 'east', 'x': str(X0), 'y': str(Y0)})
        for lib, name, loc, attrs in self.comps:
            d = {'loc': '(%d,%d)' % loc, 'name': name}
            if lib is not None:
                d['lib'] = lib
            ce_c = ET.SubElement(ce, 'comp', d)
            for k, v in attrs:
                ET.SubElement(ce_c, 'a', {'name': k, 'val': v})
        for (p, q) in self.wires:
            ET.SubElement(ce, 'wire', {'from': '(%d,%d)' % p, 'to': '(%d,%d)' % q})
        return ce


def write_project(path, circuits, main):
    root = ET.Element('project', {'source': '5.0.0', 'version': '1.0'})
    libs = [('#Wiring', '0'), ('#Gates', '1'), ('#Plexers', '2'), ('#Arithmetic', '3'),
            ('#Memory', '4'), ('#I/O', '5'), ('#TTL', '6'), ('#TCL', '7'),
            ('#Base', '8'), ('#BFH-Praktika', '9'), ('#Input/Output-Extra', '10'),
            ('#Soc', '11')]
    for d, n in libs:
        ET.SubElement(root, 'lib', {'desc': d, 'name': n})
    ET.SubElement(root, 'main', {'name': main})
    opts = ET.SubElement(root, 'options')
    ET.SubElement(opts, 'a', {'name': 'gateUndefined', 'val': 'ignore'})
    ET.SubElement(opts, 'a', {'name': 'simlimit', 'val': '1000'})
    ET.SubElement(opts, 'a', {'name': 'simrand', 'val': '0'})
    maps = ET.SubElement(root, 'mappings')
    for m in ('Button2', 'Button3', 'Ctrl Button1'):
        ET.SubElement(maps, 'tool', {'lib': '8', 'map': m, 'name': 'Menu Tool'})
    tb = ET.SubElement(root, 'toolbar')
    for lib, nm in (('8', 'Poke Tool'), ('8', 'Edit Tool'), ('8', 'Wiring Tool'), ('8', 'Text Tool')):
        ET.SubElement(tb, 'tool', {'lib': lib, 'name': nm})
    ET.SubElement(tb, 'sep')
    ET.SubElement(tb, 'tool', {'lib': '0', 'name': 'Pin'})
    t = ET.SubElement(tb, 'tool', {'lib': '0', 'name': 'Pin'})
    ET.SubElement(t, 'a', {'name': 'facing', 'val': 'west'})
    ET.SubElement(t, 'a', {'name': 'type', 'val': 'output'})
    ET.SubElement(tb, 'sep')
    for nm in ('NOT Gate', 'AND Gate', 'OR Gate', 'XOR Gate', 'NAND Gate', 'NOR Gate'):
        ET.SubElement(tb, 'tool', {'lib': '1', 'name': nm})
    ET.SubElement(tb, 'sep')
    ET.SubElement(tb, 'tool', {'lib': '4', 'name': 'D Flip-Flop'})
    ET.SubElement(tb, 'tool', {'lib': '4', 'name': 'Register'})
    for c in circuits:
        c.to_xml(root)
    ET.indent(root, space='  ')
    body = ET.tostring(root, encoding='unicode')
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + body + '\n')
