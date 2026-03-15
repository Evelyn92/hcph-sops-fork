# mreye2p0 programs

## Files
- `s1_edf2bids_program.py`: pick/select one `.EDF` file and generate BIDS-like `*.tsv.gz` + `*.json` automatically.
- `s2_et_program.py`: pick/select one `.tsv.gz`, set `criteria_ratio` (for example `0.15`), save figures, and save the clean mask `.mat`.

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

## S2 outputs
- Figures go to `./output_figs/<MIDxxxxx>/` with criterion-tagged names, e.g. `2_0_mreye_et_filtering_crit0.15.pdf`.
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

## Note
These scripts reuse modules under `code/mreye2p0_fixed/` (`write_bids_yiwei.py` and `mask_clean.py`) to stay consistent with your notebooks.
