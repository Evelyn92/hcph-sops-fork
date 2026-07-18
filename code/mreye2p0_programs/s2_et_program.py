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


def read_et_recording(input_file: Path, metadata: dict[str, object]) -> tuple[pd.DataFrame, str]:
    recording = pd.read_csv(input_file, sep="\t", na_values="n/a")
    columns = metadata.get("Columns")

    if "timestamp" not in recording.columns and isinstance(columns, list):
        fallback = pd.read_csv(input_file, sep="\t", na_values="n/a", header=None)
        if len(fallback.columns) == len(columns):
            fallback.columns = [str(column) for column in columns]
            return fallback, "headerless_with_metadata_columns"

    unnamed_columns = [column for column in recording.columns if str(column).startswith("Unnamed:")]
    if unnamed_columns:
        recording = recording.drop(columns=unnamed_columns)
        return recording, "headered_with_legacy_index_column"

    return recording, "headered"


def get_start_timestamp(metadata: dict[str, object]) -> int:
    start_timestamp = metadata.get("StartTimestamp")
    if start_timestamp is not None:
        return int(start_timestamp)

    for stamp, msg in metadata.get("LoggedMessages", []):
        if msg in {START_RECORDING_MESSAGE, START_RECORDING_MESSAGE_BACKUP}:
            return int(stamp)

    # Older S1 notebooks stored the raw EyeLink timestamp in StartTime.
    start_time = metadata.get("StartTime")
    if start_time is not None:
        return int(start_time)

    raise RuntimeError("Could not find ET start timestamp in metadata")


def get_trigger_timestamp(metadata: dict[str, object]) -> int:
    for stamp, msg in metadata.get("LoggedMessages", []):
        if msg == TRIGGER_MESSAGE:
            return int(stamp)
    raise RuntimeError("Could not find MRI trigger message in LoggedMessages")


def summarize_s2_input(recording: pd.DataFrame, metadata: dict[str, object], input_format: str) -> dict[str, object]:
    timestamp = recording["timestamp"] if "timestamp" in recording.columns else pd.Series(dtype=float)
    event_columns = [column for column in ("fixation", "saccade", "blink") if column in recording.columns]
    coordinate_columns = [column for column in ("x_coordinate", "y_coordinate") if column in recording.columns]

    return {
        "input_format": input_format,
        "sample_count": int(len(recording)),
        "metadata_columns_count": len(metadata.get("Columns", [])) if isinstance(metadata.get("Columns"), list) else None,
        "timestamp_start": int(timestamp.iloc[0]) if not timestamp.empty else None,
        "timestamp_end": int(timestamp.iloc[-1]) if not timestamp.empty else None,
        "timestamp_monotonic_increasing": bool(timestamp.is_monotonic_increasing) if not timestamp.empty else False,
        "duplicate_timestamps": int(timestamp.duplicated().sum()) if not timestamp.empty else 0,
        "coordinate_nan_ratio": {
            column: float(recording[column].isna().mean()) for column in coordinate_columns
        },
        "event_coverage_ratio": {
            column: float(recording[column].fillna(0).astype(bool).mean()) for column in event_columns
        },
        "sampling_frequency": metadata.get("SamplingFrequency"),
    }


def analyze_event_mask_overlap(coor_recording: pd.DataFrame) -> dict[str, object]:
    required = ["fixation", "saccade", "blink"]
    missing = [column for column in required if column not in coor_recording.columns]
    if missing:
        raise KeyError(f"Missing event columns for overlap analysis: {missing}")

    fixation = coor_recording["fixation"].fillna(0).astype(bool).to_numpy()
    saccade = coor_recording["saccade"].fillna(0).astype(bool).to_numpy()
    blink = coor_recording["blink"].fillna(0).astype(bool).to_numpy()
    non_fixation = ~fixation

    n_samples = len(coor_recording)
    nonfix_explained = non_fixation & (saccade | blink)
    nonfix_unexplained = non_fixation & ~(saccade | blink)

    counts = {
        "samples": int(n_samples),
        "fixation": int(fixation.sum()),
        "non_fixation": int(non_fixation.sum()),
        "saccade": int(saccade.sum()),
        "blink": int(blink.sum()),
        "nonfix_and_saccade": int((non_fixation & saccade).sum()),
        "nonfix_and_blink": int((non_fixation & blink).sum()),
        "saccade_and_blink": int((saccade & blink).sum()),
        "nonfix_explained_by_saccade_or_blink": int(nonfix_explained.sum()),
        "nonfix_not_saccade_or_blink": int(nonfix_unexplained.sum()),
        "fixation_and_saccade": int((fixation & saccade).sum()),
        "fixation_and_blink": int((fixation & blink).sum()),
        "fixation_and_saccade_and_blink": int((fixation & saccade & blink).sum()),
    }
    denominators = {
        "all_samples": max(n_samples, 1),
        "non_fixation": max(counts["non_fixation"], 1),
        "saccade": max(counts["saccade"], 1),
        "blink": max(counts["blink"], 1),
    }
    ratios = {
        "nonfix_fraction_of_all": counts["non_fixation"] / denominators["all_samples"],
        "saccade_fraction_of_all": counts["saccade"] / denominators["all_samples"],
        "blink_fraction_of_all": counts["blink"] / denominators["all_samples"],
        "nonfix_explained_by_saccade_or_blink_fraction_of_nonfix": counts[
            "nonfix_explained_by_saccade_or_blink"
        ]
        / denominators["non_fixation"],
        "nonfix_not_saccade_or_blink_fraction_of_nonfix": counts[
            "nonfix_not_saccade_or_blink"
        ]
        / denominators["non_fixation"],
        "saccade_overlaps_blink_fraction_of_saccade": counts["saccade_and_blink"]
        / denominators["saccade"],
        "blink_overlaps_saccade_fraction_of_blink": counts["saccade_and_blink"]
        / denominators["blink"],
        "fixation_overlaps_saccade_fraction_of_saccade": counts["fixation_and_saccade"]
        / denominators["saccade"],
        "fixation_overlaps_blink_fraction_of_blink": counts["fixation_and_blink"]
        / denominators["blink"],
    }

    warnings = []
    if ratios["nonfix_not_saccade_or_blink_fraction_of_nonfix"] > 0.10:
        warnings.append(
            "More than 10% of non-fixation samples are neither saccade nor blink; inspect parser/event labels."
        )
    if ratios["fixation_overlaps_saccade_fraction_of_saccade"] > 0.05:
        warnings.append(
            "More than 5% of saccade samples overlap fixation; event definitions may not be mutually exclusive."
        )
    if ratios["fixation_overlaps_blink_fraction_of_blink"] > 0.05:
        warnings.append(
            "More than 5% of blink samples overlap fixation; event definitions may not be mutually exclusive."
        )

    return {"counts": counts, "ratios": ratios, "warnings": warnings}


def compute_motion_qc(
    coor_data: pd.DataFrame,
    distance_preserve_mask: np.ndarray,
    sampling_frequency: float,
    window_samples: int = 15,
    percentile: float = 90,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, object]]:
    x_values = coor_data["x_coordinate"].to_numpy(dtype=float)
    y_values = coor_data["y_coordinate"].to_numpy(dtype=float)

    dx_values = np.diff(x_values, prepend=np.nan)
    dy_values = np.diff(y_values, prepend=np.nan)
    step_dist_px = np.sqrt(dx_values**2 + dy_values**2)
    invalid_step = np.isnan(x_values) | np.isnan(y_values) | np.isnan(dx_values) | np.isnan(dy_values)
    step_dist_px[invalid_step] = np.nan

    motion_score = (
        pd.Series(step_dist_px)
        .rolling(
            window=window_samples,
            center=True,
            min_periods=max(3, window_samples // 3),
        )
        .median()
        .to_numpy()
    )

    valid_motion = motion_score[~np.isnan(motion_score)]
    if len(valid_motion) == 0:
        motion_threshold_px = np.nan
        low_motion_mask = np.zeros_like(distance_preserve_mask, dtype=bool)
    else:
        motion_threshold_px = float(np.nanpercentile(valid_motion, percentile))
        low_motion_mask = (motion_score <= motion_threshold_px) & ~np.isnan(motion_score)

    distance_preserve_mask = np.asarray(distance_preserve_mask, dtype=bool)
    combined_preserve_mask = distance_preserve_mask & low_motion_mask
    diff_mask = distance_preserve_mask != combined_preserve_mask
    distance_preserved_count = int(distance_preserve_mask.sum())
    combined_preserved_count = int(combined_preserve_mask.sum())
    combined_over_distance_ratio = (
        combined_preserved_count / distance_preserved_count
        if distance_preserved_count > 0
        else np.nan
    )
    removed_by_motion_ratio = (
        1.0 - combined_over_distance_ratio if not np.isnan(combined_over_distance_ratio) else np.nan
    )

    motion_qc = {
        "enabled_for_main_mask": True,
        "method": "rolling median of frame-to-frame gaze displacement in pixels",
        "window_samples": int(window_samples),
        "window_ms": float(window_samples / sampling_frequency * 1000),
        "threshold_percentile": float(percentile),
        "motion_threshold_px": motion_threshold_px,
        "distance_preserved_samples": distance_preserved_count,
        "low_motion_samples": int(low_motion_mask.sum()),
        "combined_preserved_samples": combined_preserved_count,
        "distance_preserved_ratio": float(distance_preserve_mask.mean()) if len(distance_preserve_mask) else np.nan,
        "combined_preserved_ratio": float(combined_preserve_mask.mean()) if len(combined_preserve_mask) else np.nan,
        "combined_over_distance_preserved_ratio": float(combined_over_distance_ratio),
        "distance_preserved_removed_by_motion_ratio": float(removed_by_motion_ratio),
        "distance_vs_motion_diff_samples": int(diff_mask.sum()),
        "distance_vs_motion_diff_ratio": float(diff_mask.mean()) if len(diff_mask) else np.nan,
    }
    return motion_score, low_motion_mask, combined_preserve_mask, motion_qc


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
    parser.add_argument("--motion-window-samples", type=int, default=15)
    parser.add_argument("--motion-percentile", type=float, default=90.0)
    parser.add_argument("--output-root", type=Path, default=Path("."), help="Root folder for ./output_figs and ./masks")
    parser.add_argument("--no-gui-picker", action="store_true", help="Disable GUI picker and prompt for a path in terminal.")
    parser.add_argument("--no-filer-sync", action="store_true", help="Do not rsync masks/figures to the filer.")
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

    metadata = json.loads(metadata_file.read_text())
    recording, input_format = read_et_recording(input_file, metadata)
    print(f"Input TSV format detected: {input_format}")

    twix_duration = args.twix_duration if args.twix_duration is not None else TWIX_BY_TIDX[t_idx]

    start_timestamp = get_start_timestamp(metadata)
    trigger_timestamp = get_trigger_timestamp(metadata)

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

    s2_input_sanity = summarize_s2_input(recording, metadata, input_format)
    print("S2 input sanity summary:")
    print(json.dumps(to_builtin(s2_input_sanity), indent=2, sort_keys=True))

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
    event_overlap_summary = analyze_event_mask_overlap(coor_recording_LIBRE)
    print("Event mask overlap summary:")
    print(json.dumps(to_builtin(event_overlap_summary), indent=2, sort_keys=True))
    for warning in event_overlap_summary["warnings"]:
        print(f"WARNING: {warning}")

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
    motion_score_px, low_motion_mask, final_preserve_mask, motion_qc = compute_motion_qc(
        coor_data=coor_data_LIBRE_ft,
        distance_preserve_mask=Preserve_mask,
        sampling_frequency=float(sampling_frequency),
        window_samples=args.motion_window_samples,
        percentile=args.motion_percentile,
    )
    print("Motion QC summary; final saved mask uses distance AND low-motion:")
    print(json.dumps(to_builtin(motion_qc), indent=2, sort_keys=True))
    print(
        "Motion QC within distance-preserved samples: "
        f"{motion_qc['combined_over_distance_preserved_ratio']:.4f} remain low-motion; "
        f"{motion_qc['distance_preserved_removed_by_motion_ratio']:.4f} would be removed by adding motion."
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    plot_t = np.arange(len(motion_score_px)) / sampling_frequency
    ax.plot(plot_t, motion_score_px, label="rolling motion score (px)")
    if not np.isnan(motion_qc["motion_threshold_px"]):
        ax.axhline(motion_qc["motion_threshold_px"], color="r", linestyle="--", label="motion threshold")
    ax.set_title("Motion QC: rolling gaze displacement")
    ax.set_xlabel("time [s]")
    ax.set_ylabel("pixels")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_figs_dir / f"2_0_mreye_et_motion_qc_{criteria_tag}.pdf", dpi=300, bbox_inches="tight")
    fig.savefig(output_figs_dir / f"2_0_mreye_et_motion_qc_{criteria_tag}.png", dpi=300, bbox_inches="tight")

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

    count_distance_only = int(np.sum(Preserve_mask))
    count_true = int(np.sum(final_preserve_mask))
    print(f"Distance-only preserved #ET samples: {count_distance_only}")
    print(f"Final distance+motion preserved #ET samples: {count_true}")
    print(f"Size of final mask before concatenation: {len(final_preserve_mask)}")
    preffix_mask = np.zeros(offset, dtype=np.uint8)
    print(f"Concatenating prefix offset {offset}")
    Preserve_mask_cat = np.concatenate((preffix_mask, final_preserve_mask.astype(np.uint8))).astype(np.uint8)
    print(f"Size of mask after concatenation: {len(Preserve_mask_cat)}")
    print(f"twix_duration: {twix_duration}")

    assert len(Preserve_mask_cat) == int(np.round(twix_duration))

    mask_dir = output_root / "masks" / subject_idx
    mask_dir.mkdir(parents=True, exist_ok=True)
    mask_name = f"subject_{subject_idx}_mask_clean_{criteria_ratio}.mat"
    mask_file = mask_dir / mask_name
    sio.savemat(mask_file, {"array": Preserve_mask_cat})
    metadata_file_out = mask_dir / f"subject_{subject_idx}_mask_clean_{criteria_ratio}_metadata.json"
    mask_metadata = {
        "subject_idx": subject_idx,
        "source_tsv": str(input_file),
        "final_mask_method": "distance_and_low_motion",
        "distance_only_used_for_qc_only": True,
        "T_idx": int(t_idx),
        "mode": mode,
        "criteria_ratio": float(criteria_ratio),
        "motion_window_samples": int(args.motion_window_samples),
        "motion_percentile": float(args.motion_percentile),
        "twix_duration_ms": float(twix_duration),
        "offset_ms": int(offset),
        "libre_samples": int(libre_samples),
        "distance_only_preserved_samples_before_offset": count_distance_only,
        "final_preserved_samples_before_offset": count_true,
        "mask_samples_before_offset": int(len(final_preserve_mask)),
        "mask_samples_after_offset": int(len(Preserve_mask_cat)),
        "final_preserved_ratio_before_offset": float(np.mean(final_preserve_mask)) if len(final_preserve_mask) else np.nan,
        "final_preserved_ratio_after_offset": float(np.mean(Preserve_mask_cat)) if len(Preserve_mask_cat) else np.nan,
        "input_sanity": s2_input_sanity,
        "event_overlap_summary": event_overlap_summary,
        "motion_qc": motion_qc,
    }
    metadata_file_out.write_text(json.dumps(to_builtin(mask_metadata), indent=2, sort_keys=True) + "\n")
    et_metadata = json.loads(metadata_file.read_text())
    et_metadata["S2StableMask"] = to_builtin(mask_metadata)
    metadata_file.write_text(json.dumps(et_metadata, indent=2, sort_keys=True) + "\n")

    summary_file = output_figs_dir / f"2_0_mreye_et_summary_{criteria_tag}.txt"
    summary_lines = [
        f"input_file: {input_file}",
        f"input_format: {input_format}",
        f"subject_idx: {subject_idx}",
        f"T_idx: {t_idx}",
        "final_mask_method: distance_and_low_motion",
        f"criteria_ratio: {criteria_ratio}",
        f"motion_window_samples: {args.motion_window_samples}",
        f"motion_percentile: {args.motion_percentile}",
        f"timestamp_monotonic_increasing: {s2_input_sanity['timestamp_monotonic_increasing']}",
        f"duplicate_timestamps: {s2_input_sanity['duplicate_timestamps']}",
        f"coordinate_nan_ratio: {s2_input_sanity['coordinate_nan_ratio']}",
        f"event_coverage_ratio: {s2_input_sanity['event_coverage_ratio']}",
        f"distance_only_preserved_samples: {count_distance_only}",
        f"final_preserved_samples: {count_true}",
        f"motion_qc: {motion_qc}",
        f"event_overlap_summary: {event_overlap_summary}",
        f"Size of mask before concatenation: {len(final_preserve_mask)}",
        f"Concatenating prefix offset {offset}",
        f"Size of mask after concatenation: {len(Preserve_mask_cat)}",
        f"twix_duration: {twix_duration}",
        f"mask_file: {mask_file}",
        f"mask_metadata_file: {metadata_file_out}",
    ]
    summary_file.write_text("\n".join(summary_lines) + "\n")

    print(f"The mask file has been saved here: ./{mask_file.relative_to(output_root).as_posix()}")
    print(f"The mask metadata file has been saved here: ./{metadata_file_out.relative_to(output_root).as_posix()}")
    print(f"Merged S2 stable mask metadata into ET JSON sidecar: {metadata_file}")
    print(f"Run summary has been saved here: ./{summary_file.relative_to(output_root).as_posix()}")
    if args.no_filer_sync:
        print("Skipping filer sync because --no-filer-sync was set.")
    else:
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
