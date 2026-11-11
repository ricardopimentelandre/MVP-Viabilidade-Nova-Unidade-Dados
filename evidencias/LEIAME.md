# Evidências da execução em nuvem

Esta pasta guarda as **capturas de tela e os gráficos reais** que comprovam a execução no Google Colab e a persistência no Google Drive (enunciado §5.2). As imagens devem estar **legíveis** e ser **referenciadas no README**, no ponto que sustentam.

**Situação em 11/11/2026: nenhuma imagem foi anexada ainda.** O pipeline e o notebook de análise P1–P4 foram executados com sucesso no Colab (relato do autor), mas as capturas e os gráficos dessa execução não estavam acessíveis ao assistente. **Nada aqui foi simulado**: não há imagens geradas fora do Colab/Drive passando por evidência.

## O que falta fornecer

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

**C. Gráficos reais do notebook P1–P4** (baixe do Drive, de `execucoes/<id>/analises/`, para `evidencias/graficos/`, mantendo os nomes)

`p1_histogramas.png` · `p2_percentis_do_cenario.png` · `p3_indice_do_cenario.png` · `p3_indice_historico.png` · `p4_comparacao_de_cenarios.png` · `p4_sensibilidade_percentual.png` · `p4_curvas_por_dimensao.png`

**D. Opcional:** os três JSONs da execução final, em `evidencias/json/`.

Não publique credenciais, tokens, e-mails nem dados privados nas capturas.

## Como referenciar no README depois de salvar os arquivos

Cole no README, na seção 7 (Resultados P1–P4), apenas as linhas dos arquivos que existirem:

```markdown
![P1 – distribuições históricas](evidencias/graficos/p1_histogramas.png)
![P2 – posição do cenário](evidencias/graficos/p2_percentis_do_cenario.png)
![P3 – índice do cenário](evidencias/graficos/p3_indice_do_cenario.png)
![P4 – comparação de cenários](evidencias/graficos/p4_comparacao_de_cenarios.png)
![P4 – sensibilidade](evidencias/graficos/p4_sensibilidade_percentual.png)
```

E, na seção 10, troque "pendente" por o nome do arquivo correspondente (por exemplo, `evidencias/05_drive_pasta_execucao.png`).
