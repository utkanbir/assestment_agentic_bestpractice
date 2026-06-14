# Assessment Domain Ontology
**Agentic Assessment Knowledge Platform**
Version: 0.2 | Status: Draft

---

## Namespace
```
https://aakp.ai/ontology/assessment#
```

## Ontology Structure

Four OWL files:
- `assessment.owl` — assessment process concepts
- `architecture.owl` — enterprise architecture concepts
- `maturity.owl` — maturity, risk, recommendation concepts
- `organization.owl` — people and organizational concepts

---

## Domain 1: Assessment Ontology (`assessment.owl`)

### Class: Assessment
Represents an assessment engagement.

**Examples:**
- Migros Data Platform Assessment
- Retail Data Transformation Assessment

**Properties:**
| Property | Range | Notes |
|---|---|---|
| hasTask | Task | |
| hasCapability | Capability | |
| hasFinding | Finding | |
| hasRecommendation | Recommendation | |
| hasCustomer | Organization | |
| hasReport | Report | **[NEW v0.2]** |
| hasStatus | AssessmentStatus | **[NEW v0.2]** |
| hasStartDate | xsd:date | |
| hasEndDate | xsd:date | |

**AssessmentStatus values:** `Planning` / `InProgress` / `UnderReview` / `Complete`

---

### Class: Task
Represents an assessment workstream.

**Examples:**
- Data Governance Assessment
- CDP Assessment
- Lakehouse Assessment

**Properties:**
| Property | Range | Notes |
|---|---|---|
| belongsToAssessment | Assessment | |
| assessesCapability | Capability | |
| producesFinding | Finding | |
| hasInterview | Interview | **[NEW v0.2]** |
| producesReport | Report | **[NEW v0.2]** |
| dependsOnTask | Task | **[NEW v0.2]** cross-task dependency |
| hasStatus | TaskStatus | **[NEW v0.2]** |

**TaskStatus values:** `NotStarted` / `InProgress` / `FindingsCaptured` / `UnderReview` / `Complete`

---

### Class: Interview *(NEW v0.2)*
Represents a structured interview session conducted as part of a Task.

**Examples:**
- Kubernetes Resilience Interview — Session 1
- CDP Architecture Interview

**Properties:**
| Property | Range | Notes |
|---|---|---|
| conductedForTask | Task | |
| participatedBy | Stakeholder | multiple |
| facilitatedBy | Stakeholder | consultant |
| conductedAt | xsd:dateTime | |
| hasQuestion | Question | questions covered |
| producesEvidence | Evidence | |
| hasStatus | InterviewStatus | |
| durationMinutes | xsd:integer | |

**InterviewStatus values:** `Scheduled` / `InProgress` / `Completed` / `Cancelled`

---

### Class: Question
Represents an assessment question.

**Properties:**
| Property | Range | Notes |
|---|---|---|
| belongsToTask | Task | |
| askedInInterview | Interview | **[NEW v0.2]** |
| hasAnswer | Answer | |
| hasCategory | xsd:string | |
| hasPriority | Priority | High / Medium / Low |

---

### Class: Answer
Represents customer responses collected during interviews.

**Properties:**
| Property | Range | Notes |
|---|---|---|
| answersQuestion | Question | |
| supportsEvidence | Evidence | |
| providedBy | Stakeholder | |
| capturedAt | xsd:dateTime | |
| hasConfidence | Confidence | High / Medium / Low |

---

### Class: Evidence
Represents supporting evidence collected during assessment.

**Subclasses:**
- `InterviewEvidence` — direct interview statement
- `DocumentEvidence` — architecture diagram, policy doc, etc.
- `MetricEvidence` — CPU/memory/latency metrics
- `ArchitectureEvidence` — system diagrams, topology maps
- `ConfigurationEvidence` — config files, deployment specs

**Properties:**
| Property | Range | Notes |
|---|---|---|
| supportsFinding | Finding | |
| collectedInInterview | Interview | **[NEW v0.2]** |
| hasSource | xsd:string | document name, system, URL |
| hasConfidence | Confidence | High / Medium / Low |
| capturedAt | xsd:dateTime | **[NEW v0.2]** |

---

### Class: Finding
Represents an identified observation.

**Examples:**
- Metadata ownership is unclear
- Real-time activation is unavailable
- Ingestion latency is high

**Properties:**
| Property | Range | Notes |
|---|---|---|
| identifiedInTask | Task | |
| supportedByEvidence | Evidence | one or more, mandatory |
| indicatesGap | Gap | |
| indicatesRisk | Risk | |
| hasConfidence | Confidence | **[NEW v0.2]** derived from evidence |
| relatedToFinding | Finding | **[NEW v0.2]** cross-task relationships |

---

### Class: Report *(NEW v0.2)*
Represents a formal output document of a Task or Assessment.

**Examples:**
- Ingestion Bottleneck Map
- Executive Summary
- Risk Heatmap
- Cloud Strategy Roadmap

**Properties:**
| Property | Range | Notes |
|---|---|---|
| generatedFor | Task or Assessment | |
| hasType | ReportType | |
| containsFinding | Finding | |
| containsRecommendation | Recommendation | |
| containsRoadmap | Roadmap | |
| hasStatus | ReportStatus | |
| generatedAt | xsd:dateTime | |

**ReportType values:**
`TaskReport` / `ExecutiveSummary` / `RiskHeatmap` / `ArchitectureRoadmap` / `MaturityReport` / `GapAnalysis`

**ReportStatus values:** `Draft` / `UnderReview` / `Final`

---

## Domain 2: Enterprise Architecture Ontology (`architecture.owl`)

### Class: Capability
Represents business or technology capabilities. Central entity of the ontology.

**Examples:**
- Data Governance
- Metadata Management
- Data Quality
- Real-Time Activation
- Disaster Recovery
- Data Ingestion

**Properties:**
| Property | Range | Notes |
|---|---|---|
| supportedBySystem | System | |
| hasGap | Gap | |
| hasMaturityScore | MaturityScore | |
| assessedInTask | Task | |

---

### Class: System
Represents enterprise applications and platforms.

**Examples:**
- Teradata, NiFi, DataStage, Airflow
- Kubernetes, SAP, Salesforce
- Databricks, Kafka

**Properties:**
| Property | Range | Notes |
|---|---|---|
| supportsCapability | Capability | |
| dependsOnSystem | System | |
| containsDataProduct | DataProduct | |

---

### Class: DataProduct
Represents reusable data assets.

**Examples:**
- Customer Data Product
- Sales Data Product
- Campaign Data Product

**Properties:**
| Property | Range | Notes |
|---|---|---|
| ownedBy | Stakeholder | |
| servesCapability | Capability | |
| dependsOnSystem | System | |

---

### Class: DataFlow
Represents data movement between systems.

**Examples:**
- SAP → NiFi → Teradata
- Teradata → CDP → Mobile Application

**Properties:**
| Property | Range | Notes |
|---|---|---|
| sourceSystem | System | |
| targetSystem | System | |
| transfersDataProduct | DataProduct | |

---

## Domain 3: Maturity Ontology (`maturity.owl`)

### Class: Gap
Represents missing capabilities or weaknesses.

**Examples:**
- No Data Contracts
- No Metadata Ownership
- No Streaming Architecture

**Properties:**
| Property | Range | Notes |
|---|---|---|
| affectsCapability | Capability | |

---

### Class: Risk
Represents business or technical risks.

**Examples:**
- Governance Risk
- Business Continuity Risk
- Scalability Risk

**Properties:**
| Property | Range | Notes |
|---|---|---|
| affectsCapability | Capability | |
| causedByGap | Gap | |
| hasSeverity | Severity | **[NEW v0.2]** |

**Severity values:** `Critical` / `High` / `Medium` / `Low`

---

### Class: Recommendation
Represents suggested improvements.

**Examples:**
- Establish Metadata Stewardship
- Implement Event Streaming Platform
- Modernize Ingestion Platform

**Properties:**
| Property | Range | Notes |
|---|---|---|
| addressesGap | Gap | |
| mitigatesRisk | Risk | |
| improvesCapability | Capability | |
| hasHorizon | Horizon | **[NEW v0.2]** |
| hasPriority | Priority | **[NEW v0.2]** High / Medium / Low |
| isPartOfRoadmap | RoadmapItem | **[NEW v0.2]** |

**Horizon values:** `ShortTerm (0-3 months)` / `MediumTerm (3-12 months)` / `LongTerm (12+ months)`

---

### Class: MaturityScore
Represents capability maturity across multiple dimensions.

**Properties:**
| Property | Range | Notes |
|---|---|---|
| belongsToCapability | Capability | |
| hasLevel | xsd:integer (1-5) | |
| hasDimension | MaturityDimension | **[NEW v0.2]** |
| hasJustification | xsd:string | **[NEW v0.2]** |

**MaturityDimension values:** `People` / `Process` / `Technology` / `Data`

**Maturity Levels:**
- Level 1 — Initial
- Level 2 — Managed
- Level 3 — Defined
- Level 4 — Measured
- Level 5 — Optimized

---

### Class: Roadmap *(NEW v0.2)*
Represents the recommended improvement roadmap for a Task or Assessment.

**Properties:**
| Property | Range | Notes |
|---|---|---|
| generatedFor | Task or Assessment | |
| hasRoadmapItem | RoadmapItem | |
| containedInReport | Report | |

---

### Class: RoadmapItem *(NEW v0.2)*
Represents a single action item in the roadmap.

**Properties:**
| Property | Range | Notes |
|---|---|---|
| partOfRoadmap | Roadmap | |
| implementsRecommendation | Recommendation | |
| hasHorizon | Horizon | ShortTerm / MediumTerm / LongTerm |
| hasPriority | Priority | High / Medium / Low |
| dependsOnItem | RoadmapItem | sequencing |
| estimatedEffort | xsd:string | |

---

## Domain 4: Organization Ontology (`organization.owl`)

### Class: BusinessUnit
**Examples:** Marketing, Supply Chain, Data Office, Customer Experience

**Properties:**
| Property | Range | Notes |
|---|---|---|
| ownsCapability | Capability | |

---

### Class: Stakeholder
Represents people participating in the assessment.

**Examples:** Data Owner, Data Steward, Platform Owner, Architect, CTO

**Properties:**
| Property | Range | Notes |
|---|---|---|
| belongsToBusinessUnit | BusinessUnit | |
| ownsDataProduct | DataProduct | |
| participatesInInterview | Interview | **[NEW v0.2]** |

---

### Class: Owner
Subclass of: Stakeholder

---

### Class: Steward
Subclass of: Stakeholder

---

## Core Assessment Reasoning Chain

```
Capability
    ↓
  Gap
    ↓
  Risk  ──────────────────── hasSeverity → Critical / High / Medium / Low
    ↓
Recommendation ─────────────── hasHorizon → Short / Medium / Long Term
    ↓
RoadmapItem
    ↓
  Report
```

**Evidence chain (mandatory — no bypass):**

```
Interview → Question → Answer → Evidence → Finding → Risk → Recommendation
```

---

## Inference Rules

### Rule 1 (v0.1)
```
Answer supportsEvidence Evidence
Evidence supportsFinding Finding
⇒ Answer contributesToFinding Finding
```

### Rule 2 (v0.1)
```
Finding indicatesRisk Risk
Risk affectsCapability Capability
⇒ Finding impactsCapability Capability
```

### Rule 3 (v0.1)
```
Recommendation mitigatesRisk Risk
Risk affectsCapability Capability
⇒ Recommendation improvesCapability Capability
```

### Rule 4 (v0.1)
```
System supportsCapability Capability
Capability hasGap Gap
⇒ System affectedByGap Gap
```

### Rule 5 — Confidence Propagation *(NEW v0.2)*
```
Evidence hasConfidence Low
Evidence supportsFinding Finding
⇒ Finding hasConfidence Low

Evidence hasConfidence Medium
Evidence supportsFinding Finding
Finding hasConfidence NOT High
⇒ Finding hasConfidence Medium
```

### Rule 6 — Cross-Task Risk Propagation *(NEW v0.2)*
```
Task_A dependsOnTask Task_B
Task_B producesFinding Finding_B
Finding_B indicatesRisk Risk
Risk hasSeverity Critical
⇒ Task_A hasRelatedRisk Risk
```

### Rule 7 — Unsupported Finding Violation *(NEW v0.2)*
```
Finding supportedByEvidence NONE
⇒ Finding isInvalid true
```
*This rule enforces the core guardrail: no finding without evidence.*

---

## Knowledge Graph Example

```
Migros Assessment
    │
    ├── CDP Assessment Task
    │       │
    │       ├── Interview: CDP Architecture Session (2h)
    │       │       ├── Participated: CTO, Marketing Lead
    │       │       └── Question: "Real-time activation channels?"
    │       │               └── Answer → InterviewEvidence (confidence: High)
    │       │                       └── Finding: No Streaming Architecture
    │       │                               └── Risk: Customer Activation Delay (Severity: High)
    │       │                                       └── Recommendation: Implement Event Streaming
    │       │                                               └── hasHorizon: MediumTerm
    │       └── dependsOnTask: Ingestion Assessment Task  ← cross-task
    │
    └── Ingestion Assessment Task
            │
            └── Finding: NiFi Latency High (2-3h delay)
                    └── relatedToFinding: CDP Finding (cross-task link)
```

---

## Design Principles (updated v0.2)

1. Every finding must be supported by evidence.
2. Every risk must be traceable to a finding.
3. Every recommendation must address a gap or mitigate a risk.
4. Every recommendation must have a horizon (short/medium/long term).
5. Every risk must have a severity level.
6. Capabilities are the central assessment entity.
7. Maturity is multi-dimensional (People / Process / Technology / Data).
8. Cross-task dependencies must be explicitly modeled.
9. Confidence propagates from evidence to finding.
10. Assessments are knowledge-driven, not questionnaire-driven.
11. The ontology is reusable across customers and industries.

---

## What Changed: v0.1 → v0.2

| # | Change | Type |
|---|---|---|
| 1 | Added `Interview` class | New Class |
| 2 | Added `Report` class | New Class |
| 3 | Added `Roadmap` class | New Class |
| 4 | Added `RoadmapItem` class | New Class |
| 5 | Added `hasSeverity` to Risk | New Property |
| 6 | Added `hasHorizon` to Recommendation | New Property |
| 7 | Added `hasPriority` to Recommendation | New Property |
| 8 | Added `hasConfidence` to Finding | New Property |
| 9 | Added `relatedToFinding` to Finding | New Property (cross-task) |
| 10 | Added `dependsOnTask` to Task | New Property |
| 11 | Added `hasStatus` to Task and Assessment | New Property |
| 12 | Added `hasDimension` to MaturityScore | New Property |
| 13 | Added Rule 5: Confidence Propagation | New Inference Rule |
| 14 | Added Rule 6: Cross-Task Risk Propagation | New Inference Rule |
| 15 | Added Rule 7: Unsupported Finding Violation | New Guardrail Rule |

---

*Next version (v0.3) will add: Migros-specific domain instances, SHACL validation shapes, OWL formal syntax*
