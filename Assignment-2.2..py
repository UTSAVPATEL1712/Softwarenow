#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import numpy as np
import sys

# -------- Config --------
TEMPS_FOLDER = Path.cwd() / "temperatures"
OUTPUT_AVG = Path.cwd() / "average_temp.txt"
OUTPUT_RANGE = Path.cwd() / "largest_temp_range_station.txt"
OUTPUT_STABILITY = Path.cwd() / "temperature_stability_stations.txt"

# Mapping month names to numbers
MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
}

SEASON_MAP = {
    12: "Summer", 1: "Summer", 2: "Summer",
    3: "Autumn", 4: "Autumn", 5: "Autumn",
    6: "Winter", 7: "Winter", 8: "Winter",
    9: "Spring", 10: "Spring", 11: "Spring",
}

def load_all_csvs(folder: Path) -> pd.DataFrame:
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f'Folder "{folder}" not found. Create it and put .csv files inside.')
    files = sorted(folder.glob("**/*.csv"))
    if not files:
        raise FileNotFoundError(f'No .csv files found under "{folder}".')
    frames = []
    for f in files:
        try:
            df = pd.read_csv(f)
            if df.empty:
                continue
            # Ensure station column exists
            if "STATION_NAME" not in df.columns:
                print(f'[WARN] Skipping "{f.name}" – missing STATION_NAME', file=sys.stderr)
                continue
            # Melt the months into long format
            month_cols = [m for m in MONTHS.keys() if m in df.columns]
            if not month_cols:
                print(f'[WARN] Skipping "{f.name}" – no month columns found', file=sys.stderr)
                continue
            long_df = df.melt(id_vars=["STATION_NAME"], value_vars=month_cols,
                              var_name="Month", value_name="Temperature")
            long_df["MonthNum"] = long_df["Month"].map(MONTHS)
            # Create a dummy date (year is arbitrary, e.g., 2000)
            long_df["Date"] = pd.to_datetime(dict(year=2000, month=long_df["MonthNum"], day=1))
            long_df = long_df.dropna(subset=["Temperature"])
            frames.append(long_df[["STATION_NAME", "Date", "Temperature"]].rename(columns={"STATION_NAME": "Station"}))
        except Exception as e:
            print(f'[WARN] Failed to read "{f}": {e}', file=sys.stderr)
            continue
    if not frames:
        raise RuntimeError("No valid CSV files found.")
    all_df = pd.concat(frames, ignore_index=True)
    return all_df

def compute_seasonal_average(all_df: pd.DataFrame) -> pd.DataFrame:
    df = all_df.copy()
    df["Season"] = df["Date"].dt.month.map(SEASON_MAP)
    seasonal_avg = df.groupby("Season", sort=False)["Temperature"].mean().reindex(
        ["Summer", "Autumn", "Winter", "Spring"]
    )
    return seasonal_avg.to_frame(name="AverageTemperature")

def write_average_temp(seasonal_avg: pd.DataFrame, path: Path) -> None:
    lines = []
    for season in ["Summer", "Autumn", "Winter", "Spring"]:
        val = seasonal_avg.loc[season, "AverageTemperature"]
        lines.append(f"{season}: {val:.1f}°C" if pd.notna(val) else f"{season}: N/A")
    path.write_text("\n".join(lines), encoding="utf-8")

def compute_range_per_station(all_df: pd.DataFrame) -> pd.DataFrame:
    grp = all_df.groupby("Station")["Temperature"]
    stats = pd.DataFrame({
        "Min": grp.min(),
        "Max": grp.max(),
    })
    stats["Range"] = stats["Max"] - stats["Min"]
    return stats

def write_largest_range(station_stats: pd.DataFrame, path: Path) -> None:
    if station_stats.empty or station_stats["Range"].dropna().empty:
        path.write_text("No data available.", encoding="utf-8")
        return
    max_range = station_stats["Range"].max()
    winners = station_stats[station_stats["Range"] == max_range].sort_index()
    lines = [f"{station}: Range {row['Range']:.1f}°C (Max: {row['Max']:.1f}°C, Min: {row['Min']:.1f}°C)"
             for station, row in winners.iterrows()]
    path.write_text("\n".join(lines), encoding="utf-8")

def compute_stability(all_df: pd.DataFrame) -> pd.DataFrame:
    grp = all_df.groupby("Station")["Temperature"]
    stds = grp.std(ddof=1)
    return stds.to_frame(name="StdDev")

def write_stability(stds_df: pd.DataFrame, path: Path) -> None:
    if stds_df.empty:
        path.write_text("No stations have enough data to compute standard deviation.", encoding="utf-8")
        return
    min_std = stds_df["StdDev"].min()
    max_std = stds_df["StdDev"].max()
    most_stable = stds_df[stds_df["StdDev"] == min_std].sort_index()
    most_variable = stds_df[stds_df["StdDev"] == max_std].sort_index()
    lines = [f"Most Stable: {station}: StdDev {row['StdDev']:.1f}°C" for station, row in most_stable.iterrows()]
    lines += [f"Most Variable: {station}: StdDev {row['StdDev']:.1f}°C" for station, row in most_variable.iterrows()]
    path.write_text("\n".join(lines), encoding="utf-8")

def main():
    try:
        all_df = load_all_csvs(TEMPS_FOLDER)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    seasonal_avg = compute_seasonal_average(all_df)
    write_average_temp(seasonal_avg, OUTPUT_AVG)
    station_stats = compute_range_per_station(all_df)
    write_largest_range(station_stats, OUTPUT_RANGE)
    stds_df = compute_stability(all_df)
    write_stability(stds_df, OUTPUT_STABILITY)
    print(f'Wrote: "{OUTPUT_AVG.name}", "{OUTPUT_RANGE.name}", "{OUTPUT_STABILITY.name}"')

if __name__ == "__main__":
    main()
