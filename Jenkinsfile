pipeline {
    agent any

    environment {
        // ====================================================================
        AWS_REGION         = 'us-east-1'
        AWS_ACCOUNT_ID     = credentials('aws-account-id')
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
                
                withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials', passwordVariable: 'DOCKER_PAT', usernameVariable: 'DOCKER_USER')]) {
                    
                    // 1. Faz o login no Docker Hub (já sabemos que isso está funcionando!)
                    sh 'echo $DOCKER_PAT | docker login -u $DOCKER_USER --password-stdin'
                    
                    // 2. Instala o plugin do Docker Scout direto no Jenkins de forma rápida
                    sh 'curl -sSfL https://raw.githubusercontent.com/docker/scout-cli/main/install.sh | sh -s --'
                    
                    // 3. Roda o Scout nativamente (ele vai ler o login feito no passo 1 automaticamente)
                    sh "docker scout cves --exit-code --only-severity critical,high ${IMAGE_NAME}:latest"
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
                sh """
                # 0. Limpa resquícios de execuções anteriores, se houver
                docker rm -f locust-runner || true
                
                # 1. Cria o container usando a pasta /tmp (que permite gravação por qualquer usuário)
                docker create --name locust-runner \\
                  --network host \\
                  -w /tmp \\
                  locustio/locust -f /tmp/locustfile.py \\
                  --headless \\
                  -u 50 -r 10 \\
                  --run-time 30s \\
                  --host http://localhost:${STAGING_PORT} \\
                  --html=/tmp/locust_report.html \\
                  --exit-code-on-error 1
                
                # 2. Copia o arquivo Python para a pasta /tmp do container
                docker cp locustfile.py locust-runner:/tmp/locustfile.py
                
                # 3. Inicia o container e captura o resultado
                set +e
                docker start -a locust-runner
                LOCUST_EXIT=\$?
                set -e
                
                # 4. Resgata o relatório visual HTML de volta para o Jenkins
                docker cp locust-runner:/tmp/locust_report.html ./locust_report.html || true
                
                # 5. Destrói o container do Locust
                docker rm -f locust-runner || true
                
                # 6. Informa ao Jenkins o resultado final
                exit \$LOCUST_EXIT
                """
            }
        }

        stage('7. Promotion (Push para AWS ECR)') {
            steps {
                echo '📦 Testes aprovados! Promovendo imagem para a AWS...'
                script {
                    // Puxa as chaves do cofre do Jenkins
                    withCredentials([[
                        $class: 'AmazonWebServicesCredentialsBinding', 
                        credentialsId: "${AWS_CREDENTIALS_ID}", 
                        accessKeyVariable: 'AWS_ACCESS_KEY_ID', 
                        secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                    ]]) {
                        
                        // 1. Usa o container oficial da AWS para gerar o token e repassa para o docker login
                        sh """
                        docker run --rm -i \
                          -e AWS_ACCESS_KEY_ID=\$AWS_ACCESS_KEY_ID \
                          -e AWS_SECRET_ACCESS_KEY=\$AWS_SECRET_ACCESS_KEY \
                          amazon/aws-cli ecr get-login-password --region ${AWS_REGION} | \
                          docker login --username AWS --password-stdin ${ECR_REGISTRY}
                        """
                        
                        //2. Etiqueta a imagem com o número da execução do Jenkins (Ex: v7)
                        sh "docker tag ${IMAGE_NAME}:latest ${ECR_REGISTRY}/${ECR_REPO_NAME}:v${BUILD_NUMBER}"
                        // E também atualiza a latest para quem quiser sempre a última
                        sh "docker tag ${IMAGE_NAME}:latest ${ECR_REGISTRY}/${ECR_REPO_NAME}:latest"

                        // 3. Manda ambas para a nuvem
                        sh "docker push ${ECR_REGISTRY}/${ECR_REPO_NAME}:v${BUILD_NUMBER}"
                        sh "docker push ${ECR_REGISTRY}/${ECR_REPO_NAME}:latest"
                    }
                }
            }
        }
        
        stage('8. Deploy no ECS (Atualização do Site)') {
            steps {
                echo '🔄 Avisando o ECS para atualizar o container...'
                script {
                    withCredentials([[
                        $class: 'AmazonWebServicesCredentialsBinding', 
                        credentialsId: 'aws-credentials-id', 
                        accessKeyVariable: 'AWS_ACCESS_KEY_ID', 
                        secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                    ]]) {
                        // Força o gerente do ECS a matar o container antigo e puxar a nova imagem 'latest'
                        sh """
                        docker run --rm \
                          -e AWS_ACCESS_KEY_ID=\$AWS_ACCESS_KEY_ID \
                          -e AWS_SECRET_ACCESS_KEY=\$AWS_SECRET_ACCESS_KEY \
                          amazon/aws-cli ecs update-service \
                          --cluster hms-cluster-dev \
                          --service hms-portfolio-service-dev \
                          --force-new-deployment \
                          --region ${AWS_REGION}
                        """
                    }
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