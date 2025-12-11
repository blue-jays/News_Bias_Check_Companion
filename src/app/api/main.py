from fastapi import FastAPI

from src.app.settings import get_settings
from src.app.api.schemas import (
    AnalyzeUrlRequest,
    BiasAnalysisResponse,
    BiasDistribution,
    SourceItem,
)

settings = get_settings()
app = FastAPI(title = settings.app_name)

@app.get("/health")
def health_check() -> dict:
    return {
        "status" : "Ok",
        "environment": settings.environment
    }
    
def _fake_pipeline(article_url: str) -> BiasAnalysisResponse:
    # In a real run, this would:
    #   - fetch related articles
    #   - run full pipeline
    # Here we just pretend we saw 3 sources.

    bias_distribution = BiasDistribution(left=1, center=1, right=1, unknown=0)

    sources = [
        SourceItem(
            title="Example left-leaning coverage",
            url=article_url,
            outlet="Example Times",
            domain="example-left.com",
            final_bias_label="left",
            final_bias_score=-0.6,
            sentiment=-0.2,
            cluster_id=0,
        ),
        SourceItem(
            title="Example centrist coverage",
            url=article_url,
            outlet="Neutral Daily",
            domain="example-center.com",
            final_bias_label="center",
            final_bias_score=0.0,
            sentiment=0.1,
            cluster_id=1,
        ),
        SourceItem(
            title="Example right-leaning coverage",
            url=article_url,
            outlet="Liberty News",
            domain="example-right.com",
            final_bias_label="right",
            final_bias_score=0.7,
            sentiment=0.3,
            cluster_id=2,
        ),
    ]

    average_sentiment = sum(s.sentiment for s in sources) / len(sources)

    return BiasAnalysisResponse(
        bias_distribution=bias_distribution,
        average_sentiment=average_sentiment,
        sources=sources,
    )


