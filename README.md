# Muni Stop Monitor

Fetches real-time Muni arrival predictions from the [511 Transit API](https://511.org/open-data/transit) every minute and stores them in PostgreSQL for analysis and visualization in Grafana.

See [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for full architecture and schema details.

---

## Local development (Docker Compose)

**Prerequisites:** Docker, a 511.org API key

```bashe
echo "API_KEY=your-key-here" > .env
make up
```

Grafana is available at http://localhost:3000 with the **Muni Stop 13911** dashboard pre-loaded.

| Command | Effect |
|---|---|
| `make up` | Build and start everything |
| `make down` | Stop containers, keep data |
| `make wipe` | Stop containers, delete all data |
| `make logs` | Tail fetcher logs |

---

## Kubernetes deployment (Argo Workflows)

```bash
kubectl apply -f namespace.yaml
kubectl apply -f secret.yaml        # fill in API_KEY + DB_PASSWORD first
kubectl apply -f postgres-deployment.yaml
kubectl apply -f grafana-deployment.yaml
kubectl apply -f workflow-rbac.yaml
kubectl apply -f muni-cronworkflow.yaml
```

Copy `secret.yaml.example` to `secret.yaml` and fill in your credentials before applying.

---

## Configuration

| Env var | Default | Description |
|---|---|---|
| `API_KEY` | *(required)* | 511.org API key |
| `STOP_CODE` | `13911` | Muni stop to monitor |
| `AGENCY` | `SF` | Transit agency |
| `DB_HOST` | `localhost` | Postgres host |
| `DB_NAME` | `muni` | Postgres database |
| `DB_USER` | `muni` | Postgres user |
| `DB_PASSWORD` | `munipass` | Postgres password |
