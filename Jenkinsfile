pipeline {
    agent any

    environment {
        // ====================================================================
        // 🚨 CONFIGURAÇÕES DO AWS ECR (PREENCHA ESTES DADOS POSTERIORMENTE) 🚨
        // ====================================================================
        AWS_REGION         = 'us-east-1'
        AWS_ACCOUNT_ID     = 'COLOQUE_SEU_ACCOUNT_ID_AQUI'
        ECR_REPO_NAME      = 'meu-portfolio'
        ECR_REGISTRY       = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        AWS_CREDENTIALS_ID = 'aws-credentials-id' // Criaremos essa credencial na interface do Jenkins depois
        // ====================================================================
        
        IMAGE_NAME         = 'hms-portfolio-flask'
        STAGING_PORT       = '5001' // Porta que o ambiente temporário vai usar no seu Ubuntu
    }

    stages {
        stage('1. Checkout') {
            steps {
                echo '📥 Baixando código fonte do repositório da aplicação...'
                // Aqui o Jenkins vai clonar o seu repo 'meu_portfolio'
                checkout scm
            }
        }

        stage('2. Linting (Hadolint)') {
            steps {
                echo '🔎 Inspecionando Dockerfile em busca de más práticas...'
                // Roda um container efêmero do Hadolint para validar o seu Dockerfile
                sh 'docker run --rm -i hadolint/hadolint < Dockerfile'
            }
        }

        stage('3. Build') {
            steps {
                echo '🏗️ Construindo a imagem Docker da aplicação...'
                sh "docker build -t ${IMAGE_NAME}:latest ."
            }
        }

        stage('4. Security Scan (Docker Scout)') {
            steps {
                echo '🛡️ Varrendo imagem atrás de vulnerabilidades Críticas/Altas...'
                // O --exit-code aborta o pipeline se achar falhas graves
                sh "docker run --rm -v /var/run/docker.sock:/var/run/docker.sock docker/scout-cli cves --exit-code --only-severity critical,high ${IMAGE_NAME}:latest"
            }
        }

        stage('5. Staging Deploy') {
            steps {
                echo '🚀 Subindo container temporário para testes de carga...'
                // Derruba qualquer container de staging antigo que tenha ficado travado
                sh "docker rm -f staging-portfolio || true"
                // Sobe o container validado na porta 5001
                sh "docker run -d --name staging-portfolio -p ${STAGING_PORT}:5000 ${IMAGE_NAME}:latest"
                // Aguarda 5 segundos para o Gunicorn/Flask iniciar
                sleep 5 
            }
        }

        stage('6. Load Test (Locust)') {
            steps {
                echo '🔥 Iniciando ataque de estresse no container Staging...'
                // Roda o Locust usando um container efêmero na mesma rede do hospedeiro
                sh """
                docker run --rm \
                  --network host \
                  -v \${PWD}:/mnt -w /mnt \
                  locustio/locust -f locustfile.py \
                  --headless \
                  -u 50 -r 10 \
                  --run-time 30s \
                  --host http://localhost:${STAGING_PORT} \
                  --exit-code-on-error 1
                """
            }
        }

        stage('7. Promotion (Push para AWS ECR)') {
            steps {
                echo '📦 Testes aprovados! Promovendo imagem para a AWS...'
                script {
                    // Este bloco fará o login na AWS, "tageará" a imagem e fará o Push.
                    // ATENÇÃO: Ele falhará até preenchermos as variáveis do ECR no topo.
                    /*
                    withCredentials([[
                        $class: 'AmazonWebServicesCredentialsBinding', 
                        credentialsId: "${AWS_CREDENTIALS_ID}", 
                        accessKeyVariable: 'AWS_ACCESS_KEY_ID', 
                        secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                    ]]) {
                        sh "aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}"
                        sh "docker tag ${IMAGE_NAME}:latest ${ECR_REGISTRY}/${ECR_REPO_NAME}:latest"
                        sh "docker push ${ECR_REGISTRY}/${ECR_REPO_NAME}:latest"
                    }
                    */
                    echo "⚠️ (Simulado) Push para o ECR ignorado até a configuração das credenciais."
                }
            }
        }
    }

    post {
        always {
            echo '🧹 Limpando o ambiente de Staging...'
            sh "docker rm -f staging-portfolio || true"
        }
        success {
            echo '✅ Pipeline concluído com sucesso! Imagem pronta para Produção.'
        }
        failure {
            echo '❌ Pipeline falhou. Verifique os logs da etapa que quebrou.'
        }
    }
}