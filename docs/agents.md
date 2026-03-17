# Optilens Agent Architecture

## Pipeline Flow

```
orchestrator_init
  → site_intelligence
    → ux_vision, copy_content, data_performance (parallel)
      → orchestrator_synthesis
        → report_agent
```

## Agents

### 1. Orchestrator
- Initializes AuditState
- Dispatches agents
- Calculates weighted CRO score
- Generates revenue projections

### 2. Site Intelligence
- Detects site type: ecommerce | saas | landing_page | corporate | webapp
- Maps to CRO framework
- Outputs context for other agents

### 3. UX/Vision
- Analyzes screenshots with Claude vision
- WCAG 2.2 compliance
- Visual hierarchy assessment

### 4. Copy/Content
- Persuasion scoring
- A/B variant generation
- Readability analysis

### 5. Data/Performance
- Lighthouse CI
- Core Web Vitals
- Revenue leak benchmarks

## CRO Score Weights

| Category | Weight | Agent(s) |
|----------|--------|----------|
| UX & Friction | 25% | UX/Vision |
| Copy & Persuasion | 20% | Copy/Content |
| Performance & CWV | 20% | Data/Performance |
| SEO | 15% | Data/Performance |
| Conversion Psychology | 10% | UX/Vision + Copy/Content |
| Accessibility | 10% | UX/Vision |
