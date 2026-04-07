# apex-loyalty-system
Apex Retail: AI Agent Retention Solution
## OrchestrationAgent
OrchestrationAgent(python) will read all the data from SourceDataV1 folder and consolidate them to one source of truth.
## ScoringAgent
ScoringAgent(python) will read the output of the OrchestrationAgent data and analyze the data based on below rule and display in UI as those are high risk customer:
- Customer enrolled in loyalty platform 8 weeks ago but zero redemptions
- 2 support tickets in 90 days -- 1 unresolved for 6 days
- Average order value down 34% over 6 months
- 3 of last 5 orders used discount codes
## UI
- Group the data based on the risk level add a button consolidated button for each risk level group(approve and send Caampaign) to send notification with below details. Before sending popup should appear.
  - You are our valuable customer
## Technology Stack
- Angular as UI
- Python as backend