# S2 Tutorial: ET Filtering, Figures, and Mask Export

This tutorial is for:
- `/Users/cag/Documents/forclone/hcph-sops-fork/code/mreye2p0_programs/s2_et_program.py`

## 1. Environment

```bash
conda activate edfenv
```

## 2. What S2 does

Given one ET `.tsv.gz` plus its sidecar `.json`, S2:
1. Applies fixation/blink filtering and criterion thresholding
2. Saves figures (`pdf` and `png`)
3. Saves clean mask `.mat`
4. Auto-syncs outputs to filer when available:
   - `/Volumes/FS_PROJETS/MatTechLab/yiwei.jia/recon_results/<dataset_date>/<MID>_recon/T1_LIBRE_Binning/et_masks`
   - `/Volumes/FS_PROJETS/MatTechLab/yiwei.jia/recon_results/<dataset_date>/<MID>_recon/T1_LIBRE_Binning/et_figs`

## 3. Run modes

Direct CLI (recommended for batches):

```bash
python /Users/cag/Documents/forclone/hcph-sops-fork/code/mreye2p0_programs/s2_et_program.py \
  --input /absolute/path/to/file.tsv.gz \
  --criteria-ratio 0.15 \
  --no-gui-picker
```

Interactive mode:

```bash
python /Users/cag/Documents/forclone/hcph-sops-fork/code/mreye2p0_programs/s2_et_program.py
```

If GUI picker is canceled/unavailable, script falls back to terminal path input.

## 4. Output structure and naming

Local output root defaults to current working directory (`.`):
- `./masks/<MID>/subject_<MID>_mask_clean_<criteria>.mat`
- `./output_figs/<MID>/...`

To force output into the program folder regardless of current directory:

```bash
python .../s2_et_program.py \
  --input /path/file.tsv.gz \
  --criteria-ratio 0.15 \
  --output-root /Users/cag/Documents/forclone/hcph-sops-fork/code/mreye2p0_programs \
  --no-gui-picker
```

Figure suffix policy:
- Criterion-specific: filtering + horizontal/vertical displacement
  - `2_0_mreye_et_filtering_crit0.15.(pdf|png)`
  - `2_0_mreye_et_horizontal_disp_crit0.15.(pdf|png)`
  - `2_0_mreye_et_vertical_disp_crit0.15.(pdf|png)`
  - `2_0_mreye_et_summary_crit0.15.txt`
- Stable names (same across criteria):
  - `2_0_mreye_et_raw.(pdf|png)`
  - `2_0_mreye_et_nomo.(pdf|png)`

## 5. Batch example used on dataset 0012 (4 criteria)

```bash
set -euo pipefail
S2=/Users/cag/Documents/forclone/hcph-sops-fork/code/mreye2p0_programs/s2_et_program.py
for tsv in \
  /Volumes/FS_PROJETS/MatTechLab/yiwei.jia/datasets/0012/MID12072_fixation_dots_T1weighted_2026-03-14_12h03.12.659.tsv.gz \
  /Volumes/FS_PROJETS/MatTechLab/yiwei.jia/datasets/0012/MID12107_fixation_dots_T1weighted_2026-03-14_12h36.48.704.tsv.gz
do
  for c in 0.1 0.15 0.2 0.3; do
    conda run -n edfenv python "$S2" --input "$tsv" --criteria-ratio "$c" --no-gui-picker
  done
done
```

Observed `Preserved #ET samples` from this run:
- `MID12072`: `0.1 -> 28036`, `0.15 -> 56312`, `0.2 -> 98054`, `0.3 -> 178280`
- `MID12107`: `0.1 -> 33733`, `0.15 -> 68720`, `0.2 -> 108484`, `0.3 -> 183452`

Verified filer masks created for both subjects and all four criteria.

## 6. Key log lines to check

Each successful run prints lines like:
- `Preserved #ET samples: ...`
- `Size of mask before concatenation: ...`
- `Concatenating prefix offset ...`
- `Size of mask after concatenation: ...`
- `twix_duration: ...`
- `The mask file has been saved here: ./masks/...`

## 7. Troubleshooting

- `GUI selection canceled or unavailable`: use `--input ... --no-gui-picker`.
- Filer sync warnings: local files are still kept; re-run sync when mount is back.
- Missing JSON sidecar: ensure S1 completed and generated `same_name.json` next to TSV.
