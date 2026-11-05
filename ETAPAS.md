# Etapas

## 1. CNAE colado → serviços na tela (valida a correlação + Anexo VIII)
- **Objetivo**: copiar o pipeline do original, incluir a correlação e gerar um HTML onde se colam CNAEs e aparecem os serviços correspondentes (item, NBS, cIndOp, cClassTrib, anexo do Simples).
- **Aceite**: os casos 8630-5/03, 6201-5/01, 4399-1/04, 6920-6/01 e 4711-3/02 do PLANO mostram o resultado esperado. Saúde com 200029.
- **Depende de**: nada. Inclui o CLAUDE.md do projeto e o .gitignore.
- **Tamanho**: uma sessão.

## 2. Consulta do CNPJ pela BrasilAPI
- **Objetivo**: campo de CNPJ com validação do dígito verificador, consulta na BrasilAPI e CNAE principal e secundários alimentando a etapa 1. Mostrar razão social e município.
- **Aceite**: um CNPJ real de Maceió e um de outra cidade trazem os serviços; CNPJ inválido avisa antes da chamada; com a rede desligada, aparece o erro e o campo de colar CNAEs.
- **Depende de**: 1.
- **Tamanho**: uma sessão.

## 3. Impeditiva e subitens (alíquota removida depois)
- **Objetivo**: destaque vermelho para atividade impeditiva no Simples e aviso "na NFS-e Nacional use 14.14" nos subitens municipais.
- **Aceite**: caso "subitem municipal" do PLANO. A alíquota de ISS feita nesta etapa foi removida em 03/11/2026 (ver PLANO).
- **Depende de**: 2.
- **Tamanho**: meia sessão.

## 4. Busca por descrição filtrada
- **Objetivo**: trazer a busca e o vocabulário do original, restritos aos itens do CNPJ.
- **Aceite**: caso "busca filtrada" do PLANO; busca por um termo do próprio serviço encontra o item.
- **Depende de**: 1.
- **Tamanho**: uma sessão.

## 5. Acabamento para o cliente e geração da versão
- **Objetivo**: textos voltados ao cliente (sem jargão interno), modo claro e escuro, comando que gera `Consulta NFSe por CNPJ - v1 - DD-MM-AAAA.html` e README.
- **Aceite**: todos os casos do PLANO passam no Playwright CLI sobre o arquivo final.
- **Depende de**: 2, 3 e 4.
- **Tamanho**: uma sessão.

## 6. Refinamentos depois da v1 (concluída)
- **Feito**: novo visual com fontes embutidas; aba "Como usar"; ficha de exemplo; botões "Nova consulta" e "Voltar ao início"; selos "NBS mais provável" e "boa correspondência" na busca; selos de local no cIndOp; remoção da alíquota de ISS; revisão do vocabulário de busca em andamento (`revisao/`).
- **Aceite**: `python testes/teste_pagina.py` passa sobre o arquivo gerado.
