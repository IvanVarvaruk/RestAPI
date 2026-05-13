from locust import HttpUser, task, between


class LibraryUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        payload = {
            "username": "test_user",
            "password": "secure_password"
        }

        with self.client.post("/auth/login", data=payload, catch_response=True) as response:
            if response.status_code == 200:
                token = response.json().get("access_token")
                self.auth_headers = {"Authorization": f"Bearer {token}"}
            else:
                response.failure(f"Failed to log in: {response.status_code} - {response.text}")

    @task
    def get_books(self):
        if hasattr(self, 'auth_headers'):
            self.client.get("/books", headers=self.auth_headers)