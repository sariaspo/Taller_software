import os
import uuid

from locust import HttpUser, task, between


escenario = os.getenv("LOCUST_SCENARIO", "load")

esperas = {
    "load": between(1, 3),
    "stress": between(0, 0.5),
    "capacity": between(1, 2),
}

if escenario not in esperas:
    raise ValueError("LOCUST_SCENARIO debe ser load, stress o capacity")

PER_PAGE = int(os.getenv("LOCUST_PER_PAGE", "50"))
params = {"page": 1, "per_page": PER_PAGE}


def revisar_lista(resp, campos):
    if resp.status_code != 200:
        resp.failure(f"Esperaba 200 y llegó {resp.status_code}")
        return

    try:
        body = resp.json()
    except ValueError:
        resp.failure("La respuesta no es JSON")
        return

    data = body.get("data")
    if not isinstance(data, list):
        resp.failure("Falta el arreglo 'data'")
        return

    if len(data) > PER_PAGE:
        resp.failure("Llegaron más registros que per_page")
        return

    for item in data:
        if not all(c in item for c in campos):
            resp.failure("Hay registros sin los campos requeridos")
            return

    resp.success()


class Usuario(HttpUser):
    wait_time = esperas[escenario]

    @task(5)
    def listado(self):
        with self.client.get("/api/users", params=params,
                             name="GET /api/users", catch_response=True) as resp:
            revisar_lista(resp, ["id", "name", "email"])

    @task(3)
    def correos(self):
        with self.client.get("/api/users/emails", params=params,
                             name="GET /api/users/emails", catch_response=True) as resp:
            revisar_lista(resp, ["id", "email"])

    @task(2)
    def mayores_de_veinte(self):
        with self.client.get("/api/users/over-twenty", params=params,
                             name="GET /api/users/over-twenty", catch_response=True) as resp:
            revisar_lista(resp, ["id", "birth_date"])

    @task(1)
    def alta_lote(self):
        # El uuid evita correos repetidos entre usuarios virtuales
        lote = uuid.uuid4().hex
        fechas = ["1998-05-12", "2000-11-03", "1995-01-20"]

        usuarios = []
        for i, fecha in enumerate(fechas, start=1):
            usuarios.append({
                "name": f"Locust User {i}",
                "email": f"locust-{lote}-{i}@example.com",
                "birth_date": fecha,
            })

        with self.client.post("/api/users/bulk", json={"users": usuarios},
                              name="POST /api/users/bulk", catch_response=True) as resp:
            if resp.status_code != 201:
                resp.failure(f"Esperaba 201 y llegó {resp.status_code}")
                return

            try:
                creados = resp.json().get("users", [])
            except ValueError:
                resp.failure("La respuesta no es JSON")
                return

            if len(creados) != 3:
                resp.failure(f"Esperaba 3 usuarios y llegaron {len(creados)}")
            else:
                resp.success()