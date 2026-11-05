"""Normaliza o Anexo VII (cIndOp) para CSV.
Uso: python src/normaliza_anexo7.py <planilha.xlsx> <pasta_saida>
"""
import sys, csv, openpyxl
src, outdir = sys.argv[1], sys.argv[2]
ws = openpyxl.load_workbook(src, data_only=True).active
limpa = lambda x: ' '.join(str(x).split()) if x is not None else ''
rows = []
for r in ws.iter_rows(min_row=2, values_only=True):
    if r[0] and str(r[0]).strip().isdigit():
        rows.append(dict(indop=str(r[0]).strip(), tipo_operacao=limpa(r[1]), caracteristica=limpa(r[2]),
                         local_fornecimento_dfe=limpa(r[3]), dispositivo_lc214=limpa(r[4]), observacao=limpa(r[5]),
                         indNFSe=limpa(r[7]), local_incidencia_ibs=limpa(r[9])))
with open(f'{outdir}/anexo7_indop.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter=';'); w.writeheader(); w.writerows(rows)
print(len(rows), 'cIndOp')
