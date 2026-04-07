# apex-loyalty-system
Apex Retail: AI Agent Retention Solution
## OrchestrationAgent
OrchestrationAgent(python) will read all the data from SourceDataV1 folder and consolidate them to one source of truth.
## ScoringAgent
ScoringAgent(python) will read the output of the OrchestrationAgent data and analyze the data based on below rule and display in UI as those are high risk customer:
- Customer enrolled in loyalty platform 8 weeks ago but zero redemptions
## Technology Stack
- Angular as UI
- Python as backend