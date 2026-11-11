# Evidências da execução em nuvem

Esta pasta guarda as **capturas de tela e os gráficos reais** que comprovam a execução no Google Colab e a persistência no Google Drive (enunciado §5.2). As imagens devem estar **legíveis** e ser **referenciadas no README**, no ponto que sustentam.

**Situação em 11/11/2026:** os **7 gráficos reais do notebook P1–P4** (saídas do Colab, baixadas do Drive) estão em [`graficos/`](graficos/) e já aparecem no README (seção 7). **Ainda faltam as 8 capturas de tela da interface** (4 do Colab e 4 do navegador), listadas abaixo. Nada aqui foi simulado: não há imagens geradas fora do Colab/Drive passando por evidência.

## Já anexado

| Arquivo (`graficos/`) | Mostra | README |
|---|---|---|
| `p1_histogramas.png` | P1: distribuições de custo, risco e prazo | §7, P1 |
| `p2_percentis_do_cenario.png` | P2: posição do cenário (percentis 75,7 / 72,3 / 75,1) | §7, P2 |
| `p3_indice_do_cenario.png` | P3: índice 74,4 e faixa Crítica | §7, P3 |
| `p3_indice_historico.png` | P3: índice dos projetos históricos × cenário | §7, P3 |
| `p4_comparacao_de_cenarios.png` | P4: índice por cenário | §7, P4 |
| `p4_sensibilidade_percentual.png` | P4: uma dimensão por vez | §7, P4 |
| `p4_curvas_por_dimensao.png` | P4: índice × valor de cada dimensão | §7, P4 |

Observação sobre `p3_indice_do_cenario.png`: a legenda cobre o rótulo "74,4" da barra "Índice geral" (o valor consta no título do gráfico e no README). É um detalhe visual do notebook, mantido sem alteração para que a imagem corresponda ao código executado.

## O que ainda falta fornecer (8 capturas de tela)

**A. Capturas da interface do Colab** (tirar da execução já feita, sem reexecutar; se a sessão expirou, reexecute e capture)

| Arquivo sugerido | O que deve aparecer | Notebook / célula |
|---|---|---|
| `01_colab_pipeline_executado.png` | `VALIDAÇÃO CONCLUÍDA`, `linhas=3245 / colunas=13`, SHA-256 de bronze e prata, `Violações do domínio esperado: 0` | `PSP8_Pipeline_Bronze_Prata_Colab`, célula do `executar_pipeline` |
| `02_colab_remontagem_verificacao.png` | desmontagem (`Drive desmontado`), remontagem e `PERSISTÊNCIA VERIFICADA … Resultado: APROVADA` | mesmo notebook, células da seção 3 |
| `03_colab_resumo_manifesto.png` | licença `CC0: Public Domain`, versão, `coletado_em_utc`, os três SHA-256 e `Prata idêntica à bronze: True` | mesmo notebook, célula de resumo |
| `04_colab_analise_carga_prata.png` | execução usada, 3.245 registros, SHA-256 da prata, `Idêntica à v1 do Kaggle: True` | `PSP8_Analise_P1_P4`, célula de preparação |

**B. Capturas do Google Drive no navegador** (não podem ser substituídas por JSON)

| Arquivo sugerido | O que deve aparecer |
|---|---|
| `05_drive_pasta_execucao.png` | `MyDrive/UnB/PSP8/MVP_Viabilidade_Nova_Unidade/execucoes/<id>/` com `bronze/`, `prata/`, `evidencias/` e `analises/` visíveis, com o caminho na barra |
| `06_drive_evidencias_json.png` | pasta `evidencias/` com `manifesto_execucao.json`, `auditoria_qualidade.json` e `verificacao_persistencia.json` |
| `07_drive_analises.png` | pasta `analises/` com os PNGs e CSVs de P1–P4 |
| `08_repositorio_janela_anonima.png` | o repositório do GitHub aberto em janela anônima |

**C. Opcional:** os três JSONs da execução final, em `evidencias/json/`.

Não publique credenciais, tokens, e-mails nem dados privados nas capturas.

## Como referenciar as capturas no README

Depois de salvar os arquivos nesta pasta, na seção 10 do README troque "pendente" pelo nome do arquivo correspondente (por exemplo, `evidencias/05_drive_pasta_execucao.png`) e, se quiser, embuta a imagem com `![descrição](evidencias/05_drive_pasta_execucao.png)`.
