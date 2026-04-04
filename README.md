# ⚙️ HMS Cloud - Continuous Integration & Deployment (Multi-Pipeline GitOps)

Este repositório contém a inteligência de automação, os Portões de Qualidade (Quality Gates) e a orquestração completa do projeto HMS Cloud. Para garantir a segurança, integridade e estabilidade do portfólio, adotamos um modelo de Multi-Pipeline GitOps, segregando responsabilidades em três fluxos distintos e orquestrados pelo Jenkins.

A arquitetura de CI/CD foi desenhada para falhar rápido (fail-fast), garantindo que apenas código validado, imagens de container seguras e infraestrutura aprovada cheguem ao ambiente de produção na AWS.

---

## 🔄 Workflow Multi-Pipeline (Quality Gates)

O orquestrador orquestra três pipelines principais, cada uma com gatilhos e objetivos específicos. A sincronização entre elas é feita de forma automatizada.

Diagramas:

![alt text](docs/download.png)



### 1. Pipeline de Infraestrutura as Code (IaC) - HMS-Infra-Deploy:

Gatilho: Execução manual via interface do Jenkins ou git push no repositório portifolio_infra.
Objetivo: Provisionar, atualizar e manter toda a fundação da infraestrutura na AWS (Camada de Rede/VPC, Security Groups, IAM Roles, repositório ECR e a infraestrutura do ECS).

1. **Terraform Init & Validate:**T Inicializa o backend de estado no S3 e valida a sintaxe estrutural dos módulos Terraform.
2. **Terraform Plan:** Gera o plano de execução exato, detalhando quais recursos serão criados, modificados ou destruídos na AWS.
3. **Gatekeeper (Aprovação Manual):** O pipeline pausa e aguarda aprovação humana na interface do Jenkins. Essa trava garante que o deploy não ocorra às cegas e permite a revisão dos custos e arquitetura antes da aplicação.
4. **Terraform Apply:** Aplica as mudanças aprovadas de forma automatizada, construindo a infraestrutura real na AWS, deixando o terreno pronto para receber a aplicação.


### 2. Pipeline de Código de Aplicação - HMS-Cloud-Deploy:

Gatilho: git push no repositório meu_portfolio.
Objetivo: Executar os Quality Gates de código, realizar os testes e promover a imagem Docker final para a AWS.

1. **Checkout & Linting:** Clone do repositório da aplicação e análise estática do Dockerfile (via Hadolint). Más práticas de containerização detectadas interrompem o pipeline imediatamente.
2. **Build:** Construção da imagem Docker (hms-portfolio-flask) baseada no commit mais recente.
3. **Security Scan (Docker Scout):** Varredura profunda na imagem recém-construída. O pipeline é abortado se vulnerabilidades de nível Crítico ou Alto forem encontradas.
4. **Staging Deploy: A imagem aprovada é colocada em execução em um ambiente efêmero (temporário) dentro do próprio servidor Ubuntu Admin.
5. **Load Test (Locust):** Ataque de estresse automatizado contra o container temporário. O pipeline falha se o tempo de resposta exceder 500ms ou se houver erros 500 (Internal Server Error).
6. **Promotion (Push to ECR):** Com todos os testes passando, o Jenkins faz o login na AWS e executa o push da imagem validada (:latest) para o Amazon ECR, disponibilizando-a para o consumo do Cluster ECS.



### 3. Pipeline de Limpeza e Controle de Custos - HMS-Infra-Destroy

Gatilho: Execução estritamente manual (O "Botão Vermelho").
Objetivo: Destruir de forma segura e automatizada todos os recursos provisionados na nuvem para garantir zero custos na fatura da AWS quando o ambiente não estiver em uso.

1. **Terraform Init:** Prepara e sincroniza o ambiente lendo o estado atual da infraestrutura.
2. **Terraform Plan (Destroy):** Mapeia todos os recursos atrelados ao workspace atual que estão agendados para exclusão.
3. **Gatekeeper (Confirmação de Destruição):** Trava de segurança crítica que exige confirmação explícita do administrador no Jenkins, evitando a exclusão acidental do ambiente ativo.
1. **Terraform Destroy:** Comunica-se com as APIs da AWS para apagar sistematicamente instâncias EC2, redes VPC, repositórios ECR e clusters ECS, limpando a conta por completo.

---

## 🛠️ Pré-requisitos e Arquitetura do Orquestrador

O Jenkins roda de forma isolada em uma máquina administrativa (Ubuntu Admin). Para que o container do Jenkins consiga "buildar" outras imagens Docker, utilizamos a arquitetura Docker-out-of-Docker (DooD), mapeando o arquivo de soquete /var/run/docker.sock do hospedeiro.

* Servidor Ubuntu configurado com Docker Engine.
* Credenciais da AWS (Access Key e Secret Key) com permissões administrativas para gerenciar S3, EC2, ECS, ECR e IAM via Terraform.
* Repositório ECR previamente criado na AWS.
* Plugins do Jenkins necessários: Pipeline, Docker Pipeline, AWS Credentials, Amazon Web Services SDK.

---

## 📂 Estrutura do Repositório

Esta é a organização dos artefatos de infraestrutura e testes de carga deste projeto:

```text
portifolio_CI_CD/
├── .gitignore               # Proteção contra vazamento de variáveis e arquivos locais
├── docker-compose.yml       # Declaração do serviço Jenkins em arquitetura DooD
├── Dockerfile.jenkins       # Imagem customizada do Jenkins com Docker CLI e AWS CLI embutido
├── Jenkinsfile              # Pipeline Declarativo Principal (Código da Aplicação)
├── Jenkinsfile-Infra        # Pipeline Declarativo de IaC (Terraform) com Aprovação Manual
├── Jenkinsfile-ECS-Restart # Pipeline Declarativo de Rolling Update Automatizado
├── locustfile.py            # Script Python para simulação de carga e testes de SLA
├── README.md                # Documentação principal
└── docs/
    └── multi_pipeline_gitops.png # Diagrama visual do workflow Multi-Pipeline
```

---

## 🚀 Como Usar (Subindo o Orquestrador)

Siga os passos abaixo no seu servidor Ubuntu Admin para iniciar a infraestrutura do Jenkins:

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/henrique-mozart-de-souza/portifolio_CI_CD.git](https://github.com/henrique-mozart-de-souza/portifolio_CI_CD.git)
   cd portifolio_CI_CD
   ```

2. **Inicie o Jenkins (com build da imagem DooD):**

```bash
docker-compose up -d --build
```

3. **Recupere a senha inicial de Administrador:**
* O Jenkins gera uma senha de segurança no primeiro boot. Pegue-a rodando o comando abaixo:

```bash
docker exec hms-jenkins-dood cat /var/jenkins_home/secrets/initialAdminPassword
```

4. **Acesse a Interface Web:**

* Abra o navegador e acesse http://<IP_DO_SEU_UBUNTU>:8080. Cole a senha recuperada no passo anterior para iniciar a instalação dos plugins sugeridos.


* Desenvolvido com automação extrema por Henrique Mozart de Souza.