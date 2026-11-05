"""Gera a página HTML única a partir de dados.json + vocabulário + template.
Uso: python src/montar_pagina.py <pasta_processado> <pasta_dist> "v1 - 03/11/2026"
"""
import json, sys, os, base64
sys.path.insert(0, os.path.dirname(__file__))
from vocabulario import KW
pasta, dist, versao = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(f'{pasta}/dados.json', encoding='utf-8'))
for it in d['items']: it['k'] = [x.strip() for x in KW.get(it['i'], '').split(';') if x.strip()]
t = open(os.path.join(os.path.dirname(__file__), 'template.html'), encoding='utf-8').read()
# fontes embutidas (licença OFL, em src/fontes) para a página funcionar sem internet
fontes = ''
for familia, arq in [('Bricolage Grotesque', 'bricolage.woff2'), ('Instrument Sans', 'instrument.woff2')]:
    b64 = base64.b64encode(open(os.path.join(os.path.dirname(__file__), 'fontes', arq), 'rb').read()).decode()
    fontes += '@font-face{font-family:"%s";src:url(data:font/woff2;base64,%s) format("woff2");font-weight:100 900;font-display:swap}\n' % (familia, b64)
t = t.replace('/*FONTES*/', fontes)
js = json.dumps(d, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
nome = 'Consulta NFSe por CNPJ - ' + versao.replace('/', '-') + '.html'
os.makedirs(dist, exist_ok=True)
open(os.path.join(dist, nome), 'w', encoding='utf-8').write(t.replace('/*DATA*/', js).replace('/*VERSAO*/', versao))
print('gerado:', os.path.join(dist, nome))
