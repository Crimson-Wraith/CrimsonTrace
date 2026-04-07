from evtx import PyEvtxParser
import json
import pandas as pd

config_path="./ingest_config.json"

def load_evtx(path):
    '''
    This function loads evtx fiels and automatically extracts Events codes 4688 or 1, depending on if 
    Sysmon (1) or Windows Security Logs (4688).
    '''
    #Check to make sure its an EVTX file
    try:
        with open(path, "rb") as f:
            if f.read(8) != b"ElfFile\x00":
                raise Exception("\n[-] Failed to load EVTX file.... are you sure its an EVTX?")
    except OSError as e:
        raise Exception(f"[-] Failed to open file: {e}")
    
    event_ids={"4688","1"}
    parser = PyEvtxParser(path)
    records = []

    for record in parser.records_json():
        event = json.loads(record["data"])

        # Extract the EventID (may be int or dict depending on log)
        event_id = event["Event"]["System"]["EventID"]

        # Normalize EventID if it's a dict like {"#text": "4624"}
        if isinstance(event_id, dict):
            event_id = event_id.get("#text")

        # Apply filter
        if event_ids is None or str(event_id) in event_ids:
            event["_timestamp"] = record.get("timestamp")
            event["_record_id"] = record.get("record_id")
            records.append(event)
    df = pd.json_normalize(records, sep=".")
    return df

def load_csv(path):
    try:
        df = pd.from_csv(path)
    except:
        print("\n[-] Loading CSV file failed.... are you sure its a CSV?")
        sys.exit(1)
    return pd.from_csv(path)
# Windows Data ONLY !!!!!!!!
def load_field_config(config, mode="sec"):
    '''
    This function loads config.json[win_mode_fieldnames] to pull the fieldname pairings. Users need to update
    config.json if their fieldnames are different from the default. Two modes are sec for standard windows security logs
    and sysmon for Sysmon logs.
    '''
    field_config = config.get(f"win_{mode}_fieldnames")

    return field_config

def test_field_config(field_config, df):
    '''
    This function tests if the configuration for fieldnames matches the dataset provided.
    Input: field_config (dict), df (DataFrame)
    Output: None if success else raise exception
    '''
    missing = [key for key in field_config.keys() if key not in df.columns]

    if missing:
        raise KeyError(
            f"\n[-] Fieldname {missing} in config.json not found in dataset... "
            "Did you update the configuration?"
        )
    return None

def strip_evtx_columns(df, col_names):
    '''
This function takes in a DataFrame and a dictionary of field names provided by user to strip flattened
DataFrame to only relevant columns, then rename the columns to a common schema. 
By default, the columns extracted are:
    "_timestamp"                          --> timestamp
    "Event.EventData.NewProcessName"      --> process
    "Event.EventData.CommandLine"         --> commandline
    "Event.EventData.ParentProcessName"   --> parentproc
    "Event.EventData.SubjectUserName"     --> username
    '''
    df = df.rename(columns=col_names)
    new_cols = col_names.values()
    df = df[new_cols]
    return df

def strip_csv_columns(df, col_names):
    '''
This function takes in a DataFrame and a dictionary of field names provided by user to strip flattened
DataFrame to only relevant columns, then rename the columns to a common schema. 
By default, the columns extracted are:
    "_timestamp"                          --> timestamp
    "Event.EventData.NewProcessName"      --> process
    "Event.EventData.CommandLine"         --> commandline
    "Event.EventData.ParentProcessName"   --> parentproc
    "Event.EventData.SubjectUserName"     --> username
    '''
    df = df.rename(columns=col_names)
    new_cols = col_names.values()
    df = df[new_cols]
    return df

def load_strip_evtx(path, config, mode):
    #Load the file into a dataframe
    print(f"\n[*] Loading file {path}....\n") 
    df = load_evtx(path)
    #Load the fields from the config file
    print(f"\n[*] {mode} mode selected... loading field configuration\n")
    field_config = load_field_config(config, mode)
    #test to ensure the fields exist in the dataset
    print(f"\n[*] Verfiying fieldnames...")
    test_field_config(field_config, df)
    #Strip df down to relevant columns and rename to common schema 
    df = strip_evtx_columns(df, field_config)
    print("\n[+] EVTX file loaded.")
    return df

def load_strip_csv(path, config, mode):
    #Load the file into a dataframe
    print(f"\n[*] Loading file {path}....\n") 
    df = load_csv(path)
    #Load the fields from the config file
    print(f"\n[*] {mode} mode selected... loading field configuration\n")
    field_config = load_field_config(config, mode)
    #test to ensure the fields exist in the dataset
    print(f"\n[*] Verfiying fieldnames...\n")
    test_field_config(field_config, df)
    #Strip df down to relevant columns and rename to common schema 
    df = strip_csv_columns(df, field_config)
    print("\n[+] CSV file loaded.")

def run(path, config, mode, ext):
    if ext == 'evtx':
        df = load_strip_evtx(path, config, mode)
    elif ext == 'csv':
        df = load_strip_csv(path, config, mode)
    else:
        print("\n[-] Ingest.py -- Format error: Did you pass the correct format as an argument?")
        sys.exit(1)
    return df
    
    