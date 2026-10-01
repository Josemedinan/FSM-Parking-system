# -*- coding: utf-8 -*-
"""Ejecuta Logisim-evolution sin ventana (para las pruebas automaticas).

Indica la ruta de tu logisim-evolution.exe con la variable de entorno LOGISIM_EXE, por ejemplo:
    set LOGISIM_EXE=C:\\Users\\TU_USUARIO\\Downloads\\logisim-evolution-5.0.0-windows-amd64\\logisim-evolution.exe
"""
import os
import subprocess
import sys

EXE = os.environ.get(
    'LOGISIM_EXE',
    r"C:\Users\TU_USUARIO\Downloads\logisim-evolution-5.0.0-windows-amd64\logisim-evolution.exe")


def run(args, timeout=180):
    p = subprocess.run([EXE] + args, capture_output=True, timeout=timeout)
    return p.returncode, p.stdout.decode('utf-8', 'replace'), p.stderr.decode('utf-8', 'replace')


if __name__ == '__main__':
    rc, o, e = run(sys.argv[1:])
    print('RC', rc)
    print(o)
    print('ERR:', e)
