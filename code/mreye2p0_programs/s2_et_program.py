#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import copy
import matplotlib
import numpy as np
import pandas as pd
import scipy.io as sio

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCRIPT_DIR = Path(__file__).resolve().parent
LEGACY_DIR = SCRIPT_DIR.parent / "mreye2p0_fixed"
if str(LEGACY_DIR) not in sys.path:
    sys.path.insert(0, str(LEGACY_DIR))

from mask_clean import (  # noqa: E402
    cal_angles,
    cal_disp,
    filter_XY_with_mask,
    filter_criteria,
    find_mean_position,
    plot_h_v_disp,
    visualization_func,
)


START_RECORDING_MESSAGE = "RECCFG CR 1000 2 0 R"
START_RECORDING_MESSAGE_BACKUP = "ELCLCFG TOWER"
TRIGGER_MESSAGE = "Key s trigger response"

TWIX_BY_TIDX = {
    1: 371817.0,
    2: 646617.5,
}


def choose_file_interactive(use_gui_picker: bool = False) -> Path:
    entered = input("Enter full path to .tsv.gz file: ").strip()
    if entered:
        return Path(entered)

    if not use_gui_picker:
        raise RuntimeError("No TSV file provided. Re-run with --input, paste a path, or use --gui-picker.")

    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        selected = filedialog.askopenfilename(
            title="Select a .tsv.gz ET file",
            filetypes=[("TSV.GZ files", "*.tsv.gz"), ("All files", "*.*")],
        )
        root.destroy()
        if selected:
            return Path(selected)
    except Exception:
        pass

    raise RuntimeError("GUI picker failed. Re-run with --input or paste a path at the prompt.")


def ask_criteria_ratio(default: float = 0.15) -> float:
    raw = input(f"criteria_ratio [{default}]: ").strip()
    if not raw:
        return default
    value = float(raw)
    if value <= 0:
        raise ValueError("criteria_ratio must be > 0")
    return value


def extract_run_info(input_file: Path) -> tuple[str, int]:
    if not input_file.name.endswith(".tsv.gz"):
        raise ValueError("Input file must end with .tsv.gz")

    file_stem = input_file.name[: -len(".tsv.gz")]

    subject_match = re.match(r"(MID\d+)_", file_stem)
    if not subject_match:
        raise ValueError(f"Could not extract subject_idx from filename: {input_file.name}")
    subject_idx = subject_match.group(1)

    t_match = re.search(r"(^|[_\-.])T([12])(?:weighted)?(?=[_\-.]|$)", file_stem, flags=re.IGNORECASE)
    if not t_match:
        raise ValueError(f"Could not extract T_idx from filename: {input_file.name}")
    t_idx = int(t_match.group(2))

    return subject_idx, t_idx


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ET filtering/mask generation from S2 notebook logic.")
    parser.add_argument("--input", type=Path, help="Input .tsv.gz file")
    parser.add_argument("--criteria-ratio", type=float, help="Filter criteria ratio, e.g. 0.15")
    parser.add_argument("--twix-duration", type=float, help="Override twix duration in ms")
    parser.add_argument("--first-trigger-mr-start", type=float, default=0.0)
    parser.add_argument("--output-root", type=Path, default=Path("."), help="Root folder for ./output_figs and ./masks")
    parser.add_argument("--gui-picker", action="store_true", help="Use macOS/GUI file picker as fallback if no path is pasted.")
    args = parser.parse_args()

    input_file = args.input if args.input else choose_file_interactive(use_gui_picker=args.gui_picker)
    input_file = input_file.expanduser().resolve()
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    criteria_ratio = args.criteria_ratio if args.criteria_ratio is not None else ask_criteria_ratio(0.15)
    if criteria_ratio <= 0:
        raise ValueError("criteria_ratio must be > 0")

    subject_idx, t_idx = extract_run_info(input_file)
    mode = "T1" if t_idx == 1 else "T2"

    metadata_file = input_file.with_suffix("").with_suffix(".json")
    if not metadata_file.exists():
        raise FileNotFoundError(f"Metadata JSON not found: {metadata_file}")

    print(f"Selected: {input_file}")
    print(f"subject_idx = {subject_idx}")
    print(f"T_idx = {t_idx}")

    recording = pd.read_csv(input_file, sep="\t", na_values="n/a")
    metadata = json.loads(metadata_file.read_text())

    twix_duration = args.twix_duration if args.twix_duration is not None else TWIX_BY_TIDX[t_idx]

    start_timestamp = None
    trigger_timestamp = None
    for stamp, msg in metadata.get("LoggedMessages", []):
        if msg in {START_RECORDING_MESSAGE, START_RECORDING_MESSAGE_BACKUP}:
            start_timestamp = stamp
            break

    for stamp, msg in metadata.get("LoggedMessages", []):
        if msg == TRIGGER_MESSAGE:
            trigger_timestamp = stamp
            break

    if start_timestamp is None or trigger_timestamp is None:
        raise RuntimeError("Could not find start/trigger messages in LoggedMessages")

    gap_start_dot = start_timestamp - trigger_timestamp
    offset = int(np.round(args.first_trigger_mr_start + gap_start_dot))

    print(f"The first trigger (MRI start) -> MRI starts recordings:    {args.first_trigger_mr_start} ms")
    print(f"From the trigger arrival to the start of ET recording: {gap_start_dot} ms")

    recording = recording.rename(
        columns={
            "eye1_pupil_size": "pupil_size",
            "eye1_fixation": "fixation",
            "eye1_saccade": "saccade",
            "eye1_blink": "blink",
            "eye1_x_coordinate": "x_coordinate",
            "eye1_y_coordinate": "y_coordinate",
        }
    )

    for required in ("x_coordinate", "y_coordinate"):
        if required not in recording.columns:
            raise RuntimeError(f"Missing required column in input TSV: {required}")

    coor_data = recording[["x_coordinate", "y_coordinate"]].copy()
    coor_recording = recording.copy()

    sampling_frequency = metadata["SamplingFrequency"]
    libre_samples = int(np.ceil((twix_duration - offset) / sampling_frequency * sampling_frequency))

    coor_data_LIBRE = coor_data.iloc[:libre_samples].copy()
    coor_recording_LIBRE = coor_recording.iloc[:libre_samples].copy()
    coor_data_LIBRE_raw = copy.deepcopy(coor_data_LIBRE)

    if "blink" in coor_recording_LIBRE.columns:
        blink_mask = coor_recording_LIBRE.blink > 0
        coor_data_LIBRE.loc[blink_mask, ["x_coordinate", "y_coordinate"]] = np.nan
        coor_recording_LIBRE.loc[blink_mask, ["x_coordinate", "y_coordinate"]] = np.nan

    if "fixation" in coor_recording_LIBRE.columns:
        fixation_mask = coor_recording_LIBRE.fixation < 1
        coor_data_LIBRE.loc[fixation_mask, ["x_coordinate", "y_coordinate"]] = np.nan
        coor_recording_LIBRE.loc[fixation_mask, ["x_coordinate", "y_coordinate"]] = np.nan

    coor_data_LIBRE_ft = copy.deepcopy(coor_data_LIBRE)

    X_coord_ft = coor_data_LIBRE_ft["x_coordinate"]
    Y_coord_ft = coor_data_LIBRE_ft["y_coordinate"]

    med_coor_ft = find_mean_position(X_coord_ft, Y_coord_ft)
    theta_h_, theta_h_m, rho_v_, rho_v_m = cal_angles(X_coord_ft, Y_coord_ft, med_coor_ft)
    h_dis_ft, v_dis_ft = cal_disp(theta_h_, theta_h_m, rho_v_, rho_v_m)
    discarded_x_mask, discarded_y_mask = filter_criteria(h_dis_ft, v_dis_ft, criteria_ratio=criteria_ratio)

    output_root = args.output_root.expanduser().resolve()
    output_figs_dir = output_root / "output_figs" / subject_idx
    output_figs_dir.mkdir(parents=True, exist_ok=True)

    # Cell [97] figure(s): horizontal + vertical displacement plots.
    plot_h_v_disp(h_dis_ft, v_dis_ft, discarded_x_mask, discarded_y_mask, criteria_ratio=criteria_ratio)
    fig_numbers = plt.get_fignums()
    if len(fig_numbers) >= 2:
        plt.figure(fig_numbers[-2])
        plt.savefig(output_figs_dir / "2_0_mreye_et_horizontal_disp.pdf", dpi=300, bbox_inches="tight")
        plt.figure(fig_numbers[-1])
        plt.savefig(output_figs_dir / "2_0_mreye_et_vertical_disp.pdf", dpi=300, bbox_inches="tight")

    coor_data_ft_clean, Preserve_mask, Discard_mask = filter_XY_with_mask(
        coor_data_LIBRE_ft, discarded_x_mask, discarded_y_mask, seq_name=None
    )

    visualization_func(
        fig_title="Before vs After (filtering)",
        coor_data_raw=coor_data_LIBRE_raw,
        coor_data=coor_data_LIBRE_ft,
        coor_data_clean=coor_data_ft_clean,
    )
    plt.savefig(output_figs_dir / "2_0_mreye_et_filtering.pdf", dpi=300, bbox_inches="tight")

    visualization_func(
        fig_title="Before vs After (filtering)",
        coor_data_raw=coor_data_LIBRE_raw,
        coor_data=0,
        coor_data_clean=0,
    )
    plt.savefig(output_figs_dir / "2_0_mreye_et_raw.pdf", dpi=300, bbox_inches="tight")

    visualization_func(
        fig_title="Before vs After (filtering)",
        coor_data_raw=coor_data_LIBRE_ft,
        coor_data=0,
        coor_data_clean=0,
    )
    plt.savefig(output_figs_dir / "2_0_mreye_et_nomo.pdf", dpi=300, bbox_inches="tight")

    count_true = int(np.sum(Preserve_mask))
    print(f"Preserved #ET samples: {count_true}")
    print(f"Size of mask before concatenation: {len(Preserve_mask)}")
    preffix_mask = np.zeros(offset)
    print(f"Concatenating prefix offset {offset}")
    Preserve_mask_cat = np.concatenate((preffix_mask, Preserve_mask))
    print(f"Size of mask after concatenation: {len(Preserve_mask_cat)}")
    print(f"twix_duration: {twix_duration}")

    assert len(Preserve_mask_cat) == np.round(twix_duration)

    mask_dir = output_root / "masks" / subject_idx
    mask_dir.mkdir(parents=True, exist_ok=True)
    mask_name = f"subject_{subject_idx}_mask_clean_{criteria_ratio}.mat"
    mask_file = mask_dir / mask_name
    sio.savemat(mask_file, {"array": Preserve_mask_cat})

    print(f"The mask file has been saved here: ./{mask_file.relative_to(output_root).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
