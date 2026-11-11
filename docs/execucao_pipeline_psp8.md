# Etapa 2 — Pipeline de dados em nuvem (instruções de validação)

Este documento complementa [o planejamento aprovado](planejamento_psp8.md). **O desenvolvimento do código não equivale à comprovação de execução no Google Drive.** O usuário valida cada etapa antes de promover mudanças para `main`.

## Arquivos criados

- [`scripts/pipeline_etl_drive.py`](../scripts/pipeline_etl_drive.py): coleta da versão 1 com KaggleHub, preservação de CSV original, tipagem, auditoria dos 13 atributos (domínios centralizados), exportação, releitura, SHA-256, manifesto e `verificar_persistencia` (relê o Drive após remontagem).
- [`notebooks/PSP8_Pipeline_Bronze_Prata_Colab.ipynb`](../notebooks/PSP8_Pipeline_Bronze_Prata_Colab.ipynb): execução guiada no Google Colab.
- [`tests/test_pipeline_etl_drive.py`](../tests/test_pipeline_etl_drive.py): testes de unidade com linhas reais da base e entradas inválidas; não requer acesso ao Kaggle ou Drive.

O notebook inicial [`MVP_Viabilidade_Nova_Unidade_Dados.ipynb`](../MVP_Viabilidade_Nova_Unidade_Dados.ipynb) permanece intacto. As análises P1–P4 estão em [`notebooks/PSP8_Analise_P1_P4.ipynb`](../notebooks/PSP8_Analise_P1_P4.ipynb) e [`scripts/analise_ssd.py`](../scripts/analise_ssd.py); o catálogo, em [`catalogo/catalogo_dados.md`](../catalogo/catalogo_dados.md). O [README](../README.md) é a documentação principal.

## Execução no Google Colab

1. Abra o arquivo `notebooks/PSP8_Pipeline_Bronze_Prata_Colab.ipynb` no Colab.
2. Use **Executar tudo**: instala `kagglehub` e `pandas`, monta o Drive (autorize **seu próprio Drive**) e baixa o script de um commit fixo do GitHub (`8b90917`).
3. `executar_pipeline` baixa a **versão 1** do Kaggle e cria a pasta de execução no Google Drive.
4. O notebook **desmonta (com *flush*) e remonta o Drive** (autorize novamente) e `verificar_persistencia` relê os arquivos, recalcula SHA-256, tamanhos e contagens, refaz a auditoria e compara com o manifesto; a célula falha se algo divergir (`Resultado: APROVADA` se tudo conferir).
5. Execute as células de resumo (manifesto, hashes, tabela prata relida).
6. Inspecione `MyDrive/UnB/PSP8/MVP_Viabilidade_Nova_Unidade/execucoes/<id>/` no navegador.

Estrutura esperada:

```text
execucoes/<id>/
  bronze/
    Engineering_Cost_Feasibility_Dataset_original.csv
  prata/
    projetos_infraestrutura_flat.csv
  evidencias/
    manifesto_execucao.json
    auditoria_qualidade.json
    verificacao_persistencia.json
  analises/            (criada pelo notebook PSP8_Analise_P1_P4)
```

Os arquivos JSON da pasta `evidencias` registram os resultados do código; **não** substituem uma captura legível da pasta no Drive e das verificações do notebook.

## Validações para esta etapa

- **Origem:** licença **CC0: Public Domain** e **versão 1** (atualizada em 2025-07-28), obtidas da API pública do Kaggle em 2026-11-11 e gravadas no manifesto (`metadados_fonte`); **reconfirmar a licença na página do dataset**. O download é fixado em `versions/1` e o SHA-256 esperado do CSV é registrado.
- **Esquema:** 13 colunas esperadas; o código falha se faltar ou sobrar uma coluna. Para a fonte original conhecida, eram 3.245 registros, mas o pipeline não força o número: qualquer mudança deverá ser analisada.
- **Bronze:** bytes do arquivo original são copiados sem edição. Hash do arquivo original = hash da cópia.
- **Prata:** modelo *flat* com 13 colunas, tipagem explícita e sem remoção ou imputação. A ordem das linhas é mantida. Na execução observada a prata é **idêntica à bronze byte a byte** (nenhuma transformação de conteúdo); o manifesto declara isso em `transformacoes_prata`.
- **Qualidade:** auditoria por atributo de nulos, unicidade, duplicatas, conformidade com o domínio (faixas, categorias, padrão do ID), consistência entre complexidade categórica e numérica e *outliers* por IQR (informativos). Nada é removido ou corrigido; valores sinalizados exigem interpretação humana.
- **Releitura:** após gravar, o Python lê novamente bronze e prata do Drive e compara com os dados em memória. Hash e manifesto documentam integridade.
- **Segurança:** o Drive é privado; não publicar tokens, credenciais ou dados sem verificar a licença.

> Os domínios de validação têm origem declarada (`documentado_na_fonte`, `observado_v1` ou `convencao_do_projeto`; ver o [catálogo](../catalogo/catalogo_dados.md)). Em especial, `Stakeholder_Priority_Score` é validado em **0–1** (observado 0,50–1,00), não em 0–100; os escores `Resource_Allocation`, `Risk_Assessment` e `Environmental_Impact` usam 0–100 por convenção do projeto. A classificação original de viabilidade (`Feasibility_Label`) não é uma verdade de campo nem um resultado de previsão.

## Testes independentes da nuvem

Na raiz do repositório, com `pandas` instalado:

```bash
python -m unittest discover -s tests -v
```

Os testes cobrem preservação do arquivo bruto, auditoria de domínios, manifesto, `verificar_persistencia`, as análises P1–P4 e o catálogo. Para conferir também o CSV real da v1, defina `PSP8_CSV_REAL` com o caminho do arquivo. Testes locais bem-sucedidos **não comprovam a persistência no Google Drive**.

## Situação das pendências

- [x] Executar o notebook no Colab com a conta Google do usuário (confirmado pelo autor, incluindo remontagem do Drive e `Resultado: APROVADA`).
- [x] Contagens e SHA-256 conferidos nos JSONs da primeira execução: 3.245 registros, hashes de fonte, bronze e prata iguais a `a93b9f10…`, igual ao CSV público da v1 baixado de forma independente.
- [x] Licença (CC0) e versão (1) registradas a partir da API do Kaggle. Data da coleta: execução de referência em 2026-11-11; o campo `coletado_em_utc` consta nas execuções posteriores às correções.
- [x] Testes locais executados (50 testes OK, com o CSV real e sem ele).
- [x] Auditoria de cada atributo revisada; domínio de `Stakeholder_Priority_Score` corrigido para 0–1.
- [x] Perguntas P1–P4 desenvolvidas **a partir da prata relida** (notebook e módulo de análise) e catálogo, README e autoavaliação criados.
- [ ] Reconfirmar a licença na página do dataset no Kaggle.
- [x] `PSP8_Analise_P1_P4.ipynb` executado com sucesso no Colab (relato do autor).
- [x] Evidências versionadas em `evidencias/`: 5 capturas (01–04 e 06) e 7 gráficos reais. [ ] Falta a captura 05 (pasta da execução no Drive): ver [`evidencias/LEIAME.md`](../evidencias/LEIAME.md).
- [x] Licença do código definida (`LICENSE`, MIT).
- [x] Repositório público conferido em janela anônima (relato do autor). [ ] Postar o link no fórum da disciplina. (O nome do aluno já consta no README.)

**Entrega final:** a branch `psp8-etapa-2-pipeline` foi mesclada na `main` após a validação; os notebooks usam o commit fixo `8b90917` para baixar os scripts.
