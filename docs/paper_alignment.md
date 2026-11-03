# Paper and release correspondence

Checked on 2026-11-03 against the supplied Overleaf source archive for **PhysCapBench: A Cross-Domain Benchmark for Physically Grounded Video Captioning** (archive suffix `(11)`). This comparison covers all tracked release files and the repository description; it does not audit the underlying experimental validity of every paper claim.

| Item | Correspondence |
|---|---|
| Title and scope | Same title; third-person physical scenes, egocentric human manipulation, and human-operated handheld grippers. |
| Dataset size | 500 sequences in each domain, 1,500 total. One multi-view episode counts once. |
| Dimensions | Same seven dimensions as the paper’s physical-dimension table. |
| Judge | Same Doubao Seed 2.1 Pro model identifier; temperature zero, thinking disabled. |
| Scoring rubric | Same 0–100 integer range and five agreement/coverage bands. Extra facts absent from the reference receive neither credit nor a penalty unless contradictory. |
| Egocentric leaderboard | All 56 displayed values match the paper’s egocentric caption-evaluation table. |
| Third-person leaderboard | All 88 values match the project website table and archived evaluation summary. The paper presents a radar figure; its textual headline values and leaders agree. Values were not estimated from the plot. |
| Handheld-gripper leaderboard | No reported caption-strategy ranking in the paper; no scores added. |
| Overview | Exported from the paper’s original overview figure. |

## Release-specific choices

The released evaluator is not an exact implementation of the paper’s reported evaluation snapshot:

- **Aggregation and insufficient evidence:** the paper’s task-definition equation and evaluation appendix average only assessable reference dimensions. The release assigns all seven numeric scores and adds confidence only for insufficient-reference dimensions. With no directional evidence it uses score 50 and confidence 0. Confidence never changes the weights. This was a subsequent release design choice.
- **Scoring references:** the paper’s egocentric experiment uses the short `goldCaptionEn` for six dimensions and structured mechanism statements for mechanisms and causality. The release instead scores against its pinned `references.jsonl`, which contains the exported reference fields and recorded corrections/supplements. These reference snapshots are not interchangeable. The paper’s annotation-review description must not be taken as independent verification of subsequent release corrections.
- **Released inputs:** the paper’s annotation workflow uses hand tracking, interaction detections and gripper trajectories. This package supplies the videos and annotation/reference text for caption evaluation, not those raw auxiliary arrays. The gripper video is a left-wrist / high / right-wrist composite.
- **Caption generation:** the CLI’s eight-frame example is an integration helper. It does not reproduce the paper’s individual baseline prompts or sampling recipes.
- **Downstream studies:** the overview includes reconstruction and policy studies. Their training/generation pipelines are not included in this caption-evaluation repository.
- **Validation results:** `VALIDATION.json` records installation, data integrity and integration checks. Its smoke-test scores are not paper results or leaderboard entries.

The frozen protocol retains historical third-person identifiers in `version` and `reference_version`. These identify its origin, not the release’s current domain coverage. `dataset.lock.json` and the per-sample reference records define the three-domain release. The protocol bytes remain pinned to the published applicability evidence.

The public README, interactive leaderboard and downloadable leaderboard results keep the report-version scores separate from the revised evaluator. Matching the published historical scores requires the original references, candidate captions, evaluated IDs and aggregation, not just running the example generator.
