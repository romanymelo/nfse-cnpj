"""Teste de navegador da página. A BrasilAPI é simulada (CNPJs e empresas fictícios).
Uso: python testes/teste_pagina.py "<arquivo.html>" """
import sys, json, pathlib
from playwright.sync_api import sync_playwright

url = pathlib.Path(sys.argv[1]).resolve().as_uri()
API = 'https://brasilapi.com.br/api/cnpj/v1/'
FICTICIA = {'razao_social': 'EMPRESA FICTICIA DE TESTE LTDA', 'municipio': 'MACEIO', 'uf': 'AL', 'codigo_municipio_ibge': 2704302,
            'descricao_situacao_cadastral': 'ATIVA', 'cnae_fiscal': 8630503, 'cnae_fiscal_descricao': 'Atividade médica ambulatorial restrita a consultas',
            'cnaes_secundarios': [{'codigo': 4711302, 'descricao': 'Comércio varejista de mercadorias em geral'}, {'codigo': 161001, 'descricao': 'Serviço de pulverização'}]}
CASOS_CNAE = [
    ('8630-5/03', ['04.01'], ['200029', 'III ou V (Fator R)']),
    ('6201-5/01', ['01.01', '01.02'], []),
    ('4399-1/04', ['14.14'], ['14.14.02', '14.14.04', 'Na NFS-e Nacional use o item 14.14']),
    ('6920-6/01', ['17.19'], ['III']),
    ('4711-3/02', [], ['CNAE sem correspondência']),
]
falhas = 0
def check(ok, msg):
    global falhas; falhas += not ok; print(('OK   ' if ok else 'FALHA'), msg)
itens = lambda pg: pg.eval_on_selector_all('#out .item h2 .code', 'els => els.map(e => e.textContent)')

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    erros = []; pg.on('pageerror', lambda e: erros.append(str(e)))
    chamadas = []
    modo = {'v': 'ok'}
    def api(route):
        chamadas.append(route.request.url)
        if modo['v'] in ('ok', 'outra'):
            d = FICTICIA if modo['v'] == 'ok' else {**FICTICIA, 'municipio': 'ARAPIRACA', 'codigo_municipio_ibge': 2700300}
            route.fulfill(status=200, content_type='application/json', body=json.dumps(d), headers={'access-control-allow-origin': '*'})
        elif modo['v'] == '404': route.fulfill(status=404, content_type='application/json', body='{"message":"não encontrado"}', headers={'access-control-allow-origin': '*'})
        else: route.abort()
    pg.route(API + '*', api)
    pg.goto(url)

    # Etapa 1: CNAEs informados manualmente
    pg.click('#manual summary')
    for cnae, esperado, textos in CASOS_CNAE:
        pg.fill('#cnaes', cnae)
        corpo = pg.inner_text('#cnlist') + pg.inner_text('#out')
        faltam = [t for t in textos if t not in corpo]
        check(itens(pg) == esperado and not faltam, f'{cnae} -> {itens(pg)} {faltam or ""}')
    pg.fill('#cnaes', '8630-5/03')
    check(pg.eval_on_selector_all('#out .r-cc .v', 'els => els.filter(e => !e.textContent.trim()).length') == 0, 'saúde sem classificação vazia')
    tags = pg.eval_on_selector_all('#out .op', 'ops => ops.map(o => o.querySelector(".cod").textContent + ":" + [...o.querySelectorAll(".tag")].map(t => t.textContent).join("|"))')
    check('030101:estabelecimento do fornecedor' in tags and '030102:diverso do estabelecimento do fornecedor' in tags
          and '100301:serviços prestados à distância' in tags, f'selos de local: {tags}')
    pg.fill('#cnaes', '4399-1/04')
    tags = pg.eval_on_selector_all('#out .op', 'ops => ops.map(o => o.querySelector(".cod").textContent + ":" + [...o.querySelectorAll(".tag")].map(t => t.textContent).join("|"))')
    check('050101:estabelecimento do fornecedor' in tags and '050102:diverso do estabelecimento do fornecedor' in tags, 'selos de local também em 0501xx')

    # Etapa 4: busca por descrição restrita aos itens informados
    check(pg.is_visible('#q'), 'campo de busca aparece com atividades informadas')
    pg.fill('#q', 'software')
    check(itens(pg) == [] and 'Nenhum serviço da empresa' in pg.inner_text('#out'), 'só saúde + "software": nada fora dos itens do CNPJ')
    pg.fill('#cnaes', '8630-5/03\n6201-5/01\n6920-6/01')
    r = itens(pg); check(set(r) == {'01.01', '01.02'}, f'"software" com 3 CNAEs -> {r}')
    pg.fill('#q', 'contabilidade'); r = itens(pg); check(r[:1] == ['17.19'] and '04.01' not in r, f'"contabilidade" -> {r}')
    pg.fill('#q', 'consulta medica'); r = itens(pg); check(r[:1] == ['04.01'], f'"consulta medica" -> {r}')
    boas = pg.eval_on_selector_all('#out .item', 'its => its.filter(i => i.querySelector(".boa")).map(i => i.querySelector(".code").textContent)')
    mais = pg.eval_on_selector_all('#out .badge.ok:not(.boa)', 'bs => bs.map(b => b.textContent)')
    check(boas == ['04.01'] and 'mais provável' in mais, f'"consulta medica": boa correspondência em {boas}, NBS mais provável marcada')
    pg.fill('#cnaes', '8640-2/05'); pg.fill('#q', 'ultrassom')
    nbs = pg.eval_on_selector_all('#out .item:first-child .r-nbs', 'rs => rs.map(r => r.querySelector(".cod").textContent + (r.querySelector(".badge.ok") ? "*" : ""))')
    check(nbs[:1] == ['1.2301.94.00*'] and len(nbs) > 1, f'"ultrassom": NBS mais provável no topo da ficha {nbs}')
    pg.fill('#q', ''); nbs0 = pg.eval_on_selector_all('#out .item:first-child .r-nbs .cod', 'cs => cs.map(c => c.textContent)')
    check(nbs0[0] != '1.2301.94.00', f'sem busca, ordem original do Anexo: {nbs0}')
    pg.fill('#q', 'laboratorio')
    nbs = pg.eval_on_selector_all('#out .item:first-child .r-nbs', 'rs => rs.map(r => r.querySelector(".cod").textContent + (r.querySelector(".badge.ok") ? "*" : ""))')
    check(nbs[:1] == ['1.2301.93.00*'], f'"laboratorio": NBS laboratorial no topo {nbs}')
    # fora da saúde: a NBS que combina com a busca sobe e ganha o selo
    pg.fill('#cnaes', '7112-0/00\n7020-4/00'); pg.fill('#q', 'consultoria')
    fichas = pg.eval_on_selector_all('#out .item', '''its => its.map(i => { const ns = [...i.querySelectorAll(".r-nbs")];
        return { item: i.querySelector(".code").textContent, tem: ns.some(n => /consultoria/i.test(n.querySelector(".desc").textContent)),
                 primeira: ns[0].querySelector(".desc").textContent, marcada: !!ns[0].querySelector(".badge.ok") }; })''')
    ok = all((f['marcada'] and 'consultoria' in f['primeira'].lower()) if f['tem'] else not f['marcada'] for f in fichas)
    check(ok and any(f['tem'] for f in fichas), '"consultoria": NBS de consultoria no topo e marcada; item sem NBS de consultoria fica sem selo ' + str([(f['item'], f['marcada']) for f in fichas]))
    pg.fill('#q', 'topografia')
    check(not pg.query_selector('#out .r-nbs .badge.ok'), '"topografia": nenhuma NBS menciona, nenhuma marcada')
    pg.fill('#cnaes', '8630-5/03\n6201-5/01\n6920-6/01')
    pg.fill('#q', 'contabilidade')
    boas = pg.eval_on_selector_all('#out .item', 'its => its.filter(i => i.querySelector(".boa")).map(i => i.querySelector(".code").textContent)')
    check(boas[:1] == ['17.19'], f'"contabilidade": boa correspondência em {boas}')
    pg.fill('#q', 'contabilidde'); r = itens(pg); check('17.19' in r, f'erro de digitação "contabilidde" -> {r}')
    pg.fill('#q', 'venda de mercadoria'); check('ICMS' in pg.inner_text('#note'), 'aviso de ICMS para venda')
    pg.fill('#q', '17.19'); check(itens(pg) == ['17.19'], 'busca pelo número do item')
    pg.fill('#q', ''); check(len(itens(pg)) == 4, 'busca vazia volta a mostrar todos os serviços')

    # Etapa 2: CNPJ
    pg.fill('#cnaes', '')
    check(not pg.is_visible('#q'), 'sem atividades, campo de busca escondido')
    pg.fill('#cnpj', '11.222.333/0001-82')
    pg.click('#consultar')
    check('inválido' in pg.inner_text('#msg') and not chamadas, 'CNPJ inválido avisa sem chamar a API')

    pg.fill('#cnpj', '11.222.333/0001-81')  # válido: consulta automática ao completar
    pg.wait_for_selector('#empresa .emp')
    emp = pg.inner_text('#empresa')
    check('EMPRESA FICTICIA' in emp and 'MACEIO/AL' in emp, 'razão social e município: ' + emp.splitlines()[-1])
    check(itens(pg) == ['04.01', '07.13'], f'serviços do CNPJ: {itens(pg)} (0161-0/01 com zero à esquerda)')
    pg.wait_for_timeout(700)  # fim da animação de entrada
    folga = pg.evaluate("document.querySelector('.emp').getBoundingClientRect().top - document.querySelector('.amostra').getBoundingClientRect().bottom")
    check(folga > 0, f'cartão da empresa não cobre a ficha de exemplo (folga {folga:.0f}px)')
    check('CNAE sem correspondência' in pg.inner_text('#cnlist') and 'Comércio varejista' in pg.inner_text('#cnlist'), 'comércio sem correspondência, com a descrição da Receita')
    check(len(chamadas) == 1 and chamadas[0].endswith('11222333000181'), 'uma chamada à API com o CNPJ limpo')

    # Etapa 3: alíquota só para Maceió; impeditiva em destaque
    tab = pg.inner_text('#cnlist')
    check('ISS' not in tab and '%' not in tab + pg.inner_text('#out'), 'Maceió: nenhuma alíquota de ISS na tela')
    check(pg.evaluate("Object.values(DATA.cnae).every(e => e.s.every(s => s.length === 4 && !/^\\d+([.,]\\d+)?$/.test(s[2])))"), 'alíquota também ausente dos dados embutidos')
    modo['v'] = 'outra'
    pg.fill('#cnpj', ''); pg.fill('#cnpj', '11.222.333/0001-81'); pg.wait_for_selector('#empresa .emp')
    check('ARAPIRACA' in pg.inner_text('#empresa') and itens(pg) == ['04.01', '07.13'], 'outro município: mesmos serviços')
    modo['v'] = 'ok'
    pg.fill('#cnaes', '0161-0/99\n6499-9/99')
    imp = pg.eval_on_selector_all('#cnlist tr', 'trs => trs.filter(t => t.querySelector(".badge.bad")).map(t => t.textContent)')
    check(len(imp) == 2 and any('17.05' in t for t in imp) and any('15.02' in t for t in imp) and not any('10.05' in t for t in imp),
          'impeditiva destacada só nos itens impeditivos (17.05, 15.02; não 10.05)')

    # Nova consulta: limpa tudo
    pg.fill('#q', 'consulta'); pg.click('#nova')
    vazios = pg.evaluate("['#cnpj','#cnaes','#q'].every(s => !document.querySelector(s).value)")
    check(vazios and not pg.inner_text('#empresa').strip() and not itens(pg) and not pg.is_visible('#q')
          and not pg.eval_on_selector('#manual', 'e => e.open') and pg.evaluate("document.activeElement.id") == 'cnpj', 'Nova consulta limpa tudo e volta ao CNPJ')

    pg.fill('#cnpj', '12.ABC.345/01DE-35')
    pg.click('#consultar'); pg.wait_for_selector('#empresa .emp')
    check(chamadas[-1].endswith('12ABC34501DE35'), 'CNPJ alfanumérico aceito')

    modo['v'] = '404'
    pg.fill('#cnpj', ''); pg.fill('#cnpj', '11.222.333/0001-81')
    pg.wait_for_function("document.querySelector('#msg').classList.contains('erro')")
    check('não encontrado' in pg.inner_text('#msg') and pg.eval_on_selector('#manual', 'e => e.open'), 'CNPJ não encontrado: aviso e campo manual aberto')

    modo['v'] = 'rede'
    pg.reload(); pg.fill('#cnpj', '11.222.333/0001-81')
    pg.wait_for_function("document.querySelector('#msg').classList.contains('erro')")
    check('Não foi possível consultar' in pg.inner_text('#msg') and pg.eval_on_selector('#manual', 'e => e.open'), 'sem rede: aviso e campo manual aberto')
    pg.fill('#cnaes', '8630503')
    check(itens(pg) == ['04.01'], 'sem rede: CNAE colado funciona')

    # Voltar ao início: escondido no topo, aparece ao rolar e volta ao topo
    pg.fill('#cnaes', '8630-5/03\n6201-5/01\n6920-6/01\n4399-1/04')
    pg.evaluate('scrollTo(0, 0)'); pg.wait_for_timeout(300)
    escondido = not pg.eval_on_selector('#topo', 'b => b.classList.contains("on")')
    pg.evaluate('scrollTo(0, document.body.scrollHeight)'); pg.wait_for_timeout(300)
    visivel = pg.eval_on_selector('#topo', 'b => b.classList.contains("on")')
    pg.click('#topo'); pg.wait_for_function('scrollY === 0', timeout=3000)
    check(escondido and visivel, 'Voltar ao início: escondido no topo, aparece ao rolar e leva ao topo')
    pg.fill('#cnaes', '8630-5/03')

    # Aba "Como usar": troca a tela e volta sem perder a consulta
    pg.click('#aba-ajuda')
    check(pg.is_visible('#tela-ajuda') and not pg.is_visible('#out') and not pg.is_visible('#cnpj') and 'Impeditiva' in pg.inner_text('#tela-ajuda'), 'aba Como usar mostra a ajuda e esconde a consulta')
    pg.click('#aba-consulta')
    check(not pg.is_visible('#tela-ajuda') and itens(pg) == ['04.01'], 'volta para Consulta com os serviços mantidos')

    check(not erros, f'erros JS: {erros or "nenhum"}')
    b.close()
sys.exit(1 if falhas else 0)
