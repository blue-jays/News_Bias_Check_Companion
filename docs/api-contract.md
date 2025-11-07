# API Contract — News Sentiment Bias Analyzer (FastAPI)

**Base URL (dev):** `http://127.0.0.1:8000`  
**Versioning:** `/api/v1/*` (breaking changes bump to `/api/v2/*`)  
**Auth:** None in dev (header `X-API-Key` reserved for prod)  
**Content-Type:** `application/json; charset=utf-8`

---

## 1) Health

### GET `/api/v1/health`
**200**
```json
{ "status": "healthy" }
