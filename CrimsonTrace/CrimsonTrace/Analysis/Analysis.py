from sklearn.ensemble import IsolationForest
import numpy as np
import os
import pandas as pd
from datetime import datetime

def run_isoForest(in_df):
    '''
    This function executes an IsolationForest analysis with 100 estimators with automatic contamination
    Input: DataFrame with feature engineering complete
    Output: DataFrame of anomalies based on the IsolationForest
    '''
    out_df = in_df.copy()
    IForest = IsolationForest(n_estimators=100, contamination='auto')
    IForest.fit(out_df)
    predictions = IForest.predict(out_df)

    #Add prediction to the output df
    out_df['anomaly'] = predictions
    anom_df = out_df.loc[out_df['anomaly'] == -1].copy()
    anom_df.drop('anomaly', axis=1, inplace=True)
    print(f"[Analysis] Isolation Forest flagged {len(anom_df)} amomalies")
    return anom_df

def _get_hdbscan_backend():
    """
    Attempt to load GPU-accelerated HDBSCAN via RAPIDS cuML.
    Falls back to CPU hdbscan if cuML is not available.
    Returns (hdbscan_class, using_gpu: bool)
    """
    try:
        from cuml.cluster import HDBSCAN as cuHDBSCAN
        import cudf  # confirms full RAPIDS stack is functional
        print("[HDBSCAN] GPU acceleration enabled via RAPIDS cuML")
        return cuHDBSCAN, True
    except ImportError:
        import hdbscan
        print("[HDBSCAN] GPU not available — falling back to CPU HDBSCAN")
        return hdbscan.HDBSCAN, False


#def run_hdbscan(anomaly_features, min_cluster_size=None, min_samples=None, metric='euclidean'):
#Changed to pull hyperparameters from config
def run_hdbscan(anomaly_features, config):
    n_anomalies = len(anomaly_features)

    # Adaptive defaults
    #if min_cluster_size is None:
     #   min_cluster_size = max(5, int(n_anomalies * 0.05))
    #if min_samples is None:
     #   min_samples = max(3, min_cluster_size // 2)
    
    HDBSCAN, using_gpu = _get_hdbscan_backend()
    #Pull Hyperparameters from config.json, passed to function
    min_cluster_size = config['min_cluster_size']
    min_samples = config['min_samples']
    metric = config['metric']
    
    print(f"[HDBSCAN] n_anomalies={n_anomalies} | "
          f"min_cluster_size={min_cluster_size} | min_samples={min_samples}")

    if using_gpu:
        import cudf
        # cuML expects a cuDF DataFrame or cupy array
        features_gpu = cudf.DataFrame(anomaly_features)
        clusterer = HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric=metric,
            cluster_selection_method='eom',
            prediction_data=True
        )
        cluster_labels = clusterer.fit_predict(features_gpu).to_numpy()  # bring back to CPU
    else:
        clusterer = HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric=metric,
            cluster_selection_method='eom',
            prediction_data=True
        )
        cluster_labels = clusterer.fit_predict(anomaly_features)

    # Quality warnings
    n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
    noise_pct   = (cluster_labels == -1).mean() * 100

    if noise_pct > 60:
        print(f"[WARNING] {noise_pct:.1f}% of anomalies are noise — consider lowering min_cluster_size or min_samples")
    elif n_clusters == 1:
        print("[WARNING] Only 1 cluster found — consider lowering min_cluster_size for more granularity")
    elif n_clusters > 20:
        print(f"[WARNING] {n_clusters} clusters found — consider raising min_cluster_size to reduce fragmentation")

    return cluster_labels, clusterer, using_gpu

def run(df, config):
    '''
    This is the main function for this module, executing the Isolation Forest and HDBSCAN.
    '''
    #Call and execution IsoForest
    print("\n[*] Running Isolation Forest....")
    anom_df = run_isoForest(df)
    #Execute HDBSCAN
    try:
        print("\n[*] Running HDBSCAN....")
        cluster_labels = run_hdbscan(anom_df, config)[0]
    except:
        print("[-] An error occurred. Its possible the dataset is too large and caused your RAM to overload.")
    print("\n[+] Analysis complete!")
    
    return anom_df, cluster_labels
    