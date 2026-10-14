**Table 2. Calibration stage (all pairs of the 200 enrollment recordings: 900 target / 19,000 non-target)**

| Model              |   EER, % |   minDCF (P_tar=0.01) |   minDCF (P_tar=0.05) |   τ (cosine similarity) |
|:-------------------|---------:|----------------------:|----------------------:|------------------------:|
| PyAnnote           |     4.44 |                 0.074 |                 0.063 |                   0.294 |
| WavLM-base-sv      |     6.76 |                 0.385 |                 0.293 |                   0.925 |
| WavLM-base-plus-sv |     5.78 |                 0.518 |                 0.336 |                   0.916 |
| TitaNet            |     4.11 |                 0.068 |                 0.06  |                   0.326 |
| ECAPA-TDNN         |     4.67 |                 0.076 |                 0.073 |                   0.292 |

*τ is the EER threshold of the calibration set; it is frozen for all later experiments.*

**Table 4. Testing stage, bona fide trials (400 target / 7,600 zero-effort impostor)**

| Model              |   EER, % |   minDCF (0.01) |   minDCF (0.05) |   FAR at τ, % |   FRR at τ, % |   HTER at τ, % |
|:-------------------|---------:|----------------:|----------------:|--------------:|--------------:|---------------:|
| PyAnnote           |     1.5  |           0.052 |           0.045 |          6.37 |          0.75 |           3.56 |
| WavLM-base-sv      |     6.46 |           0.458 |           0.317 |          7.22 |          5.5  |           6.36 |
| WavLM-base-plus-sv |     5.01 |           0.503 |           0.327 |          6.43 |          3.75 |           5.09 |
| TitaNet            |     1.51 |           0.09  |           0.067 |          4.78 |          1    |           2.89 |
| ECAPA-TDNN         |     1.75 |           0.095 |           0.075 |          4.83 |          1.75 |           3.29 |

*EER and minDCF are threshold-free; FAR/FRR/HTER use the frozen calibration threshold τ.*

**Table 7. Attack success rate (IAPMR, %) with identical linguistic content, threshold τ; 95% CI from speaker-level bootstrap (2,000 resamples). n = 400 attacks per cell**

| Cloning tool   | PyAnnote            | WavLM-base-sv    | WavLM-base-plus-sv   | TitaNet             | ECAPA-TDNN          |
|:---------------|:--------------------|:-----------------|:---------------------|:--------------------|:--------------------|
| ElevenLabs     | 100.0 [100.0–100.0] | 96.0 [91.5–99.5] | 92.5 [86.5–97.5]     | 99.8 [99.2–100.0]   | 100.0 [100.0–100.0] |
| RVC            | 100.0 [100.0–100.0] | 79.0 [63.5–93.0] | 66.8 [49.8–82.2]     | 100.0 [100.0–100.0] | 100.0 [100.0–100.0] |
| Tortoise       | 91.2 [85.5–96.0]    | 65.8 [50.5–79.8] | 53.8 [37.7–68.8]     | 88.8 [80.0–96.5]    | 88.0 [79.2–95.0]    |
| XTTS           | 100.0 [100.0–100.0] | 79.8 [66.8–91.2] | 74.0 [59.5–86.5]     | 100.0 [100.0–100.0] | 99.8 [99.2–100.0]   |

*For reference, genuine acceptance at τ: PyAnnote 99.2%, WavLM-base-sv 94.5%, WavLM-base-plus-sv 96.2%, TitaNet 99.0%, ECAPA-TDNN 98.2%.*

**Table 8. Attack success rate (IAPMR, %) with varied linguistic content, threshold τ; 95% CI from speaker-level bootstrap (2,000 resamples). n = 400 attacks per cell**

| Cloning tool   | PyAnnote            | WavLM-base-sv     | WavLM-base-plus-sv   | TitaNet             | ECAPA-TDNN          |
|:---------------|:--------------------|:------------------|:---------------------|:--------------------|:--------------------|
| ElevenLabs     | 100.0 [100.0–100.0] | 97.5 [94.0–100.0] | 91.5 [84.5–97.0]     | 99.8 [99.2–100.0]   | 100.0 [100.0–100.0] |
| RVC            | 100.0 [100.0–100.0] | 81.5 [67.0–94.2]  | 72.8 [56.2–87.0]     | 100.0 [100.0–100.0] | 100.0 [100.0–100.0] |
| Tortoise       | 96.0 [92.5–98.8]    | 70.8 [53.8–85.2]  | 59.2 [44.8–73.0]     | 92.5 [86.5–97.2]    | 89.8 [83.5–95.0]    |
| XTTS           | 100.0 [100.0–100.0] | 79.5 [66.5–91.0]  | 72.8 [59.0–85.2]     | 100.0 [100.0–100.0] | 100.0 [100.0–100.0] |

*For reference, genuine acceptance at τ: PyAnnote 99.2%, WavLM-base-sv 94.5%, WavLM-base-plus-sv 96.2%, TitaNet 99.0%, ECAPA-TDNN 98.2%.*

**Table 9. Attack success (IAPMR) and genuine rejection (FRR) at three operating points (identical + varied content, 800 attacks per tool)**

| Operating point   | Model              |   FRR (genuine), % |   IAPMR ElevenLabs, % |   IAPMR RVC, % |   IAPMR Tortoise, % |   IAPMR XTTS, % |
|:------------------|:-------------------|-------------------:|----------------------:|---------------:|--------------------:|----------------:|
| τ (EER)           | PyAnnote           |                0.8 |                 100   |          100   |                93.6 |           100   |
| τ (EER)           | WavLM-base-sv      |                5.5 |                  96.8 |           80.2 |                68.2 |            79.6 |
| τ (EER)           | WavLM-base-plus-sv |                3.8 |                  92   |           69.8 |                56.5 |            73.4 |
| τ (EER)           | TitaNet            |                1   |                  99.8 |          100   |                90.6 |           100   |
| τ (EER)           | ECAPA-TDNN         |                1.8 |                 100   |          100   |                88.9 |            99.9 |
| FAR = 1%          | PyAnnote           |                1.5 |                  99.6 |          100   |                77.1 |            99.2 |
| FAR = 1%          | WavLM-base-sv      |               18   |                  72   |           48.2 |                36.5 |            49.8 |
| FAR = 1%          | WavLM-base-plus-sv |               17.5 |                  53.5 |           30   |                18.6 |            30.4 |
| FAR = 1%          | TitaNet            |                2.2 |                  99.6 |          100   |                66.6 |            99.8 |
| FAR = 1%          | ECAPA-TDNN         |                2   |                  99.5 |           99.4 |                66.6 |            92   |
| FAR = 0.1%        | PyAnnote           |                3.5 |                  98.9 |           99.6 |                60.2 |            92.1 |
| FAR = 0.1%        | WavLM-base-sv      |               39.8 |                  32.6 |           17.6 |                11.8 |            17.5 |
| FAR = 0.1%        | WavLM-base-plus-sv |               45.8 |                  16   |            5.1 |                 2.2 |             6.4 |
| FAR = 0.1%        | TitaNet            |                5.8 |                  94.9 |           94.1 |                26.5 |            74.6 |
| FAR = 0.1%        | ECAPA-TDNN         |                6.5 |                  85.5 |           84.8 |                29.1 |            70   |

*FAR = 1% and 0.1% thresholds are set on the 7,600 zero-effort impostor trials.*

**Table 10. Spoof-EER (%), genuine target trials vs. cloned attacks, threshold-free**

| Model              |   ElevenLabs |   RVC |   Tortoise |   XTTS |
|:-------------------|-------------:|------:|-----------:|-------:|
| PyAnnote           |         33   |  32   |       16.5 |   24.5 |
| WavLM-base-sv      |         36.1 |  29   |       24.8 |   29.8 |
| WavLM-base-plus-sv |         30.5 |  21.2 |       18.2 |   21.7 |
| TitaNet            |         23   |  27.9 |       13.1 |   17   |
| ECAPA-TDNN         |         25.1 |  29   |       12.5 |   21   |

*50% = clones indistinguishable from genuine speech; 0% = perfect separation.*

**Table 11. Effect of linguistic content (speaker-level paired Wilcoxon signed-rank test, 20 speakers; Holm correction over 20 tests)**

| Cloning tool   | Model              |   Identical, % |   Varied, % |   Δ (identical − varied), pp |   p (Wilcoxon) |   p (Holm) |
|:---------------|:-------------------|---------------:|------------:|-----------------------------:|---------------:|-----------:|
| ElevenLabs     | PyAnnote           |          100   |       100   |                         0    |          1     |      1     |
| ElevenLabs     | WavLM-base-sv      |           96   |        97.5 |                        -1.5  |          0.167 |      1     |
| ElevenLabs     | WavLM-base-plus-sv |           92.5 |        91.5 |                         1    |          0.418 |      1     |
| ElevenLabs     | TitaNet            |           99.8 |        99.8 |                         0    |          1     |      1     |
| ElevenLabs     | ECAPA-TDNN         |          100   |       100   |                         0    |          1     |      1     |
| RVC            | PyAnnote           |          100   |       100   |                         0    |          1     |      1     |
| RVC            | WavLM-base-sv      |           79   |        81.5 |                        -2.5  |          0.245 |      1     |
| RVC            | WavLM-base-plus-sv |           66.7 |        72.7 |                        -6    |          0.014 |      0.34  |
| RVC            | TitaNet            |          100   |       100   |                         0    |          1     |      1     |
| RVC            | ECAPA-TDNN         |          100   |       100   |                         0    |          1     |      1     |
| Tortoise       | PyAnnote           |           91.2 |        96   |                        -4.75 |          0.04  |      0.914 |
| Tortoise       | WavLM-base-sv      |           65.8 |        70.7 |                        -5    |          0.087 |      1     |
| Tortoise       | WavLM-base-plus-sv |           53.8 |        59.2 |                        -5.5  |          0.04  |      0.914 |
| Tortoise       | TitaNet            |           88.8 |        92.5 |                        -3.75 |          0.144 |      1     |
| Tortoise       | ECAPA-TDNN         |           88   |        89.8 |                        -1.75 |          0.347 |      1     |
| XTTS           | PyAnnote           |          100   |       100   |                         0    |          1     |      1     |
| XTTS           | WavLM-base-sv      |           79.8 |        79.5 |                         0.25 |          0.969 |      1     |
| XTTS           | WavLM-base-plus-sv |           74   |        72.7 |                         1.25 |          0.806 |      1     |
| XTTS           | TitaNet            |          100   |       100   |                         0    |          1     |      1     |
| XTTS           | ECAPA-TDNN         |           99.8 |       100   |                        -0.25 |          0.317 |      1     |

**Table 12. AASIST countermeasure (ASVspoof 2019 LA weights): CM-EER and APCER at BPCER = 5%**

| Condition           | ElevenLabs CM-EER / APCER, %   | RVC CM-EER / APCER, %   | Tortoise CM-EER / APCER, %   | XTTS CM-EER / APCER, %   |
|:--------------------|:-------------------------------|:------------------------|:-----------------------------|:-------------------------|
| Clean               | 37.0 / 95.8                    | 22.5 / 93.5             | 38.7 / 99.2                  | 23.9 / 92.0              |
| White noise 20 dB   | 45.0 / 98.4                    | 29.0 / 97.4             | 50.1 / 99.5                  | 32.7 / 96.1              |
| White noise 10 dB   | 48.8 / 98.2                    | 28.1 / 89.2             | 55.1 / 98.9                  | 32.5 / 93.5              |
| G.711 (8 kHz μ-law) | 37.7 / 96.2                    | 20.0 / 94.2             | 38.9 / 98.6                  | 24.5 / 93.8              |

*The CM threshold is set on bona fide test audio only (5% of genuine recordings rejected).*

**Table 13. Cascaded system: speaker verification (threshold τ) followed by AASIST (BPCER = 5%), clean condition**

| Model              | FRR SV → SV+CM, %   | IAPMR ElevenLabs: SV → SV+CM, %   | IAPMR RVC: SV → SV+CM, %   | IAPMR Tortoise: SV → SV+CM, %   | IAPMR XTTS: SV → SV+CM, %   |
|:-------------------|:--------------------|:----------------------------------|:---------------------------|:--------------------------------|:----------------------------|
| PyAnnote           | 0.7 → 5.5           | 100.0 → 95.8                      | 100.0 → 93.5               | 93.6 → 93.1                     | 100.0 → 92.0                |
| WavLM-base-sv      | 5.5 → 9.8           | 96.8 → 92.8                       | 80.2 → 75.1                | 68.2 → 67.6                     | 79.6 → 75.1                 |
| WavLM-base-plus-sv | 3.7 → 8.2           | 92.0 → 87.9                       | 69.8 → 65.0                | 56.5 → 56.1                     | 73.4 → 69.2                 |
| TitaNet            | 1.0 → 6.0           | 99.8 → 95.6                       | 100.0 → 93.5               | 90.6 → 89.9                     | 100.0 → 92.0                |
| ECAPA-TDNN         | 1.7 → 6.8           | 100.0 → 95.8                      | 100.0 → 93.5               | 88.9 → 88.2                     | 99.9 → 91.9                 |

**Table 14. Degraded acoustic conditions (applied to test and attack audio; enrollment and τ from clean audio)**

| Model              | Metric                      | Clean     | White noise 20 dB   | White noise 10 dB   | G.711 (8 kHz μ-law)   |
|:-------------------|:----------------------------|:----------|:--------------------|:--------------------|:----------------------|
| PyAnnote           | Bona fide EER / FRR at τ, % | 1.5 / 0.8 | 1.7 / 0.5           | 2.5 / 2.0           | 4.7 / 5.0             |
|                    | IAPMR ElevenLabs, %         | 100.0     | 99.6                | 99.6                | 95.8                  |
|                    | IAPMR RVC, %                | 100.0     | 100.0               | 96.2                | 78.5                  |
|                    | IAPMR Tortoise, %           | 93.6      | 90.9                | 84.6                | 66.8                  |
|                    | IAPMR XTTS, %               | 100.0     | 99.8                | 97.2                | 78.1                  |
| WavLM-base-sv      | Bona fide EER / FRR at τ, % | 6.5 / 5.5 | 9.5 / 18.2          | 15.5 / 44.2         | 9.0 / 12.2            |
|                    | IAPMR ElevenLabs, %         | 96.8      | 90.8                | 63.2                | 92.9                  |
|                    | IAPMR RVC, %                | 80.2      | 65.1                | 31.9                | 70.5                  |
|                    | IAPMR Tortoise, %           | 68.2      | 59.6                | 36.8                | 62.1                  |
|                    | IAPMR XTTS, %               | 79.6      | 63.0                | 48.0                | 70.8                  |
| WavLM-base-plus-sv | Bona fide EER / FRR at τ, % | 5.0 / 3.8 | 5.8 / 7.0           | 8.2 / 22.8          | 5.7 / 5.2             |
|                    | IAPMR ElevenLabs, %         | 92.0      | 90.6                | 76.8                | 94.4                  |
|                    | IAPMR RVC, %                | 69.8      | 56.2                | 38.8                | 68.9                  |
|                    | IAPMR Tortoise, %           | 56.5      | 45.8                | 33.1                | 55.5                  |
|                    | IAPMR XTTS, %               | 73.4      | 67.1                | 56.0                | 69.9                  |
| TitaNet            | Bona fide EER / FRR at τ, % | 1.5 / 1.0 | 1.0 / 0.2           | 1.5 / 0.5           | 2.7 / 2.5             |
|                    | IAPMR ElevenLabs, %         | 99.8      | 99.8                | 99.6                | 99.2                  |
|                    | IAPMR RVC, %                | 100.0     | 100.0               | 99.9                | 99.5                  |
|                    | IAPMR Tortoise, %           | 90.6      | 88.8                | 84.2                | 69.5                  |
|                    | IAPMR XTTS, %               | 100.0     | 100.0               | 99.1                | 89.4                  |
| ECAPA-TDNN         | Bona fide EER / FRR at τ, % | 1.7 / 1.8 | 1.3 / 0.5           | 3.0 / 2.0           | 4.7 / 4.8             |
|                    | IAPMR ElevenLabs, %         | 100.0     | 99.8                | 99.0                | 99.5                  |
|                    | IAPMR RVC, %                | 100.0     | 100.0               | 96.6                | 99.4                  |
|                    | IAPMR Tortoise, %           | 88.9      | 82.9                | 79.1                | 78.8                  |
|                    | IAPMR XTTS, %               | 99.9      | 95.4                | 93.6                | 90.4                  |

**Table 15. Computational cost (CPU inference, Apple M4 Pro, 14 cores; mean recording length 8.0 s)**

| Model              |   Parameters, M | Time per recording, ms (mean ± sd)   |   Real-time factor |
|:-------------------|----------------:|:-------------------------------------|-------------------:|
| PyAnnote           |             4.3 | 6 ± 2                                |             0.0008 |
| WavLM-base-sv      |           101.1 | 142 ± 81                             |             0.0186 |
| WavLM-base-plus-sv |           101.1 | 123 ± 65                             |             0.016  |
| TitaNet            |            25.3 | 141 ± 103                            |             0.021  |
| ECAPA-TDNN         |            22.2 | 28 ± 11                              |             0.0038 |
| AASIST (CM)        |             0.3 | 111 ± 51                             |             0.0149 |

*Embedding extraction only; cosine scoring against a stored voiceprint adds < 0.1 ms. Parameter counts include the models' classification heads where present.*

**Table 16. Gender-disaggregated and per-speaker attack success (all tools, both content conditions, clean)**

| Model              |   IAPMR male, % |   IAPMR female, % |   p (Mann–Whitney, speakers) | Per-speaker IAPMR, mean ± sd, %   | Min–max, %   |
|:-------------------|----------------:|------------------:|-----------------------------:|:----------------------------------|:-------------|
| PyAnnote           |            98.8 |              98.1 |                        0.119 | 98.4 ± 2.3                        | 91.9–100.0   |
| WavLM-base-sv      |            72.7 |              89.8 |                        0.049 | 81.2 ± 16.3                       | 54.4–100.0   |
| WavLM-base-plus-sv |            66.6 |              79.2 |                        0.045 | 72.9 ± 15.4                       | 36.9–99.4    |
| TitaNet            |            97.9 |              97.3 |                        0.194 | 97.6 ± 4.0                        | 88.8–100.0   |
| ECAPA-TDNN         |            98.3 |              96.1 |                        0.089 | 97.2 ± 4.0                        | 85.0–100.0   |
