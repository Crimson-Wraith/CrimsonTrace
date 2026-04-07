from pathlib import Path
import json
import time
import argparse
import numpy as np
from CrimsonTrace.Ingest import ingest
from CrimsonTrace.Parsing import parse
from CrimsonTrace.FeatureGen import genFeature
from CrimsonTrace.Analysis import Analysis
from CrimsonTrace.Analysis import Tune
from CrimsonTrace.UI import UI


#Functions init
def load_config():
    config_path = Path(__file__).parent/"config.json" # Correct line for production
    #config = json.load(open(Path("./config.json")))
    config = json.load(open(Path(config_path)))
    return config

def collect_args():
    desc = """
    Executes an Isolation Forest and HDBSCAN on the provided process creation logs file.
    """
    epi = """
    """
    parser = argparse.ArgumentParser(description=desc,epilog=epi)
    
    parser.add_argument("--format", required=True, type=str, help="Format of input file. Supported file types: evtx, csv") #args[0]
    parser.add_argument("--type", required=True, type=str, help="Type of log, Security or Sysmon.") #args[1]
    parser.add_argument("--path", required=True, type=str, help="Absolute path to target file.") #args[2]
    parser.add_argument("--tune", required=False, action='store_true', help="Enable tuning mode to tune hyperparameters.")
    args, unknown = parser.parse_known_args()
    if unknown:
        print("\n[-] Unexpected arguments detected:")
        for item in unknown:
            print(f"{item}")

    return vars(args)

def main():
    UI.print_banner()
    time.sleep(2)
    #Get user arguments
    args = collect_args()

    #Load config file 
    config = load_config()

    #Initialize variables
    path = args['path']
    mode = args['type']
    ext = args['format']
    tune = args['tune'] #Boolean
    
    #Run the modules
    #Ingest log file
    print("\n[*] Ingesting File....")
    df = ingest.run(path, config['ingest'], mode, ext)
    #Parse entries to ensure consistent formatting
    print("\n[*] Parsing File....")
    df = parse.run(df)
    #Generate Features
    print("\n[*] Performing Feature Engineering....")
    f_df = genFeature.run(df)
    #TODO 
    #Implement Pulling Hyperparameters from config file

    #Tune switch here
    if tune:
        print("\n[*] Running Tuner Module...")
        tune_df = Analysis.run_isoForest(f_df)
        Tune.run(tune_df)
    else:
        #Run IsoForest and HDBSCAN
        print("\n[*] Running Analysis... This may take bit.")
        anom_df, cluster_labels = Analysis.run(f_df,config['analysis'])

        #Grab the anomalous rows from the original dataframe
        anom_df_full = df.loc[anom_df.index]
    
        #Add cluster labels
        anom_df_full['cluster'] = cluster_labels
        
        #Print and export results
        UI.export_cluster_report(anom_df_full)

   
    print("\n[+] CrimsonTrace complete, happy hunting!\n")

    

if __name__ == "__main__":
    main()