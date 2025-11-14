# News Sentiment Bias Analyzer

A full-stack system that analyzes how different news outlets cover the same story by comparing sentiment, political leaning, and narrative framing. The system combines a Chrome Extension interface, a FastAPI backend, and a modular Machine Learning pipeline following production-grade MLOps principles.

---

## Executive Summary

Modern news is fragmented. The same event can look dramatically different depending on who reports it. This system brings transparency by analyzing political bias patterns across sources in real time.

Given any news topic, the **News Sentiment Bias Analyzer** automatically:

- Retrieves related articles from multiple outlets  
- Clusters them to group similar storylines  
- Assigns political bias (Left, Center, Right) based on external datasets  
- Computes sentiment and embedding-based similarity scores  
- Aggregates all results into a clean, structured JSON view  
- Returns the results directly to a Chrome Extension UI  

The result is a complete, data-driven snapshot of how different outlets frame the same topic.

---

## Architecture
![Full System Archtecture](Docs/full_architecture/System_design.png)

## Key Features

### Chrome Extension UI
- Extracts the page topic using lightweight NLP  
- Sends the query securely to the backend  
- Displays sentiment breakdowns, political leanings, and alternative coverage  
- Designed for instant, real-time bias comparison  

### FastAPI Backend
- API gateway connecting the extension to the pipeline  
- Uses Pydantic models for strict request/response contracts  
- Handles telemetry, caching, logging, and validation  
- Produces a final `BiasView` object consumed by the UI  

### Full Modular ML Pipeline

**Pipeline Stages:**

1. **Ingest**  
   Fetches related articles using NewsAPI / RSS feeds / custom scrapers.

2. **Preprocess**  
   Text cleaning, deduplication, normalization, and summarization.

3. **Structural Validation**  
   Schema validation using Pydantic BaseModels.

4. **Semantic Validation**  
   Great Expectations checks for completeness, quality, and consistency.

5. **Feature Engineering**  
   SBERT embeddings, TF-IDF vectors, sentiment scoring (VADER).

6. **Modeling**  
   Clustering related articles into common narratives.  
   Scoring political bias strength across outlets.

7. **Aggregation**  
   Produces a unified topic-level “bias view” JSON object.

Built to be compatible with DVC, MLflow, and modular re-training.

---

## Bias Mapping Layer

Located under `resources/bias_maps/`, containing:

- Outlet → Political leaning (Left, Center, Right)  
- Reliability scores  
- Bias confidence values  

Sources include:
- **AllSides Media Bias Ratings**  
- **Ad Fontes Media Reliability Scores**

---

## Monitoring & Observability

This system includes:

- **Evidently dashboards** for drift detection  
- **Prometheus** metrics exports  
- **FastAPI request profiling** for latency and throughput  
- **Dataset quality checks** after each pipeline stage  

---

## Architecture Overview

### Application Layer (`src/app/`)
```
src/app/
 ├── api/            # FastAPI routers
 ├── schemas/        # Request/response Pydantic models
 ├── settings.py     # Environment + YAML config loader
 ├── telemetry/      # Logging & metrics
 ├── main.py         # FastAPI entrypoint
```

### Machine Learning Layer (`src/ml/`)
```
src/ml/
 ├── ingest/
 ├── preprocess/
 ├── validate/
 │     ├── structural/
 │     └── semantic/       # Great Expectations
 ├── features/
 ├── model/
 ├── aggregate/
 ├── utils/
 ├── pipeline.py           # Master orchestrator of all stages
```

### Data & Resources Layer
```
configs/                   # YAML configs per pipeline stage
data/
 ├── raw/
 ├── processed/
 ├── validated/
 ├── features/
 ├── predictions/
 ├── artifacts/
models/                    # SBERT embeddings, clustering models
resources/
 ├── bias_maps/            # AllSides + Ad Fontes media bias datasets
validation/
 ├── great_expectations/   # GX expectation suites
monitoring/
 ├── dashboards/           # Evidently reports
```

---

## High-Level Data Flow

1. Chrome Extension extracts the active page’s topic  
2. Sends topic → FastAPI backend  
3. Backend triggers ML pipeline  
4. Pipeline flows:  
   ingest → preprocess → structural_validate → semantic_validate → features → model → aggregate  
5. Final `BiasView` object returned  
6. Extension displays bias distribution, sentiment breakdown, and alternative coverage  

---

## Example Output (`BiasView`)

```json
{
  "topic": "US Election Debate",
  "clusters": 3,
  "sources": [
    {
      "outlet": "CNN",
      "bias": "Left",
      "sentiment": -0.23,
      "summary": "Coverage highlighting policy conflicts...",
      "url": "https://cnn.com/...",
      "cluster_id": 0
    },
    {
      "outlet": "Fox News",
      "bias": "Right",
      "sentiment": 0.14,
      "summary": "Coverage emphasizing candidate strength...",
      "url": "https://foxnews.com/...",
      "cluster_id": 0
    }
  ],
  "bias_distribution": {
    "left": 43,
    "center": 21,
    "right": 36
  }
}
```

---

## Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/news-bias-analyzer.git
cd news-bias-analyzer
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create `.env` file
```env
NEWS_API_KEY="your_api_key"
MODEL_DIR="./models/"
```

### 4. Start the backend
```bash
uvicorn src.app.main:app --reload
```

### 5. Load Chrome Extension
1. Open `chrome://extensions/`  
2. Enable Developer Mode  
3. Load unpacked  
4. Select the `extension/` folder

---

## License

MIT License.
