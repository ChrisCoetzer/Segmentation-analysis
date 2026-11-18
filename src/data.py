"""Local dataset access. Loading never downloads or trains anything."""
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
UPLIFT_FEATURES = [f'f{i}' for i in range(12)]


def load_dataset(name, columns=None):
    """Read a prepared dataset; select columns to reduce memory usage."""
    if name not in ('uplift', 'attribution'):
        raise ValueError('Choose uplift or attribution')
    path = ROOT / 'data' / 'processed' / f'{name}.parquet'
    if not path.exists():
        raise FileNotFoundError(f'Prepare the dataset first: {path}')
    return pd.read_parquet(path, columns=columns)


def iter_batches(name, columns=None, batch_size=100_000):
    """Yield DataFrames without loading the whole dataset into memory."""
    if name not in ('uplift', 'attribution'):
        raise ValueError('Choose uplift or attribution')
    path = ROOT / 'data' / 'processed' / f'{name}.parquet'
    for batch in pq.ParquetFile(path).iter_batches(batch_size=batch_size, columns=columns):
        yield batch.to_pandas()
