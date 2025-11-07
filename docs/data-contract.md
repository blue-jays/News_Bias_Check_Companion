A strict definition of how the data must look like.
- Schemas
- Data types
- Expectations and Validation Rules.

It ensures that the pipeline does not break when the data sources changes.

# Data Contract — News Sentiment Bias Analyzer

**Owner:** ML Platform  
**Applies to:** `data/raw`, `data/processed`, `src/pipelines/*`, `src/ml/*`  
**Validated by:** Great Expectations (schema/quality) + Evidently (drift/monitoring)  
**Last updated:** 2025-11-06

---

## 1) Scope & Purpose
This contract defines the allowed structure and quality guarantees for article data used by the News Sentiment Bias Analyzer. Pipelines must **fail fast** when inputs violate these rules.

---

## 2) Data Sources

| Source            | Purpose                                | Example fields                     |
|-------------------|----------------------------------------|------------------------------------|
| News APIs (e.g., NewsAPI, Bing) | Article metadata & content            | title, url, source, published_at   |
| AllSides          | Outlet bias label (Left/Center/Right)  | domain → bias_label                |
| Ad Fontes         | Outlet bias + reliability score        | domain → bias_label, reliability   |

---

## 3) Raw Article Schema (`data/raw/*.jsonl` or `*.csv`)
Each record represents one article.

| Field             | Type                       | Required | Constraints / Notes                                    |
|------------------|----------------------------|----------|--------------------------------------------------------|
| `source_name`     | string                     | ✅        | Non-empty                                              |
| `source_domain`   | string                     | ✅        | e.g., `cnn.com`                                        |
| `title`           | string                     | ✅        | 3–300 chars                                            |
| `description`     | string \| null             | ❌        | Optional                                               |
| `url`             | string (URL)               | ✅        | Must be valid absolute URL                             |
| `published_at`    | string (ISO 8601 UTC)      | ✅        | Example `2025-11-06T17:20:00Z`                        |
| `content`         | string \| null             | ❌        | Raw text when available                                |
| `language`        | string (ISO 639-1)         | ❌        | Default `en`                                           |
| `fetched_at`      | string (ISO 8601 UTC)      | ✅        | Ingestion timestamp                                    |
| `bias_label`      | enum{Left,Center,Right} \| null | ❌   | From AllSides/Ad Fontes by `source_domain`             |
| `reliability`     | number \| null             | ❌        | 0–100 (Ad Fontes)                                      |

**Great Expectations (Minimum Checks)**  
- `expect_column_values_to_not_be_null`: `source_name`, `source_domain`, `title`, `url`, `published_at`, `fetched_at`  
- `expect_column_values_to_match_regex`: `url` (valid URL)  
- `expect_column_values_to_match_strftime_format`: `published_at`, `fetched_at` → `%Y-%m-%dT%H:%M:%SZ`  
- `expect_column_values_to_be_in_set`: `bias_label` ∈ {Left, Center, Right, null}  
- `expect_table_row_count_to_be_between`: 10 ≤ N ≤ 10_000 per batch

---

## 4) Processed Schema (`data/processed/articles_*.csv`)
Produced after feature extraction, clustering, and scoring.

| Field                 | Type                 | Constraints / Notes                                   |
|----------------------|----------------------|-------------------------------------------------------|
| `article_id`         | string (uuid)        | Deterministic hash of `url` or API id                 |
| `source_domain`      | string               | Copied from raw                                      |
| `title`              | string               | Copied from raw                                      |
| `url`                | string               | Copied from raw                                      |
| `published_at`       | string (ISO 8601)    | Copied from raw                                      |
| `topic_cluster_id`   | string               | e.g., `cluster_9b1f2a` (Sentence-BERT + HDBSCAN/KMeans) |
| `sentiment_score`    | number               | Range −1.0 to +1.0 (VADER/Transformer)                |
| `bias_label`         | enum                 | Left/Center/Right (from mapping)                      |
| `source_reliability` | number \| null       | 0–100                                                |
| `summary`            | string \| null       | Optional abstractive summary                          |

**Great Expectations (Additional Checks)**  
- `expect_column_values_to_be_between`: `sentiment_score` ∈ [−1, 1]  
- `expect_column_values_to_be_in_set`: `bias_label` ∈ {Left, Center, Right}  
- `expect_column_values_to_not_be_null`: `topic_cluster_id` once clustering is assigned  
- `expect_column_value_lengths_to_be_between`: `title` length 3–300  

---

## 5) Bias Distribution Output (per topic cluster)
Emitted by API and stored in analytics tables.

```json
{
  "topic_cluster_id": "cluster_9b1f2a",
  "articles_analyzed": 12,
  "bias_distribution": { "Left": 0.45, "Center": 0.35, "Right": 0.20 },
  "average_sentiment": 0.12,
  "dominant_bias": "Left",
  "window_start": "2025-11-05T00:00:00Z",
  "window_end":   "2025-11-06T00:00:00Z"
}
