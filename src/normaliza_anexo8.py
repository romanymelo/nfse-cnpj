"""Normaliza a aba "tabela geral" do Anexo VIII (células mescladas, linhas de continuação).
Uso: python src/normaliza_anexo8.py <planilha.xlsx> <pasta_saida>
"""
import sys, csv, openpyxl
src, outdir = sys.argv[1], sys.argv[2]
wb = openpyxl.load_workbook(src)
ws = wb['tabela geral']
grid = {}
for row in ws.iter_rows(min_row=2, max_col=10):
    for c in row:
        grid[(c.row, c.column)] = c.value
for m in ws.merged_cells.ranges:
    if m.min_row < 2: continue
    v = grid.get((m.min_row, m.min_col))
    for r in range(m.min_row, m.max_row + 1):
        for c in range(m.min_col, m.max_col + 1):
            grid[(r, c)] = v
def g(r, c):
    v = grid.get((r, c))
    if v is None: return ''
    return str(v).strip()
main, alt = [], []
item = idesc = ''; last = None; prev_item = None
for r in range(2, ws.max_row + 1):
    a, b = g(r,1), g(r,2)
    if a: item, idesc = a, b
    nbs, nd, ind = g(r,3), g(r,4), g(r,7)
    if not item: continue
    if item != prev_item: last = None; prev_item = item
    if nbs:
        main.append([item, idesc, nbs, nd, ind, g(r,8), g(r,5), g(r,6), g(r,9), g(r,10)])
        last = (nbs, nd, g(r,9), g(r,10))
    else:
        # linha de continuação sem NBS: o cIndOp pertence à última NBS do mesmo item
        if ind and last:
            main.append([item, idesc, last[0], last[1], ind, g(r,8), g(r,5), g(r,6), last[2], last[3]])
        if g(r,9) and (not last or g(r,9) != last[2]):
            alt.append([item, idesc, g(r,9), g(r,10)])
h5 = str(ws.cell(1,5).value or '')
if h5.startswith('COD_ATIV_SN'):
    hdr = ['item_lc116','descricao_item','nbs','descricao_nbs','indop','local_incidencia_ibs','cod_ativ_sn','desc_ativ_sn','cclasstrib','nome_cclasstrib']
else:
    hdr = ['item_lc116','descricao_item','nbs','descricao_nbs','indop','local_incidencia_ibs','ps_onerosa','adq_exterior','cclasstrib','nome_cclasstrib']
with open(f'{outdir}/anexo8_principal.csv','w',newline='',encoding='utf-8-sig') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(hdr); w.writerows(main)
with open(f'{outdir}/anexo8_cclasstrib_alternativos.csv','w',newline='',encoding='utf-8-sig') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['item_lc116','descricao_item','cclasstrib','nome_cclasstrib']); w.writerows(alt)
print(len(main), len(alt), len({m[0] for m in main}))
