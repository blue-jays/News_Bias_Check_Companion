from typing import List, Literal, Optional
from pydantic import BaseModel, HttpUrl

"""
Schema check on API response. Are we getting the data we want ? 
SO we have to know what we will be getting to make the classes.


"""
class AnalyzeUrlRequest(BaseModel):
    url: HttpUrl
    title: Optional[str] = None
    
class BiasDistribution(BaseModel):
    left: int = 0
    center: int = 0
    right: int = 0
    unknown: int = 0

class SourceItem(BaseModel):
    title: str 
    url: HttpUrl
    outlet: str
    domain: str
    final_bias_label: Literal["left", "center", "right", "unknown"]
    final_bias_score: float
    sentiment: float
    cluster_id: Optional[int] = None

class BiasAnalysisResponse(BaseModel):
    bias_distribution: BiasDistribution
    average_sentiment: float
    sources: List[SourceItem]
