# Execução Local do SageMaker para Validação de Embeddings

## 1. Contexto da Tarefa

Esta tarefa tem como objetivo viabilizar a execução e validação local de um endpoint SageMaker, de forma a permitir testes de integração do projeto **Longinus** sem dependência direta da infraestrutura AWS.

Atualmente, o projeto consome embeddings semânticos gerados por um endpoint SageMaker em produção. No entanto, para desenvolvimento local, testes automatizados e experimentação, é necessário garantir que:

- O modelo de embeddings possa ser executado localmente;
- A interface de comunicação seja compatível com o contrato esperado pelo SageMaker;
- O restante da stack (Search, Longinus, testes) consiga consumir esse endpoint sem alterações significativas.

O foco desta iniciativa **não é replicar integralmente o SageMaker**, mas sim **simular o comportamento essencial do endpoint** de inferência.

## 2. Motivação

Os principais problemas observados antes desta tarefa eram:

- Forte acoplamento entre código de aplicação e endpoint SageMaker remoto;
- Dificuldade de rodar testes de integração localmente;
- Dependência de credenciais AWS mesmo em cenários de desenvolvimento;
- Pouca previsibilidade do comportamento do modelo durante mudanças na stack.

Essa limitação impacta diretamente:
- Produtividade do time;
- Confiabilidade dos testes;
- Velocidade de iteração em features que dependem de embeddings.

## 3. Escopo da Solução

A solução proposta se baseia nos seguintes princípios:

- Execução **local** do modelo de embeddings;
- Comunicação via HTTP seguindo o **contrato do SageMaker**;
- Orquestração da stack via **Docker Compose**;
- Mínima necessidade de mudanças no código do projeto consumidor.

O objetivo é garantir que, do ponto de vista do Longinus/Search, **não haja diferença perceptível entre o endpoint local e o endpoint em nuvem**.

## 4. Ajustes Necessários na Stack

### 4.1 Containerização do Modelo

O modelo de embeddings passa a ser executado em um container dedicado, responsável por:

- Carregar o modelo na inicialização;
- Expor endpoints compatíveis com o SageMaker:
  - `/ping` (health check);
  - `/invocations` (inferência).

Esse container **não depende da imagem oficial do SageMaker**, mas implementa apenas o comportamento mínimo esperado, reduzindo complexidade e tempo de build.


### 4.2 Contrato de Comunicação

Foi mantido o mesmo contrato utilizado em produção:

- Requisição via `POST`;
- Payload em JSON contendo o campo `search_term`;
- Resposta contendo o vetor de `embedding`.

Essa decisão garante:
- Compatibilidade total com o código existente;
- Nenhuma bifurcação de lógica entre ambiente local e produção;
- Facilidade para testes automatizados.


### 4.3 Orquestração via Docker Compose

Toda a stack local passa a ser iniciada via `docker-compose`, incluindo:

- Serviço do modelo de embeddings;
- Serviços dependentes (Search, Longinus, etc.).

Com isso:
- A stack pode ser iniciada com um único comando;
- A configuração de portas, redes e dependências fica centralizada;
- Facilita onboarding e execução em CI local.

### 4.4 Configuração de Ambiente

Alguns ajustes de configuração são necessários:

- Substituição do nome do endpoint SageMaker por uma URL local;
- Externalização dessas configurações via variáveis de ambiente;
- Evitar dependência de credenciais AWS em ambiente local.

Esse isolamento garante que:
- O código seja o mesmo para todos os ambientes;
- A diferença entre local e produção seja apenas **configuracional**.

## 5. Impacto nos Testes

Com essa abordagem, torna-se possível:

- Executar testes de integração localmente;
- Validar que o modelo responde corretamente com embeddings;
- Garantir que falhas de contrato sejam detectadas cedo;
- Rodar pipelines de teste sem acesso à AWS.

Os testes deixam de validar apenas lógica interna e passam a cobrir também:
- Serialização/deserialização;
- Comunicação HTTP;
- Comportamento real do modelo.

## 6. Benefícios Esperados

- Redução de custo operacional;
- Aumento da confiabilidade dos testes;
- Menor dependência de infraestrutura externa;
- Feedback mais rápido durante o desenvolvimento;
- Base sólida para futuras automações em CI/CD.

---

## 7. Considerações Finais

A adoção de um SageMaker local simplificado representa um avanço importante na maturidade da stack, aproximando o desenvolvimento local do comportamento real de produção, sem o ônus de complexidade ou custo adicional.

Essa abordagem favorece práticas modernas de engenharia, como testes de integração reais, ambientes reprodutíveis e menor acoplamento com infraestrutura específica.


####




# Execução Local do SageMaker para Validação de Embeddings (Longinus)

## 1. Contexto da Tarefa

Esta tarefa viabiliza a execução local de um endpoint de inferência no **formato SageMaker**, permitindo validar que o modelo responde com embeddings e habilitando testes de integração do **Longinus** sem dependência direta de um endpoint na AWS.

A proposta é executar localmente o container de inferência (imagem oficial do SageMaker) e apontar a stack (via `docker-compose`) para esse endpoint local, mantendo o contrato `/ping` e `/invocations`.

---

## 2. Motivação

Os principais ganhos esperados com o SageMaker local são:

- Reduzir acoplamento com infraestrutura AWS durante desenvolvimento;
- Permitir smoke tests e testes de integração localmente;
- Validar contrato do endpoint (payload/response) cedo, antes de chegar em produção;
- Melhorar reprodutibilidade e onboarding.

---

## 3. Abordagem de Stack

A abordagem adotada usa a **imagem oficial do SageMaker PyTorch Inference**, hospedada no **AWS ECR**.

Isso traz duas implicações diretas na stack:

1. **É necessário autenticar no ECR** para baixar a imagem;
2. A execução local do container deve montar o diretório do “modelo” (`/opt/ml/model`) contendo o `inference.py` e dependências do runtime.

---

## 4. Pré-requisitos

- AWS CLI configurada e funcional (credenciais válidas);
- Acesso ao ECR público/privado correspondente (neste caso, ECR da conta do SageMaker);
- Podman instalado (ou Docker, se aplicável ao ambiente);
- Estrutura local contendo o artefato do modelo e o script `inference.py`.

---

## 5. Autenticação e Pull da Imagem (ECR)

### 5.1 Validar credenciais AWS

```bash
aws sts get-caller-identity

5.2 Login no ECR (us-east-1)

aws ecr get-login-password --region us-east-1 \
| podman login \
  --username AWS \
  --password-stdin 763104351884.dkr.ecr.us-east-1.amazonaws.com

5.3 Baixar imagem de inferência do SageMaker (PyTorch)

podman pull 763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-inference:2.1.0-cpu-py310-ubuntu20.04-sagemaker

6. Execução do Container (SageMaker Local)

A execução local segue o padrão do SageMaker container:

- expõe HTTP na porta 8080;
- usa SAGEMAKER_PROGRAM para indicar o entrypoint de inferência (inference.py);
- monta o diretório local em /opt/ml/model (onde o SageMaker espera encontrar o modelo e o código).

6.1 Exemplo (modelo em ./local_model)

podman run --rm -p 8080:8080 \
  -e SAGEMAKER_PROGRAM=inference.py \
  -e SAGEMAKER_SUBMIT_DIRECTORY=/opt/ml/model/code \
  -e SAGEMAKER_CONTAINER_LOG_LEVEL=20 \
  -e SAGEMAKER_REGION=us-east-1 \
  -v "$(pwd)/local_model:/opt/ml/model:Z" \
  763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-inference:2.1.0-cpu-py310-ubuntu20.04-sagemaker \
  serve

6.2 Exemplo (modelo em ./src/sagemaker)

podman run --rm -p 8080:8080 \
  -e SAGEMAKER_PROGRAM=inference.py \
  -e SAGEMAKER_SUBMIT_DIRECTORY=/opt/ml/model/code \
  -e SAGEMAKER_CONTAINER_LOG_LEVEL=20 \
  -e SAGEMAKER_REGION=us-east-1 \
  -v "$(pwd)/src/sagemaker:/opt/ml/model:Z" \
  763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-inference:2.1.0-cpu-py310-ubuntu20.04-sagemaker \
  serve

7. Smoke Tests do Endpoint (Contrato SageMaker)

Em outro terminal:

7.1 Healthcheck

curl -i http://localhost:8080/ping

7.2 Inferência (embedding)

curl -i -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"search_term":"geladeira frost free 375 litros"}'

Critério mínimo esperado:

- status 200;
- resposta JSON contendo o campo embedding (lista de floats).

8. Ajustes Necessários no docker-compose da Stack

8.1 Objetivo

Permitir que os serviços do projeto (ex.: Longinus) “vejam” o endpoint local de embeddings sem mudança de lógica — apenas por configuração.

8.2 Principais ajustes recomendados

a) Incluir um serviço sagemaker-local no compose

- Responsável por expor 8080;
- Opcionalmente, já rodar com a imagem do ECR (quando a autenticação do ambiente permitir);
- Montar o diretório do modelo/código.

b) Rede interna e DNS

Ao invés de localhost:8080, dentro do compose os serviços devem referenciar o host pelo nome do serviço:
http://sagemaker-local:8080

c) Variáveis de ambiente no serviço consumidor (Longinus/Search)

- Trocar EndpointName/config de endpoint AWS por uma URL configurável em ambiente local;
- Evitar exigir AWS credentials quando rodando em modo local.

d) Healthcheck + depends_on

- Adicionar healthcheck no serviço sagemaker-local usando /ping;
- Configurar depends_on (com condição de saúde) no serviço que consome embeddings para reduzir flakiness na subida.
