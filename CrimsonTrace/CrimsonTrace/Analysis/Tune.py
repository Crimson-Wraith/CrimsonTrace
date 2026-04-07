import json
import hdbscan
import numpy as np
import pandas as pd
from itertools import product
from hdbscan.validity import validity_index



def _get_hdbscan_backend():
    try:
        from cuml.cluster import HDBSCAN as cuHDBSCAN
        import cudf
        print("[HDBSCAN] GPU acceleration enabled via RAPIDS cuML")
        return cuHDBSCAN, True
    except ImportError:
        print("[HDBSCAN] GPU not available — falling back to CPU HDBSCAN")
        return hdbscan.HDBSCAN, False


def tune_hdbscan(features, min_cluster_sizes=None, min_samples_list=None):
    """
    Sweeps HDBSCAN parameters using DBCV scoring and writes the best
    result to the config file. Run manually — not part of the main pipeline.
    """
    if min_cluster_sizes is None:
        min_cluster_sizes = [2, 3]
    if min_samples_list is None:
        min_samples_list  = [1, 2]

    results     = []
    best_score  = -np.inf
    best_params = None

    print(f"[Tuner] Sweeping {len(min_cluster_sizes) * len(min_samples_list)} combinations...")
    
    #Check for GPU accel
    HDBSCAN, using_gpu = _get_hdbscan_backend()
    if using_gpu:
        import cudf
        features_input = cudf.DataFrame(features)
    else:
        features_input = features
    #GPU check complete
    
    for i, (mcs, ms) in enumerate(product(min_cluster_sizes, min_samples_list)):
        if ms > mcs:
            continue
        print(f"[Tuner] Combo {i}: mcs={mcs}, ms={ms}", flush=True)
        clusterer = HDBSCAN(
            min_cluster_size         = mcs,
            min_samples              = ms,
            metric                   = 'euclidean',
            cluster_selection_method = 'eom',
            prediction_data          = True
        )
        labels     = clusterer.fit_predict(features_input)
        if using_gpu:
            labels_np = labels.to_numpy()
        else:
            labels_np = labels
        n_clusters = len(set(labels_np)) - (1 if -1 in labels_np else 0)
        noise_pct  = (labels == -1).mean() * 100
        #score      = clusterer.relative_validity_ if n_clusters >= 2 else -np.inf
        if n_clusters >= 2:
            if using_gpu:
                features_np = features_input.to_pandas().to_numpy()
            else:
                features_np = features_input

            score = validity_index(features_np, labels_np)
        else:
            score = -np.inf
            
        results.append({
            'min_cluster_size' : mcs,
            'min_samples'      : ms,
            'n_clusters'       : n_clusters,
            'noise_pct'        : round(noise_pct, 1),
            'dbcv_score'       : round(score, 4)
        })

        if score > best_score:
            best_score  = score
            best_params = {'min_cluster_size': mcs, 'min_samples': ms}

    results_df = pd.DataFrame(results).sort_values('dbcv_score', ascending=False)

    print(f"\n[Tuner] Top 5 combinations:")
    print(results_df.head(5).to_string(index=False))

    # Read existing config to preserve non-tuned fields, then overwrite only the tuned params
    #with open(CONFIG_PATH, 'r') as f:
     #   config = json.load(f)

    #config['min_cluster_size'] = best_params['min_cluster_size']
    #config['min_samples']      = best_params['min_samples']

    #with open(CONFIG_PATH, 'w') as f:
    #    json.dump(config, f, indent=2)

    #print(f"\n[Tuner] Config updated at {CONFIG_PATH}")
    #print(f"  min_cluster_size → {best_params['min_cluster_size']}")
    #print(f"  min_samples      → {best_params['min_samples']}")

    return results_df
def tune_hdbscan2(features, min_cluster_sizes=None, min_samples_list=None):
    if min_cluster_sizes is None:
        min_cluster_sizes = [2, 3, 5, 7, 10, 15, 20]
    if min_samples_list is None:
        min_samples_list  = [1, 2, 3, 5, 7, 10, 15, 20]

    results     = []
    best_score  = -np.inf
    best_params = None

    print(f"[Tuner] Sweeping {len(min_cluster_sizes) * len(min_samples_list)} combinations...", flush=True)
    
    HDBSCAN, using_gpu = _get_hdbscan_backend()
    if using_gpu:
        import cudf
        features_input = cudf.DataFrame(features)
    else:
        features_input = features
    
    for mcs, ms in product(min_cluster_sizes, min_samples_list):
        if ms > mcs:
            continue
           
        clusterer = HDBSCAN(
            min_cluster_size         = mcs,
            min_samples              = ms,
            metric                   = 'euclidean',
            cluster_selection_method = 'eom',
            prediction_data          = True
        )
        labels = clusterer.fit_predict(features_input)

        if using_gpu:
            labels_np = labels.to_numpy()
        else:
            labels_np = labels

        n_clusters = len(set(labels_np)) - (1 if -1 in labels_np else 0)
        noise_pct  = (labels == -1).mean() * 100

        if n_clusters >= 2:
            if using_gpu:
                features_np = features_input.to_pandas().to_numpy()
            else:
                features_np = np.asarray(features_input)

            score = validity_index(features_np, labels_np)
        else:
            score = -np.inf
            
        results.append({
            'min_cluster_size' : mcs,
            'min_samples'      : ms,
            'n_clusters'       : n_clusters,
            'noise_pct'        : round(noise_pct, 1),
            'dbcv_score'       : round(score, 4)
        })

        if score > best_score:
            best_score  = score
            best_params = {'min_cluster_size': mcs, 'min_samples': ms}

    results_df = pd.DataFrame(results).sort_values('dbcv_score', ascending=False)

    print(f"\n[Tuner] Top 5 combinations:")
    print(results_df.head(5).to_string(index=False))

    return results_df

def run(df):
    """
    Executes the tuner module and prints the Top 5 hyperparameters.
    """
    tune_hdbscan2(df)
    
    return None