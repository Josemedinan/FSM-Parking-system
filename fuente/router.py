# -*- coding: utf-8 -*-
"""Enrutador ortogonal sobre rejilla de 10 px.

Reglas (para que Logisim no una redes por accidente):
  * dos redes distintas nunca comparten una arista
  * una red ajena solo puede cruzar en linea recta y perpendicular,
    en un vertice donde ninguna de las dos termina o dobla
  * un pin ajeno nunca se toca
"""
import heapq

DIRS = {'E': (10, 0), 'W': (-10, 0), 'N': (0, -10), 'S': (0, 10)}
OPP = {'E': 'W', 'W': 'E', 'N': 'S', 'S': 'N'}


def _dir(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    if dx > 0:
        return 'E'
    if dx < 0:
        return 'W'
    return 'S' if dy > 0 else 'N'


class Router:
    BEND = 6
    CROSS = 5

    def __init__(self, circ, margin=120):
        self.c = circ
        pts = []
        for b in circ.blocks:
            pts += [(b[0], b[1]), (b[2], b[3])]
        pts += list(circ.terminals)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        self.xmin, self.xmax = min(xs) - margin, max(xs) + margin
        self.ymin, self.ymax = min(ys) - margin, max(ys) + margin
        self.blocked = set()
        for (x1, y1, x2, y2) in circ.blocks:
            for x in range(x1, x2 + 1, 10):
                for y in range(y1, y2 + 1, 10):
                    self.blocked.add((x, y))
        self.pinpts = {}
        self.edges = {}
        self.vuse = {}
        self.tree = {}

    # --------------------------------------------------------------
    def _addedge(self, ni, p, q):
        self.edges[frozenset((p, q))] = ni
        for a, b in ((p, q), (q, p)):
            self.vuse.setdefault(a, {}).setdefault(ni, set()).add(_dir(a, b))
        self.tree.setdefault(ni, set()).update([p, q])

    def _others(self, p, ni):
        u = self.vuse.get(p)
        if not u:
            return []
        return [(m, ds) for m, ds in u.items() if m != ni]

    def run(self):
        c = self.c
        order = []
        for i, (name, refs, poly) in enumerate(c.nets):
            if len(refs) < 2:
                continue
            xs = [r.x for r in refs]
            ys = [r.y for r in refs]
            hp = (max(xs) - min(xs)) + (max(ys) - min(ys))
            order.append((len(refs) > 2, hp, i))
            for r in refs:
                if r.pt in self.pinpts and self.pinpts[r.pt] != i:
                    raise RuntimeError('pin %s en dos redes: %s y %s' % (
                        r.pt, c.nets[self.pinpts[r.pt]][0], name))
                self.pinpts[r.pt] = i
        for p in self.pinpts:
            self.blocked.discard(p)
        # reservar el tramo pin->stub de TODOS los terminales
        self.conn = {}
        for i, (name, refs, poly) in enumerate(c.nets):
            if poly is None:
                continue
            for pl in poly:
                for a, b in zip(pl, pl[1:]):
                    dx = (b[0] > a[0]) - (b[0] < a[0])
                    dy = (b[1] > a[1]) - (b[1] < a[1])
                    cur = a
                    while cur != b:
                        nx = (cur[0] + 10 * dx, cur[1] + 10 * dy)
                        e = self.edges.get(frozenset((cur, nx)))
                        if e is not None and e != i:
                            raise RuntimeError('cable manual %s choca con %s' % (name, c.nets[e][0]))
                        self._addedge(i, cur, nx)
                        cur = nx
        order = [o for o in order if c.nets[o[2]][2] is None]
        for _, _, i in order:
            for r in c.nets[i][1]:
                if not self._stub_ok(r.stub, i):
                    raise RuntimeError('red %s: stub bloqueado en %s (pin %s)' % (
                        c.nets[i][0], r.stub, r.pt))
                self._addedge(i, r.pt, r.stub)
        order.sort()
        for _, _, i in order:
            self.route_net(i)

    def validate(self):
        """Comprueba que no haya cortos, T accidentales ni cables sobre cuerpos."""
        c = self.c
        for p, u in self.vuse.items():
            if len(u) > 1:
                if p in self.pinpts:
                    raise RuntimeError('cable de otra red toca el pin %s' % (p,))
                if len(u) > 2:
                    raise RuntimeError('tres redes en el punto %s' % (p,))
                sets = list(u.values())
                if not ((sets[0] == {'E', 'W'} and sets[1] == {'N', 'S'}) or
                        (sets[0] == {'N', 'S'} and sets[1] == {'E', 'W'})):
                    names = [c.nets[m][0] for m in u]
                    raise RuntimeError('redes %s se tocan mal en %s' % (names, p))
            if p in self.blocked and p not in self.pinpts:
                raise RuntimeError('cable pasa por un cuerpo/texto en %s (red %s)' % (
                    p, [c.nets[m][0] for m in u]))
        # conectividad de cada red
        for ni, (name, refs, poly) in enumerate(c.nets):
            if len(refs) < 2:
                continue
            adj = {}
            for e, n in self.edges.items():
                if n == ni:
                    a, b = tuple(e)
                    adj.setdefault(a, set()).add(b)
                    adj.setdefault(b, set()).add(a)
            start = refs[0].pt
            if start not in adj:
                raise RuntimeError('red %s: el pin %s no tiene cable' % (name, start))
            seen = {start}
            stack = [start]
            while stack:
                q = stack.pop()
                for z in adj.get(q, ()):
                    if z not in seen:
                        seen.add(z)
                        stack.append(z)
            for r in refs:
                if r.pt not in seen:
                    raise RuntimeError('red %s: el pin %s queda desconectado' % (name, r.pt))

    def _stub_ok(self, s, ni):
        if s in self.blocked:
            return False
        if s in self.pinpts and self.pinpts[s] != ni:
            return False
        return not self._others(s, ni)

    def route_net(self, ni):
        name, refs, _ = self.c.nets[ni]
        drv = refs[0]
        conn = {drv.pt, drv.stub}
        sinks = sorted(refs[1:], key=lambda r: abs(r.x - drv.x) + abs(r.y - drv.y))
        for r in sinks:
            st = r.stub
            if st in conn:
                conn.update([r.pt, st])
                continue
            path = self.astar(ni, st, r.d, conn)
            if path is None:
                raise RuntimeError('red %s: sin ruta hacia %s' % (name, r.pt))
            conn.update([r.pt, st])
            for a, b in zip(path, path[1:]):
                dx = (b[0] > a[0]) - (b[0] < a[0])
                dy = (b[1] > a[1]) - (b[1] < a[1])
                cur = a
                while cur != b:
                    nx = (cur[0] + 10 * dx, cur[1] + 10 * dy)
                    self._addedge(ni, cur, nx)
                    conn.add(nx)
                    cur = nx

    # --------------------------------------------------------------
    def _move(self, ni, p, d):
        dx, dy = DIRS[d]
        cur = p
        cost = 0
        while True:
            nxt = (cur[0] + dx, cur[1] + dy)
            if not (self.xmin <= nxt[0] <= self.xmax and self.ymin <= nxt[1] <= self.ymax):
                return None
            en = self.edges.get(frozenset((cur, nxt)))
            if en is not None and en != ni:
                return None
            if nxt in self.blocked:
                return None
            if nxt in self.pinpts and self.pinpts[nxt] != ni:
                return None
            others = self._others(nxt, ni)
            cost += 0 if en == ni else 1
            if not others:
                return nxt, cost
            axis = 'h' if d in 'EW' else 'v'
            for m, ds in others:
                if axis == 'h' and ds == {'N', 'S'}:
                    continue
                if axis == 'v' and ds == {'E', 'W'}:
                    continue
                return None
            cost += self.CROSS
            cur = nxt

    def astar(self, ni, start, startdir, targets):
        if not targets:
            return None
        tl = list(targets)

        def h(p):
            return min(abs(p[0] - t[0]) + abs(p[1] - t[1]) for t in tl) // 10

        dist = {(start, startdir): 0}
        prev = {}
        pq = [(h(start), 0, start, startdir)]
        while pq:
            f, g, p, d = heapq.heappop(pq)
            if dist.get((p, d), 1e18) < g:
                continue
            if p in targets:
                path = [p]
                st = (p, d)
                while st in prev:
                    st = prev[st]
                    path.append(st[0])
                path.reverse()
                return path
            for nd in 'ENSW':
                if nd == OPP[d]:
                    continue
                res = self._move(ni, p, nd)
                if res is None:
                    continue
                land, cost = res
                ng = g + cost + (self.BEND if nd != d else 0)
                key = (land, nd)
                if ng < dist.get(key, 1e18):
                    dist[key] = ng
                    prev[key] = (p, d)
                    heapq.heappush(pq, (ng + h(land), ng, land, nd))
        return None

    # --------------------------------------------------------------
    def segments(self):
        segs = []
        bynet = {}
        for e, ni in self.edges.items():
            bynet.setdefault(ni, []).append(tuple(e))
        term = set(self.pinpts)
        for ni, es in bynet.items():
            adj = {}
            for a, b in es:
                adj.setdefault(a, set()).add(b)
                adj.setdefault(b, set()).add(a)

            def keypoint(p):
                nb = adj[p]
                if len(nb) != 2 or p in term:
                    return True
                a, b = tuple(nb)
                return not ((a[0] == p[0] == b[0]) or (a[1] == p[1] == b[1]))
            seen = set()
            for p in adj:
                if not keypoint(p):
                    continue
                for q in adj[p]:
                    if frozenset((p, q)) in seen:
                        continue
                    path = [p, q]
                    seen.add(frozenset((p, q)))
                    cur, prv = q, p
                    while not keypoint(cur):
                        nx = [z for z in adj[cur] if z != prv][0]
                        seen.add(frozenset((cur, nx)))
                        path.append(nx)
                        prv, cur = cur, nx
                    segs.append((path[0], path[-1]))
        return segs
