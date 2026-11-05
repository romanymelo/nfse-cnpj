"""Junta Anexo VIII + Anexo VII + correlação CNAE e gera dados.json.
items: item -> NBS -> cIndOp/cClassTrib (só os itens usados pela correlação)
cnae:  CNAE (7 dígitos) -> descrição e serviços [item da correlação, item do Anexo VIII, anexo SN, descrição SN]
Uso: python src/gerar_json.py <pasta_processado>
"""
import csv, json, sys, collections
pasta = sys.argv[1]
ler = lambda nome: list(csv.DictReader(open(f'{pasta}/{nome}', encoding='utf-8-sig'), delimiter=';'))
ind = {r['indop']: r for r in ler('anexo7_indop.csv')}
items = collections.OrderedDict()
for r in ler('anexo8_principal.csv'):
    it = items.setdefault(r['item_lc116'], {'i': r['item_lc116'], 'd': r['descricao_item'].strip(), 'n': [], 'a': []})
    n = next((x for x in it['n'] if x['c'] == r['nbs']), None)
    if not n:
        n = {'c': r['nbs'], 'd': r['descricao_nbs'].strip(), 'o': [], 'cc': []}
        it['n'].append(n)
    if r['indop'] and r['indop'] not in n['o']: n['o'].append(r['indop'])
    if r['cclasstrib'] and all(x[0] != r['cclasstrib'] for x in n['cc']): n['cc'].append([r['cclasstrib'], r['nome_cclasstrib'].strip()])

cnae, sem_item = {}, set()
for r in ler('correlacao.csv'):
    it = r['item_lc116']
    nac = it if it in items else '.'.join(it.split('.')[:2])  # subitem municipal (14.14.01) -> item pai (14.14)
    if nac not in items: sem_item.add(it); continue
    c = cnae.setdefault(r['cnae'], {'d': r['descricao_cnae'], 's': []})
    c['s'].append([it, nac, r['anexo_sn'], r['desc_sn']])
usados_it = {s[1] for c in cnae.values() for s in c['s']}
items = [v for k, v in items.items() if k in usados_it]
usados = {o for it in items for n in it['n'] for o in n['o']}
indop = {}
for k in sorted(usados):
    v = ind.get(k)
    indop[k] = {'t': v['tipo_operacao'], 'l': v['local_fornecimento_dfe']} if v else {'t': 'descrição indisponível (consultar o Anexo VII)', 'l': ''}
json.dump({'items': items, 'indop': indop, 'cnae': cnae}, open(f'{pasta}/dados.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(cnae), 'CNAEs;', len(items), 'itens;', sum(len(i['n']) for i in items), 'pares item×NBS;', len(usados), 'cIndOp; sem descrição:', sorted(usados - set(ind)), '; itens da correlação fora do Anexo VIII:', sorted(sem_item))
