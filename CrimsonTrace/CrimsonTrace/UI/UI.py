import os
import pandas as pd
from datetime import datetime

def export_cluster_report(df, output_dir="output", cluster_col="cluster"):
    """
    Prints a summary of each cluster and writes the full cluster data to an output file.
    NOTE: df should only contain IsolationForest-flagged events.

    Parameters:
        df          : DataFrame containing only IsolationForest-flagged events with cluster labels
        output_dir  : Directory to write output files to
        cluster_col : Name of the cluster label column (default: 'cluster')
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"cluster_report_{timestamp}.csv")

    total       = len(df)
    isolated    = df[df[cluster_col] == -1]
    clustered   = df[df[cluster_col] >= 0]
    cluster_ids = sorted(clustered[cluster_col].unique().astype(int))

    # ── Header ────────────────────────────────────────────────────────────────
    print("=" * 60)
    print("           HDBSCAN CLUSTER REPORT")
    print(f"           Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"  Total events  : {total}")
    print(f"  Isolated      : {len(isolated)}  (cluster = -1)")
    print(f"  Clustered     : {len(clustered)}  across {len(cluster_ids)} cluster(s)")
    print("=" * 60)

    all_output_rows = []

    # ── Per-cluster summary ───────────────────────────────────────────────────
    for cluster_id in cluster_ids:
        cluster_df = df[df[cluster_col] == cluster_id]
        print(f"\n  CLUSTER {cluster_id}")
        print(f"  {'─' * 40}")
        print(f"  Events        : {len(cluster_df)}")
        print(f"  % of total    : {len(cluster_df)/total*100:.1f}%")

        if 'membership_prob' in df.columns:
            print(f"  Avg membership probability : {cluster_df['membership_prob'].mean():.3f}")
        if 'outlier_score' in df.columns:
            print(f"  Avg outlier score          : {cluster_df['outlier_score'].mean():.3f}")
        if 'iso_score' in df.columns:
            print(f"  Avg isolation forest score : {cluster_df['iso_score'].mean():.3f}")

        all_output_rows.append(cluster_df)

    # ── Isolated events summary ───────────────────────────────────────────────
    if len(isolated) > 0:
        print(f"\n  ISOLATED EVENTS (cluster = -1)")
        print(f"  {'─' * 40}")
        print(f"  Events        : {len(isolated)}")
        print(f"  % of total    : {len(isolated)/total*100:.1f}%")
        if 'iso_score' in df.columns:
            print(f"  Avg isolation forest score : {isolated['iso_score'].mean():.3f}")
        all_output_rows.append(isolated)

    print("\n" + "=" * 60)

    # ── Write to file ─────────────────────────────────────────────────────────
    if all_output_rows:
        output_df = pd.concat(all_output_rows).sort_values(by=cluster_col)
        output_df.to_csv(output_path, index=True)
        print(f"  Report written to: {output_path}")
    else:
        print("  [WARNING] No events found — output file not written.")

    print("=" * 60)

def print_banner():
    print('#' * 100)
    print('*' * 100)
    print(r'''
     _______  ______ _____ _______ _______  _____  __   _ _______  ______ _______ _______ _______
     |       |_____/   |   |  |  | |______ |     | | \  |    |    |_____/ |_____| |       |______
     |_____  |    \_ __|__ |  |  | ______| |_____| |  \_|    |    |    \_ |     | |_____  |______                                                                                
        
        ''')
    print('*' * 100)
    print('#' * 100)

    
    