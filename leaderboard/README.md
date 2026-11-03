# Leaderboard sources and scope

The [interactive leaderboard](https://hfwang2001.github.io/PhysCapBench/) and repository README display the project’s report-version leaderboard snapshot. `results.json` stores exactly the same reported numbers and overall ranks.

| Domain | Strategies | Source |
|---|---:|---|
| Third-person | 11 | Project leaderboard table, checked against the archived third-person caption evaluation summary |
| Egocentric | 7 | The tech report table “Physical caption evaluation on the egocentric dataset,” checked against its seven-dimension summary and per-video records |
| Handheld grippers | — | No leaderboard results reported |

The report is **PhysCapBench: A Cross-Domain Benchmark for Physically Grounded Video Captioning**. All 144 displayed scores (seven dimensions and overall for 18 strategies) match the source summaries after rounding to two decimal places. The 56 egocentric values also match the report table directly.

These are captioning-strategy comparisons under the report's experimental setup. LingBot strategies are reconstructed from the paper description; LingBot Static is a diagnostic condition. Physis uses caption version 0921-2301, and Meta uses source captions. Strategy names retain the existing leaderboard labels.

Overall values average per-video scores over dimensions supported by that version's reference. Different dimensions can therefore have different denominators. Scores are preserved verbatim; overall is not recalculated from rounded dimension averages. Ranking is descending by the reported overall score, with ties sharing the same rank.

The released benchmark uses revised references and seven numeric scores for every video, with confidence only where reference evidence is insufficient. This snapshot is not a full 1,500-video evaluation under that release. New results should record their dataset revision, protocol hash, evaluated IDs, judge configuration and aggregation before being compared or added.

The presentation follows the project website: fixed overall order, colored dimension headers, competition ranks and medals for each metric. The interactive view supports domain switching, model location without filtering, and CSV export. No backbone labels are shown or exported. The README uses generated SVG tables with accessible text tables below them.

`results.json` is the single score source for the interactive view and SVGs. Regenerate the README images with `python leaderboard/render_readme.py`. See [paper and release correspondence](../docs/paper_alignment.md) for the repository-wide comparison.
