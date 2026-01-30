# Daily Poetry Generation Roadmap

## Overview

This roadmap outlines the steps required to implement automated daily poem generation for all MARTA routes using Azure Logic Apps, Azure Functions, or similar scheduling tools.

---

## Implementation Phases

### Phase 1: Foundation (High Priority)

- [ ] **Add rate-limit handling to RouteAgent**
  - Implement exponential backoff for Azure OpenAI API calls
  - Track rate limits and pause generation if thresholds approached
  - Effort: Low | Impact: High

- [ ] **Create route configuration system**
  - Define default parameters for each route (story_influence, time_of_day, location, passenger_count)
  - Load route configuration from JSON or config file
  - Allow per-route customization of generation parameters
  - Effort: Low | Impact: High

- [ ] **Set up Azure Functions timer trigger**
  - Create timer-based Azure Function to trigger daily generation (e.g., 6am)
  - Loop through all configured routes
  - Call FastAPI endpoint for each route
  - Effort: Low | Impact: High

### Phase 2: Reliability (Medium Priority)

- [ ] **Add error handling and retry logic**
  - Implement robust error handling for API failures
  - Add retry mechanism with exponential backoff
  - Log failures and send notifications on critical errors
  - Effort: Medium | Impact: High

- [ ] **Migrate storage from JSON to Cosmos DB**
  - Refactor `poem_store.py` to use Azure Cosmos DB instead of JSON files
  - Maintain backward compatibility with existing data
  - Add indexing for efficient queries
  - Effort: Medium | Impact: High

- [ ] **Add narrative continuity tracking**
  - Query recent poems before generation (last 7 days per route)
  - Track themes used to avoid repetition
  - Adjust narrative constraints based on recent poem history
  - Effort: Medium | Impact: Medium

### Phase 3: Optimization (Lower Priority)

- [ ] **Implement response caching**
  - Cache narrative constraints and character definitions
  - Reduce redundant API calls for stable route properties
  - Set cache expiration (e.g., 24 hours)
  - Effort: Medium | Impact: Medium

- [ ] **Add cost tracking and budgeting**
  - Monitor daily API costs
  - Set daily budget alerts
  - Track cost per route to identify optimization opportunities
  - Effort: Low | Impact: Medium

- [ ] **Create monitoring dashboard**
  - Track daily generation success rate
  - Monitor poem quality metrics (narrative adherence scores)
  - Alert on anomalies or failures
  - Effort: Medium | Impact: Medium

- [ ] **Add narrative deduplication logic**
  - Detect similar themes across routes for the same day
  - Implement diversity constraints
  - Ensure story coherence across route set
  - Effort: Medium | Impact: Medium

---

## Proof of Concept Setup

**Simple Flow**:
```
Azure Logic Apps / Functions Timer (6am daily)
  └─ Loop through route list
     ├─ Call FastAPI /api/poetry endpoint
     ├─ Use default parameters
     └─ Store poems to storage
```

**Minimum Requirements**:
1. Route configuration with default parameters
2. Rate-limit handling
3. Azure Functions timer trigger
4. Error handling and notifications

---

## Production Setup

**Enhanced Flow**:
```
Azure Functions Timer (6am daily)
  └─ Query route configuration from Cosmos DB
     └─ For each route:
        ├─ Query recent poems (deduplication check)
        ├─ Generate narrative constraints
        ├─ Call poetry generation API
        ├─ Evaluate narrative adherence
        ├─ Store to Cosmos DB
        └─ Update consistency tracking
     └─ Handle rate limits with exponential backoff
     └─ Log metrics and notify on completion
```

**Full Requirements**:
1. Cosmos DB storage (Phase 2)
2. Rate-limit handling (Phase 1)
3. Narrative continuity tracking (Phase 2)
4. Error handling and retry logic (Phase 2)
5. Cost monitoring (Phase 3)
6. Monitoring dashboard (Phase 3)

---

## Cost Considerations

- **Estimated Daily Cost**: $50-200/day (depending on model and route count)
- **Monthly Cost**: $1,500-6,000 (70 routes × 30 days)
- **Cost Reduction Strategies**:
  - Use GPT-3.5-turbo instead of GPT-4
  - Implement response caching
  - Batch similar route generations
  - Consider Azure Cache for Redis

---

## Timeline Estimate

| Phase | Effort | Timeline |
|-------|--------|----------|
| Phase 1 | 3-4 hours | 1-2 days |
| Phase 2 | 8-10 hours | 3-5 days |
| Phase 3 | 6-8 hours | 2-4 days |
| **Total** | **17-22 hours** | **6-11 days** |

---

## Success Criteria

- [ ] 1 poem generated per route per day
- [ ] 95%+ generation success rate
- [ ] Narrative adherence maintained (>0.4 average)
- [ ] Daily cost stays within budget
- [ ] No manual intervention required
- [ ] All poems persisted to scalable storage
- [ ] Monitoring dashboard shows health metrics
