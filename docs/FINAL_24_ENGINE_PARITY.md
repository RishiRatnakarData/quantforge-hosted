# Final-audit route and engine parity inventory

Baseline: 94a95616618f273286a3f113dde31780e90f79ed. No numerical engine was deleted. 36 private-prefixed JavaScript modules are identical after LF normalization. Changes in private.js concern the shared network/state bridge; the old computation definitions remain covered by the complete numerical suite.

## Normal routes and compatibility

The visible primary navigation remains exactly Explore, Compare, Models, Portfolio and Methods. Sign-in/account is an owner access state, not a sixth research section. Old hash/DOM handlers and calculator controls remain compatibility implementations where the shared shell or retained numerical modules still reference them. They are not extra normal destinations. No deletion is justified merely because the five-tab shell hides a legacy node.

The historical allocation replay is preserved in public Overview and private What If. Actual owner Overview contains saved balances, positions, receipt activity and server-recorded marks. Unrecorded account history, flow-adjusted percentage returns or benchmarks cannot be reconstructed from current holdings; unsupported account returns remain withheld.

## Feature-to-destination evidence

| Capability | Retained source | Shared destination | Verification |
| --- | --- | --- | --- |
| SEC provenance / ratios / peers | sec_analytics.js; sec_peer_model.js; tools/build_public_sec_snapshot.py | Explore Financials; Compare Reported financials; Methods Data | Existing SEC/provenance suite; v27 peers and full named-view matrix |
| Single-company / common-date history | research_core_v20.js; research_compare_portfolio_v21.js; cloud/api.py | Private Explore Market; Compare; Models; Portfolio studies | A/B routes; aligned-history numerical tests; provider outage cases |
| Direction classification and calibration | private_predictive_ml_v180.js; research_models_core_v22.js | Models Prediction Results/Evaluation/Method; worked Methods | Chronology/maturity/Brier Node tests; retained-engine and layout journeys |
| Risk / regression / bootstrap / factors | research_deep_v25.js; research_deep_ui_v25.js; private_french_factors_v87.js; private_factor_scenarios_v86.js | Models Risk; Portfolio Analysis; Methods worked examples | Full numerical suite; six retained-engine journeys including proxy and independent factor inputs |
| Optimization / strategy / walk-forward | private_optimizer.js; private_walkforward_v65.js; private_robustness_v120.js | Portfolio What If / Analysis; Models Strategy | Existing constraints/look-ahead/cost tests; shared route and deep browser studies |
| SEC cash-flow valuation and capital | private_value_v73.js; private_forecast_v65.js; research_models_core_v22.js | Models Valuation; worked DCF; SEC case report | Negative/missing FCF, discount/terminal guards; valuation source and scenario browser evidence |
| Historical SEC revisions / quality | private_pit_validation_v97.js; private_sec_coverage_v98.js; private_archived_sec_v99.js; private_archive_quality_v100.js | Methods Data optional session-only revision diagnostics | Retained-engine browser parses local fixtures, tests revision withholding and mode isolation |
| Headline TF-IDF / negation / aggregate | cloud/news_intelligence_v180.py | Explore News & filings; worked Methods NLP | New neutral-dominance and malformed/sparse/conflicting cases; generated error fixture equals actual implementation |
| Saved virtual account / contributions | cloud/api.py; cloud/supabase.sql; private.js; portfolio_workflow_v27.js; funding_workflow_v28.js | Private Portfolio Overview Buy/Sell/Fund, ledger and recorded marks | Decimal, replay, simultaneous CAS, negative auth; new workflow suite across 15 browser/width combinations |
| Notes / archived assessments / session | private_research_intelligence_v96.js; research_private_shell_v23.js; private.js | Explore contextual saved research; compact Account; public/private switching | A/D and retained engine edit/reload/logout tests; no real account used |

## Complete JavaScript source inventory

Bundled means the exact full source occurs in the generated artifact or is explicitly referenced by its builder. Builder expansion of templates can prevent exact substring matching. A matching filename test is an index, not proof of every branch. The full suites and browser evidence provide behavioral verification. Optional independent-source workflows remain clearly optional.

| Source | Relation to baseline | Build evidence | Direct named test files |
| --- | --- | --- | --- |
| web/site/app.js | unchanged | builder reference | integration coverage or no direct filename match; see feature map and suites |
| web/site/explore_research_v27.js | changed | full source in bundle | integration coverage or no direct filename match; see feature map and suites |
| web/site/funding_workflow_v28.js | new | full source in bundle | integration coverage or no direct filename match; see feature map and suites |
| web/site/investment_picker_v27.js | changed | full source in bundle | integration coverage or no direct filename match; see feature map and suites |
| web/site/methods_lab_v27.js | changed | full source in bundle | integration coverage or no direct filename match; see feature map and suites |
| web/site/model.js | unchanged | full source in bundle | web/tests/public_model_evidence_v181.test.cjs, web/tests/research_models_core_v22.test.cjs, web/tests/sec_peer_model.test.cjs |
| web/site/news_context_v27.js | changed | full source in bundle | integration coverage or no direct filename match; see feature map and suites |
| web/site/news_policy_examples_v28.js | new | full source in bundle | integration coverage or no direct filename match; see feature map and suites |
| web/site/portfolio_workflow_v27.js | changed | full source in bundle | integration coverage or no direct filename match; see feature map and suites |
| web/site/private.js | changed | full source in bundle | web/tests/private_allocation_v74.test.cjs, web/tests/private_archived_sec_v99.test.cjs, web/tests/private_archive_quality_v100.test.cjs, web/tests/private_candidate_v85.test.cjs, web/tests/private_decision_center_v84.test.cjs, web/tests/private_decision_integrity_v130.test.cjs, web/tests/private_decision_review_v92.test.cjs, web/tests/private_decision_v72.test.cjs, web/tests/private_diagnostics_v66.test.cjs, web/tests/private_factor_scenarios_v86.test.cjs, web/tests/private_french_factors_v87.test.cjs, web/tests/private_guide_v79.test.cjs, web/tests/private_historical_panel_v110.test.cjs, web/tests/private_ideas_v70.test.cjs, web/tests/private_integrity_v67.test.cjs, web/tests/private_investment_intelligence_v94.test.cjs, web/tests/private_multimarket.test.cjs, web/tests/private_optimizer.test.cjs, web/tests/private_optimizer_chart.test.cjs, web/tests/private_pit_validation_v97.test.cjs, web/tests/private_portfolio_validation_v95.test.cjs, web/tests/private_predictive_ml_v180.test.cjs, web/tests/private_release_acceptance_v150.test.cjs, web/tests/private_research_brief_v93.test.cjs, web/tests/private_research_context_v651.test.cjs, web/tests/private_research_intelligence_v96.test.cjs, web/tests/private_research_orchestrator_v91.test.cjs, web/tests/private_research_os_v90.test.cjs, web/tests/private_research_v65.test.cjs, web/tests/private_risk_clarity_v75.test.cjs, web/tests/private_robustness_v120.test.cjs, web/tests/private_robustness_v68.test.cjs, web/tests/private_sec_coverage_v98.test.cjs, web/tests/private_simple_research_v170.test.cjs, web/tests/private_unified_decision_v160.test.cjs, web/tests/private_value_v73.test.cjs, web/tests/private_workflow_v140.test.cjs |
| web/site/private_allocation_v74.js | unchanged | full source in bundle | web/tests/private_allocation_v74.test.cjs |
| web/site/private_archive_quality_v100.js | unchanged | full source in bundle | web/tests/private_archive_quality_v100.test.cjs |
| web/site/private_archived_sec_v99.js | unchanged | full source in bundle | web/tests/private_archived_sec_v99.test.cjs |
| web/site/private_candidate_v85.js | unchanged | full source in bundle | web/tests/private_candidate_v85.test.cjs |
| web/site/private_decision_center_v84.js | unchanged | full source in bundle | web/tests/private_decision_center_v84.test.cjs |
| web/site/private_decision_integrity_v130.js | unchanged | full source in bundle | web/tests/private_decision_integrity_v130.test.cjs |
| web/site/private_decision_review_v92.js | unchanged | full source in bundle | web/tests/private_decision_review_v92.test.cjs |
| web/site/private_decision_v72.js | unchanged | full source in bundle | web/tests/private_decision_v72.test.cjs |
| web/site/private_diagnostics_v66.js | unchanged | full source in bundle | web/tests/private_diagnostics_v66.test.cjs |
| web/site/private_factor_scenarios_v86.js | unchanged | full source in bundle | web/tests/private_factor_scenarios_v86.test.cjs |
| web/site/private_forecast_v65.js | unchanged | full source in bundle | integration coverage or no direct filename match; see feature map and suites |
| web/site/private_french_factors_v87.js | unchanged | full source in bundle | web/tests/private_french_factors_v87.test.cjs |
| web/site/private_guide_v79.js | unchanged | full source in bundle | web/tests/private_guide_v79.test.cjs |
| web/site/private_historical_attribution_v130.js | unchanged | full source in bundle | integration coverage or no direct filename match; see feature map and suites |
| web/site/private_historical_panel_v110.js | unchanged | full source in bundle | web/tests/private_historical_panel_v110.test.cjs |
| web/site/private_ideas_v70.js | unchanged | full source in bundle | web/tests/private_ideas_v70.test.cjs |
| web/site/private_integrity_v67.js | unchanged | full source in bundle | web/tests/private_integrity_v67.test.cjs |
| web/site/private_investment_intelligence_v94.js | unchanged | full source in bundle | web/tests/private_investment_intelligence_v94.test.cjs |
| web/site/private_multimarket.js | unchanged | full source in bundle | web/tests/private_multimarket.test.cjs |
| web/site/private_optimizer.js | unchanged | full source in bundle | web/tests/private_optimizer.test.cjs, web/tests/private_optimizer_chart.test.cjs |
| web/site/private_pit_validation_v97.js | unchanged | full source in bundle | web/tests/private_pit_validation_v97.test.cjs |
| web/site/private_portfolio_validation_v95.js | unchanged | full source in bundle | web/tests/private_portfolio_validation_v95.test.cjs |
| web/site/private_predictive_ml_v180.js | unchanged | full source in bundle | web/tests/private_predictive_ml_v180.test.cjs |
| web/site/private_release_acceptance_v150.js | unchanged | full source in bundle | web/tests/private_release_acceptance_v150.test.cjs |
| web/site/private_research_brief_v93.js | unchanged | full source in bundle | web/tests/private_research_brief_v93.test.cjs |
| web/site/private_research_intelligence_v96.js | unchanged | full source in bundle | web/tests/private_research_intelligence_v96.test.cjs |
| web/site/private_research_orchestrator_v91.js | unchanged | full source in bundle | web/tests/private_research_orchestrator_v91.test.cjs |
| web/site/private_research_os_v90.js | unchanged | full source in bundle | web/tests/private_research_os_v90.test.cjs |
| web/site/private_robustness_v120.js | unchanged | full source in bundle | web/tests/private_robustness_v120.test.cjs |
| web/site/private_robustness_v68.js | unchanged | full source in bundle | web/tests/private_robustness_v68.test.cjs |
| web/site/private_sec_coverage_v98.js | unchanged | full source in bundle | web/tests/private_sec_coverage_v98.test.cjs |
| web/site/private_simple_research_v170.js | unchanged | full source in bundle | web/tests/private_simple_research_v170.test.cjs |
| web/site/private_unified_decision_v160.js | unchanged | full source in bundle | web/tests/private_unified_decision_v160.test.cjs |
| web/site/private_value_v73.js | unchanged | full source in bundle | web/tests/private_value_v73.test.cjs |
| web/site/private_walkforward_v65.js | unchanged | full source in bundle | integration coverage or no direct filename match; see feature map and suites |
| web/site/private_workflow_v140.js | unchanged | full source in bundle | web/tests/private_workflow_v140.test.cjs |
| web/site/public_evidence_v76.js | unchanged | full source in bundle | web/tests/public_evidence_v76.test.cjs |
| web/site/public_lab_v77.js | unchanged | full source in bundle | web/tests/public_lab_v77.test.cjs |
| web/site/public_model_evidence_v181.js | unchanged | full source in bundle | web/tests/public_model_evidence_v181.test.cjs |
| web/site/research_account_history_v25.js | unchanged | full source in bundle | web/tests/research_account_history_v25.test.cjs |
| web/site/research_app_v20.js | changed | full source in bundle | integration coverage or no direct filename match; see feature map and suites |
| web/site/research_compare_portfolio_v21.js | unchanged | full source in bundle | web/tests/research_compare_portfolio_v21.test.cjs |
| web/site/research_completion_v28.js | new | full source in bundle | integration coverage or no direct filename match; see feature map and suites |
| web/site/research_core_v20.js | unchanged | full source in bundle | web/tests/research_core_v20.test.cjs |
| web/site/research_deep_ui_v25.js | changed | full source in bundle | integration coverage or no direct filename match; see feature map and suites |
| web/site/research_deep_v25.js | unchanged | full source in bundle | web/tests/research_deep_v25.test.cjs |
| web/site/research_errors_v24.js | changed | full source in bundle | web/tests/research_errors_v24.test.cjs |
| web/site/research_evidence_v26.js | changed | full source in bundle | web/tests/research_evidence_v26.test.cjs |
| web/site/research_exhibits_v24.js | changed | full source in bundle | integration coverage or no direct filename match; see feature map and suites |
| web/site/research_models_core_v22.js | unchanged | full source in bundle | web/tests/research_models_core_v22.test.cjs |
| web/site/research_models_methods_ui_v22.js | changed | full source in bundle | integration coverage or no direct filename match; see feature map and suites |
| web/site/research_private_shell_v23.js | changed | full source in bundle | integration coverage or no direct filename match; see feature map and suites |
| web/site/sec_analytics.js | unchanged | full source in bundle | web/tests/sec_analytics.test.cjs |
| web/site/sec_peer_model.js | unchanged | full source in bundle | web/tests/sec_peer_model.test.cjs |
| web/site/sec_visuals_v81.js | unchanged | full source in bundle | integration coverage or no direct filename match; see feature map and suites |

Owner acceptance remains separate. The reopened Buy complaint has local reproductions and guarded fixes, but this branch is not deployed. Earlier owner confirmation does not sign off these changes.
