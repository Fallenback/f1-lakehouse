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
Ainda que a coleta seja feita em um servidor próprio, enviei esses dados para um Bucket S3 na AWS. Assim, Databricks acessa os dados brutos para realizar a ingestão em nosso Lakehouse.

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

## Executando com Docker

### Pré-requisitos

Um arquivo `.env` na raiz do projeto com as credenciais:

```
AWS_KEY=...
AWS_SECRET_KEY=...
```

### 1. Exportar os certificados da rede

A rede corporativa faz inspeção de HTTPS e reassina o tráfego com um certificado
próprio. Esse certificado está no repositório do Windows, mas não na imagem Linux,
então sem ele o `pip` e as chamadas à AWS falham na validação SSL dentro do container.

```bash
python export_windows_certs.py --extra "C:\certs\unimedsc-ca.pem"
```

Isso grava um arquivo `.crt` por certificado em `certs/` (pasta ignorada pelo git),
que o Dockerfile registra com `update-ca-certificates`. **A verificação SSL continua
ligada** — estamos adicionando confiança, não desligando a validação.

Rode de novo sempre que os certificados da rede mudarem, e refaça o build.

### 2. Build

```bash
docker compose build
```

### 3. Coleta e envio

```bash
# Envia os parquets de data/ para o bucket S3
docker compose run --rm sender

# Regrava os Parquets existentes no S3 com timestamps em microssegundos
docker compose run --rm rewrite-parquets

# Coleta, envia e garante a compatibilidade dos timestamps em uma sÃ³ execuÃ§Ã£o
docker compose run --rm sender python main.py

# Coleta (o comando padrão cobre 2021-2023, corridas e sprints)
docker compose run --rm collect

# Coleta com outro intervalo
docker compose run --rm collect python collect.py --start 2024 --stop 2025 -m R S
```

A pasta `data/` é montada como volume, então os parquets gerados pelo `collect`
ficam visíveis no host e são consumidos pelo `sender`. O cache do fastf1 fica em
um volume nomeado e é preservado entre execuções.

### Por que o upload falhava (`ConnectionClosedError`)

Desde 2025 os SDKs da AWS enviam o corpo do upload no formato `aws-chunked`, com
o checksum num trailer no fim da requisição. O proxy da rede derruba a conexão
nesse formato — daí o `ConnectionClosedError` / `RemoteDisconnected`. O sintoma
engana: listar o bucket e consultar o Athena funcionam normalmente, só o upload
com conteúdo falha.

A correção é a variável `AWS_REQUEST_CHECKSUM_CALCULATION=when_required`, já
definida no `docker-compose.yml`. Com ela o checksum só é calculado quando a
operação exige e o upload volta a ser um `PUT` comum, que o proxy deixa passar.

Verificado neste projeto conferindo no bucket se o objeto chegou com o tamanho
correto, 3 tentativas em cada configuração: **0 de 3** no padrão, **3 de 3** com
a correção.

Se algum download (e não upload) apresentar o mesmo sintoma, o equivalente do
lado da resposta é `AWS_RESPONSE_CHECKSUM_VALIDATION=when_required`.
