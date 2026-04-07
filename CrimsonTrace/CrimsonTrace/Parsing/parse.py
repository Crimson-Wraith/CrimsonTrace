import os

# 1. Parse the process down to just the executable name
# 2. Parse the command line to compress the arguments into a list
# 3. Parse the parent process down to just the exectuable name

def parse_process(process):
    '''
    parse_process removes any paths from the process field and returns only the exe. Written to take one row at a time to
    enable use of the .apply() function. Can also be used for parent process.
    Input: Process from dataframe row
    Output: Process executable (str) 
    '''    
    return os.path.basename(process.replace("\\", "/")) 

def parse_command_line(cmd: str) -> list[str]:
    '''
    parse_commandline compresses the arguments into a list.
    Input: command line string
    Output: List of arguments
    '''
    args = []
    current = []
    in_single = False
    in_double = False
    escape = False

    i = 0
    length = len(cmd)

    while i < length:
        c = cmd[i]

        # Handle escape only inside quotes
        if escape:
            current.append(c)
            escape = False
            i += 1
            continue

        # Backslash only escapes quotes when inside a quoted string
        if c == '\\' and (in_single or in_double):
            # Look ahead: only escape if next char is a quote
            if i + 1 < length and cmd[i+1] in ("'", '"'):
                escape = True
                i += 1
                continue
            else:
                # Literal backslash
                current.append(c)
                i += 1
                continue

        # Toggle single-quote mode
        if c == "'" and not in_double:
            in_single = not in_single
            i += 1
            continue

        # Toggle double-quote mode
        if c == '"' and not in_single:
            in_double = not in_double
            i += 1
            continue

        # Whitespace ends argument only if not inside quotes
        if c.isspace() and not in_single and not in_double:
            if current:
                args.append(''.join(current))
                current = []
            i += 1
            continue

        # Normal character
        current.append(c)
        i += 1

    # Append last argument
    if current:
        args.append(''.join(current))

    # Strip surrounding quotes
    cleaned = []
    for a in args:
        if len(a) >= 2:
            if (a[0] == '"' and a[-1] == '"') or (a[0] == "'" and a[-1] == "'"):
                cleaned.append(a[1:-1])
                continue
        cleaned.append(a)

    return cleaned    

def run(df):
    df['process'] = df['process'].map(parse_process)
    df['parentproc'] = df['parentproc'].map(parse_process)
    df['args'] = df['commandline'].map(parse_command_line)
    print("\n[+] Parsing complete!")
    return df