# Evidências da execução em nuvem

Esta pasta guarda as **capturas de tela e os gráficos reais** que comprovam a execução no Google Colab e a persistência no Google Drive (enunciado §5.2). Tudo aqui é da execução real; **nada foi simulado**. As imagens são referenciadas no README (seções 7 e 10).

## Já anexado

### Capturas de tela (`capturas/`)

Execução do pipeline: `20261111T213507Z_0ef8b8d7`. Execução cuja prata foi usada em P1–P4: `20261111T195017Z_c1039983`. Os dois SHA-256 coincidem (`a93b9f10f889c95145dc5bdae9894a42582bb04c51b3bd1817ef515ff5920dc6`).

| Arquivo | Mostra | Execução |
|---|---|---|
| `01_colab_pipeline_executado.png` | `VALIDAÇÃO CONCLUÍDA`, 3.245 × 13, SHA-256 de bronze e prata, 0 violações do domínio | `…213507Z_0ef8b8d7` |
| `02_colab_remontagem_verificacao.png` | Drive desmontado (flush), remontado e `Resultado: APROVADA` | `…213507Z_0ef8b8d7` |
| `03_colab_resumo_manifesto.png` | licença CC0, `coletado_em_utc`, três SHA-256, prata idêntica à bronze, hash igual ao da v1 | `…213507Z_0ef8b8d7` |
| `04_colab_analise_carga_prata.png` | notebook P1–P4 carregando a prata (3.245 / 13, SHA-256 idêntico à v1) | `…195017Z_c1039983` |
| `06_drive_evidencias_json.png` | pasta `evidencias/` no Drive com os três JSONs | `…213507Z_0ef8b8d7` |

Observação sobre a captura 03: `versão baixada: None`. No Colab o `kagglehub` usa o cache local (`/kaggle/input/...`), cujo caminho não traz o número da versão; a versão 1 foi solicitada e é confirmada pelo hash (`Hash confere com a v1 documentada: True`).

### Gráficos de P1–P4 (`graficos/`)

`p1_histogramas.png` · `p2_percentis_do_cenario.png` · `p3_indice_do_cenario.png` · `p3_indice_historico.png` · `p4_comparacao_de_cenarios.png` · `p4_sensibilidade_percentual.png` · `p4_curvas_por_dimensao.png` (saídas do notebook `PSP8_Analise_P1_P4`, baixadas de `execucoes/<id>/analises/`).

Observação sobre `p3_indice_do_cenario.png`: a legenda cobre o rótulo "74,4" da barra "Índice geral" (o valor consta no título do gráfico e no README). É um detalhe visual do notebook, mantido sem alteração para que a imagem corresponda ao código executado.

## O que ainda falta

**Captura 05** (única pendente): `05_drive_pasta_execucao.png`, salva em `capturas/`. Deve mostrar, no navegador, a pasta `MyDrive/UnB/PSP8/MVP_Viabilidade_Nova_Unidade/execucoes/20261111T213507Z_0ef8b8d7/` com as subpastas `bronze/`, `prata/` e `evidencias/` visíveis e o caminho na barra de navegação. Depois de salva, no README (seção 10) troque "Pendente" da linha 05 pelo link do arquivo e, se quiser, embuta a imagem com `![05 — Pasta da execução no Drive](evidencias/capturas/05_drive_pasta_execucao.png)`.

Não publique credenciais, tokens, e-mails, abas, favoritos nem dados privados nas capturas (recorte a janela do navegador, se necessário). A visibilidade pública do repositório foi conferida pelo autor em janela anônima; essa captura não será publicada.
