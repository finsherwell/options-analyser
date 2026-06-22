import pandas as pd

def load_file_chunks(file_path, start_date, end_date, chunksize=100_000):
    chunks = []
    for chunk in pd.read_csv(file_path, chunksize=chunksize, parse_dates=['date']):
        mask = ((chunk['date'] >= start_date) & (chunk['date'] <= end_date))
        chunks.append(chunk[mask])
    
    df = pd.concat(chunks)
    return df