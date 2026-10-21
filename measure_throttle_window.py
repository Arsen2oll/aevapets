#!/usr/bin/env python3
"""
measure_throttle_window.py

Passive measurement of EOP throttle window length from PMTA accounting logs.

PASSIVE: Parses historical logs only. Does NOT send any traffic.
Zero risk of provoking escalation to permanent ban.

Approach
--------
For each 451 4.7.500 (AS2162) event in the accounting log, find the next
successful delivery (type=d) from the SAME source IP and compute the elapsed
time. That elapsed time is the throttle window (or a lower bound, if traffic
resumed later than the window actually closed).

Usage
-----
    python3 measure_throttle_window.py /var/log/pmta/acct-*.csv

Assumes PMTA default accounting format with columns including:
    type,timeLogged,timeQueued,orig,rcpt,orig-ip,dsnStatus,dsnDiag

If your acct-file-def columns differ, pass --orig-ip-col N etc.

Dependencies: Python 3.6+ stdlib only.
"""

import argparse
import csv
import glob
import sys
from collections import defaultdict
from datetime import datetime
from statistics import median


THROTTLE_MARKER = "AS2162"
THROTTLE_DSN = "4.7.500"


def parse_time(s):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromtimestamp(int(s))
    except (ValueError, OSError):
        return None


def iter_rows(paths):
    for pattern in paths:
        for path in sorted(glob.glob(pattern)) or [pattern]:
            try:
                with open(path, newline="") as fh:
                    reader = csv.DictReader(fh)
                    for row in reader:
                        row["__source"] = path
                        yield row
            except FileNotFoundError:
                print(f"warn: {path} not found", file=sys.stderr)


def classify(row):
    rtype = (row.get("type") or "").strip()
    dsn = (row.get("dsnStatus") or "").strip()
    diag = (row.get("dsnDiag") or "")
    if rtype == "d":
        return "delivered"
    if THROTTLE_MARKER in diag or (dsn == THROTTLE_DSN and "try again later" in diag.lower()):
        return "throttled"
    return "other"


def compute_windows(rows):
    by_ip = defaultdict(list)
    for row in rows:
        ts = parse_time(row.get("timeLogged") or row.get("timeQueued") or "")
        if ts is None:
            continue
        kind = classify(row)
        if kind == "other":
            continue
        ip = (row.get("orig-ip") or row.get("origIp") or "unknown").strip()
        by_ip[ip].append((ts, kind))

    windows = defaultdict(list)
    for ip, events in by_ip.items():
        events.sort(key=lambda e: e[0])
        last_throttle = None
        for ts, kind in events:
            if kind == "throttled":
                if last_throttle is None:
                    last_throttle = ts
                else:
                    last_throttle = ts
            elif kind == "delivered" and last_throttle is not None:
                elapsed = (ts - last_throttle).total_seconds()
                windows[ip].append(elapsed)
                last_throttle = None
    return windows


def summarize(windows):
    if not windows:
        print("No 451 4.7.500 → successful-delivery pairs found.")
        print("Either you have never hit the throttle, or the log window is too short.")
        return

    print(f"{'source-ip':<20} {'samples':>8} {'min(s)':>10} {'median(s)':>12} {'p95(s)':>10} {'max(s)':>10}")
    print("-" * 72)
    all_samples = []
    for ip, samples in sorted(windows.items()):
        all_samples.extend(samples)
        samples_sorted = sorted(samples)
        p95 = samples_sorted[int(0.95 * (len(samples_sorted) - 1))]
        print(f"{ip:<20} {len(samples):>8} {min(samples):>10.0f} {median(samples):>12.0f} "
              f"{p95:>10.0f} {max(samples):>10.0f}")

    if len(windows) > 1:
        all_sorted = sorted(all_samples)
        p95 = all_sorted[int(0.95 * (len(all_sorted) - 1))]
        print("-" * 72)
        print(f"{'ALL':<20} {len(all_samples):>8} {min(all_samples):>10.0f} "
              f"{median(all_samples):>12.0f} {p95:>10.0f} {max(all_samples):>10.0f}")

    print()
    med = median(all_samples)
    print(f"Interpretation: median elapsed = {med:.0f}s ({med/60:.1f} min).")
    print("Set `max-msg-rate` so (per-ip-quota / rate_per_min) ≈ this window length,")
    print("i.e. deliver ~2500 recipients over ~{:.0f} minutes to stay just under.".format(med/60))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="+", help="PMTA accounting CSV path(s) or globs")
    args = ap.parse_args()
    windows = compute_windows(iter_rows(args.logs))
    summarize(windows)


if __name__ == "__main__":
    main()
