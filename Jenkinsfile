pipeline {
    agent any

    environment {
        // ====================================================================
        AWS_REGION         = 'us-east-1'
        AWS_ACCOUNT_ID     = '365916940374'
        ECR_REPO_NAME      = 'meu-portfolio'
        ECR_REGISTRY       = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        AWS_CREDENTIALS_ID = 'aws-credentials-id'
        // ====================================================================
        
        IMAGE_NAME         = 'hms-portfolio-flask'
        STAGING_PORT       = '5001'
    }

    stages {
        stage('1. Checkout') {
            steps {
                echo '📥 Baixando código da Pipeline de Testes (CI/CD)...'
                checkout scm
                
                echo '📥 Baixando código fonte da Aplicação...'
                // Remove a pasta app antiga (se existir) para evitar conflitos
                sh 'rm -rf app || true'
                // Clona o seu repositório da aplicação para dentro da pasta "app"
                sh 'git clone https://github.com/henrique-mozart-de-souza/meu_portfolio.git app'
            }
        }

        stage('2. Linting (Hadolint)') {
            steps {
                echo '🔎 Inspecionando Dockerfile em busca de más práticas...'
                // Entra na pasta da aplicação para rodar a análise
                dir('app') {
                    sh 'docker run --rm -i hadolint/hadolint < Dockerfile'
                }
            }
        }

        stage('3. Build') {
            steps {
                echo '🏗️ Construindo a imagem Docker da aplicação...'
                // Entra na pasta da aplicação para fazer o build
                dir('app') {
                    sh "docker build -t ${IMAGE_NAME}:latest ."
                }
            }
        }

        stage('4. Security Scan (Docker Scout)') {
            steps {
                echo '🛡️ Autenticando no Docker Hub e varrendo vulnerabilidades...'
                
                // Abre o cofre e puxa as variáveis de usuário e senha
                withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials', passwordVariable: 'DOCKER_PAT', usernameVariable: 'DOCKER_USER')]) {
                    
                    // Faz o login no motor Docker do Ubuntu usando as credenciais do cofre
                    sh 'echo $DOCKER_PAT | docker login -u $DOCKER_USER --password-stdin'
                    
                    // Roda o Scout mapeando o arquivo de autenticação gerado (.docker) para dentro do container
                    sh "docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v /var/jenkins_home/.docker:/root/.docker docker/scout-cli cves --exit-code --only-severity critical,high ${IMAGE_NAME}:latest"
                }
            }
        }

        stage('5. Staging Deploy') {
            steps {
                echo '🚀 Subindo container temporário para testes de carga...'
                sh "docker rm -f staging-portfolio || true"
                sh "docker run -d --name staging-portfolio -p ${STAGING_PORT}:5000 ${IMAGE_NAME}:latest"
                sleep 5 
            }
        }

        stage('6. Load Test (Locust)') {
            steps {
                echo '🔥 Iniciando ataque de estresse no container Staging e gerando artefatos...'
                // Como o locustfile.py está na raiz do CI/CD, NÃO usamos o dir('app') aqui!
                sh """
                docker run --rm \
                  --network host \
                  -v \${PWD}:/mnt -w /mnt \
                  locustio/locust -f locustfile.py \
                  --headless \
                  -u 50 -r 10 \
                  --run-time 30s \
                  --host http://localhost:${STAGING_PORT} \
                  --html=locust_report.html \
                  --exit-code-on-error 1
                """
            }
        }

        stage('7. Promotion (Push para AWS ECR)') {
            steps {
                echo '📦 Testes aprovados! Promovendo imagem para a AWS...'
                script {
                    echo "⚠️ (Simulado) Push para o ECR ignorado até configurarmos o Account ID."
                }
            }
        }
    }

    post {
        always {
            echo '🧹 Limpando o ambiente de Staging...'
            sh "docker rm -f staging-portfolio || true"
            
            echo '📊 Salvando relatório visual de performance (HTML)...'
            archiveArtifacts artifacts: 'locust_report.html', allowEmptyArchive: true
        }
        success {
            echo '✅ Pipeline concluído com sucesso! Imagem pronta para Produção.'
        }
        failure {
            echo '❌ Pipeline falhou. Verifique os logs da etapa que quebrou.'
        }
    }
}