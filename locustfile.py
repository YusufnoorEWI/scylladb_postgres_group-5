import random
from locust import HttpUser, task, between

# http://34.90.113.225:8080 postgres
# http://34.76.24.226:8080 scylla
class QuickstartUser(HttpUser):
    wait_time = between(5, 9)

    @task
    def index_page(self):
        user = self.client.post("/users/create")
        user_id = user.json()
        user_id = user_id["user_id"]
        self.client.post(f"/users/credit/add/{user_id}/100")
        order_id = self.client.post(f"/orders/create/{user_id}")
        order_id = order_id.json()["order_id"]

        item_1 = self.client.post(f"/stock/item/create/5")
        item_2 = self.client.post(f"/stock/item/create/10")

        item_id_1 = item_1.json()["item_id"]
        item_id_2 = item_2.json()["item_id"]

        self.client.post(f"/stock/add/{item_id_1}/5")
        self.client.post(f"/stock/add/{item_id_2}/5")

        self.client.post(f"/orders/addItem/{order_id}/{item_id_1}")
        self.client.post(f"/orders/addItem/{order_id}/{item_id_2}")
        self.client.post(f"/orders/addItem/{order_id}/{item_id_2}")

        self.client.post(f"/orders/checkout/{order_id}")
