# Architecture — News Sentiment Bias Analyzer

**Repo root:** `news-bias-analyzer/`  
**Doc siblings:** `api-contract.md`, `data-contract.md`  
**Stack:** Chrome Extension (MV3) → FastAPI → NLP/ML → Prometheus → Grafana Cloud  
**Quality gates:** Great Expectations (validation), Evidently (data/model drift)

---

## 1) System Goal (one line)
Analyze a news article’s topic across multiple outlets and show **bias distribution (Left/Center/Right)** and **sentiment trends** in a Chrome extension, with production-grade validation and monitoring.

---

## 2) High-Level Diagram

```
[ User Browser ]
      │
      ▼ (tab URL, title)
[ Chrome Extension (MV3) ]
      │  POST /api/v1/analyze
      ▼
[ FastAPI Backend ] ─────────────┐
  ├─ Router: /analyze             │
  ├─ Services: clustering, bias   │
  ├─ GE: data validation          │
  ├─ Metrics: /metrics (Prom)     │
  └─ Config: configs/*.yaml       │
                                 ▼
                       [ NLP / ML Layer ]
                        ├─ Embeddings (Sentence-BERT style)
                        ├─ Clustering (HDBSCAN/KMeans)
                        ├─ Sentiment (VADER/transformer)
                        └─ Bias map lookup (AllSides/Ad Fontes)
                                 │
                                 ▼
                        [ Processed Outputs ]
                        ├─ bias_distribution {L,C,R}
                        ├─ average_sentiment
                        └─ sources[] with per-outlet scores
                                 │
                                 ├──────────► [ Evidently ]
                                 │              ├─ Drift report (HTML/JSON)
                                 │              └─ Prometheus gauges
                                 │
                                 └──────────► [ Prometheus ]
                                                │  remote_write
                                                ▼
                                          [ Grafana Cloud ]
```

---

## 3) Core Components & Responsibilities

### 3.1 Chrome Extension (MV3)
- **Files:** `extension/manifest.json`, `popup.html/js`, `content_script.js`, `background.js`
- **Responsibility:** Capture page context (URL/title), call backend, render bias chart and sentiment summary.
- **Privacy note:** Do not store browsing history; send only current tab URL, optional title.

### 3.2 FastAPI Backend
- **Files:** `src/app/api/main.py`, `routers/analyze.py`, `health.py`
- **Responsibilities:** 
  - Validate inputs (Pydantic schemas).
  - Fetch/aggregate related articles (by topic/url).
  - Call ML services for embeddings → clustering → sentiment → bias mapping.
  - Enforce **data contracts** via Great Expectations before scoring.
  - Expose Prometheus metrics at `/metrics`.

### 3.3 ML/NLP Layer
- **Files:** `src/ml/{data,features,models,utils,drift}`
- **Responsibilities:**
  - `data/fetch_articles.py`: external API calls (News API/Bing) and normalization.
  - `features/sentiment.py`: sentiment scoring (VADER or transformer).
  - `models/rank_bias.py`: compute bias distribution using outlet bias maps (`resources/bias_maps/*`).
  - `utils/vectorizer.py`: embeddings (Sentence-BERT-compatible clients).
  - `drift/evidently_runner.py`: periodic drift reports (HTML/JSON).
  - `drift/evidently_exporter.py`: Prometheus gauges for drift metrics.

### 3.4 Data Validation — Great Expectations
- **Files:** `validation/great_expectations/*`
- **Responsibility:** Schema, types, ranges (e.g., URL validity, ISO dates, sentiment in −1..1).  
- **Contract:** see `docs/data-contract.md` → enforced pre-ML.

### 3.5 Monitoring — Prometheus + Grafana Cloud + Evidently
- **Files:** `infra/monitoring/prometheus.yml`, `infra/grafana/dashboards/bias_dashboard.json`
- **Responsibility:** 
  - Prometheus scrapes `/metrics` (FastAPI & Evidently exporter).
  - `remote_write` to Grafana Cloud → dashboards & alerts.
  - Evidently produces drift metrics and full HTML reports.

---

## 4) Data Flow (Step-by-Step)

1) **Extension event**  
   - User lands on an article.  
   - Extension reads `window.location.href`, `document.title`.

2) **API request**  
   - `POST /api/v1/analyze` with `{ url, title?, source? }` (see `api-contract.md`).

3) **Ingestion & Validation**  
   - Backend fetches similar/related articles into a dataframe.  
   - Great Expectations validates:
     - Required fields present (`url`, `title`, `published_at`).
     - URLs valid; timestamps ISO 8601; row count bounds; optional bias label enum.

4) **Feature & Modeling**  
   - Embeddings (Sentence-BERT style) → cluster by topic.  
   - Map outlets to bias via `resources/bias_maps/*`.  
   - Sentiment scoring (headline/body).  
   - Aggregate into **bias_distribution** and **average_sentiment**.

5) **Response**  
   - Return JSON to extension: `{ bias_distribution, average_sentiment, sources[] }`.  
   - If articles < 3 → `204 No Content` with reason.

6) **Monitoring & Drift**  
   - Evidently nightly job compares **current vs reference** (e.g., last week).  
   - Export gauges:
     - `data_drift_share`
     - `sentiment_drift_score`  
   - Prometheus scrapes; Grafana visualizes & alerts.

---

## 5) Contracts & Interfaces

- **Data contract:** `docs/data-contract.md`  
  - Raw & processed schemas, validation rules, drift storage locations.
- **API contract:** `docs/api-contract.md`  
  - Endpoints, request/response examples, error envelope, limits.

**Rule:** Any change to fields or endpoint shapes requires updating the relevant contract and version bump if breaking.

---

## 6) Configuration & Secrets

- **Files:** `configs/app.yaml`, `configs/sources.yaml`, `configs/bias_maps.yaml`, `.env`  
- **Examples:**
  - `app.yaml`: service ports, timeouts, feature flags (e.g., `use_transformer_sentiment: false`).
  - `sources.yaml`: upstream API endpoints and keys (read from environment).
  - `bias_maps.yaml`: precedence rules (AllSides vs Ad Fontes) and fallback defaults.
- **Secrets:** never commit. Use `.env` locally; in CI use encrypted secrets.

---

## 7) Observability

**Metrics (Prometheus)**
- API performance: `http_requests_total`, `http_request_duration_seconds_*` (route-labelled)
- Validation: `data_validation_pass`, `data_validation_fail`
- Drift: `data_drift_share`, `sentiment_drift_score`

**Dashboards (Grafana)**
- Panels for:
  - p95 latency per route
  - validation failures (rate over time)
  - drift share & sentiment drift trend
- Alerts:
  - `data_drift_share > 0.25 for 1h`
  - `rate(data_validation_fail[30m]) > 0`

**Reports (Evidently)**
- HTML reports stored at `monitoring/evidently/reports/`
- JSON profiles at `monitoring/evidently/profiles/`

---

## 8) Deployment & Environments

**Local (recommended)**
- Run with `compose.yaml`: FastAPI, Prometheus, Evidently exporter.
- Grafana Cloud `remote_write` from `infra/monitoring/prometheus.yml`.

**Dev/Prod**
- Containerize FastAPI (Dockerfile).  
- Host on Render/Fly.io/EC2/K8s.  
- Keep Prometheus sidecar or hosted Prometheus that scrapes `/metrics`.  
- Remote-write to Grafana Cloud for dashboards/alerts.

**Scaling**
- Stateless FastAPI → scale horizontally.  
- Cache external news lookups if rate-limited.  
- Batch jobs (nightly drift) via cron or GitHub Actions.

---

## 9) Failure Modes & Safeguards

| Failure | Impact | Mitigation |
|--------|--------|------------|
| External API timeout | Slow or empty results | Timeouts + retries + circuit breaker; respond 504/204 |
| Bad input data | Wrong outputs or crashes | Great Expectations: fail fast, increment `data_validation_fail` |
| Drift (topic/sentiment) | Degraded quality | Evidently alerts → review/retune thresholds/models |
| Bias map mismatch | Mislabeling | Validate domain coverage; default to `Unknown` with warning metric |
| Heavy traffic | Latency spikes | Horizontal scale; cap `max_articles`; async I/O |

---

## 10) Testing Strategy

- **Unit tests:**  
  - `tests/unit` for services (bias scorer, sentiment, clustering).
- **Integration tests:**  
  - `tests/integration` for router + service wiring, schema adherence.
- **E2E (optional):**  
  - `tests/e2e` → simulate extension call → backend → full pipeline.
- **Contract tests:**  
  - Validate responses match `api-contract.md` shape (Pydantic models).  
  - Data batches must pass Great Expectations suites.

---

## 11) CI/CD (GitHub Actions)

- **Workflows:** `.github/workflows/ci.yml`, `nightly-fetch.yml`  
  - CI: lint (ruff), type-check (mypy), unit/integration tests, build images.  
  - Nightly: data fetch sample, run GE validation, run Evidently, push drift metrics.

---

## 12) Security & Privacy

- No browsing history stored.  
- Only current tab URL/title sent by the extension.  
- Strip PII from logs; metrics are aggregate (no raw content).  
- Optional API keys via `X-API-Key` for hosted deployments.  
- Rate limiting for public endpoints.

---

## 13) Directory Map (selected)

```
src/
  app/
    api/main.py           # FastAPI app + /metrics exposure
    routers/analyze.py    # POST /api/v1/analyze
    service/*             # clustering, bias scorer, summarizer
    telemetry/*           # prometheus instrumentation & logging
    settings.py           # config loader (.env + configs/*.yaml)
  ml/
    data/*                # external fetch, normalization
    features/sentiment.py # sentiment scoring
    models/rank_bias.py   # bias distribution logic
    drift/*               # evidently runner & exporter
validation/great_expectations/*  # GE suites & checkpoints
monitoring/evidently/{profiles,reports}
infra/monitoring/prometheus.yml
infra/grafana/dashboards/bias_dashboard.json
```

---

## 14) Extension–Backend Sequence (ASCII)

```
Extension popup.js
   └─► POST /api/v1/analyze { url, title, source? }
           FastAPI /analyze
             ├─ validate body (Pydantic)
             ├─ fetch related articles
             ├─ GE validate raw batch
             ├─ embed + cluster + bias map + sentiment
             ├─ aggregate → bias_distribution + average_sentiment
             ├─ record metrics
             └─ return JSON to extension
```

---

## 15) Trade-offs & Future Work

- **Embeddings**: Start with local CPU-friendly model; upgrade to hosted embeddings for speed/quality.  
- **Sentiment**: VADER is fast; consider transformer for nuanced tone (cost/latency trade-off).  
- **MLflow (optional)**: Add experiment tracking + registry when iterations grow.  
- **Storage**: Start file-based under `data/`; move to Postgres/S3 as volume increases.  
- **Caching**: Add response caching for repeated articles/topics.

---

## 16) Runbook (quick start)

1) **Scaffold**: `python scaffold.py`  
2) **Configs**: Fill `.env` (API keys), review `configs/app.yaml`  
3) **Dev run**: `docker compose up` or `uvicorn src.app.api.main:app --reload`  
4) **Check**:  
   - API: `http://127.0.0.1:8000/docs`  
   - Metrics: `http://127.0.0.1:8000/metrics`  
   - Drift exporter: `http://127.0.0.1:8001/metrics`  
5) **Grafana**: Add `remote_write` creds in `infra/monitoring/prometheus.yml` and start Prometheus.  
6) **Extension**: Load `extension/` as unpacked in Chrome → test on a news article page.

---
