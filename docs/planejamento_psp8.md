# PSP8 — Planejamento e perguntas de negócio do MVP

**Projeto:** Sistema de Suporte à Decisão para Avaliação de Viabilidade de Nova Unidade de Infraestrutura de Dados  
**Base de referência:** [Engineering Project Cost Feasibility Dataset](https://www.kaggle.com/datasets/ziya07/engineering-project-cost-feasibility-dataset) (Kaggle)  
**Documento de avaliação:** `TRAB SSD EP UNB.pdf`, Prof. André Luiz Marques Serrano, Engenharia de Produção/UnB  
**Status deste documento:** proposta aprovada para a evolução do MVP; implementação, resultados e evidências ainda sujeitos a validação.

## 1. Contexto, problema e objetivo

Decisões de implantação de uma nova unidade de infraestrutura de dados exigem considerar orçamento, exposição a riscos e prazo de implantação. A comparação com projetos históricos pode apoiar uma **triagem preliminar**, indicando dimensões que merecem revisão antes de uma decisão de investimento.

**Objetivo:** desenvolver e documentar um pipeline reprodutível de dados em nuvem que colete uma base de projetos de infraestrutura, persista dados brutos e tratados, avalie sua qualidade e produza análises para apoiar a priorização de verificações de custo, risco e prazo de um cenário proposto.

A base contém projetos de infraestrutura em geral, **não uma amostra específica de data centers**. Consequentemente, as conclusões são comparações relativas à distribuição da base; não representam certificação de viabilidade financeira, previsão de sucesso ou probabilidade estatística de inviabilidade.

**Hipótese de uso do MVP:** um índice transparente de exposição relativa, acompanhado de seus componentes e limitações, ajuda a identificar quais dimensões de um projeto hipotético merecem análise adicional.

**Decisão apoiada:** quais aspectos de custo, risco e prazo devem ser revisados antes de avançar para o planejamento detalhado. A decisão final permanece humana.

## 2. Perguntas de negócio aprovadas

Estas perguntas orientam **a evolução do notebook existente**. O protótipo inicial e sua base já existiam antes desta formalização; não se afirma que as perguntas precederam a primeira implementação.

| ID | Pergunta | Método e evidência esperada | Situação inicial |
|---|---|---|---|
| P1 | Qual é o comportamento histórico dos custos, riscos e prazos dos projetos? | Estatísticas descritivas (mínimo, máximo, média, mediana, quartis e dispersão), com interpretação das distribuições. | Parcialmente implementada no notebook original. |
| P2 | Como um cenário de nova unidade se posiciona em relação a esse histórico? | Percentis empíricos separados para custo, risco e prazo, calculados sobre os dados tratados e persistidos. | Implementada no notebook original, ainda sem pipeline persistente. |
| P3 | Qual é a exposição geral do cenário e quais revisões são recomendadas? | Média dos três percentis, classificação em faixas e recomendações por dimensão, com justificativa dos critérios adotados. | Implementada como regra heurística no notebook original. |
| P4 | Como alterações de custo, risco e prazo mudam a classificação e as recomendações? | Comparação reproduzível de cenários e análise de sensibilidade de cada dimensão. | **Ainda não implementada**; faz parte da expansão aprovada. |

### Premissas explícitas do índice

No protótipo original, custo, risco e prazo têm **pesos iguais**. Para um valor `v`, o percentil empírico é a fração dos registros históricos com valor menor ou igual a `v`, multiplicada por 100. O índice é a média dos três percentis.

As faixas originais são `Favorável` (índice abaixo de 33), `Atenção` (de 33 até abaixo de 67) e `Crítica` (a partir de 67). Esses pesos e cortes são **hipóteses de projeto, não limiares validados por especialistas ou evidência de desempenho financeiro**. O índice mede exposição relativa ao benchmark escolhido; percentil alto de custo ou prazo não significa, por si só, inviabilidade.

## 3. Arquitetura técnica aprovada (a implementar e comprovar)

1. **Origem / coleta:** obter a base pública `ziya07/engineering-project-cost-feasibility-dataset` via `kagglehub` no Python/Google Colab; registrar URL, versão quando disponível, data efetiva da coleta, licença/termos e metadados do arquivo.
2. **Camada bronze (Google Drive):** gravar cópia verificável do CSV original com contagem de linhas, colunas e hash. Não confundir cache temporário do Colab com persistência na nuvem.
3. **Qualidade e transformação (Colab/Pandas):** auditar **todos os 13 atributos** quanto a nulos, unicidade, tipos, domínios, consistência e valores potencialmente implausíveis. Registrar decisões de transformação; nunca substituir ou apagar observações silenciosamente.
4. **Camada prata (Google Drive):** persistir um conjunto **flat por conceito**, com atributos tipados e regras documentadas. A versão inicial manterá os 13 atributos da fonte, salvo necessidade técnica justificada na auditoria.
5. **Validação de carga:** reler a prata **do Drive**; verificar esquema, contagens, restrições e consistência dos dados usados nas análises. Registros de execução e hashes servirão como evidências auxiliares.
6. **Análise e SSD (Colab):** responder P1–P4 a partir dos dados da prata relida; gerar tabelas, gráficos, comparação de cenários e recomendações compreensíveis. Explicitar limitações e interpretação de cada resposta.
7. **Documentação e evidências:** manter README com objetivo, perguntas, etapas de execução e respostas; criar catálogo com tipo, significado, domínio, obrigatoriedade e linhagem por atributo; guardar evidências legíveis da execução em nuvem e dos resultados.

A plataforma escolhida é **Google Colab + Google Drive**, permitida pelo enunciado. O Google Drive atuará como armazenamento de arquivos; não deve ser descrito como um Data Warehouse gerenciado ou banco de dados analítico.

## 4. Critérios de conclusão da implementação

- [ ] Coleta executável e documentada, inclusive licença e data efetiva.
- [ ] Bronze e prata comprovadamente gravadas **e relidas** do Google Drive.
- [ ] Modelo flat, catálogo de dados completo e linhagem documentada.
- [ ] Qualidade examinada para cada atributo, com resultados e tratamento de achados.
- [ ] Regras de ETL reproduzíveis, com testes e logs de integridade.
- [ ] Quatro perguntas respondidas por evidências, com interpretação e limites; eventuais perguntas não respondidas são mantidas e discutidas.
- [ ] Cenários alternativos e sensibilidade realmente executados e demonstrados.
- [ ] README organizado, evidências reais, ética/licença e autoavaliação.
- [ ] Repositório público verificável e checklist do enunciado revisado.

A matriz de avaliação publicada no enunciado atribui: objetivo 1,0; coleta 0,5; modelagem 2,0; carga 1,0; análise 3,0; autoavaliação 0,5; capricho 2,0 pontos.

## 5. Controle de escopo e etapas de validação

**Fora do escopo desta etapa:** mudanças no notebook original, publicação de resultados ainda não calculados, apresentação de eficácia em data centers reais e afirmações de que o pipeline já foi executado em nuvem.

As entregas avançarão após revisão do usuário:
- **Etapa 1 — Documento de planejamento e perguntas:** este arquivo, em branch de trabalho.
- **Etapa 2 — Pipeline e armazenamento:** implementação do fluxo Kaggle → Colab → Drive (bronze/prata) com testes.
- **Etapa 3 — Análise e SSD:** perguntas P1–P4, qualidade, cenários, recomendações e evidências.
- **Etapa 4 — Documentação e auditoria:** catálogo, README, autoavaliação, reproduzibilidade e validação do enunciado.
- **Etapa 5 — Short paper:** redigir somente depois dos resultados auditados.
- **Etapa 6 — Apresentação:** PowerPoint, roteiro didático e notas do apresentador, alinhados ao short paper.

> **Ponto de controle:** este documento registra a proposta e o trabalho previsto, **não comprova a execução técnica**. A branch de revisão não deve ser mesclada à `main` antes da validação.
