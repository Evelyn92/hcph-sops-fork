#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
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
FILER_RECON_ROOT = Path("/Volumes/FS_PROJETS/MatTechLab/yiwei.jia/recon_results")

TWIX_BY_TIDX = {
    1: 371817.0,
    2: 646617.5,
}


def to_builtin(value: object) -> object:
    if isinstance(value, dict):
        return {k: to_builtin(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_builtin(v) for v in value]
    if isinstance(value, tuple):
        return tuple(to_builtin(v) for v in value)
    if isinstance(value, np.generic):
        return value.item()
    return value


def identify_start_end_event(df: pd.DataFrame, events: list[str]) -> dict[str, object]:
    event_dict: dict[str, object] = {}
    df = df.reset_index(drop=True).copy()

    for event in events:
        if event not in df.columns:
            raise KeyError(f"Missing event column: {event}")

        event_shift = f"{event}_shift"
        event_change = f"{event}_change"

        df[event_shift] = df[event].shift(1, fill_value=0)
        df[event_change] = df[event] - df[event_shift]

        event_starts = df.index[df[event_change] == 1].tolist()
        event_ends = df.index[df[event_change] == -1].tolist()

        if len(event_starts) > len(event_ends) and int(df[event].iloc[-1]) == 1:
            event_ends.append(df.index[-1])

        event_durations = [end - start + 1 for start, end in zip(event_starts, event_ends)]
        event_dict[f"num_{event}"] = len(event_starts)
        event_dict[f"{event}_durations"] = event_durations

    return event_dict


def cal_event_stat(event_duration: list[int] | np.ndarray) -> dict[str, float | int]:
    event_duration = np.asarray(event_duration)
    if event_duration.size == 0:
        return {
            "mean_duration": np.nan,
            "median_duration": np.nan,
            "std_duration": np.nan,
            "min_duration": np.nan,
            "max_duration": np.nan,
            "total_duration": 0,
            "times": 0,
        }

    return {
        "mean_duration": float(np.mean(event_duration)),
        "median_duration": float(np.median(event_duration)),
        "std_duration": float(np.std(event_duration)),
        "min_duration": int(np.min(event_duration)),
        "max_duration": int(np.max(event_duration)),
        "total_duration": int(np.sum(event_duration)),
        "times": int(len(event_duration)),
    }


def save_event_statistics(
    output_figs_dir: Path,
    subject_idx: str,
    coor_recording_libre: pd.DataFrame,
) -> dict[str, dict[str, float | int]]:
    events = ["saccade", "fixation", "blink"]
    subject_event_dict = identify_start_end_event(coor_recording_libre, events)
    subject_event_stat = {
        event: cal_event_stat(subject_event_dict[f"{event}_durations"])
        for event in events
    }

    subject_event_stat_df = pd.DataFrame(subject_event_stat).T
    subject_event_stat_df.index.name = "event"

    print("")
    print("Event statistics:")
    print(subject_event_stat_df.to_string())

    event_stats_json = output_figs_dir / "2_0_mreye_et_event_stats.json"
    event_stats_txt = output_figs_dir / "2_0_mreye_et_event_stats.txt"
    event_stats_payload = {
        "subject_idx": subject_idx,
        "event_stats": subject_event_stat,
        "event_counts": {k: v for k, v in subject_event_dict.items() if k.startswith("num_")},
    }
    with event_stats_json.open("w") as f:
        json.dump(to_builtin(event_stats_payload), f, indent=2)
    event_stats_txt.write_text(
        "\n".join(
            [
                f"subject_idx: {subject_idx}",
                "",
                subject_event_stat_df.to_string(),
                "",
                f"event_counts: {event_stats_payload['event_counts']}",
            ]
        )
        + "\n"
    )

    print(f"Event statistics saved here: {event_stats_json}")
    print(f"Event statistics text saved here: {event_stats_txt}")
    for event in events:
        print(f"{event}: {subject_event_stat[event]}")

    return subject_event_stat


def _plot_kde_dimension(
    output_figs_dir: Path,
    raw_values: pd.Series,
    filtered_values: pd.Series,
    dimension_name: str,
    title: str,
    x_label: str,
    x_limits: tuple[float, float],
) -> None:
    fig, ax = plt.subplots(1, 1, figsize=(16, 8))
    raw = raw_values.dropna()
    filtered = filtered_values.dropna()

    plotted = False
    try:
        import seaborn as sns  # type: ignore

        if len(raw) > 0:
            sns.kdeplot(raw, ax=ax, color="blue", fill=True, label=f"raw_{dimension_name}")
            plotted = True
        if len(filtered) > 0:
            sns.kdeplot(filtered, ax=ax, color="orange", fill=True, label=f"filtered_{dimension_name}")
            plotted = True
    except Exception as exc:  # pragma: no cover - fallback for minimal environments
        print(f"Warning: seaborn KDE failed for {dimension_name} ({exc}); falling back to histogram density.")
        bins = 60
        if len(raw) > 0:
            ax.hist(raw, bins=bins, density=True, alpha=0.35, color="blue", label=f"raw_{dimension_name}")
            plotted = True
        if len(filtered) > 0:
            ax.hist(filtered, bins=bins, density=True, alpha=0.35, color="orange", label=f"filtered_{dimension_name}")
            plotted = True

    if not plotted:
        plt.close(fig)
        return

    ax.set_title(f"{dimension_name.upper()} Coordinate: Raw vs. Filtered")
    ax.set_xlabel(x_label)
    ax.set_ylabel("Density")
    ax.set_xlim(x_limits)
    ax.legend()
    fig.suptitle(title, fontsize=16)
    fig.tight_layout(rect=[0, 0, 1, 0.94])

    pdf_file = output_figs_dir / f"2_0_mreye_et_distribution_{dimension_name}_dimension.pdf"
    png_file = output_figs_dir / f"2_0_mreye_et_distribution_{dimension_name}_dimension.png"
    fig.savefig(pdf_file, dpi=300, bbox_inches="tight")
    fig.savefig(png_file, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved KDE plot: {pdf_file}")
    print(f"Saved KDE plot: {png_file}")


def choose_file_interactive(use_gui_picker: bool = True) -> Path:
    if use_gui_picker:
        if platform.system() == "Darwin":
            result = subprocess.run(
                [
                    "osascript",
                    "-e",
                    'set f to choose file with prompt "Select a .tsv.gz ET file"',
                    "-e",
                    "POSIX path of f",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                selected = result.stdout.strip()
                if selected:
                    selected_path = Path(selected)
                    if selected_path.name.endswith(".tsv.gz"):
                        return selected_path
                    print("Selected file is not .tsv.gz, please pick again or paste a path.")
            else:
                err = (result.stderr or "").strip()
                if err:
                    print(f"GUI selection canceled or unavailable ({err}).")
                else:
                    print("GUI selection canceled or unavailable.")

        # Fallback GUI picker (avoid file type filter to prevent macOS Tk crashes seen before).
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            selected = filedialog.askopenfilename(title="Select a .tsv.gz ET file")
            root.destroy()
            if selected:
                selected_path = Path(selected)
                if selected_path.name.endswith(".tsv.gz"):
                    return selected_path
                print("Selected file is not .tsv.gz, please pick again or paste a path.")
        except Exception as exc:
            print(f"Secondary GUI picker failed ({exc}).")
        if platform.system() != "Darwin":
            print("GUI picker is currently implemented for macOS only; falling back to prompt.")

    entered = input("Enter full path to .tsv.gz file: ").strip()
    if entered:
        return Path(entered)
    raise RuntimeError("No TSV file provided.")


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


def sync_to_filer_if_available(
    input_file: Path,
    subject_idx: str,
    local_mask_file: Path,
    local_fig_dir: Path,
    criteria_tag: str,
) -> None:
    if not FILER_RECON_ROOT.exists():
        print(f"Filer not found at {FILER_RECON_ROOT}; skipping sync.")
        return

    recon_folder_date = input_file.parent.name
    recon_base = FILER_RECON_ROOT / recon_folder_date / f"{subject_idx}_recon" / "T1_LIBRE_Binning"
    mask_dst = recon_base / "et_masks"
    figs_dst = recon_base / "et_figs"
    mask_dst.mkdir(parents=True, exist_ok=True)
    figs_dst.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            ["rsync", "-av", str(local_mask_file), f"{mask_dst}/"],
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"Warning: filer mask sync failed ({exc}); local outputs kept.")
        return
    to_sync = []
    to_sync.extend(sorted(local_fig_dir.glob(f"*_{criteria_tag}.pdf")))
    to_sync.extend(sorted(local_fig_dir.glob(f"*_{criteria_tag}.png")))
    to_sync.extend(sorted(local_fig_dir.glob(f"*_{criteria_tag}.txt")))
    to_sync.extend(sorted(local_fig_dir.glob("2_0_mreye_et_distribution_*_dimension.pdf")))
    to_sync.extend(sorted(local_fig_dir.glob("2_0_mreye_et_distribution_*_dimension.png")))
    to_sync.extend(sorted(local_fig_dir.glob("2_0_mreye_et_event_stats.txt")))
    to_sync.extend(sorted(local_fig_dir.glob("2_0_mreye_et_event_stats.json")))
    for stem in (
        "2_0_mreye_et_raw",
        "2_0_mreye_et_nomo",
    ):
        for ext in ("pdf", "png"):
            candidate = local_fig_dir / f"{stem}.{ext}"
            if candidate.exists():
                to_sync.append(candidate)

    if not to_sync:
        print(f"No figures found to sync for {criteria_tag}; skipping figure sync.")
    else:
        for fig in to_sync:
            try:
                subprocess.run(["rsync", "-av", str(fig), f"{figs_dst}/"], check=True)
            except subprocess.CalledProcessError as exc:
                print(f"Warning: filer figure sync failed for {fig.name} ({exc}); continuing.")
    print(f"Synced mask to filer: {mask_dst}")
    print(f"Synced figures to filer: {figs_dst}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ET filtering/mask generation from S2 notebook logic.")
    parser.add_argument("--input", type=Path, help="Input .tsv.gz file")
    parser.add_argument("--criteria-ratio", type=float, help="Filter criteria ratio, e.g. 0.15")
    parser.add_argument("--twix-duration", type=float, help="Override twix duration in ms")
    parser.add_argument("--first-trigger-mr-start", type=float, default=0.0)
    parser.add_argument("--output-root", type=Path, default=Path("."), help="Root folder for ./output_figs and ./masks")
    parser.add_argument("--no-gui-picker", action="store_true", help="Disable GUI picker and prompt for a path in terminal.")
    args = parser.parse_args()

    input_file = args.input if args.input else choose_file_interactive(use_gui_picker=not args.no_gui_picker)
    input_file = input_file.expanduser().resolve()
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    criteria_ratio = args.criteria_ratio if args.criteria_ratio is not None else ask_criteria_ratio(0.15)
    if criteria_ratio <= 0:
        raise ValueError("criteria_ratio must be > 0")
    criteria_tag = f"crit{criteria_ratio}"

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

    output_root = args.output_root.expanduser().resolve()
    output_figs_dir = output_root / "output_figs" / subject_idx
    output_figs_dir.mkdir(parents=True, exist_ok=True)

    if "blink" in coor_recording_LIBRE.columns:
        blink_mask = coor_recording_LIBRE.blink > 0
        coor_data_LIBRE.loc[blink_mask, ["x_coordinate", "y_coordinate"]] = np.nan
        coor_recording_LIBRE.loc[blink_mask, ["x_coordinate", "y_coordinate"]] = np.nan

    if "fixation" in coor_recording_LIBRE.columns:
        fixation_mask = coor_recording_LIBRE.fixation < 1
        coor_data_LIBRE.loc[fixation_mask, ["x_coordinate", "y_coordinate"]] = np.nan
        coor_recording_LIBRE.loc[fixation_mask, ["x_coordinate", "y_coordinate"]] = np.nan

    save_event_statistics(output_figs_dir=output_figs_dir, subject_idx=subject_idx, coor_recording_libre=coor_recording_LIBRE)

    coor_data_LIBRE_ft = copy.deepcopy(coor_data_LIBRE)

    X_coord_ft = coor_data_LIBRE_ft["x_coordinate"]
    Y_coord_ft = coor_data_LIBRE_ft["y_coordinate"]

    med_coor_ft = find_mean_position(X_coord_ft, Y_coord_ft)
    theta_h_, theta_h_m, rho_v_, rho_v_m = cal_angles(X_coord_ft, Y_coord_ft, med_coor_ft)
    h_dis_ft, v_dis_ft = cal_disp(theta_h_, theta_h_m, rho_v_, rho_v_m)
    discarded_x_mask, discarded_y_mask = filter_criteria(h_dis_ft, v_dis_ft, criteria_ratio=criteria_ratio)

    # Cell [97] figure(s): horizontal + vertical displacement plots.
    plot_h_v_disp(h_dis_ft, v_dis_ft, discarded_x_mask, discarded_y_mask, criteria_ratio=criteria_ratio)
    fig_numbers = plt.get_fignums()
    if len(fig_numbers) >= 2:
        plt.figure(fig_numbers[-2])
        plt.savefig(output_figs_dir / f"2_0_mreye_et_horizontal_disp_{criteria_tag}.pdf", dpi=300, bbox_inches="tight")
        plt.savefig(output_figs_dir / f"2_0_mreye_et_horizontal_disp_{criteria_tag}.png", dpi=300, bbox_inches="tight")
        plt.figure(fig_numbers[-1])
        plt.savefig(output_figs_dir / f"2_0_mreye_et_vertical_disp_{criteria_tag}.pdf", dpi=300, bbox_inches="tight")
        plt.savefig(output_figs_dir / f"2_0_mreye_et_vertical_disp_{criteria_tag}.png", dpi=300, bbox_inches="tight")

    coor_data_ft_clean, Preserve_mask, Discard_mask = filter_XY_with_mask(
        coor_data_LIBRE_ft, discarded_x_mask, discarded_y_mask, seq_name=None
    )

    visualization_func(
        fig_title="Before vs After (filtering)",
        coor_data_raw=coor_data_LIBRE_raw,
        coor_data=coor_data_LIBRE_ft,
        coor_data_clean=coor_data_ft_clean,
    )
    plt.savefig(output_figs_dir / f"2_0_mreye_et_filtering_{criteria_tag}.pdf", dpi=300, bbox_inches="tight")
    plt.savefig(output_figs_dir / f"2_0_mreye_et_filtering_{criteria_tag}.png", dpi=300, bbox_inches="tight")

    visualization_func(
        fig_title="Before vs After (filtering)",
        coor_data_raw=coor_data_LIBRE_raw,
        coor_data=0,
        coor_data_clean=0,
    )
    plt.savefig(output_figs_dir / "2_0_mreye_et_raw.pdf", dpi=300, bbox_inches="tight")
    plt.savefig(output_figs_dir / "2_0_mreye_et_raw.png", dpi=300, bbox_inches="tight")

    visualization_func(
        fig_title="Before vs After (filtering)",
        coor_data_raw=coor_data_LIBRE_ft,
        coor_data=0,
        coor_data_clean=0,
    )
    plt.savefig(output_figs_dir / "2_0_mreye_et_nomo.pdf", dpi=300, bbox_inches="tight")
    plt.savefig(output_figs_dir / "2_0_mreye_et_nomo.png", dpi=300, bbox_inches="tight")

    _plot_kde_dimension(
        output_figs_dir=output_figs_dir,
        raw_values=coor_data_LIBRE_raw["x_coordinate"],
        filtered_values=coor_data_LIBRE["x_coordinate"],
        dimension_name="x",
        title="Distribution of Eye-Tracking Data Along X Dimension",
        x_label="X Coordinate (px)",
        x_limits=(250, 550),
    )
    _plot_kde_dimension(
        output_figs_dir=output_figs_dir,
        raw_values=coor_data_LIBRE_raw["y_coordinate"],
        filtered_values=coor_data_LIBRE["y_coordinate"],
        dimension_name="y",
        title="Distribution of Eye-Tracking Data Along Y Dimension",
        x_label="Y Coordinate (px)",
        x_limits=(250, 350),
    )

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

    summary_file = output_figs_dir / f"2_0_mreye_et_summary_{criteria_tag}.txt"
    summary_lines = [
        f"input_file: {input_file}",
        f"subject_idx: {subject_idx}",
        f"T_idx: {t_idx}",
        f"criteria_ratio: {criteria_ratio}",
        f"Preserved #ET samples: {count_true}",
        f"Size of mask before concatenation: {len(Preserve_mask)}",
        f"Concatenating prefix offset {offset}",
        f"Size of mask after concatenation: {len(Preserve_mask_cat)}",
        f"twix_duration: {twix_duration}",
        f"mask_file: {mask_file}",
    ]
    summary_file.write_text("\n".join(summary_lines) + "\n")

    print(f"The mask file has been saved here: ./{mask_file.relative_to(output_root).as_posix()}")
    print(f"Run summary has been saved here: ./{summary_file.relative_to(output_root).as_posix()}")
    sync_to_filer_if_available(
        input_file=input_file,
        subject_idx=subject_idx,
        local_mask_file=mask_file,
        local_fig_dir=output_figs_dir,
        criteria_tag=criteria_tag,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
