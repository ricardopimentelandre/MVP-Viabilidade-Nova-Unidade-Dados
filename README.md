# MVP – Viabilidade de Nova Unidade de Dados

Este projeto apresenta um Mínimo Produto Viável (MVP) de um **Sistema de Suporte à Decisão** para apoiar a implantação de uma nova unidade de infraestrutura de dados.

## Objetivo

Avaliar um novo projeto com base em três dimensões principais:

- **Custo estimado**
- **Risco do projeto**
- **Prazo de implantação**

## Base de dados

Foi utilizado o dataset **Engineering Project Cost Feasibility Dataset**, disponível no Kaggle, com 3.245 projetos de infraestrutura.

Como a base não é específica de data centers, ela foi utilizada como referência histórica geral para comparação de custo, risco e prazo.

## Funcionamento do MVP

O sistema compara os valores informados para uma nova unidade com os projetos históricos da base.

Cada dimensão é convertida em um percentil de exposição e, em seguida, é calculado um índice geral com pesos iguais para custo, risco e tempo.

O projeto é classificado como:

- **Favorável**
- **Atenção**
- **Crítico**

Além da classificação, o sistema apresenta recomendações para apoiar o planejamento da implantação.

## Cenário demonstrado

No exemplo utilizado no notebook:

- Custo estimado: **US$ 5.500.000**
- Risco: **80/100**
- Prazo: **480 dias**

O índice geral calculado foi de **74,4%**, classificando o cenário como **Crítico**.

## Arquivo principal

`MVP_Viabilidade_Nova_Unidade_Dados.ipynb`
