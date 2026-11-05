"""Normaliza a correlação CNAE -> item LC 116 de Maceió para CSV.
Usa só CNAE, item e enquadramento no Simples; NBS, cIndOp e cClassTrib vêm do Anexo VIII.
A alíquota de ISS da planilha é ignorada de propósito: ela varia com o faturamento e não deve ser mostrada ao cliente.
Uso: python src/normaliza_correlacao.py <planilha.xlsx> <pasta_saida>
"""
import sys, csv, re, openpyxl
src, outdir = sys.argv[1], sys.argv[2]
ws = openpyxl.load_workbook(src, read_only=True)['Correlação']
limpa = lambda x: ' '.join(str(x).split()) if x is not None else ''
rows = []
for r in ws.iter_rows(min_row=2, values_only=True):
    cnae = re.sub(r'\D', '', limpa(r[0]))
    if len(cnae) != 7 or not r[2]: continue
    rows.append(dict(cnae=cnae, descricao_cnae=limpa(r[1]), item_lc116=limpa(r[2]), anexo_sn=limpa(r[7]), desc_sn=limpa(r[8])))
with open(f'{outdir}/correlacao.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter=';'); w.writeheader(); w.writerows(rows)
print(len(rows), 'linhas;', len({r['cnae'] for r in rows}), 'CNAEs')
