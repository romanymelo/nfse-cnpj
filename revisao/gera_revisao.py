"""Gera a planilha de revisão do vocabulário de busca. Uso: python gera_revisao.py <raiz_projeto> <saida.xlsx>"""
import sys, csv, json, importlib.util
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation

raiz, saida = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location('vocabulario', f'{raiz}/src/vocabulario.py')
voc = importlib.util.module_from_spec(spec); spec.loader.exec_module(voc)
desc = {}
for r in csv.DictReader(open(f'{raiz}/dados/processado/anexo8_principal.csv', encoding='utf-8-sig'), delimiter=';'):
    desc.setdefault(r['item_lc116'], r['descricao_item'].strip())
usados = {i['i'] for i in json.load(open(f'{raiz}/dados/processado/dados.json', encoding='utf-8'))['items']}

F = 'Arial'
base = Font(name=F, size=10); neg = Font(name=F, size=10, bold=True); tit = Font(name=F, size=14, bold=True)
cab = Font(name=F, size=10, bold=True, color='FFFFFF'); fill_cab = PatternFill('solid', fgColor='0A3540')
fill_in = PatternFill('solid', fgColor='FFF2CC')  # células para preencher
fina = Side(style='thin', color='D5E5E2'); borda = Border(bottom=fina)
topo = Alignment(vertical='top', wrap_text=True)

wb = Workbook()
# ---------- Aba de instruções ----------
ins = wb.active; ins.title = 'Como revisar'
ins.column_dimensions['A'].width = 26; ins.column_dimensions['B'].width = 90
linhas = [
    ('Revisão do vocabulário de busca', None),
    ('O que é', 'Palavras que o cliente pode digitar na busca da página "Consulta NFSe por CNPJ" e o item da LC 116 a que cada uma leva. '
               'Foram sugeridas por IA e nunca tiveram revisão fiscal. Aparecem para o cliente na linha "Relacionado a:" da ficha do serviço.'),
    ('O que não é', 'Não define item, NBS, cIndOp nem classificação: esses vêm só dos Anexos VII e VIII e da correlação de CNAE.'),
    ('Onde preencher', 'Aba "Vocabulário", só nas colunas amarelas: Decisão, Nova palavra e Observação.'),
    ('Decisão', 'Manter: a palavra leva ao item certo.  Remover: não tem relação com o item.  '
                'Alterar: escreva a forma correta em "Nova palavra".  Incluir: palavra nova para o item (use as linhas em branco no fim da aba).'),
    ('Dica', 'Use o filtro da coluna "Usado na consulta por CNPJ" para começar pelos itens que os clientes realmente veem.'),
    ('Exemplo de preenchimento', 'Só para mostrar o formato. Não é uma decisão já tomada sobre essas palavras.'),
]
ins['A1'] = linhas[0][0]; ins['A1'].font = tit
r = 3
for k, v in linhas[1:]:
    ins.cell(r, 1, k).font = neg
    if v: ins.cell(r, 2, v).font = base
    ins.cell(r, 1).alignment = topo; ins.cell(r, 2).alignment = topo
    r += 1
ex_cab = ['Item', 'Palavra-chave', 'Decisão', 'Nova palavra', 'Observação']
ex = [['04.09', 'musicoterapia', 'Manter', '', 'Terapia, conforme descrição do item 04.09.'],
      ['17.19', 'contador', 'Alterar', 'contabilidade', 'Prefiro a atividade, não a profissão.']]
for j, h in enumerate(ex_cab):
    c = ins.cell(r, 1 + j); c.value = h; c.font = cab; c.fill = fill_cab
for e in ex:
    r += 1
    for j, v in enumerate(e):
        c = ins.cell(r, 1 + j, v); c.font = base
for col, w in zip('CDE', (12, 16, 40)):
    ins.column_dimensions[col].width = max(ins.column_dimensions[col].width or 0, w)
r_andamento = r + 2

# ---------- Aba do vocabulário ----------
ws = wb.create_sheet('Vocabulário')
hdr = ['Item LC 116', 'Descrição do item (Anexo VIII)', 'Usado na consulta por CNPJ', 'Palavra-chave', 'Decisão', 'Nova palavra', 'Observação']
larg = [11, 60, 14, 32, 12, 26, 44]
for j, (h, w) in enumerate(zip(hdr, larg), 1):
    c = ws.cell(1, j, h); c.font = cab; c.fill = fill_cab; c.alignment = Alignment(vertical='center', wrap_text=True)
    ws.column_dimensions[c.column_letter].width = w
ws.row_dimensions[1].height = 30
lin = 2
for item in sorted(voc.KW):
    for p in [x.strip() for x in voc.KW[item].split(';') if x.strip()]:
        vals = [item, desc.get(item, '(item não encontrado no Anexo VIII)'), 'Sim' if item in usados else 'Não', p, None, None, None]
        for j, v in enumerate(vals, 1):
            c = ws.cell(lin, j, v); c.font = base; c.alignment = topo; c.border = borda
            if j >= 5: c.fill = fill_in
        lin += 1
ultima = lin - 1
for k in range(30):  # linhas em branco para "Incluir"
    for j in range(1, 8):
        c = ws.cell(lin, j); c.font = base; c.border = borda
        if j in (1, 4, 5, 6, 7): c.fill = fill_in
    lin += 1
dv = DataValidation(type='list', formula1='"Manter,Remover,Alterar,Incluir"', allow_blank=True)
dv.error = 'Escolha Manter, Remover, Alterar ou Incluir.'; dv.errorTitle = 'Decisão'
ws.add_data_validation(dv); dv.add(f'E2:E{lin - 1}')
ws.freeze_panes = 'E2'
# andamento da revisão (fórmulas, recalculam conforme a aba Vocabulário é preenchida)
r = r_andamento
ins.cell(r, 1, 'Andamento').font = neg
for k, d in enumerate(['Manter', 'Remover', 'Alterar', 'Incluir']):
    ins.cell(r + 1 + k, 1, d).font = base
    ins.cell(r + 1 + k, 2, f'=COUNTIF(Vocabulário!$E$2:$E${lin - 1},"{d}")').font = base
ins.cell(r + 5, 1, 'Palavras sem decisão').font = base
ins.cell(r + 5, 2, f'=COUNTA(Vocabulário!$D$2:$D${ultima})-COUNTA(Vocabulário!$E$2:$E${ultima})').font = base
for k in range(5): ins.cell(r + 1 + k, 2).alignment = Alignment(horizontal='left')
ws.auto_filter.ref = f'A1:G{lin - 1}'
from openpyxl.workbook.properties import CalcProperties
wb.calculation = CalcProperties(fullCalcOnLoad=True)  # Excel recalcula as fórmulas ao abrir
wb.save(saida)
print('itens:', len(voc.KW), '| palavras:', ultima - 1, '| itens usados na consulta por CNPJ:', sum(1 for i in voc.KW if i in usados))
