#F1 Lake

Coletar, armazenar, processar dados de Fórmula 1 para construção de análises e modelos preditivos.

Apresentação
Etapas do projeto
Coleta
Envio dos Dados
Camada Bronze
Camada Silver
Camada Gold
Treinamento do Modelo
Aplicação para usuário


Coleta
Utilizei a biblioteca FastF1 como fonte de dados, a partir de scripts em Python para realizar a coleta das informações históricas.

Esta etapa é executada em um servidor próprio de maneira agendada.

Envio dos dados
Ainda que a coleta seja feita em um servidor próprio, enviei esses dados para um Bucket S3 na AWS. Assim, a Nekt acessa os dados brutos para realizar a ingestão em nosso Lakehouse.

Em termos de camada de dados, ela nos serve de camada raw, ou camada de dados brutos.

Camada Bronze
Na camada bronze, os dados estão consolidados em formato Delta com histórico de modificações, facilitando suas consulta. Além disso, tem uma representação fiel de como este dado poderia ser encontrado em sua origem.

Camada Silver
A partir dos dados na camada anterior, já dentro do Lakehouse, foram realizadas novas modelagens de dados e também criação de Feature Stores com o histórico de cada entidade de nosso interesse.

Camada Gold
Aqui, deixei apenas tabelas em formatos de relatórios e dados sumarizados para que sejam facilmente analisados e conectados em ferramentas de BI/dashboards.

Treinamento do Modelo
Utilizando dados das Feature Store e eventos de interesse, gerei uma Analytical Base Table (ABT) para treinar nossos algoritmos de Machine Learning.

Os modelos são treinados e comparados localmente, fazendo uso do MLFlow hospedado em nosso servidor próprio.

Aplicação para usuário
Com o modelo treinado, podemos criar uma aplicação onde entusiastas de Fórmula 1 poderão acompanhar as predições do modelo.
