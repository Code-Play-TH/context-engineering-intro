# Implementation Tasks - KOL Selection & AI Recommendation (MVP)

## Overview

This task list covers the MVP implementation of manual KOL selection, AI-powered recommendations, campaign brief analysis, and budget optimization.

**Estimated Time: 6-7 days**

---

## Phase 1: Core Models

-   [x] 1. Create CampaignKOL model

    -   Define `app/models/campaign_kol.py` with CampaignKOL table
    -   Fields: id, campaign_id, kol_id, status, fee, notes, added_by, added_at
    -   Add status enum (shortlisted, assigned, accepted, declined)
    -   Create database migration
    -   Add relationships to Campaign and KOL models
    -   _Requirements: 1.1, 1.4_

-   [x] 2. Create KOLRecommendation model

    -   Define `app/models/kol_recommendation.py`
    -   Fields: id, campaign_id, kol_id, overall_score, niche_alignment_score, engagement_score, performance_score, audience_match_score, budget_fit_score, explanation, created_at
    -   Store detailed scoring breakdown for transparency
    -   Create database migration
    -   _Requirements: 2.2, 2.4_

-   [x] 3. Create AudienceDemographics model

    -   Define `app/models/audience_demographics.py`
    -   Fields: id, kol_id, platform, age_distribution (JSON), gender_distribution (JSON), location_distribution (JSON), interests (Array), fetched_at
    -   Store demographic data from social media APIs
    -   Create database migration
    -   _Requirements: 5.1, 5.2_

---

## Phase 2: Manual KOL Selection Service

-   [ ] 4. Create KOLSelectionService

    -   Create `app/services/kol_selection_service.py`
    -   Implement `search_kols(campaign_id, filters)` method with budget constraints
    -   Implement `add_to_shortlist(campaign_id, kol_id)` method
    -   Implement `remove_from_shortlist(campaign_id, kol_id)` method
    -   Implement `get_shortlist_summary(campaign_id)` method with cost and reach
    -   _Requirements: 1.1, 1.3, 1.4_

-   [ ] 5. Implement shortlist management

    -   Calculate total estimated cost and projected reach
    -   Check budget constraints and display warnings
    -   Check for scheduling conflicts with other campaigns
    -   Track shortlist changes and history
    -   _Requirements: 1.4, 1.5, 1.6_

-   [ ] 6. Create manual selection endpoints
    -   GET `/api/v1/campaigns/{id}/kol-selection/search` - Search KOLs with filters
    -   POST `/api/v1/campaigns/{id}/kol-selection/shortlist` - Add to shortlist
    -   DELETE `/api/v1/campaigns/{id}/kol-selection/shortlist/{kol_id}` - Remove from shortlist
    -   GET `/api/v1/campaigns/{id}/kol-selection/shortlist` - Get shortlist summary
    -   _Requirements: 1.1, 1.3_

---

## Phase 3: AI Recommendation Engine

-   [ ] 7. Create AIRecommendationService

    -   Create `app/services/ai_recommendation_service.py`
    -   Implement `generate_recommendations(campaign_id, criteria)` method
    -   Implement `score_kol(kol_id, campaign_id)` method with weighted scoring
    -   Implement `explain_recommendation(kol_id, campaign_id)` method
    -   Complete within 10 seconds for 100K+ KOL database
    -   _Requirements: 2.1, 2.2, 2.4, 2.7_

-   [ ] 8. Implement scoring algorithm

    -   Niche alignment: 30% weight (Jaccard similarity)
    -   Engagement rate: 25% weight (normalized score)
    -   Past performance: 20% weight (recent campaigns weighted higher)
    -   Audience match: 15% weight (demographic overlap)
    -   Budget fit: 10% weight (within pricing tier)
    -   _Requirements: 2.2, 2.3_

-   [ ] 9. Create recommendation endpoints
    -   POST `/api/v1/campaigns/{id}/kol-selection/recommend` - Generate recommendations
    -   GET `/api/v1/campaigns/{id}/kol-selection/recommendations` - Get saved recommendations
    -   Allow adjusting criteria and re-calculating scores
    -   _Requirements: 2.1, 2.5_

---

## Phase 4: Campaign Brief Analysis

-   [ ] 10. Create BriefAnalysisService

    -   Create `app/services/brief_analysis_service.py`
    -   Implement `analyze_campaign_brief(brief_text)` method using OpenAI API
    -   Extract target audience demographics (age, gender, location, interests)
    -   Identify required content types and brand values
    -   Map to KOL niche categories and platform preferences
    -   _Requirements: 3.1, 3.2, 3.3, 3.4_

-   [ ] 11. Implement brief parsing and validation

    -   Extract budget range and filter KOLs accordingly
    -   Handle uncertain analysis with user confirmation prompts
    -   Store analysis results for reuse
    -   Validate extracted requirements against available data
    -   _Requirements: 3.6, 3.7_

-   [ ] 12. Create brief analysis endpoints
    -   POST `/api/v1/campaigns/{id}/kol-selection/analyze-brief` - Analyze brief text
    -   GET `/api/v1/campaigns/{id}/brief-analysis` - Get stored analysis
    -   Allow manual adjustment of extracted requirements
    -   _Requirements: 3.1, 3.7_

---

## Phase 5: Historical Performance Analysis

-   [ ] 13. Create PerformanceAnalysisService

    -   Create `app/services/performance_analysis_service.py`
    -   Implement `get_historical_performance(kol_id)` method
    -   Implement `calculate_performance_score(kol_id)` method
    -   Weight recent campaigns (last 6 months) higher than older ones
    -   Identify similar brand campaigns and highlight relevant experience
    -   _Requirements: 4.1, 4.2, 4.5_

-   [ ] 14. Implement performance scoring

    -   Calculate average reach, engagement, and conversion rates
    -   Track reliability score (cancellation rate, on-time delivery)
    -   Display performance trends over last 12 months
    -   Add badges for "New KOL", "Top Performer", reliability warnings
    -   _Requirements: 4.2, 4.3, 4.6, 4.7_

-   [ ] 15. Create performance analysis endpoints
    -   GET `/api/v1/kols/{id}/performance-history` - Get historical performance
    -   GET `/api/v1/kols/{id}/similar-campaigns` - Get similar brand campaigns
    -   Include performance trends and reliability indicators
    -   _Requirements: 4.1, 4.4_

---

## Phase 6: Audience Demographics Matching

-   [ ] 16. Create AudienceMatchingService

    -   Create `app/services/audience_matching_service.py`
    -   Implement `fetch_audience_demographics(kol_id, platform)` method
    -   Implement `calculate_match_score(kol_demographics, target_demographics)` method
    -   Implement `compare_audiences(kol_ids)` method for side-by-side comparison
    -   _Requirements: 5.1, 5.2, 5.7_

-   [ ] 17. Implement demographic matching algorithm

    -   Calculate match percentage for age, gender, location dimensions
    -   Display warnings for matches below 60%
    -   Highlight "Excellent Match" for matches above 85%
    -   Estimate demographics when API data unavailable
    -   _Requirements: 5.2, 5.3, 5.4, 5.5_

-   [ ] 18. Create audience matching endpoints
    -   GET `/api/v1/kols/{id}/audience-demographics` - Get demographics
    -   POST `/api/v1/campaigns/{id}/kol-selection/compare-audiences` - Compare multiple KOLs
    -   Display pie charts for demographic breakdowns
    -   _Requirements: 5.1, 5.6, 5.7_

---

## Phase 7: Budget Optimization

-   [ ] 19. Create BudgetOptimizationService

    -   Create `app/services/budget_optimization_service.py`
    -   Implement `optimize_kol_mix(campaign_id, strategy)` method
    -   Implement `calculate_projected_reach(kol_ids)` method
    -   Implement `estimate_audience_overlap(kol_ids)` method
    -   Support "Max Reach", "Max Engagement", and "Balanced" strategies
    -   _Requirements: 6.1, 6.2, 6.4, 6.7_

-   [ ] 20. Implement optimization algorithms

    -   Max Reach: Optimize for followers per dollar
    -   Max Engagement: Optimize for engagement rate per dollar
    -   Balanced: Mix of Nano (20%), Micro (50%), Mid-tier (30%)
    -   Account for audience overlap between KOLs
    -   _Requirements: 6.1, 6.2, 6.3, 6.4_

-   [ ] 21. Create budget optimization endpoints
    -   POST `/api/v1/campaigns/{id}/kol-selection/optimize` - Get optimized mix
    -   POST `/api/v1/campaigns/{id}/kol-selection/projected-reach` - Calculate reach
    -   Allow real-time budget adjustment and re-optimization
    -   _Requirements: 6.1, 6.5, 6.6_

---

## Phase 8: Content Quality and Brand Safety (Basic)

-   [ ] 22. Create ContentQualityService

    -   Create `app/services/content_quality_service.py`
    -   Implement `evaluate_content_quality(kol_id)` method
    -   Implement `check_brand_safety(kol_id, brand_rules)` method
    -   Analyze recent posts for quality and engagement patterns
    -   Check for competitor brand conflicts
    -   _Requirements: 7.1, 7.4_

-   [ ] 23. Implement basic safety checks

    -   Scan for inappropriate content or controversial topics
    -   Check for competitor brand collaborations
    -   Rate content quality as High, Medium, or Low
    -   Allow Campaign Manager override for flagged KOLs
    -   _Requirements: 7.2, 7.3, 7.7_

-   [ ] 24. Create content quality endpoints
    -   GET `/api/v1/kols/{id}/content-quality` - Get quality assessment
    -   GET `/api/v1/kols/{id}/brand-safety` - Get safety check results
    -   Allow setting brand safety rules per campaign
    -   _Requirements: 7.1, 7.6_

---

## Phase 9: Integration and Workflow

-   [ ] 25. Integrate with existing KOL database

    -   Use existing KOL search and filtering functionality
    -   Extend KOL model with recommendation scores
    -   Add performance history tracking
    -   Ensure compatibility with existing KOL management
    -   _Requirements: 1.1, 2.1_

-   [ ] 26. Create unified selection workflow

    -   Combine manual search with AI recommendations
    -   Allow switching between manual and AI-assisted modes
    -   Preserve shortlist across different selection methods
    -   Track selection decisions and reasoning
    -   _Requirements: 1.1, 2.1_

-   [ ] 27. Add selection analytics and tracking
    -   Track which recommendations are accepted/rejected
    -   Measure recommendation accuracy over time
    -   Identify successful selection patterns
    -   Improve algorithm based on feedback
    -   _Requirements: 2.4, 4.1_

---

## Phase 10: Testing & Documentation

-   [ ]\* 28. Write unit tests

    -   Test scoring algorithm accuracy
    -   Test niche alignment calculation
    -   Test audience match calculation
    -   Test budget optimization logic
    -   Test brief analysis parsing
    -   _Requirements: All_

-   [ ]\* 29. Write integration tests
    -   Test end-to-end recommendation flow
    -   Test brief analysis with LLM
    -   Test audience demographics fetching
    -   Test shortlist management
    -   Test performance analysis
    -   _Requirements: All_

---

## Success Criteria

✅ Campaign Managers can manually search and select KOLs  
✅ AI generates ranked recommendations based on campaign brief  
✅ Campaign briefs are analyzed to extract requirements  
✅ Historical performance influences recommendations  
✅ Audience demographics are matched with targets  
✅ Budget optimization suggests optimal KOL mix  
✅ Content quality and brand safety are assessed  
✅ Shortlist management tracks costs and conflicts  
✅ Recommendations complete within 10 seconds  
✅ System handles 100K+ KOL database efficiently

---

## Notes

-   MVP focuses on core recommendation engine and manual selection
-   Skip advanced content analysis for MVP (Phase 2)
-   Skip complex brand safety rules for MVP (Phase 2)
-   Skip real-time social media API integration for MVP (Phase 2)
-   Use cached demographic data where possible
-   Advanced machine learning features can be added in Phase 2
-   Focus on accuracy and performance of core algorithms
