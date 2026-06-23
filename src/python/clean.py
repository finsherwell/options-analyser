import os
import sys

import pandas as pd
import numpy as np

from datetime import datetime
from src.python.utils import load_file_chunks

def process_options_stream(options_path, underlying_df, output_path, start_date, end_date, chunksize=100_000):
    first_write = True

    for chunk in pd.read_csv(options_path, chunksize=chunksize, parse_dates=['date']):
        chunk = chunk[(chunk['date'] >= start_date) & (chunk['date'] <= end_date)]

        if chunk.empty:
            continue

        columns = ['am_set_flag', 'am_settlement', 'ss_flag', 'index_flag', 'issuer', 'secid']

        chunk = chunk.drop(columns=columns, errors='ignore')

        chunk['exdate'] = pd.to_datetime(chunk['exdate'], format='%Y-%m-%d')

        chunk = chunk.merge(
            underlying_df[['date', 'spot', 'spx_return']],
            on='date',
            how='left'
        )

        # Feature Engineering
        chunk = chunk.dropna(subset=['impl_volatility', 'delta', 'gamma', 'vega', 'theta'])

        chunk['strike_price'] = chunk['strike_price'] / 1000
        chunk['dte'] = (chunk['exdate'] - chunk['date']).dt.days

        chunk['mid'] = (chunk['best_bid'] + chunk['best_offer']) / 2
        chunk['bid_ask_spread'] = chunk['best_offer'] - chunk['best_bid']

        chunk['moneyness'] = chunk['strike_price'] / chunk['spot']
        chunk['log_moneyness'] = np.log(chunk['moneyness'])

        chunk = chunk.drop(columns=['exercise_style'], errors='ignore')

        # Write Immediate
        chunk.to_csv(
            output_path,
            mode='w' if first_write else 'a',
            header=first_write,
            index=False
        )

        first_write = False

if __name__ == "__main__":
    sys.path.append(os.path.join(os.getcwd(), "../"))

    DATA_PATH = os.path.join(os.getcwd(), "data")
    OPTIONS_DATA_PATH = os.path.join(DATA_PATH, "spx_options.csv")
    UNDERLYING_DATA_PATH = os.path.join(DATA_PATH, "spx_underlying.csv")
    OUTPUT_PATH = os.path.join(DATA_PATH, "spx_options_processed.csv")

    start_date = datetime(2010, 1, 1)
    end_date = datetime(2025, 8, 29)

    underlying_df = load_file_chunks(UNDERLYING_DATA_PATH, start_date, end_date)
    underlying_df = underlying_df.drop(columns=['secid'])
    underlying_df = underlying_df.rename(columns={'close': 'spot', 'return': 'spx_return'})

    process_options_stream(OPTIONS_DATA_PATH, underlying_df, OUTPUT_PATH, start_date, end_date)