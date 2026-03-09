from locust import HttpUser, task, between

class PortfolioUser(HttpUser):
    # Simula o tempo de espera "humano" entre cliques (1 a 3 segundos)
    wait_time = between(1, 3)

    @task(3)
    def load_home(self):
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 500:
                response.failure("Erro 500: Internal Server Error na Home!")
            elif response.elapsed.total_seconds() > 0.5:
                response.failure(f"SLA Violado na Home: {response.elapsed.total_seconds():.3f}s")
            else:
                response.success()

    @task(1)
    def download_cv(self):
        # Rota exata do currículo no seu Flask
        with self.client.get("/static/docs/curriculo.pdf", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Falha ao baixar CV! Código retornado: {response.status_code}")
            else:
                response.success()