# Data sources and terms

The dataset combines materials with different terms. There is no single unrestricted license for all videos. Keep this notice, `provenance.jsonl` with any redistribution. Downstream recipients must retain those attributions and comply with the applicable upstream terms.

| Domain | Source and credit | Video terms |
|---|---|---|
| Third-person | PhysCapBench contributor-collected videos | The contributors have authorized public distribution of these selected videos for the benchmark. Underlying source rights are retained; this statement does not grant additional rights in third-party material. |
| Egocentric | [EgoDex, Apple](https://github.com/apple-aiml-research/ml-egodex) | The [upstream README](https://github.com/apple-aiml-research/ml-egodex#license) specifies CC BY-NC-ND for the dataset without specifying a version. This statement concerns the data, not the separate Apple software license. The selected original MP4 files are distributed unchanged, with benchmark IDs as filenames. |
| Handheld grippers | [Hy-Embodied-0.5-VLA-Data, Tencent Robotics X and Tencent Hy Team](https://huggingface.co/datasets/tencent/Hy-Embodied-0.5-VLA-Data) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Selected episodes are rendered as three-view composite videos (left wrist, high, right wrist). |

The third-person source declaration is supplied by the PhysCapBench contributors. `provenance.jsonl` retains the selection clip and source-group identifiers. For EgoDex, it gives the original archive URL and member path. For gripper episodes, it gives the source repository, immutable revision, table and episode index. Selection and processing changes are recorded per sample.

Benchmark-authored annotations, supplements and selection metadata are provided under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) by the PhysCapBench contributors. This applies only to their original contributions; it does not replace upstream rights or terms for source material reproduced in an annotation. Attribute PhysCapBench and retain the source-specific credits. Corrections and additions are identified in `supplements.jsonl`.

The evaluation software in the [GitHub repository](https://github.com/hfwang2001/PhysCapBench) is separately licensed under MIT. Its license does not license the videos or the paper artwork. The data are provided for benchmark research; users must follow each applicable source's restrictions, including non-commercial and no-derivatives conditions where stated.
