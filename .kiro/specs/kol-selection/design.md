# Design Document - KOL Selection & AI Recommendation

## Overview

The KOL Selection system combines manual search/filtering with AI-powered recommendations to help Campaign Managers select optimal influencers based on campaign objectives, historical performance, audience demographics, and budget constraints.

## Architecture

```
┌──────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend   │─────▶│   FastAPI    │─────▶│ PostgreSQL  │
│  Selection   │◀─────│   Selection  │◀─────│  Database   │
│  Interface   │      │   Service    │      └─────────────┘
└──────────────┘      └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  OpenAI/     │
                     │  Anthropic   │
                     │  API         │
                     └──────────────┘
```

## Components and Interfaces

### Backend Services

```python
class KOLSelectionService:
    async def search_kols(campaign_id: int, filters: KOLFilters) -> List[KOL]
    async def add_to_shortlist(campaign_id: int, kol_id: int) -> None
    async def remove_from_shortlist(campaign_id: int, kol_id: int) -> None
    async def get_shortlist(campaign_id: int) -> ShortlistSummary
    async def check_availability(kol_id: int, start_date: date, end_date: date) -> bool

class AIRecommendationService:
    async def generate_recommendations(campaign_id: int, criteria: RecommendationCriteria) -> List[KOLRecommendation]
    async def analyze_campaign_brief(brief_text: str) -> BriefAnalysis
    async def score_kol(kol_id: int, campaign_id: int) -> KOLScore
    async def explain_recommendation(kol_id: int, campaign_id: int) -> str

class PerformanceAnalysisService:
    async def get_historical_performance(kol_id: int) -> PerformanceHistory
    async def calculate_performance_score(kol_id: int) -> float
    async def get_similar_campaigns(kol_id: int, campaign_id: int) -> List[Campaign]

class AudienceMatchingService:
    async def fetch_audience_demographics(kol_id: int, platform: str) -> AudienceDemographics
    async def calculate_match_score(kol_demographics: dict, target_demographics: dict) -> float
    async def compare_audiences(kol_ids: List[int]) -> AudienceComparison

class BudgetOptimizationService:
    async def optimize_kol_mix(campaign_id: int, strategy: str) -> OptimizedMix
    async def calculate_projected_reach(kol_ids: List[int]) -> ProjectedReach
    async def estimate_audience_overlap(kol_ids: List[int]) -> float
```

## Data Models

### CampaignKOL Model

```python
class CampaignKOL(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id", index=True)
    kol_id: int = Field(foreign_key="kol.id", index=True)
    status: str = Field(default="shortlisted")  # shortlisted, assigned, accepted, declined
    fee: Optional[Decimal] = Field(max_digits=10, decimal_places=2)
    notes: Optional[str]
    added_by: int = Field(foreign_key="user.id")
    added_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    campaign: "Campaign" = Relationship(back_populates="kols")
    kol: "KOL" = Relationship(back_populates="campaigns")
```

### KOLRecommendation Model

```python
class KOLRecommendation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id")
    kol_id: int = Field(foreign_key="kol.id")
    overall_score: Decimal = Field(max_digits=5, decimal_places=2)  # 0-100
    niche_alignment_score: Decimal = Field(max_digits=5, decimal_places=2)
    engagement_score: Decimal = Field(max_digits=5, decimal_places=2)
    performance_score: Decimal = Field(max_digits=5, decimal_places=2)
    audience_match_score: Decimal = Field(max_digits=5, decimal_places=2)
    budget_fit_score: Decimal = Field(max_digits=5, decimal_places=2)
    explanation: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### AudienceDemographics Model

```python
class AudienceDemographics(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    kol_id: int = Field(foreign_key="kol.id")
    platform: str
    age_distribution: dict = Field(sa_column=Column(JSON))  # {"18-24": 30, "25-34": 45, ...}
    gender_distribution: dict = Field(sa_column=Column(JSON))  # {"male": 40, "female": 60}
    location_distribution: dict = Field(sa_column=Column(JSON))  # {"US": 50, "UK": 20, ...}
    interests: List[str] = Field(sa_column=Column(ARRAY(String)))
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
```

## API Endpoints

```python
# Manual Selection
GET    /api/v1/campaigns/{id}/kol-selection/search      # Search KOLs with filters
POST   /api/v1/campaigns/{id}/kol-selection/shortlist   # Add to shortlist
DELETE /api/v1/campaigns/{id}/kol-selection/shortlist/{kol_id}  # Remove from shortlist
GET    /api/v1/campaigns/{id}/kol-selection/shortlist   # Get shortlist summary

# AI Recommendations
POST   /api/v1/campaigns/{id}/kol-selection/recommend   # Generate recommendations
POST   /api/v1/campaigns/{id}/kol-selection/analyze-brief  # Analyze campaign brief
GET    /api/v1/campaigns/{id}/kol-selection/recommendations  # Get saved recommendations

# Performance Analysis
GET    /api/v1/kols/{id}/performance-history             # Get historical performance
GET    /api/v1/kols/{id}/similar-campaigns               # Get similar campaigns

# Audience Matching
GET    /api/v1/kols/{id}/audience-demographics           # Get audience demographics
POST   /api/v1/campaigns/{id}/kol-selection/compare-audiences  # Compare multiple KOLs

# Budget Optimization
POST   /api/v1/campaigns/{id}/kol-selection/optimize     # Optimize KOL mix
POST   /api/v1/campaigns/{id}/kol-selection/projected-reach  # Calculate projected reach
```

## AI Recommendation Algorithm

### Scoring Formula

```python
def calculate_overall_score(kol: KOL, campaign: Campaign) -> float:
    weights = {
        'niche_alignment': 0.30,
        'engagement_rate': 0.25,
        'past_performance': 0.20,
        'audience_match': 0.15,
        'budget_fit': 0.10
    }

    scores = {
        'niche_alignment': calculate_niche_alignment(kol, campaign),
        'engagement_rate': normalize_engagement_rate(kol),
        'past_performance': calculate_performance_score(kol),
        'audience_match': calculate_audience_match(kol, campaign),
        'budget_fit': calculate_budget_fit(kol, campaign)
    }

    overall = sum(scores[key] * weights[key] for key in weights)
    return round(overall, 2)
```

### Niche Alignment Calculation

```python
def calculate_niche_alignment(kol: KOL, campaign: Campaign) -> float:
    kol_niches = set(kol.niche)
    campaign_niches = set(campaign.target_niches)

    if not campaign_niches:
        return 50.0  # Neutral score if no niches specified

    intersection = kol_niches & campaign_niches
    union = kol_niches | campaign_niches

    jaccard_similarity = len(intersection) / len(union) if union else 0
    return jaccard_similarity * 100
```

### Audience Match Calculation

```python
def calculate_audience_match(kol: KOL, campaign: Campaign) -> float:
    kol_demographics = get_audience_demographics(kol.id)
    target_demographics = campaign.target_audience

    age_match = calculate_distribution_overlap(
        kol_demographics.age_distribution,
        target_demographics.get('age_distribution', {})
    )

    gender_match = calculate_distribution_overlap(
        kol_demographics.gender_distribution,
        target_demographics.get('gender_distribution', {})
    )

    location_match = calculate_distribution_overlap(
        kol_demographics.location_distribution,
        target_demographics.get('location_distribution', {})
    )

    # Weighted average
    return (age_match * 0.4 + gender_match * 0.3 + location_match * 0.3)
```

### Brief Analysis with LLM

```python
async def analyze_campaign_brief(brief_text: str) -> BriefAnalysis:
    prompt = f"""
    Analyze this campaign brief and extract key requirements:

    {brief_text}

    Extract:
    1. Target audience (age, gender, location, interests)
    2. Required content types (posts, stories, videos)
    3. Brand values and tone
    4. Niche categories
    5. Platform preferences
    6. Budget range

    Return as structured JSON.
    """

    response = await openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return parse_brief_analysis(response.choices[0].message.content)
```

## Budget Optimization Strategies

### Max Reach Strategy

```python
def optimize_for_max_reach(campaign: Campaign, available_kols: List[KOL]) -> List[KOL]:
    """Select KOLs to maximize total reach within budget"""
    kols_sorted = sorted(available_kols, key=lambda k: k.total_followers / k.estimated_fee, reverse=True)

    selected = []
    remaining_budget = campaign.total_budget

    for kol in kols_sorted:
        if kol.estimated_fee <= remaining_budget:
            selected.append(kol)
            remaining_budget -= kol.estimated_fee

    return selected
```

### Max Engagement Strategy

```python
def optimize_for_max_engagement(campaign: Campaign, available_kols: List[KOL]) -> List[KOL]:
    """Select KOLs to maximize engagement within budget"""
    kols_sorted = sorted(available_kols,
                        key=lambda k: (k.engagement_rate * k.total_followers) / k.estimated_fee,
                        reverse=True)

    selected = []
    remaining_budget = campaign.total_budget

    for kol in kols_sorted:
        if kol.estimated_fee <= remaining_budget:
            selected.append(kol)
            remaining_budget -= kol.estimated_fee

    return selected
```

### Balanced Strategy

```python
def optimize_balanced(campaign: Campaign, available_kols: List[KOL]) -> List[KOL]:
    """Mix of nano, micro, and mid-tier KOLs for balanced reach and engagement"""
    budget_allocation = {
        'nano': campaign.total_budget * 0.20,
        'micro': campaign.total_budget * 0.50,
        'mid': campaign.total_budget * 0.30
    }

    selected = []
    for tier, budget in budget_allocation.items():
        tier_kols = [k for k in available_kols if k.tier == tier]
        tier_selected = select_best_in_budget(tier_kols, budget)
        selected.extend(tier_selected)

    return selected
```

## Performance Considerations

### Caching Strategy

-   Recommendations: Cache for 1 hour
-   Audience demographics: Cache for 24 hours
-   Performance scores: Cache for 6 hours

### Database Indexes

```sql
CREATE INDEX idx_campaign_kol_campaign ON campaignkol(campaign_id);
CREATE INDEX idx_campaign_kol_status ON campaignkol(status);
CREATE INDEX idx_kol_recommendation_campaign ON kolrecommendation(campaign_id);
CREATE INDEX idx_audience_demographics_kol ON audiencedemographics(kol_id);
```

### Async Processing

-   Generate recommendations as background task for large KOL databases
-   Fetch audience demographics in parallel for multiple KOLs
-   Calculate scores in batches of 50 KOLs

## Testing Strategy

### Unit Tests

-   Scoring algorithm accuracy
-   Niche alignment calculation
-   Audience match calculation
-   Budget optimization logic

### Integration Tests

-   End-to-end recommendation flow
-   Brief analysis with LLM
-   Audience demographics fetching
-   Shortlist management

### Performance Tests

-   Recommendation generation for 100K+ KOLs
-   Concurrent recommendation requests
-   Audience comparison for 20+ KOLs
