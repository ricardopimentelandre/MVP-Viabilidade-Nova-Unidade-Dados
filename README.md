# MVP — Viabilidade de Nova Unidade de Infraestrutura de Dados

Sistema de Suporte à Decisão (SSD) para **triagem preliminar** de um cenário de nova unidade de infraestrutura de dados, comparando **custo, risco e prazo** com um histórico de projetos. Pipeline de dados em nuvem: **Kaggle → Google Colab (Python/Pandas) → Google Drive (bronze e prata) → análise P1–P4**.

| | |
|---|---|
| Disciplina | PSP8 — Departamento de Engenharia de Produção, Universidade de Brasília |
| Professor | André Luiz Marques Serrano |
| Trabalho | Individual · MVP: pipeline de dados em nuvem documentado em repositório público |
| Aluno | Ricardo Pimentel André |

> **Aviso sobre o escopo dos dados.** A base usada reúne **projetos genéricos de infraestrutura (estradas, pontes, edifícios, usinas, obras hídricas)**. **Não é uma amostra específica de data centers.** Os resultados são comparações relativas a essa distribuição: **não são probabilidade de viabilidade, previsão de sucesso nem certificação financeira.** A decisão final permanece humana.

**Estado da validação (leia antes dos resultados).** O **pipeline e o notebook de análise P1–P4 foram executados com sucesso no Google Colab** (relato do autor): coleta da versão 1, gravação de bronze e prata no Drive, Drive desmontado e remontado, 3.245 registros relidos, SHA-256 conferido e `Resultado: APROVADA`. Os números de P1–P4 abaixo foram calculados e conferidos **localmente sobre o mesmo CSV (mesmo SHA-256)**. As **capturas de tela e os gráficos da execução no Colab ainda não estão anexados** em [`evidencias/`](evidencias/LEIAME.md) (ver [Evidências](#10-evidências)).

## Sumário
1. [Objetivo, problema e perguntas](#1-objetivo-problema-e-perguntas) · 2. [Fonte, licença e coleta](#2-fonte-licença-e-coleta) · 3. [Plataforma e arquitetura](#3-plataforma-e-arquitetura) · 4. [Modelagem e catálogo](#4-modelagem-e-catálogo) · 5. [ETL e carga](#5-etl-e-carga) · 6. [Qualidade dos dados](#6-qualidade-dos-dados) · 7. [Resultados P1–P4](#7-resultados-p1p4) · 8. [Discussão geral e limitações](#8-discussão-geral-e-limitações) · 9. [Como reproduzir](#9-como-reproduzir) · 10. [Evidências](#10-evidências) · 11. [Autoavaliação](#11-autoavaliação) · 12. [Estrutura do repositório](#12-estrutura-do-repositório)

---

## 1. Objetivo, problema e perguntas

**Problema.** Decidir a implantação de uma nova unidade de infraestrutura de dados exige considerar orçamento, exposição a riscos e prazo. Comparar um cenário proposto com projetos históricos pode apoiar uma **triagem**: indicar quais dimensões merecem revisão antes do planejamento detalhado.

**Objetivo.** Construir e documentar um pipeline reprodutível em nuvem que colete uma base pública de projetos de infraestrutura, persista dados brutos e tratados, avalie a qualidade e produza análises que apoiem a priorização de verificações de custo, risco e prazo de um cenário proposto.

**Hipótese de uso.** Um índice transparente de exposição relativa, acompanhado de seus componentes e limitações, ajuda a identificar quais dimensões de um projeto hipotético merecem análise adicional. *Critério de refutação adotado na avaliação:* a hipótese seria enfraquecida se o índice não distinguisse cenários (por exemplo, se mudanças relevantes de custo, risco ou prazo não alterassem a faixa) ou se contradissesse de forma sistemática a classificação de viabilidade da própria base.

**Decisão apoiada.** Quais aspectos de custo, risco e prazo revisar antes de avançar para o planejamento detalhado.

**Perguntas de negócio** (documentadas em [`docs/planejamento_psp8.md`](docs/planejamento_psp8.md), mantidas íntegras):

| ID | Pergunta | Método |
|---|---|---|
| P1 | Qual é o comportamento histórico dos custos, riscos e prazos dos projetos? | Estatísticas descritivas, distribuições e correlações |
| P2 | Como um cenário de nova unidade se posiciona em relação a esse histórico? | Percentis empíricos de custo, risco e prazo |
| P3 | Qual é a exposição geral do cenário e quais revisões são recomendadas? | Média dos três percentis, faixas e recomendações por dimensão |
| P4 | Como alterações de custo, risco e prazo mudam a classificação e as recomendações? | Comparação de cenários e análise de sensibilidade |

**Premissas do índice (heurísticas do protótipo original, não validadas por especialistas):** custo, risco e prazo têm **pesos iguais**; percentil empírico = fração dos projetos históricos com valor **menor ou igual** ao do cenário (×100); índice = média dos três percentis; faixas **Favorável** (< 33), **Atenção** (33 a < 67) e **Crítica** (≥ 67); recomendação específica quando o percentil da dimensão é ≥ 67. Não há aprendizado de máquina.

**Ordem do trabalho (transparência).** O protótipo e a base já existiam antes da formalização das perguntas (veja [Autoavaliação](#11-autoavaliação)). O protótipo original está preservado em [`MVP_Viabilidade_Nova_Unidade_Dados.ipynb`](MVP_Viabilidade_Nova_Unidade_Dados.ipynb), sem alterações.

## 2. Fonte, licença e coleta

| Item | Registro |
|---|---|
| Base | *Engineering Project Cost Feasibility Dataset* — [`ziya07/engineering-project-cost-feasibility-dataset`](https://www.kaggle.com/datasets/ziya07/engineering-project-cost-feasibility-dataset) |
| Versão | **1** ("Initial release", 2025-07-28); o pipeline fixa `versions/1` |
| **Licença** | **CC0: Public Domain**, que permite redistribuição e uso derivado. Fonte: API pública do Kaggle (consulta em 2026-11-11). *Reconfirme na página do dataset antes da entrega.* |
| Formato original | CSV UTF-8, com cabeçalho; `Engineering_Cost_Feasibility_Dataset.csv` |
| Volume | 3.245 registros × 13 colunas; 261.932 bytes |
| SHA-256 | `a93b9f10f889c95145dc5bdae9894a42582bb04c51b3bd1817ef515ff5920dc6` (fonte = bronze = prata na execução do Colab) |
| Data da coleta | Execução de referência em **2026-11-11** (manifesto `20261111T004425Z_bc476d5a`, 00:44:25 UTC). O campo `coletado_em_utc` das execuções posteriores consta em cada `manifesto_execucao.json`. |
| Procedência | **Não documentada** pelo autor da base. Os dados podem ser sintéticos (hipótese sustentada por indícios em P1, não por documentação). |
| Coleta | Via `kagglehub` (download oficial, sem *web scraping*). |

**Ética e proteção de dados.** Nenhum atributo identifica pessoas (LGPD não se aplica a dados pessoais aqui). A licença CC0 permite redistribuição, mas **os dados não são versionados neste repositório** (`.gitignore` exclui CSVs): o pipeline os baixa da fonte. Nenhuma credencial é armazenada no código. Não foram usados dados de empresa.

## 3. Plataforma e arquitetura

**Google Colab (Python/Pandas) + Google Drive.** O enunciado permite plataformas além do Databricks. O **Google Drive é armazenamento de arquivos**; **não** é um *data warehouse* nem um banco gerenciado. O custo de operação não foi medido; a execução usou contas Google pessoais.

```
Kaggle (CC0, v1)
   │  kagglehub (versão fixada)
   ▼
Colab / Pandas ── auditoria de qualidade ── manifesto (hashes, versões, regras)
   │
   ├──► Drive: execucoes/<id>/bronze/    CSV original (cópia byte a byte)
   ├──► Drive: execucoes/<id>/prata/     tabela flat, 13 atributos
   ├──► Drive: execucoes/<id>/evidencias/ manifesto, auditoria, verificação de persistência
   └──► Drive: execucoes/<id>/analises/  tabelas e gráficos de P1–P4 (a partir da prata relida)
```

## 4. Modelagem e catálogo

Modelo **flat por conceito** (estilo *data lake*): uma tabela de projetos de infraestrutura, com `Project_ID` como chave natural. O **[catálogo de dados](catalogo/catalogo_dados.md)** descreve os 13 atributos (tipo, descrição, domínio, obrigatoriedade, linhagem), o diagrama do modelo e a cadeia de transformação. A fonte não publica dicionário de dados: onde a descrição ou o domínio é inferido, o catálogo diz **explicitamente a origem da regra** (documentada na fonte, observada na v1 ou convenção do projeto).

## 5. ETL e carga

Implementação: [`scripts/pipeline_etl_drive.py`](scripts/pipeline_etl_drive.py), executada pelo notebook [`notebooks/PSP8_Pipeline_Bronze_Prata_Colab.ipynb`](notebooks/PSP8_Pipeline_Bronze_Prata_Colab.ipynb).

| Etapa | Regra (explícita) |
|---|---|
| Extração | Download da versão 1 por `kagglehub`; exige exatamente um CSV. |
| Bronze | **Cópia byte a byte** do CSV; falha se o SHA-256 da cópia diferir da origem. |
| Prata | 13 colunas, mesma ordem e **todas as linhas**. Textos como `string`; numéricos por `to_numeric` (erro se houver valor inválido). **Sem imputação, deduplicação, padronização de chaves ou conversão de unidade.** Na execução observada, a **prata é idêntica à bronze byte a byte**: na prática, é uma cópia validada e tipada, o que o manifesto declara. |
| Releitura | Bronze e prata são relidas dos arquivos gravados e comparadas com os dados em memória. |
| Evidências | `manifesto_execucao.json` (licença, versão, tamanhos, datas, versões de Python/pandas, hashes, regras), `auditoria_qualidade.json` e `verificacao_persistencia.json`. |
| Persistência | O notebook **desmonta (com *flush*) e remonta o Drive**, e `verificar_persistencia` relê os arquivos, recalcula SHA-256, tamanhos e contagens, **refaz a auditoria** e compara com o manifesto. Falha se algo divergir. |

Cada execução cria uma pasta nova em `execucoes/<id>/`, sem sobrescrever as anteriores. Se uma execução não gravar os arquivos, o pipeline falha em vez de declarar sucesso.

## 6. Qualidade dos dados

Auditoria por atributo ([`auditar_prata`](scripts/pipeline_etl_drive.py)): **completude** (nulos, vazios), **unicidade** (ID e linhas), **conformidade** (domínio de validação), **consistência** (complexidade textual × numérica), **acurácia** (indícios: *outliers* por 1,5×IQR, só informativos) e **atualidade** (conjunto estático, sem dimensão temporal). **Nada é removido nem corrigido automaticamente.**

| Atributo | Domínio de validação (origem) | Observado na v1 | Problemas |
|---|---|---|---|
| `Project_ID` | `P` + 4 dígitos (observado) | P0001–P3245, 3.245 únicos | nenhum |
| `Project_Name` | 5 nomes (observado) | 679 / 659 / 651 / 633 / 623 | nenhum; **não identifica** o projeto |
| `Project_Type` | 5 tipos (observado) | 689 / 649 / 641 / 638 / 628 | nenhum |
| `Scope_Complexity` | Low, Medium, High (observado) | 1.063 / 1.094 / 1.088 | nenhum |
| `Estimated_Cost_USD` | > 0 (convenção) | 1.000.404–6.998.223 | nenhum |
| `Resource_Allocation_Score` | 0–100 inteiro (convenção) | 50–99 | nenhum |
| `Risk_Assessment_Score` | 0–100 inteiro (convenção) | 30–99 | nenhum |
| `Environmental_Impact_Score` | 0–100 inteiro (convenção) | 20–99 | nenhum |
| `Historical_Cost_Deviation_%` | ≥ 0 (convenção) | 0,00–10,00 | nenhum |
| `Stakeholder_Priority_Score` | **0–1** (observado; **não** 0–100) | 0,50–1,00 | nenhum (escala corrigida no código; veja abaixo) |
| `Time_Estimate_Days` | > 0 (convenção) | 120–599 | nenhum |
| `Feasibility_Label` | Feasible, Not Feasible, Borderline (documentado) | 1.931 / 823 / 491 | nenhum |
| `Scope_Complexity_Numeric` | {1, 2, 3} (observado) | mapeamento 1:1 com `Scope_Complexity` | nenhum |

**Resultado:** nenhum problema encontrado — **0 nulos, 0 IDs repetidos, 0 linhas duplicadas, 0 violações de domínio, 0 inconsistências de complexidade, 0 *outliers* por IQR** (calculado sobre o mesmo CSV, reproduzido localmente; a primeira execução no Colab confirmou nulos, duplicatas, mínimos, máximos, categorias e consistência). Como a base é aparentemente curada, não houve tratamento a fazer; o resultado "sem problemas" está demonstrado atributo a atributo, como pede o enunciado.

**Achados sobre o *pipeline*, não sobre a base.** A auditoria do próprio trabalho encontrou e corrigiu: (i) `Stakeholder_Priority_Score` era validado como escala 0–100, mas a base usa 0–1; (ii) testes com valores que não existem na base (rótulo "Medium", Stakeholder = 65), substituídos por linhas reais; (iii) a prova de persistência dependia de leitura possivelmente em cache, hoje conferida após desmontar e remontar o Drive.

## 7. Resultados P1–P4

Notebook: [`notebooks/PSP8_Analise_P1_P4.ipynb`](notebooks/PSP8_Analise_P1_P4.ipynb). Lê a **prata do Drive** (conferindo o SHA-256 contra o manifesto), gera as tabelas e gráficos e grava tudo em `execucoes/<id>/analises/`. Lógica em [`scripts/analise_ssd.py`](scripts/analise_ssd.py), com testes. **Cenário demonstrado (hipotético, do protótipo original):** custo US$ 5.500.000, risco 80/100, prazo 480 dias. Separamos o que é **resultado observado** do que é **interpretação** e do que é **premissa**.

### P1 — Comportamento histórico

| | Mín | Q1 | Mediana | Q3 | Máx | Média | Desvio | CV |
|---|---|---|---|---|---|---|---|---|
| Custo (US$) | 1.000.404 | 2.564.718 | 3.994.200 | 5.450.812 | 6.998.223 | 4.014.064 | 1.708.536 | 42,6 % |
| Risco (0–100) | 30 | 47 | 64 | 82 | 99 | 64,6 | 20,2 | 31,3 % |
| Prazo (dias) | 120 | 232 | 356 | 480 | 599 | 357,5 | 141,0 | 39,5 % |

**Observado:** as três distribuições são **simétricas e aproximadamente planas** (assimetria ≈ 0, média ≈ mediana), sem *outliers* por IQR; **não há correlação linear relevante** entre custo, risco e prazo (|r| < 0,02); as médias das três dimensões são praticamente iguais entre os rótulos Feasible, Not Feasible e Borderline. **Interpretação (hipótese):** esse perfil é típico de dados gerados artificialmente; a fonte não documenta a origem. **Resposta:** custo, risco e prazo se espalham de forma ampla e simétrica, sem projetos atípicos e sem correlação linear relevante entre si; "alto" ou "baixo" tem significado puramente posicional.

### P2 — Posição do cenário (percentis)

| Dimensão | Valor do cenário | Mediana histórica | Percentil | Projetos com valor ≤ ao do cenário |
|---|---|---|---|---|
| Custo | US$ 5.500.000 | 3.994.200 | **75,7** | 2.457 de 3.245 |
| Risco | 80 | 64 | **72,3** | 2.347 de 3.245 |
| Prazo | 480 dias | 356 | **75,1** | 2.438 de 3.245 |

**Resposta:** o cenário está **bem acima da mediana nas três dimensões**, perto do terceiro quartil (percentis 72–76), de forma equilibrada. *Cuidado:* o percentil é **posição relativa** na amostra; não é a probabilidade de o cenário ser viável ou inviável, e um percentil alto de custo ou prazo não implica, por si só, inviabilidade.

### P3 — Índice de exposição e recomendações

**Observado:** índice **74,4** (média de 75,7, 72,3 e 75,1) → faixa **Crítica**; cada dimensão contribui com cerca de um terço (33,9 % / 32,4 % / 33,7 %). Recomendações geradas (todas as dimensões ≥ 67): *revisar orçamento, fornecedores e criar reserva de contingência; elaborar plano formal de mitigação de riscos; dividir a implantação em etapas e acompanhar marcos críticos; não iniciar a implantação sem revisão do planejamento.*

Aplicado aos próprios projetos históricos, o índice os distribui em **Favorável 15,3 % · Atenção 67,9 % · Crítica 16,7 %** (índice médio 50,3); o índice do cenário é maior ou igual ao de **92,3 %** dos projetos históricos (**7,7 %** têm índice maior).

**Resultado negativo relevante.** **Não há associação descritiva relevante entre o índice e o `Feasibility_Label` da fonte**: índice médio 51,2 (Borderline), 50,2 (Feasible) e 49,9 (Not Feasible), e distribuição quase idêntica nas faixas (Crítica: 16,9 % / 17,3 % / 15,3 %). Isso não valida nem invalida o índice (o rótulo da fonte não é verdade de campo e sua geração não é documentada), mas mostra que, **nesta base, o índice não reproduz a classificação de viabilidade da fonte e não deve ser lido como previsão dela.**

**Resposta:** exposição geral **74,4 (Crítica)**, com revisão recomendada de custo, risco e prazo; é uma **triagem heurística**, não uma previsão. Pesos iguais e cortes 33/67 são **premissas**: com outros valores a faixa pode mudar.

### P4 — Sensibilidade

Cenários (hipotéticos e ilustrativos; índice e faixa):

| Cenário | Custo | Risco | Prazo | Índice | Faixa |
|---|---|---|---|---|---|
| Base | 5,5 mi | 80 | 480 | 74,4 | Crítica |
| A: custo −20 % | 4,4 mi | 80 | 480 | 68,2 | Crítica |
| B: risco 80 → 60 | 5,5 mi | 60 | 480 | 65,3 | Atenção |
| C: prazo −20 % | 5,5 mi | 80 | 384 | 68,0 | Crítica |
| D: A + B + C | 4,4 mi | 60 | 384 | 52,7 | Atenção |
| E: piora de 20 % | 6,6 mi | 96 | 576 | 94,6 | Crítica |
| F: perfil mediano | 3,99 mi | 64 | 356 | 50,1 | Atenção |

Variando **uma dimensão por vez** em −20 %: índice 68,2 (custo), 67,0 (risco; 66,985 → Atenção, faixa decidida sem arredondar) e 67,9 (prazo): queda de 6,2 a 7,4 pontos. **Pontos de virada** (maior valor que mantém o índice < 67, com as demais fixas): custo ≈ US$ 4,22 mi (−23,2 %), risco 64 (−20,0 %), prazo 370 dias (−22,9 %). **Nenhuma redução isolada leva a Favorável** (< 33; o mínimo alcançável é ≈ 49–51). Medindo em desvios-padrão (comparável entre dimensões), ±1 desvio move o índice de 64,6–64,9 a 82,5–83,6 nas três dimensões: **nenhuma domina**. Varrendo cada dimensão pela faixa observada, a curva é praticamente linear (r ≥ 0,9998).

**Interpretação:** com pesos iguais e dimensões sem correlação linear relevante e de distribuição plana, o índice reage de modo aproximadamente simétrico; ele **não indica qual alavanca priorizar** (isso depende do custo de agir em cada dimensão, informação que a base não traz). **Resposta:** reduções isoladas de ~20 % aproximam o cenário da fronteira Crítica/Atenção sem torná-lo Favorável; combinar reduções nas três dimensões leva a Atenção com folga. A análise é determinística (sem incerteza estatística), os cenários são escolhas nossas e pesos diferentes mudariam as conclusões.

## 8. Discussão geral e limitações

**Solução do problema.** Em relação ao histórico da base, o cenário é **alto nas três dimensões** (percentis 72–76; índice 74,4, Crítica); a triagem sugere revisar custo, risco e prazo antes do planejamento detalhado e mostra que reduções isoladas de ~20 % não bastam para torná-lo favorável. **Hipótese:** parcialmente sustentada — o índice distingue cenários e muda de faixa com variações relevantes (não foi refutada pelo critério da seção 1), mas **não reproduz o rótulo de viabilidade da fonte** e **não indica por si só onde agir**.

**Limitações dos dados.** Projetos genéricos (não data centers); procedência não documentada e indícios de dado sintético (distribuições planas, ausência de correlação linear relevante entre as dimensões) — hipótese; sem dimensão temporal; sem dicionário de dados (sentido do risco, escalas dos escores e unidade do custo são premissas); `Feasibility_Label` sem critério documentado.

**Limitações do método.** Percentil é posição relativa, não probabilidade; pesos iguais e cortes 33/67 são heurísticas não validadas; cenários e variações de P4 são ilustrativos; a análise é determinística e não quantifica incerteza; não há ML.

## 9. Como reproduzir

**Na nuvem (Google Colab + Drive do próprio usuário):**
1. Abra `notebooks/PSP8_Pipeline_Bronze_Prata_Colab.ipynb` ([abrir no Colab](https://colab.research.google.com/github/ricardopimentelandre/MVP-Viabilidade-Nova-Unidade-Dados/blob/psp8-etapa-2-pipeline/notebooks/PSP8_Pipeline_Bronze_Prata_Colab.ipynb)) e use **Executar tudo**. Autorize o Drive (duas vezes: montagem inicial e remontagem). Resultado esperado: `Resultado: APROVADA` e uma nova pasta em `MyDrive/UnB/PSP8/MVP_Viabilidade_Nova_Unidade/execucoes/<id>/`.
2. Abra `notebooks/PSP8_Analise_P1_P4.ipynb` ([abrir no Colab](https://colab.research.google.com/github/ricardopimentelandre/MVP-Viabilidade-Nova-Unidade-Dados/blob/psp8-etapa-2-pipeline/notebooks/PSP8_Analise_P1_P4.ipynb)) e use **Executar tudo**. Ele usa a execução verificada mais recente e grava `analises/` na mesma pasta.

Os notebooks baixam os scripts da branch `psp8-etapa-2-pipeline`; para uma entrega final, fixe a URL em um commit validado.

**Testes locais** (não substituem a execução no Drive): com Python 3.10+ e `pandas`,
```bash
python -m unittest discover -s tests -v
# opcional, com o CSV real da v1:  PSP8_CSV_REAL=/caminho/Engineering_Cost_Feasibility_Dataset.csv python -m unittest discover -s tests -v
```

## 10. Evidências

Os arquivos JSON (manifesto, auditoria e verificação) são gerados pelo código e ficam no Drive em `execucoes/<id>/evidencias/`. **Nenhuma imagem de evidência foi simulada**: as capturas da execução real no Colab e no Drive devem ser salvas em [`evidencias/`](evidencias/LEIAME.md), que traz a lista exata, os nomes de arquivo e o trecho do README a ativar em cada caso.

| Evidência | Situação |
|---|---|
| Pipeline executado no Colab: 3.245 registros relidos, SHA-256 de fonte, bronze e prata iguais a `a93b9f10…`, `Resultado: APROVADA` | **Executado e confirmado pelo autor.** Manifesto e auditoria da primeira execução (`20261111T004425Z_bc476d5a`) conferidos nos JSONs; **captura da interface: pendente** |
| Drive desmontado e remontado antes da releitura | **Executado e confirmado pelo autor;** captura da célula: pendente |
| Notebook de análise P1–P4 executado no Colab | **Executado com sucesso (relato do autor);** gráficos e saídas ainda **não anexados** |
| Pasta `execucoes/<id>/` no Drive, com `bronze/`, `prata/`, `evidencias/` e `analises/` | **Pendente** (captura no navegador) |
| Repositório aberto em janela anônima | **Pendente** (o repositório responde como público na API do GitHub) |

**Pendências efetivas:** (1) anexar as capturas e os gráficos listados em [`evidencias/LEIAME.md`](evidencias/LEIAME.md); (2) reconfirmar a licença CC0 na página do dataset; (3) decidir a licença do código (`LICENSE`); (4) conferir o repositório em janela anônima e postar o link no fórum da disciplina.

## 11. Autoavaliação

**Quais perguntas foram respondidas e quais não foram? Por quê?** As quatro foram **respondidas tecnicamente** (P1–P4, seção 7), com as ressalvas de que as respostas são **descritivas e heurísticas**: P2 e P3 posicionam o cenário em relação ao histórico, mas **não** estimam probabilidade de viabilidade; P4 mostra a sensibilidade do índice, mas **não** indica qual alavanca priorizar. A hipótese foi apenas **parcialmente sustentada**: o índice distingue cenários, mas não reproduz o rótulo de viabilidade da base. O pipeline e o notebook P1–P4 foram executados no Colab; as capturas da execução ainda precisam ser anexadas ao repositório.

**Que limitações dos dados condicionaram os resultados?** Projetos genéricos de infraestrutura (não data centers); procedência não documentada e indícios de dado sintético (distribuições planas e ausência de correlação linear relevante entre as dimensões), o que torna o índice quase simétrico; ausência de dicionário de dados (sentido do risco, escalas e unidades são premissas); rótulo de viabilidade sem critério documentado; ausência de dimensão temporal.

**Que decisões técnicas eu tomaria de outra forma?** (i) Definir o problema e as perguntas **antes** de escolher a base — o enunciado alerta para esse erro e aqui a base e o protótipo vieram primeiro; (ii) escolher uma base **específica de data centers**, com procedência documentada; (iii) confrontar o pipeline com os **dados reais desde o início** (a escala de `Stakeholder_Priority_Score` foi assumida como 0–100 e só corrigida na auditoria); (iv) fixar a versão da fonte e o *hash* desde a primeira execução; (v) provar a persistência no Drive por remontagem e captura de tela já na primeira carga; (vi) avaliar o Databricks, plataforma com apoio da disciplina.

**Que extensões transformariam o MVP em uma solução de uso contínuo?** Base com dados reais de projetos de data centers e *refresh* agendado; pesos e cortes elicitados com especialistas (por exemplo, AHP) e calibrados contra resultados reais; quantificação de incerteza (intervalos, simulação); formato colunar (Parquet) e catálogo/linhagem automáticos; monitoramento de qualidade em cada carga; interface para o gestor informar cenários; e, só depois, modelos preditivos validados.

**Dificuldades encontradas.** Base sem documentação dos atributos; garantir que a releitura vinha do Drive e não de *cache* local; domínio incorreto de um atributo que passou despercebido por testes com valores artificiais; limitação de comprovar a execução em nuvem sem capturas.

## 12. Estrutura do repositório

| Caminho | Conteúdo |
|---|---|
| `README.md` | Este documento |
| `MVP_Viabilidade_Nova_Unidade_Dados.ipynb` | Protótipo original (preservado, sem alterações) |
| `notebooks/PSP8_Pipeline_Bronze_Prata_Colab.ipynb` | Coleta, ETL, carga no Drive e verificação de persistência |
| `notebooks/PSP8_Analise_P1_P4.ipynb` | Análise P1–P4 a partir da prata relida |
| `scripts/pipeline_etl_drive.py` · `scripts/analise_ssd.py` | Rotinas de ETL/qualidade e de análise |
| `tests/` | Testes automatizados (dados sintéticos com linhas reais; testes opcionais com o CSV real) |
| `catalogo/catalogo_dados.md` | Catálogo de dados, modelo e linhagem |
| `docs/` | Planejamento aprovado e instruções de execução da Etapa 2 (parcialmente desatualizadas em relação a este README) |
| `evidencias/` | Capturas de tela e gráficos da execução no Colab/Drive ([lista do que falta](evidencias/LEIAME.md)) |
| `.gitignore` | Exclui dados, credenciais, ambientes virtuais e arquivos locais |

**Licença.** Dados: CC0 (fonte). **Licença do código: ainda não definida** — o arquivo `LICENSE` pedido no enunciado está pendente de escolha do autor.
