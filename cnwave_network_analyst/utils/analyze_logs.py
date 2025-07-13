import os
import sys
import re
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import pandas as pd

def find_log_directory(base_path: Path, override_name: str = None) -> Path:
    if override_name:
        target_dir = base_path / override_name
    else:
        all_dirs = sorted([d for d in base_path.iterdir() if d.is_dir()], key=os.path.getmtime, reverse=True)
        target_dir = all_dirs[0] if all_dirs else None

    if not target_dir or not target_dir.exists():
        raise FileNotFoundError(f"Log directory not found: {override_name or 'latest'}")
    return target_dir


def parse_openai_log(log_file):
    with open(log_file, "r") as f:
        lines = f.readlines()

    request_times = []
    response_times = []
    token_entries = []

    current_response_time = None

    for line in lines:
        if "OpenAI request started at" in line:
            timestamp_str = line.split("at ")[1].strip()
            request_times.append(datetime.fromisoformat(timestamp_str))

        elif "OpenAI response ID" in line:
            match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)", line)
            if match:
                timestamp_str = match.group(1).replace(",", ".")
                current_response_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                response_times.append(current_response_time)

        elif '"total_tokens":' in line and current_response_time:
            match = re.search(r'"total_tokens": (\d+)', line)
            if match:
                token_entries.append({
                    "Response Time": current_response_time,
                    "Total Tokens": int(match.group(1))
                })

    # Match request and response durations
    durations = []
    for i in range(min(len(request_times), len(response_times))):
        durations.append({
            "Request Time": request_times[i],
            "Response Time": response_times[i],
            "Duration (s)": (response_times[i] - request_times[i]).total_seconds()
        })

    df_duration = pd.DataFrame(durations)
    df_tokens = pd.DataFrame(token_entries)
    df_report = pd.merge(df_duration, df_tokens, on="Response Time", how="left")
    return df_report

def parse_cnmaestro_log(filepath: Path):
    with open(filepath) as f:
        lines = f.readlines()

    calls = []
    failures = []
    i = 0
    while i < len(lines):
        line = lines[i]
        call_match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - INFO - Tool call: (\w+)( with args .*|)", line)
        if call_match:
            ts_start = datetime.strptime(call_match.group(1), "%Y-%m-%d %H:%M:%S,%f")
            api = call_match.group(2)
            # look ahead for result or error
            found = False
            for j in range(i + 1, min(i + 10, len(lines))):
                result_info = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - INFO - Tool result: (.*)", lines[j])
                result_error = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ERROR - Error response: .*?\{.*\}", lines[j])
                if result_info:
                    ts_end = datetime.strptime(result_info.group(1), "%Y-%m-%d %H:%M:%S,%f")
                    duration = round((ts_end - ts_start).total_seconds(), 2)
                    result = result_info.group(2).strip()
                    failed = result.startswith('{"error"') or result == '{}' or "'status': 'error'" in result
                    if failed:
                        failures.append({"API": api, "Time": ts_start.strftime("%H:%M:%S"), "Reason": result})
                    calls.append({"Time": ts_start.strftime("%H:%M:%S"), "API Call": api, "Duration (sec)": duration})
                    found = True
                    i = j
                    break
                elif result_error:
                    reason = lines[j].split("- ERROR -")[-1].strip()
                    failures.append({"API": api, "Time": ts_start.strftime("%H:%M:%S"), "Reason": reason})
                    found = True
                    i = j
                    break
            if not found:
                failures.append({"API": api, "Time": ts_start.strftime("%H:%M:%S"), "Reason": "No result or error line found"})
        i += 1
    return calls, failures


def print_table(title, rows, headers):
    if not rows:
        print(f"\n=== {title} ===\n(No data)")
        return
    print(f"\n=== {title} ===")
    col_widths = [max(len(str(row[h])) for row in rows) for h in headers]
    col_widths = [max(w, len(h)) for w, h in zip(col_widths, headers)]
    header_row = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(header_row)
    print("-|-".join("-" * w for w in col_widths))
    for row in rows:
        print(" | ".join(str(row[h]).ljust(w) for h, w in zip(headers, col_widths)))


def main():
    logs_base = Path("logs")
    log_folder = sys.argv[1] if len(sys.argv) > 1 else None
    log_dir = find_log_directory(logs_base, log_folder)

    print(f"Analyzing logs in: {log_dir.name}\n")

    openai_log = log_dir / "openai.log"
    cnmaestro_log = log_dir / "cnmaestro.log"

    report = parse_openai_log(openai_log)
    print(report.to_string(index=False))
    api_calls, api_failures = parse_cnmaestro_log(cnmaestro_log) if cnmaestro_log.exists() else ([], [])

    #print_table("OpenAI Token Usage", openai_data, ["ID", "Time", "Prompt Tokens", "Completion Tokens", "Total Tokens", "Model", "Duration (sec)"])
    print_table("cnMaestro API Call Timings", api_calls, ["Time", "API Call", "Duration (sec)"])

    if api_failures:
        print_table("❓ cnMaestro API Failures", api_failures, ["Time", "API", "Reason"])
    else:
        print("\n✅ No cnMaestro API failures detected.")


if __name__ == "__main__":
    main()