# CrimsonTrace

CrimsonTrace is a command-line threat hunting tool that applies unsupervised machine learning to Windows process creation logs. It uses an [**Isolation Forest**](https://www.datacamp.com/tutorial/isolation-forest) to flag anomalous process executions, then clusters those anomalies with [**HDBSCAN**](https://arize.com/blog-course/understanding-hdbscan-a-deep-dive-into-hierarchical-density-based-clustering/) so analysts can quickly triage related suspicious activity together rather than sifting through raw events one by one.

## Why CrimsonTrace?
 
Enterprise EDR solutions are the gold standard for detecting malicious activity on endpoints, but they come with significant licensing costs that put them out of reach for many individuals, small teams, and organizations. CrimsonTrace exists to fill that gap — it's a free, offline tool that anyone can point at a set of Windows process creation logs to surface suspicious activity.
 
Unlike signature-based detection, CrimsonTrace doesn't rely on known-bad indicators or threat intelligence feeds. It is purely mathematical: it identifies process executions that are statistically anomalous relative to the rest of the dataset, then groups similar anomalies into clusters. This means it can flag novel or previously unseen techniques that signature-based tools would miss entirely.
 
It's especially useful when you're staring down tens or hundreds of thousands of log entries and need a starting point. Rather than reading every line, you can let CrimsonTrace narrow the dataset down to the events that are most worth investigating — the ones that don't look like everything else.
 
**Typical use cases:**
 
- Threat hunting on networks without EDR coverage
- Triaging large forensic exports (EVTX or CSV) during incident response
- Supplementing signature-based tools with a behavioral, math-driven second opinion
- Training and education — learning what "normal" vs. "anomalous" process activity looks like in real log data

## How It Works

CrimsonTrace runs a four-stage pipeline:

1. **Ingest** — Loads Windows process creation events from `.evtx` files (Security Event 4688 or Sysmon Event 1) or `.csv` exports. Column names are mapped to a common schema via `config.json`.
2. **Parse** — Normalizes each record: strips file paths down to executable names, tokenizes command lines into argument lists.
3. **Feature Engineering** — Generates a feature vector per event:
   - Frequency-based ordinal encoding of process and parent-process names
   - Command-line length, argument count, and average argument length
   - Shannon entropy of the raw command line
   - Per-user process rarity and per-host process rarity
   - Parent→child relationship rarity (information-theoretic surprisal)
   - All features are then standard-scaled.
4. **Analysis** — Runs Isolation Forest (100 estimators, auto contamination) to isolate anomalies, then HDBSCAN to group those anomalies into clusters. Results are exported as a timestamped CSV report.

An optional **Tune** mode sweeps HDBSCAN hyperparameters and scores each combination with DBCV, printing the top-5 configurations so you can update `config.json` accordingly.

## Requirements

**Python 3.10+**

Core dependencies:

- pandas
- numpy
- scikit-learn
- hdbscan
- python-evtx (`evtx`)

Optional (GPU acceleration):

- RAPIDS cuML — enables GPU-accelerated Isolation Forest and HDBSCAN
- cuDF

To install cuML see this guide here:
https://docs.rapids.ai/install/

Install the core dependencies with:

```bash
pip install pandas numpy scikit-learn hdbscan evtx
```
Or install from requirements.txt
```bash
pip install -r ./requirements.txt
```

## Usage

```bash
python3 CrimsonTrace.py --format <evtx|csv> --type <Security|Sysmon> --path /absolute/path/to/logfile
```

**Arguments:**

| Flag | Required | Description |
|------|----------|-------------|
| `--format` | Yes | Input file format: `evtx` or `csv` |
| `--type` | Yes | Log source type: `Security` or `Sysmon` |
| `--path` | Yes | Absolute path to the log file |
| `--tune` | No | Run HDBSCAN hyperparameter tuning instead of the normal pipeline |

**Examples:**

```bash
# Analyze a Sysmon EVTX file
python3 CrimsonTrace.py --format evtx --type Sysmon --path /data/sysmon.evtx

# Analyze a CSV export of Windows Security logs
python3 CrimsonTrace.py --format csv --type Security --path /data/proccreation.csv

# Run the hyperparameter tuner
python3 CrimsonTrace.py --format evtx --type Sysmon --path /data/sysmon.evtx --tune
```

## Configuration

`config.json` controls field-name mappings and HDBSCAN hyperparameters.

### Field Mappings

CrimsonTrace needs six fields from each log record. The config maps your source column names to the internal schema. Three mapping profiles are provided by default:

- `win_Security_fieldnames` — Windows Security Event 4688 from EVTX
- `win_Sysmon_fieldnames` — Sysmon Event 1 from EVTX
- `csv_fieldnames` — Generic CSV export

If your column names differ from the defaults, update the relevant mapping in `config.json`. The six required internal fields are: `timestamp`, `computername`, `process`, `commandline`, `parentproc`, and `username`.

### HDBSCAN Hyperparameters

The `analysis` section controls clustering behavior:

```json
{
  "analysis": {
    "min_cluster_size": 5,
    "min_samples": 3,
    "metric": "euclidean",
    "cluster_selection_method": "eom"
  }
}
```

Use `--tune` mode to find optimal values for your dataset, then paste the best `min_cluster_size` and `min_samples` back into the config.

## Output

Results are written to the `output/` directory as a CSV file named `cluster_report_<timestamp>.csv`. Each row is an anomalous event with its original fields plus a `cluster` column:

- **cluster ≥ 0** — The event belongs to a numbered cluster of similar anomalies.
- **cluster = -1** — The event is an isolated anomaly that didn't fit any cluster (often the most interesting finds).

A summary is also printed to the console showing event counts, noise percentage, and per-cluster breakdowns.

## Project Structure

```
CrimsonTrace/
├── CrimsonTrace.py          # Entry point and pipeline orchestration
├── config.json               # Field mappings and hyperparameters
├── CrimsonTrace/
│   ├── Ingest/ingest.py      # EVTX/CSV loading and column normalization
│   ├── Parsing/parse.py      # Executable name extraction, command-line tokenization
│   ├── FeatureGen/genFeature.py  # Feature engineering and scaling
│   ├── Analysis/
│   │   ├── Analysis.py       # Isolation Forest + HDBSCAN pipeline
│   │   └── Tune.py           # HDBSCAN hyperparameter sweep (DBCV scoring)
│   └── UI/UI.py              # Banner, console output, CSV report export
└── output/                   # Generated cluster reports
```

## License

GNU General Public License v3.0
