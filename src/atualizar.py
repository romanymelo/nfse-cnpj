"""Pipeline completo: planilhas -> CSV -> JSON -> página HTML.
Uso:
  python src/atualizar.py --anexo8 "dados/oficial/Anexo VIII - v1.02.00 (26-10-2026).xlsx" --anexo7 "dados/oficial/Anexo VII - v1.03.00 (NT 009).xlsx" --correlacao "dados/correlacao/Correlacao CNAE Maceio.xlsx" --versao "v1 - 03/11/2026"
"""
import argparse, subprocess, sys, os
ap = argparse.ArgumentParser()
ap.add_argument('--anexo8', required=True); ap.add_argument('--anexo7', required=True)
ap.add_argument('--correlacao', required=True); ap.add_argument('--versao', required=True)
a = ap.parse_args()
raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
proc, dist = os.path.join(raiz, 'dados', 'processado'), os.path.join(raiz, 'dist')
def rodar(*args): subprocess.run([sys.executable, '-I', *args], check=True, cwd=raiz)
rodar('src/normaliza_anexo8.py', a.anexo8, proc)
rodar('src/normaliza_anexo7.py', a.anexo7, proc)
rodar('src/normaliza_correlacao.py', a.correlacao, proc)
rodar('src/gerar_json.py', proc)
rodar('src/montar_pagina.py', proc, dist, a.versao)
