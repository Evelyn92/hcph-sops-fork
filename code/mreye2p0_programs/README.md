# mreye2p0 programs

Detailed tutorials:
- `TUTORIAL_S1_EDF2BIDS.md`
- `TUTORIAL_S2_ET.md`
- `S3` is currently documented in this README.

## Files
- `s1_edf2bids_program.py`: pick/select one `.EDF` file and generate BIDS-like `*.tsv.gz` + `*.json` automatically.
- `s2_et_program.py`: pick/select one `.tsv.gz`, set `criteria_ratio` (for example `0.15`), save figures, and save the clean mask `.mat`.
- `s3_emask_qc_program.py`: check eMask `.mat` array sizes against expected T1w/T2w lengths using the scan log Excel file.
- `run_s1_s2_batch_gui.py`: UI form to pick one dataset folder (for example `.../datasets/0010`) and run S1 then S2 across a criteria array.

## Run
From repository root:

```bash
conda activate edfenv
python code/mreye2p0_programs/s1_edf2bids_program.py
python code/mreye2p0_programs/s2_et_program.py
```

For `s2_et_program.py`, macOS Finder GUI file selection is enabled by default (no need to paste paths).
If you want terminal-only mode, add `--no-gui-picker`.

Optional direct arguments:

```bash
python code/mreye2p0_programs/s1_edf2bids_program.py --edf /path/to/file.EDF
python code/mreye2p0_programs/s2_et_program.py --input /path/to/file.tsv.gz --criteria-ratio 0.15
```

## Batch UI runner

```bash
conda activate edfenv
python code/mreye2p0_programs/run_s1_s2_batch_gui.py
```

What it does:
- lets you choose a dataset folder with a form
- lets you set criteria array (for example `0.1,0.15,0.2,0.3`)
- auto-runs S1 on all `fixation_dots*.EDF` files in that folder
- auto-runs S2 for every generated TSV and every criteria
- shows full logs in the window

## S2 outputs
- Figures go to `./output_figs/<MIDxxxxx>/` with criterion-tagged names, e.g. `2_0_mreye_et_filtering_crit0.15.pdf`.
- Per-run text summary also saved with criterion tag, e.g. `2_0_mreye_et_summary_crit0.15.txt` (includes preserved count and mask sizing lines).
- Mask goes to `./masks/<MIDxxxxx>/subject_<MIDxxxxx>_mask_clean_<criteria_ratio>.mat`.
- Console prints the same key summary lines as notebook cell 106, including:
  - `Preserved #ET samples: ...`
  - `Size of mask before concatenation: ...`
  - `Concatenating prefix offset ...`
  - `Size of mask after concatenation: ...`
  - `twix_duration: ...`
  - `The mask file has been saved here: ./masks/...`
- If filer mount exists at `/Volumes/FS_PROJETS/MatTechLab/yiwei.jia/recon_results`, outputs are auto-synced to:
  - `<recon_date>/<MIDxxxxx>_recon/T1_LIBRE_Binning/et_masks`
  - `<recon_date>/<MIDxxxxx>_recon/T1_LIBRE_Binning/et_figs` (only current criterion-tagged figures)

## S3 eMask QC

Default run across all subjects found in the scan log:

```bash
python code/mreye2p0_programs/s3_emask_qc_program.py
```

Single subject example:

```bash
python code/mreye2p0_programs/s3_emask_qc_program.py --subject 0001
```

What it checks:
- reads `/Users/cag/Library/CloudStorage/OneDrive-HESSO/09_scan_log/MREye2-0.xlsx`
- uses sheet `Acquisition`
- maps each subject to `T1w` and `T2w` MID
- checks `subject_<MID>_mask_clean_0.1.mat` by default
- reads MAT variable `array` and compares `array.size`
- expected sizes:
  - `T1w -> 371817`
  - `T2w -> 646618`

Outputs:
- terminal summary with `OK`, `MISSING`, or `SIZE_MISMATCH`
- CSV and TXT reports in `code/mreye2p0_programs/emask_qc_reports/`

## Note
These scripts reuse modules under `code/mreye2p0_fixed/` (`write_bids_yiwei.py` and `mask_clean.py`) to stay consistent with your notebooks.
