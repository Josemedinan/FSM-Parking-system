# -*- coding: utf-8 -*-
"""Genera los esquemas (PNG) de ../docs/img:  bloques del sistema y diagramas de estados.

Requiere matplotlib (solo para generar las imagenes):  pip install matplotlib
Uso:   python generar_diagramas.py
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'img')
os.makedirs(OUT, exist_ok=True)

AZUL, NARANJA, VERDE, ROJO = '#2563eb', '#ea580c', '#16a34a', '#dc2626'
GRIS = '#475569'
LED = {'CERRADA': '#ef4444', 'ABRIENDO': '#facc15', 'ABIERTA': '#22c55e', 'CERRANDO': '#fb923c',
       'SIN_TECLAS': '#e2e8f0', 'PASO_1': '#93c5fd', 'PASO_2': '#c4b5fd'}


# ------------------------------------------------------------------ utilidades
def estado(ax, xy, nombre, codigo, extra, color, r=1.0, fs=11):
    ax.add_patch(Circle(xy, r, fc=color, ec='#0f172a', lw=2, zorder=3))
    ax.text(xy[0], xy[1] + 0.28, nombre, ha='center', va='center', fontsize=fs, fontweight='bold', zorder=4)
    ax.text(xy[0], xy[1] - 0.12, codigo, ha='center', va='center', fontsize=9, color='#1e293b', zorder=4)
    if extra:
        ax.text(xy[0], xy[1] - 0.45, extra, ha='center', va='center', fontsize=8, style='italic',
                color='#1e293b', zorder=4)


def flecha(ax, a, b, rad=0.0, color=GRIS, lw=2, ra=1.0, rb=1.0):
    import numpy as np
    a, b = np.array(a, float), np.array(b, float)
    v = b - a
    v = v / np.linalg.norm(v)
    p = FancyArrowPatch(tuple(a + v * ra), tuple(b - v * rb), connectionstyle='arc3,rad=%s' % rad,
                        arrowstyle='-|>', mutation_scale=18, lw=lw, color=color, zorder=2)
    ax.add_patch(p)


def etiqueta(ax, xy, texto, color=GRIS, fs=9.5, ha='center'):
    ax.text(xy[0], xy[1], texto, ha=ha, va='center', fontsize=fs, color=color, fontweight='bold', zorder=5,
            bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=color, lw=1))


def lazo(ax, xy, texto, color=GRIS, theta=90, r=1.0, alto=1.5, dy_txt=0.55):
    """Flecha que sale y vuelve al mismo estado (curva hacia afuera, en la direccion theta)."""
    import math
    from matplotlib.path import Path
    x, y = xy
    def pt(ang, rad):
        return (x + rad * math.cos(math.radians(ang)), y + rad * math.sin(math.radians(ang)))
    p0, p3 = pt(theta - 32, r), pt(theta + 32, r)
    p1, p2 = pt(theta - 30, r + alto), pt(theta + 30, r + alto)
    path = Path([p0, p1, p2, p3], [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
    ax.add_patch(FancyArrowPatch(path=path, arrowstyle='-|>', mutation_scale=18, lw=2, color=color, zorder=2))
    lx, ly = pt(theta, r + alto * 0.75 + dy_txt)
    etiqueta(ax, (lx, ly), texto, color)


def lienzo(w, h, titulo):
    fig, ax = plt.subplots(figsize=(w, h), dpi=130)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(titulo, fontsize=14, fontweight='bold', pad=14)
    return fig, ax


# ------------------------------------------------------------------ FSM 1 (Moore)
def fsm1():
    fig, ax = lienzo(10, 8.5, 'FSM 1 (Moore) - Controlador de la barrera')
    pos = {'CERRADA': (0, 0), 'ABRIENDO': (6.5, 0), 'ABIERTA': (6.5, -5.5), 'CERRANDO': (0, -5.5)}
    cod = {'CERRADA': 'Q1Q0 = 00', 'ABRIENDO': 'Q1Q0 = 01', 'ABIERTA': 'Q1Q0 = 10', 'CERRANDO': 'Q1Q0 = 11'}
    led = {'CERRADA': 'LED rojo', 'ABRIENDO': 'LED amarillo', 'ABIERTA': 'LED verde', 'CERRANDO': 'LED naranja'}
    r = 1.35
    for n, p in pos.items():
        estado(ax, p, n, cod[n], led[n], LED[n], r=r, fs=12)
    ax.annotate('', xy=(-1.35, 0.0), xytext=(-3.0, 0.0), arrowprops=dict(arrowstyle='-|>', lw=2, color=GRIS))
    ax.text(-3.0, 0.45, 'inicio / RST', fontsize=9.5, fontweight='bold', color=GRIS)
    flecha(ax, pos['CERRADA'], pos['ABRIENDO'], ra=r, rb=r, color=VERDE)
    etiqueta(ax, (3.25, 0.75), 'OK = 1\n(código correcto)', VERDE)
    lazo(ax, pos['CERRADA'], 'OK = 0', GRIS, theta=90, r=r)
    flecha(ax, pos['ABRIENDO'], pos['ABIERTA'], ra=r, rb=r)
    etiqueta(ax, (6.5, -2.75), 'siempre\n(1 ciclo)', GRIS)
    lazo(ax, pos['ABIERTA'], 'SENSOR = 1', GRIS, theta=0, r=r, alto=1.6, dy_txt=1.0)
    flecha(ax, pos['ABIERTA'], pos['CERRANDO'], rad=0.28, ra=r, rb=r, color=NARANJA)
    etiqueta(ax, (3.25, -4.0), 'SENSOR = 0', NARANJA)
    flecha(ax, pos['CERRANDO'], pos['ABIERTA'], rad=0.28, ra=r, rb=r, color=ROJO)
    etiqueta(ax, (3.25, -7.0), 'SENSOR = 1\n(seguridad: se reabre)', ROJO)
    flecha(ax, pos['CERRANDO'], pos['CERRADA'], ra=r, rb=r)
    etiqueta(ax, (0, -2.75), 'SENSOR = 0', GRIS)
    ax.set_xlim(-4.3, 10.6)
    ax.set_ylim(-9.4, 4.0)
    ax.text(3.25, -8.7, 'Moore: la salida (LED) depende solo del estado en el que está la máquina.',
            ha='center', fontsize=9.5, color='#334155')
    fig.savefig(os.path.join(OUT, 'fsm1_moore.png'), bbox_inches='tight')
    plt.close(fig)


# ------------------------------------------------------------------ FSM 2 (Mealy)
def fsm2():
    fig, ax = lienzo(13, 7.5, 'FSM 2 (Mealy) - Verificador del código secreto  A → C → B')
    pos = {'SIN_TECLAS': (0, 0), 'PASO_1': (6.5, 0), 'PASO_2': (13, 0)}
    cod = {'SIN_TECLAS': 'P1P0 = 00', 'PASO_1': 'P1P0 = 01', 'PASO_2': 'P1P0 = 10'}
    r = 1.3
    ext = {'SIN_TECLAS': 'nada correcto aún', 'PASO_1': 'la A ya se pulsó', 'PASO_2': 'A y C ya se pulsaron'}
    for n, p in pos.items():
        estado(ax, p, n, cod[n], ext[n], LED[n], r=r, fs=11)
    ax.annotate('', xy=(-1.3, 0.9), xytext=(-2.7, 1.9), arrowprops=dict(arrowstyle='-|>', lw=2, color=GRIS))
    ax.text(-3.4, 2.0, 'RST / EN = 0', fontsize=9.5, fontweight='bold', color=GRIS)
    # avances correctos (arriba)
    flecha(ax, pos['SIN_TECLAS'], pos['PASO_1'], rad=-0.18, ra=r, rb=r, color=VERDE)
    etiqueta(ax, (3.25, 1.35), 'A / –', VERDE)
    flecha(ax, pos['PASO_1'], pos['PASO_2'], rad=-0.18, ra=r, rb=r, color=VERDE)
    etiqueta(ax, (9.75, 1.35), 'C / –', VERDE)
    # lazos (se mantiene la tecla)
    lazo(ax, pos['PASO_1'], 'A (se mantiene) / –', GRIS, theta=90, r=r)
    lazo(ax, pos['PASO_2'], 'C (se mantiene) / –', GRIS, theta=90, r=r)
    lazo(ax, pos['SIN_TECLAS'], 'B o C / ALARMA', ROJO, theta=90, r=r)
    # regresos (abajo)
    flecha(ax, pos['PASO_1'], pos['SIN_TECLAS'], rad=-0.18, ra=r, rb=r, color=ROJO)
    etiqueta(ax, (3.25, -1.55), 'B / ALARMA', ROJO)
    flecha(ax, pos['PASO_2'], pos['SIN_TECLAS'], rad=-0.42, ra=r, rb=r, color=VERDE, lw=2.6)
    etiqueta(ax, (6.5, -3.35), 'B / CODIGO_OK   ✔ abre la barrera', VERDE, fs=10.5)
    flecha(ax, pos['PASO_2'], pos['SIN_TECLAS'], rad=-0.62, ra=r, rb=r, color=ROJO)
    etiqueta(ax, (6.5, -5.35), 'A / ALARMA   ✘ se borra el progreso', ROJO, fs=10)
    ax.set_xlim(-4.2, 15.0)
    ax.set_ylim(-6.8, 4.6)
    ax.text(6.5, -6.4,'Mealy: cada flecha dice  tecla / salida.  La salida depende del estado Y de la tecla pulsada '
                       '(solo con EN = 1, barrera cerrada).', ha='center', fontsize=9.5, color='#334155')
    fig.savefig(os.path.join(OUT, 'fsm2_mealy.png'), bbox_inches='tight')
    plt.close(fig)


# ------------------------------------------------------------------ bloques del sistema
def caja(ax, x, y, w, h, texto, fc, ec, fs=10, bold=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.12', fc=fc, ec=ec, lw=2,
                                zorder=2))
    ax.text(x + w / 2, y + h / 2, texto, ha='center', va='center', fontsize=fs,
            fontweight='bold' if bold else 'normal', zorder=3)


def lin(ax, a, b, color=GRIS, flecha_=True, lw=1.8, rad=0.0, ls='-'):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle='-|>' if flecha_ else '-', mutation_scale=14, lw=lw,
                                 color=color, connectionstyle='arc3,rad=%s' % rad, zorder=1, ls=ls))


def maquina(ax, x, y, titulo, color, fondo, salidas, ent_nsl, nombre_q, mealy):
    ax.add_patch(FancyBboxPatch((x, y), 12.2, 4.3, boxstyle='round,pad=0.02,rounding_size=0.2', fc=fondo,
                                ec=color, lw=2.5, zorder=0))
    ax.text(x + 0.3, y + 4.0, titulo, fontsize=11.5, fontweight='bold', color=color, va='center')
    nx, rx, ox = x + 0.7, x + 4.4, x + 8.3
    caja(ax, nx, y + 1.2, 2.9, 1.7, 'Next state\nlogic', 'white', color)
    caja(ax, rx, y + 1.2, 2.9, 1.7, 'State register\n%s' % nombre_q, 'white', color, fs=9)
    caja(ax, ox, y + 1.2, 2.9, 1.7, 'Output\nlogic', 'white', color)
    lin(ax, (nx + 2.9, y + 2.05), (rx, y + 2.05))
    ax.text(nx + 3.65, y + 2.3, 'D', fontsize=9, ha='center', color=GRIS)
    lin(ax, (rx + 2.9, y + 2.05), (ox, y + 2.05))
    ax.text(rx + 3.65, y + 2.3, 'Q', fontsize=9, ha='center', color=GRIS)
    # realimentacion
    ax.plot([rx + 3.5, rx + 3.5, nx + 1.45], [y + 2.05, y + 0.85, y + 0.85], color=GRIS, lw=1.6, ls='--', zorder=1)
    lin(ax, (nx + 1.45, y + 0.85), (nx + 1.45, y + 1.2), color=GRIS)
    ax.text(rx - 0.3, y + 0.5, 'Q (realimentación)', fontsize=8.5, color=GRIS, ha='center')
    ax.text(nx - 0.2, y + 3.25, ent_nsl, fontsize=8.5, color='#0f172a', ha='left')
    ax.text(ox + 0.2, y + 3.25, salidas, fontsize=8.5, color='#0f172a', ha='left')
    if mealy:
        ax.text(ox + 1.45, y + 0.35, 'las teclas A, B, C y EN llegan\ntambién a la output logic (Mealy)',
                fontsize=7.5, color=color, ha='center', style='italic')


def bloques():
    fig, ax = plt.subplots(figsize=(14, 9.2), dpi=130)
    ax.set_xlim(0, 28.5)
    ax.set_ylim(0, 18)
    ax.axis('off')
    ax.set_title('Arquitectura del sistema: dos FSM, un solo reloj', fontsize=15, fontweight='bold')
    maquina(ax, 8.4, 11.2, 'FSM 2 - MEALY  ·  Verificador del código secreto', NARANJA, '#fff7ed',
            'CODIGO_OK, ALARMA\nPASO_1, PASO_2', 'A, B, C, EN, RST', 'P1 P0', True)
    maquina(ax, 8.4, 2.2, 'FSM 1 - MOORE  ·  Controlador de la barrera', AZUL, '#eff6ff',
            'CERRADA, ABRIENDO,\nABIERTA, CERRANDO', 'SENSOR, OK', 'Q1 Q0', False)
    # entradas
    caja(ax, 0.6, 13.6, 5.2, 1.5, 'Teclado A, B, C\n(botones)', '#fef3c7', '#b45309', fs=10)
    caja(ax, 0.6, 5.6, 5.2, 1.5, 'SENSOR\n(hay un carro)', '#fef3c7', '#b45309', fs=10)
    caja(ax, 0.6, 9.3, 5.2, 1.5, 'CLK único  ·  RST', '#e2e8f0', GRIS, fs=10)
    lin(ax, (5.8, 14.35), (8.4, 13.25), color='#b45309')
    lin(ax, (5.8, 6.35), (8.4, 4.25), color='#b45309')
    lin(ax, (5.8, 10.6), (8.4, 12.2), color=GRIS)
    lin(ax, (5.8, 9.6), (8.4, 3.4), color=GRIS)
    ax.text(5.9, 11.7, 'CLK, RST', fontsize=8.5, color=GRIS)
    ax.text(5.9, 7.2, 'CLK, RST', fontsize=8.5, color=GRIS)
    # interaccion
    lin(ax, (22.6, 11.2), (22.6, 6.5), color=VERDE, lw=3)
    ax.text(22.9, 8.9, 'CODIGO_OK  →  OK\n(abre la barrera)', fontsize=9.5, color=VERDE, fontweight='bold', va='center')
    lin(ax, (21.1, 6.5), (21.1, 11.2), color=AZUL, lw=3)
    ax.text(15.7, 8.9, 'CERRADA  →  EN\n(solo acepta código con\nla barrera cerrada)', fontsize=9.5, color=AZUL,
            fontweight='bold', va='center', ha='left')
    # salidas
    caja(ax, 22.9, 13.6, 5.3, 1.5, 'LEDs: CODIGO_OK, ALARMA,\nPASO_1, PASO_2', '#dcfce7', VERDE, fs=8.5)
    caja(ax, 22.9, 3.0, 5.3, 1.5, 'LEDs: CERRADA, ABRIENDO,\nABIERTA, CERRANDO', '#dcfce7', VERDE, fs=8.5)
    lin(ax, (20.6, 14.0), (22.9, 14.35), color=VERDE)
    lin(ax, (20.6, 4.9), (22.9, 3.75), color=VERDE)
    ax.text(0.6, 0.6, 'Línea punteada = realimentación del estado.  Cada máquina: Next state logic → State register → Output logic.',
            fontsize=9, color='#334155')
    fig.savefig(os.path.join(OUT, 'arquitectura_sistema.png'), bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    fsm1()
    fsm2()
    bloques()
    print('Imagenes generadas en', os.path.abspath(OUT))
