# slmsuite 0.5.0: transport seed vs quadratic + remove_vortices

slmsuite 0.5.0 (/home/mike/slmsuite-0.5.0/slmsuite/__init__.py), numpy 2.4.6, SLM 256px, farfield 512px, 100 iterations, 5 seeds per config (target center jittered +-6 px, random phase reseeded), 8 single-threaded workers on 16 vCPU. remove_vortices every 10 iterations via the docstring callback.

## controls

- runs whose timed and traced repeats disagreed: 0 of 270
- WGS-Leonardo quadratic+rv final phase bit-identical to quadratic: 30 of 30
- WGS-Kim quadratic+rv final phase differs from quadratic: 30 of 30
- WGS-Kim, phase fixed: vortices in stored phase_ff (target>0 mask) per removal call, median 23 -> 22

## results (median over seeds, [min-max] for vortices)

fidelity = slmsuite's computational overlap stat. ripple = std/mean of I/I_target in the 50% support. time = seed + all iterations. to-threshold columns: iterations (and seconds incl. seed) until fidelity >= F and ripple <= r, `-` = not reached in 100 its in any seed, `k/n` = reached in k of n seeds (median over those).

| target | method | arm | vortices | fidelity | ripple | time s | its/s to F.95 r.20 | its/s to F.99 r.10 |
|---|---|---|---|---|---|---|---|---|
| flattop_center | WGS-Leonardo | random | 80 [77-86] | 0.876 | 0.435 | 2.8 | - | - |
| flattop_center | WGS-Leonardo | quadratic | 45 [35-64] | 0.906 | 0.401 | 2.9 | - | - |
| flattop_center | WGS-Leonardo | quadratic+rv | 45 [35-64] | 0.906 | 0.401 | 13.4 | - | - |
| flattop_center | WGS-Leonardo | ot | 0 [0-0] | 0.999 | 0.008 | 3.8 | 1 / 0.7 | 2 / 0.7 |
| flattop_center | WGS-Kim | random | 203 [200-227] | 0.619 | 3.505 | 2.8 | - | - |
| flattop_center | WGS-Kim | quadratic | 129 [99-264] | 0.698 | 4.202 | 2.6 | - | - |
| flattop_center | WGS-Kim | quadratic+rv | 94 [72-111] | 0.656 | 2.948 | 5.1 | - | - |
| flattop_center | WGS-Kim | ot | 0 [0-0] | 0.997 | 0.039 | 3.7 | 1 / 0.7 | 2 / 0.7 |
| flattop_center | WGS-Kim | ot+rv | 58 [23-81] | 0.731 | 6.804 | 4.8 | 1 / 0.7 | 2 / 0.8 |
| flattop_offcenter | WGS-Leonardo | random | 46 [40-52] | 0.875 | 0.442 | 2.8 | - | - |
| flattop_offcenter | WGS-Leonardo | quadratic | 15 [10-22] | 0.934 | 0.235 | 2.8 | - | - |
| flattop_offcenter | WGS-Leonardo | quadratic+rv | 15 [10-22] | 0.934 | 0.235 | 9.0 | - | - |
| flattop_offcenter | WGS-Leonardo | ot | 0 [0-0] | 1.000 | 0.008 | 3.6 | 2 / 0.5 | 2 / 0.5 |
| flattop_offcenter | WGS-Kim | random | 112 [99-120] | 0.656 | 2.395 | 2.8 | - | - |
| flattop_offcenter | WGS-Kim | quadratic | 54 [44-63] | 0.698 | 3.826 | 2.8 | - | - |
| flattop_offcenter | WGS-Kim | quadratic+rv | 45 [39-52] | 0.709 | 2.773 | 4.1 | - | - |
| flattop_offcenter | WGS-Kim | ot | 0 [0-0] | 0.998 | 0.027 | 3.5 | 2 / 0.5 | 2 / 0.5 |
| flattop_offcenter | WGS-Kim | ot+rv | 27 [23-34] | 0.867 | 1.449 | 4.4 | 2 / 0.5 | 2 / 0.5 |
| flattop_small_offcenter | WGS-Leonardo | random | 7 [6-17] | 0.904 | 0.305 | 2.8 | - | - |
| flattop_small_offcenter | WGS-Leonardo | quadratic | 1 [0-3] | 0.981 | 0.121 | 2.9 | 15 / 0.4 | - |
| flattop_small_offcenter | WGS-Leonardo | quadratic+rv | 1 [0-3] | 0.981 | 0.121 | 6.5 | 15 / 1.0 | - |
| flattop_small_offcenter | WGS-Leonardo | ot | 0 [0-0] | 0.999 | 0.011 | 3.3 | 1 / 0.2 | 2 / 0.2 |
| flattop_small_offcenter | WGS-Kim | random | 31 [25-36] | 0.578 | 3.100 | 2.8 | - | - |
| flattop_small_offcenter | WGS-Kim | quadratic | 3 [1-4] | 0.914 | 0.510 | 2.7 | 12 / 0.3 (2/5) | - |
| flattop_small_offcenter | WGS-Kim | quadratic+rv | 12 [2-27] | 0.880 | 0.693 | 3.2 | 12 / 0.4 (2/5) | - |
| flattop_small_offcenter | WGS-Kim | ot | 0 [0-3] | 0.987 | 0.064 | 3.2 | 1 / 0.2 | 2 / 0.2 (4/5) |
| flattop_small_offcenter | WGS-Kim | ot+rv | 10 [8-20] | 0.719 | 2.251 | 4.1 | 1 / 0.2 | 2 / 0.3 (4/5) |
| ring_mraf_center | WGS-Leonardo | random | 13 [11-14] | 0.579 | 0.220 | 2.2 | - | - |
| ring_mraf_center | WGS-Leonardo | quadratic | 0 [0-0] | 0.944 | 0.001 | 2.1 | - | - |
| ring_mraf_center | WGS-Leonardo | quadratic+rv | 0 [0-0] | 0.944 | 0.001 | 3.3 | - | - |
| ring_mraf_center | WGS-Leonardo | ot | 1 [0-2] | 0.865 | 0.046 | 2.4 | - | - |
| ring_mraf_center | WGS-Kim | random | 101 [86-112] | 0.054 | 3.455 | 2.1 | - | - |
| ring_mraf_center | WGS-Kim | quadratic | 0 [0-0] | 0.721 | 0.025 | 2.0 | - | - |
| ring_mraf_center | WGS-Kim | quadratic+rv | 0 [0-0] | 0.542 | 0.011 | 3.1 | - | - |
| ring_mraf_center | WGS-Kim | ot | 3 [1-6] | 0.566 | 0.169 | 2.3 | - | - |
| ring_mraf_center | WGS-Kim | ot+rv | 0 [0-0] | 0.521 | 0.012 | 3.4 | - | - |
| ring_offcenter | WGS-Leonardo | random | 2 [2-6] | 0.875 | 0.190 | 3.1 | - | - |
| ring_offcenter | WGS-Leonardo | quadratic | 0 [0-1] | 0.972 | 0.018 | 3.1 | 8 / 0.3 | - |
| ring_offcenter | WGS-Leonardo | quadratic+rv | 0 [0-1] | 0.972 | 0.018 | 4.0 | 8 / 0.3 | - |
| ring_offcenter | WGS-Leonardo | ot | 0 [0-0] | 0.971 | 0.043 | 3.3 | 19 / 0.9 | - |
| ring_offcenter | WGS-Kim | random | 27 [22-31] | 0.629 | 2.800 | 3.0 | - | - |
| ring_offcenter | WGS-Kim | quadratic | 0 [0-0] | 0.940 | 0.209 | 3.0 | 8 / 0.3 | - |
| ring_offcenter | WGS-Kim | quadratic+rv | 6 [5-17] | 0.773 | 1.933 | 3.7 | 8 / 0.3 | - |
| ring_offcenter | WGS-Kim | ot | 3 [1-5] | 0.877 | 0.510 | 3.3 | - | - |
| ring_offcenter | WGS-Kim | ot+rv | 8 [8-14] | 0.706 | 1.974 | 4.2 | - | - |
| twobars_offcenter | WGS-Leonardo | random | 16 [12-23] | 0.869 | 0.342 | 2.7 | - | - |
| twobars_offcenter | WGS-Leonardo | quadratic | 8 [7-12] | 0.904 | 0.203 | 2.7 | - | - |
| twobars_offcenter | WGS-Leonardo | quadratic+rv | 8 [7-12] | 0.904 | 0.203 | 7.4 | - | - |
| twobars_offcenter | WGS-Leonardo | ot | 0 [0-2] | 0.972 | 0.008 | 3.4 | 31 / 1.3 | - |
| twobars_offcenter | WGS-Kim | random | 56 [51-62] | 0.617 | 3.181 | 2.6 | - | - |
| twobars_offcenter | WGS-Kim | quadratic | 26 [20-31] | 0.750 | 1.828 | 2.7 | - | - |
| twobars_offcenter | WGS-Kim | quadratic+rv | 23 [21-45] | 0.738 | 1.575 | 3.7 | - | - |
| twobars_offcenter | WGS-Kim | ot | 5 [4-7] | 0.917 | 0.493 | 3.4 | - | - |
| twobars_offcenter | WGS-Kim | ot+rv | 15 [2-16] | 0.778 | 2.255 | 3.8 | - | - |

## cost

- WGS-Leonardo ot: seed 0.40 s, 100 iterations 3.09 s (median)
- WGS-Leonardo quadratic: seed 0.01 s, 100 iterations 2.83 s (median)
- WGS-Leonardo quadratic+rv: seed 0.01 s, 100 iterations 6.76 s (median)
- WGS-Kim quadratic+rv: seed 0.01 s, 100 iterations 3.66 s (median)

## WGS-Kim fairness checks (`kimcheck_v050.py`, 2 seeds each)

Kim degrades on these extended targets whatever the seed, so two possible excuses were tested.

| check | arm | vortices | fidelity | ripple |
|---|---|---|---|---|
| hard-edged flat top (no tanh tail), off-center | quadratic | 54, 60 | 0.645, 0.489 | 4.55, 7.14 |
| | quadratic+rv | 43, 21 | 0.692, 0.738 | 1.70, 1.10 |
| | ot | 0, 0 | 0.944, 0.940 | 0.24, 0.26 |
| smooth off-center flat top, fix_phase_iteration=30 | quadratic | 24, 24 | 0.834, 0.853 | 1.60, 1.08 |
| | quadratic+rv | 43, 39 | 0.647, 0.669 | 2.90, 2.68 |
| | ot | 0, 0 | 0.999, 0.999 | 0.014, 0.011 |

Neither the soft tail nor an early phase fix explains it. With the fix at 30, removal makes quadratic worse.
