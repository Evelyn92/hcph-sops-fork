# ET QC Check Form: Subjects 0040-0050

Generated: 2026-07-07 12:17:38

Source scope: local MREye2.0 outputs under `/Users/cag/Documents/forclone/hcph-sops-fork/code/mreye2p0_programs` plus mounted raw/source files under `/Volumes/FS_PROJETS/MatTechLab/yiwei.jia/datasets`.

## Coverage Definitions

- `fixation_coverage_all_samples`, `blink_coverage_all_samples`, and `saccade_coverage_all_samples` are ratios against the full sample timeline reported by S1/S2, not only valid gaze-coordinate samples.
- `coord_nan_x`, `coord_nan_y`, and `coord_nan_max` are coordinate invalid/missing ratios across the full sample timeline.
- `both_xy_valid_estimate` is approximated as `1 - max(coord_nan_x, coord_nan_y)` because the local summaries store x/y NaN ratios but not exact x/y joint-valid counts for all subjects.
- `final_preserved_ratio_crit*` is the final distance-and-low-motion mask preserved ratio before offset, from the S2 metadata/summary for each criterion.
- `raw_data_status=raw_edf_only` means a raw EDF exists on the mounted dataset, but local TSV/S1/S2 QC outputs are absent in this workspace.

## Append Notes

Append future subjects as new rows using the same CSV header in `et_qc.csv`. For Markdown, append to the Summary Table and Full Rates Table with the same column order. Keep `qc_source_status=available` when S2 summaries/metadata are present; use `missing_local_qc` when a subject still needs processing.

## Rating Heuristic

- `Good`: low coordinate dropout, good preserved ratio, and no major automated event-profile concern.
- `Usable with caution`: moderate dropout, moderate preserved ratio, or elevated blink/non-fixation.
- `Poor`: high dropout, low preserved ratio, or strong blink/non-fixation abnormality.
- `Fail`: severe coordinate dropout or very low preserved ratio, likely unreliable for ET mask-based binning.
- `Missing QC`: raw/source data or subject row exists, but no local S2 QC output is available yet.

Rating counts: Fail: 3, Good: 7, Missing QC: 3, Poor: 3, Usable with caution: 5

## Summary Table

| subject_id | scan_type | mid | raw_data_status | qc_source_status | general_rating | coord_nan_max | both_xy_valid_estimate | fixation_coverage_all_samples | blink_coverage_all_samples | saccade_coverage_all_samples | nonfix_fraction_all_samples | final_preserved_ratio_crit0.2 | assumption | important_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0040 | T1w | MID40081 | raw_edf_only | missing_local_qc | Missing QC |  |  |  |  |  |  |  | Raw EDF exists but S1/S2 outputs are absent locally. | run S1 then S2 before rating ET quality |
| 0040 | T2w | MID40087 | raw_edf_only | missing_local_qc | Missing QC |  |  |  |  |  |  |  | Raw EDF exists but S1/S2 outputs are absent locally. | run S1 then S2 before rating ET quality |
| 0041 | T1w | MID41569 | s1_available | available | Good | 0.0056 | 0.9944 | 0.9895 | 0.0096 | 0.0105 | 0.0111 | 0.8835 | stable fixation/tracking likely | low coordinate dropout; good preserved ratio at crit0.2 |
| 0041 | T2w | MID41563 | s1_available | available | Good | 0.0197 | 0.9803 | 0.9601 | 0.0311 | 0.0399 | 0.0220 | 0.8415 | stable fixation/tracking likely | low coordinate dropout; good preserved ratio at crit0.2 |
| 0042 | T1w | MID42075 | s1_available | available | Poor | 0.1396 | 0.8604 | 0.7630 | 0.1874 | 0.2294 | 0.2358 | 0.3197 | no major automated QC concern from local summaries | moderate coordinate dropout; low preserved ratio at crit0.2 |
| 0042 | T2w | MID42071 | s1_available | available | Usable with caution | 0.0878 | 0.9122 | 0.8251 | 0.1399 | 0.1749 | 0.1492 | 0.5835 | stable fixation/tracking likely | low coordinate dropout; moderate preserved ratio at crit0.2 |
| 0043 | T1w | MID43114 | s1_available | available | Good | 0.0430 | 0.9570 | 0.9256 | 0.0601 | 0.0744 | 0.0663 | 0.6509 | stable fixation/tracking likely | low coordinate dropout; good preserved ratio at crit0.2 |
| 0043 | T2w | MID43119 | s1_available | available | Usable with caution | 0.0921 | 0.9079 | 0.8700 | 0.1211 | 0.1297 | 0.1290 | 0.5077 | stable fixation/tracking likely | low coordinate dropout; moderate preserved ratio at crit0.2 |
| 0044 | T1w | MID44240 | s1_available | available | Good | 0.0464 | 0.9536 | 0.9055 | 0.0769 | 0.0945 | 0.0858 | 0.6977 | stable fixation/tracking likely | low coordinate dropout; good preserved ratio at crit0.2 |
| 0044 | T2w | MID44236 | s1_available | available | Good | 0.0392 | 0.9608 | 0.9271 | 0.0465 | 0.0729 | 0.0603 | 0.6576 | stable fixation/tracking likely | low coordinate dropout; good preserved ratio at crit0.2 |
| 0045 | T1w | MID45069 | s1_available | available | Usable with caution | 0.0806 | 0.9194 | 0.8716 | 0.1105 | 0.1284 | 0.1266 | 0.4241 | stable fixation/tracking likely | low coordinate dropout; moderate preserved ratio at crit0.2 |
| 0045 | T2w | MID45065 | s1_available | available | Usable with caution | 0.0842 | 0.9158 | 0.8603 | 0.1317 | 0.1392 | 0.1203 | 0.5358 | stable fixation/tracking likely | low coordinate dropout; moderate preserved ratio at crit0.2 |
| 0046 |  |  | missing_dataset_dir | missing_local_qc | Missing QC |  |  |  |  |  |  |  | No mounted subject dataset directory found for this subject. | verify whether subject was skipped or stored elsewhere |
| 0047 | T1w | MID47040 | s1_available | available | Good | 0.0175 | 0.9825 | 0.9702 | 0.0238 | 0.0295 | 0.0300 | 0.7064 | stable fixation/tracking likely | low coordinate dropout; good preserved ratio at crit0.2 |
| 0047 | T2w | MID47036 | s1_available | available | Usable with caution | 0.0420 | 0.9580 | 0.9269 | 0.0512 | 0.0721 | 0.0572 | 0.4784 | stable fixation/tracking likely | low coordinate dropout; moderate preserved ratio at crit0.2 |
| 0048 | T1w | MID48377 | s1_available | available | Fail | 0.7205 | 0.2795 | 0.1400 | 0.8235 | 0.8447 | 0.7878 | 0.1441 | likely eye closure/sleepiness or major tracking loss; blink-heavy run; saccade/non-fixation-heavy run; large non-fixation fraction | severe coordinate dropout; very low preserved ratio at crit0.2 |
| 0048 | T2w | MID48373 | s1_available | available | Poor | 0.1673 | 0.8327 | 0.3645 | 0.4535 | 0.6344 | 0.5738 | 0.2113 | blink-heavy run; saccade/non-fixation-heavy run; large non-fixation fraction | moderate coordinate dropout; low preserved ratio at crit0.2 |
| 0049 | T1w | MID49036 | s1_available | available | Fail | 0.3143 | 0.6857 | 0.2353 | 0.5727 | 0.7642 | 0.6561 | 0.1343 | partial tracking loss; inspect before using as primary ET binning evidence; blink-heavy run; saccade/non-fixation-heavy run; large non-fixation fraction | high coordinate dropout; very low preserved ratio at crit0.2 |
| 0049 | T2w | MID49059 | s1_available | available | Fail | 0.4293 | 0.5707 | 0.4362 | 0.4493 | 0.4868 | 0.5172 | 0.1045 | partial tracking loss; inspect before using as primary ET binning evidence; large non-fixation fraction | high coordinate dropout; very low preserved ratio at crit0.2 |
| 0050 | T1w | MID50102 | s1_available | available | Good | 0.0623 | 0.9377 | 0.9007 | 0.0778 | 0.0990 | 0.0656 | 0.6208 | stable fixation/tracking likely | low coordinate dropout; good preserved ratio at crit0.2 |
| 0050 | T2w | MID50107 | s1_available | available | Poor | 0.2301 | 0.7699 | 0.7125 | 0.2508 | 0.2808 | 0.3088 | 0.3379 | no major automated QC concern from local summaries | moderate coordinate dropout; low preserved ratio at crit0.2 |

## Full Rates Table

| subject_id | scan_type | mid | edf_file_size_mb | sample_count | libre_samples | mask_samples_after_offset | missing_samples_from_timestamp_range | timestamp_monotonic_increasing | duplicate_timestamps | coord_nan_x | coord_nan_y | final_preserved_ratio_crit0.1 | final_preserved_ratio_crit0.15 | final_preserved_ratio_crit0.2 | final_preserved_ratio_crit0.3 | final_preserved_samples_crit0.1 | final_preserved_samples_crit0.15 | final_preserved_samples_crit0.2 | final_preserved_samples_crit0.3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0040 | T1w | MID40081 | 5.2012 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 0040 | T2w | MID40087 | 10.9757 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 0041 | T1w | MID41569 | 6.4491 | 621516 | 371811 | 371817 | 0 | True | 0 | 0.0055 | 0.0056 | 0.7635 | 0.8600 | 0.8835 | 0.8879 | 283866 | 319753 | 328485 | 330116 |
| 0041 | T2w | MID41563 | 9.6633 | 911526 | 646612 | 646618 | 0 | True | 0 | 0.0172 | 0.0197 | 0.6662 | 0.7985 | 0.8415 | 0.8658 | 430764 | 516306 | 544135 | 559856 |
| 0042 | T1w | MID42075 | 6.5314 | 621516 | 371811 | 371817 | 0 | True | 0 | 0.1195 | 0.1396 | 0.1113 | 0.2168 | 0.3197 | 0.4995 | 41391 | 80594 | 118856 | 185708 |
| 0042 | T2w | MID42071 | 9.6595 | 911523 | 646612 | 646618 | 0 | True | 0 | 0.0760 | 0.0878 | 0.3067 | 0.4811 | 0.5835 | 0.6731 | 198343 | 311098 | 377267 | 435210 |
| 0043 | T1w | MID43114 | 6.6070 | 621516 | 371810 | 371817 | 0 | True | 0 | 0.0416 | 0.0430 | 0.3009 | 0.5094 | 0.6509 | 0.7766 | 111874 | 189418 | 242003 | 288737 |
| 0043 | T2w | MID43119 | 9.2606 | 911524 | 646613 | 646618 | 0 | True | 0 | 0.0921 | 0.0908 | 0.1798 | 0.3485 | 0.5077 | 0.6868 | 116290 | 225318 | 328315 | 444120 |
| 0044 | T1w | MID44240 | 6.9230 | 621505 | 371803 | 371817 | 0 | True | 0 | 0.0447 | 0.0464 | 0.3979 | 0.5891 | 0.6977 | 0.7635 | 147928 | 219017 | 259407 | 283857 |
| 0044 | T2w | MID44236 | 10.4310 | 911536 | 646610 | 646618 | 0 | True | 0 | 0.0299 | 0.0392 | 0.3678 | 0.5437 | 0.6576 | 0.7699 | 237845 | 351571 | 425185 | 497798 |
| 0045 | T1w | MID45069 | 6.6087 | 621515 | 371810 | 371817 | 0 | True | 0 | 0.0770 | 0.0806 | 0.1487 | 0.2962 | 0.4241 | 0.6198 | 55285 | 110113 | 157699 | 230435 |
| 0045 | T2w | MID45065 | 9.5418 | 911519 | 646611 | 646618 | 0 | True | 0 | 0.0808 | 0.0842 | 0.2366 | 0.4022 | 0.5358 | 0.7026 | 152990 | 260053 | 346470 | 454325 |
| 0046 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 0047 | T1w | MID47040 | 6.6864 | 621520 | 371811 | 371817 | 0 | True | 0 | 0.0172 | 0.0175 | 0.2896 | 0.5322 | 0.7064 | 0.8471 | 107673 | 197896 | 262651 | 314976 |
| 0047 | T2w | MID47036 | 9.9803 | 911527 | 646612 | 646618 | 0 | True | 0 | 0.0420 | 0.0416 | 0.1359 | 0.2975 | 0.4784 | 0.6709 | 87863 | 192360 | 309318 | 433836 |
| 0048 | T1w | MID48377 | 2.2949 | 621516 | 371810 | 371817 | 0 | True | 0 | 0.7204 | 0.7205 | 0.0822 | 0.1244 | 0.1441 | 0.1603 | 30551 | 46250 | 53564 | 59612 |
| 0048 | T2w | MID48373 | 9.9758 | 911535 | 646610 | 646618 | 0 | True | 0 | 0.1611 | 0.1673 | 0.0845 | 0.1474 | 0.2113 | 0.3002 | 54635 | 95312 | 136600 | 194084 |
| 0049 | T1w | MID49036 | 7.7974 | 621483 | 371808 | 371817 | 0 | True | 0 | 0.1072 | 0.3143 | 0.0428 | 0.0905 | 0.1343 | 0.1981 | 15911 | 33632 | 49924 | 73637 |
| 0049 | T2w | MID49059 | 6.9245 | 911490 | 646612 | 646618 | 0 | True | 0 | 0.4235 | 0.4293 | 0.0287 | 0.0627 | 0.1045 | 0.1938 | 18544 | 40518 | 67571 | 125336 |
| 0050 | T1w | MID50102 | 6.4827 | 621486 | 371810 | 371817 | 0 | True | 0 | 0.0596 | 0.0623 | 0.2939 | 0.4776 | 0.6208 | 0.7555 | 109261 | 177575 | 230817 | 280899 |
| 0050 | T2w | MID50107 | 8.4728 | 911491 | 646613 | 646618 | 0 | True | 0 | 0.2066 | 0.2301 | 0.1298 | 0.2346 | 0.3379 | 0.4724 | 83923 | 151683 | 218501 | 305449 |

## Source Columns In CSV

The CSV also includes `raw_edf_path`, `source_tsv`, `s1_sanity_path`, `source_summary_crit0.2`, and `source_metadata_crit0.2` for provenance and later append/recheck.
