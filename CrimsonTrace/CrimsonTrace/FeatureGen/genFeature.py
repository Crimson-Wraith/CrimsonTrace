import math
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd

def freq_ord_encode(col):
    '''
    Encodes column of dataframe using Frequency Based Ordinal Encoding (See Wiki for explaination)
    '''
    freq_counts = col.value_counts()
    rank_dict = {value: (i+1)/freq_counts.iloc[i] for i, value in enumerate(freq_counts.index)}
    col_encoded = col.map(rank_dict)
    return col_encoded
    
def fgen_exe_name(col):
    '''
    Simple function wrapper that called freq_ord_encode on the passed column. Intended for use with
    process and parentproc columns.
    '''
    feature_col = freq_ord_encode(col)
    return feature_col

def fgen_cmd_len(commandline):
    '''
    Input: commandline string (list of arguments)
    Output: Integer of total command length
    '''
    feature_cmd_len = sum(len(i) for i in commandline)
    return feature_cmd_len

def fgen_arg_count(commandline):
    '''
    Input: commandline string (list of arguments)
    Output: Integer of number of arguments 
    '''
    feature_arg_count = len(commandline)
    return feature_arg_count

def fgen_per_user_rarity(df):
    '''
    Input: dataframe with 2 columns (username, process(or parentproc))
    Output: Float value representing how 'rare' that process is for the given user
    '''
    #Count occurances of user:process
    counts = df.groupby(['username','process']).size().rename('count')

    #Merge back
    df = df.merge(counts, on=['username','process'], how='left')

    #Compute rarity and create new column
    df['rarity'] = 1 / df['count']    
    
    return df['rarity']

def fgen_per_host_rarity(df):
    '''
    Input: dataframe with 2 columns (computername, process)
    Output: Float value representing how 'rare' that process is for the given user
    '''
    #Count occurances of user:process
    counts = df.groupby(['computername','process']).size().rename('count')

    #Merge back
    df = df.merge(counts, on=['computername','process'], how='left')

    #Compute rarity and create new column
    df['rarity'] = 1 / df['count']    
    
    return df['rarity']

def fgen_entropy(commandline: str) -> float:
    if not commandline:
        return 0.0
    length = len(commandline)
    counts = {}
    for char in commandline:
        counts[char] = counts.get(char, 0) + 1

    return -sum(
        (freq / length) * math.log2(freq / length)
        for freq in counts.values()
    )

def fgen_parent_child_rarity(df, parent_col: str, child_col: str) -> "pd.DataFrame":
    """
    Adds a 'PCrarity' column to the DataFrame representing the rarity of each
    parent-child process relationship (0.0 = common, 1.0 = rare).

    Args:
        df:         A pandas DataFrame
        parent_col: Column name for the parent process
        child_col:  Column name for the child process

    Returns:
        The original DataFrame with a new 'PCrarity' column
    """
    pair_counts = {}
    parent_counts = {}

    for parent, child in zip(df[parent_col], df[child_col]):
        pair = (parent, child)
        pair_counts[pair] = pair_counts.get(pair, 0) + 1
        parent_counts[parent] = parent_counts.get(parent, 0) + 1

    total_unique_pairs = len(pair_counts)
    max_surprisal = math.log2(total_unique_pairs) if total_unique_pairs > 1 else 1.0

    def rarity(parent, child):
        pair = (parent, child)
        p_conditional = pair_counts[pair] / parent_counts[parent]
        surprisal = -math.log2(p_conditional)
        return min(surprisal / max_surprisal, 1.0)

    col = df.apply(lambda row: rarity(row[parent_col], row[child_col]), axis=1)
    return col

def fgen_avg_arg_len(args):
    if not args:
        return 0.0
    return sum(len(s) for s in args) / len(args)

def run(o_df):
    df = o_df.copy(deep=True)
    df['f_exe'] = fgen_exe_name(df['process'])
    df['f_pexe'] = fgen_exe_name(df['parentproc'])
    df['f_cmdlen'] = df['args'].map(fgen_cmd_len)
    df['f_argcount'] = df['args'].map(fgen_arg_count)
    df['f_userRare'] = fgen_per_user_rarity(df)
    df['f_hostRare'] = fgen_per_host_rarity(df)
    df['f_entropy'] = df['commandline'].map(fgen_entropy)
    df['f_PCrare'] = fgen_parent_child_rarity(df, 'process', 'parentproc')
    df['f_av_arg_len'] = df['args'].map(fgen_avg_arg_len)

    #Before returning, apply standard Scaler and strip original columns
    exclude_col = ['timestamp','computername','process','commandline','parentproc','username','args']
    df = df.loc[:, ~df.columns.isin(exclude_col)]
    scaler = StandardScaler()
    scaler.fit(df)
    scaled_np = scaler.transform(df)
    
    scaled_df = pd.DataFrame(scaled_np, columns=df.columns)
    return scaled_df