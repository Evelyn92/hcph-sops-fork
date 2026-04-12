# S1 Tutorial: EDF to BIDS-like TSV/JSON

This tutorial is for:
- `/Users/cag/Documents/forclone/hcph-sops-fork/code/mreye2p0_programs/s1_edf2bids_program.py`

## 1. Environment

```bash
conda activate edfenv
```

Optional but recommended:
- `edf2asc` available in `PATH` (used automatically as fallback when `pyedfread` fails on some EDF files).

## 2. What S1 does

Given one `.EDF` file, S1 writes:
- `<same_name>.tsv.gz`
- `<same_name>.json`

By default, output is saved in the same folder as the EDF.

## 3. Run modes

Direct file path:

```bash
python /Users/cag/Documents/forclone/hcph-sops-fork/code/mreye2p0_programs/s1_edf2bids_program.py \
  --edf /absolute/path/to/file.EDF
```

Interactive terminal prompt:

```bash
python /Users/cag/Documents/forclone/hcph-sops-fork/code/mreye2p0_programs/s1_edf2bids_program.py
```

Interactive with GUI picker fallback:

```bash
python /Users/cag/Documents/forclone/hcph-sops-fork/code/mreye2p0_programs/s1_edf2bids_program.py --gui-picker
```

## 4. Robust fallback behavior

S1 first tries `pyedfread` in a subprocess.  
If it crashes/fails, S1 automatically falls back to:
1. `edf2asc -y <file>.EDF`
2. Parse `.asc` samples/events/messages
3. Continue writing TSV/JSON

This avoids full script crash when EDF is only partially compatible with `pyedfread`.

## 5. Batch example used on dataset 0012

```bash
conda run -n edfenv python /Users/cag/Documents/forclone/hcph-sops-fork/code/mreye2p0_programs/s1_edf2bids_program.py \
  --edf /Volumes/FS_PROJETS/MatTechLab/yiwei.jia/datasets/0012/MID12072_fixation_dots_T1weighted_2026-03-14_12h03.12.659.EDF

conda run -n edfenv python /Users/cag/Documents/forclone/hcph-sops-fork/code/mreye2p0_programs/s1_edf2bids_program.py \
  --edf /Volumes/FS_PROJETS/MatTechLab/yiwei.jia/datasets/0012/MID12107_fixation_dots_T2weighted_2026-03-14_12h36.48.704.EDF
```

Produced:
- `/Volumes/FS_PROJETS/MatTechLab/yiwei.jia/datasets/0012/MID12072_fixation_dots_T1weighted_2026-03-14_12h03.12.659.tsv.gz`
- `/Volumes/FS_PROJETS/MatTechLab/yiwei.jia/datasets/0012/MID12072_fixation_dots_T1weighted_2026-03-14_12h03.12.659.json`
- `/Volumes/FS_PROJETS/MatTechLab/yiwei.jia/datasets/0012/MID12107_fixation_dots_T1weighted_2026-03-14_12h36.48.704.tsv.gz`
- `/Volumes/FS_PROJETS/MatTechLab/yiwei.jia/datasets/0012/MID12107_fixation_dots_T1weighted_2026-03-14_12h36.48.704.json`

## 6. Troubleshooting

- If GUI selection fails/cancels, re-run with `--edf /path/file.EDF`.
- If conversion fails with EDF parser errors, ensure `edf2asc` is installed and callable.
- If you need a separate output folder, use:

```bash
python .../s1_edf2bids_program.py --edf /path/file.EDF --out-dir /path/output_dir
```
