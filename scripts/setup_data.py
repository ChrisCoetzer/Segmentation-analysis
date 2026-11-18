"""Download official releases, verify hashes, and prepare lossless Parquet copies."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
SPECS = {
    'uplift': {
        'repo': 'criteo/criteo-uplift',
        'file': 'criteo-research-uplift-v2.1.csv.gz',
        'rows': 13_979_592,
        'sep': ',',
        'columns': [f'f{i}' for i in range(12)] + ['treatment', 'conversion', 'visit', 'exposure'],
        'floats': [f'f{i}' for i in range(12)],
        'binary': ['treatment', 'conversion', 'visit', 'exposure'],
    },
    'attribution': {
        'repo': 'criteo/criteo-attribution-dataset',
        'file': 'criteo_attribution_dataset.tsv.gz',
        'rows': 16_468_027,
        'sep': '\t',
        'columns': ['timestamp', 'uid', 'campaign', 'conversion', 'conversion_timestamp',
                    'conversion_id', 'attribution', 'click', 'click_pos', 'click_nb',
                    'cost', 'cpo', 'time_since_last_click'] + [f'cat{i}' for i in range(1, 10)],
        'floats': ['cost', 'cpo'],
        'binary': ['conversion', 'attribution', 'click'],
    },
}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def fetch_json(url):
    with urlopen(url, timeout=90) as response:
        return json.load(response)


def download(name, spec):
    raw = ROOT / 'data' / 'raw' / name
    raw.mkdir(parents=True, exist_ok=True)
    manifest_path = raw / 'manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
    else:
        info = fetch_json(f"https://huggingface.co/api/datasets/{spec['repo']}")
        revision = info['sha']
        files = fetch_json(f"https://huggingface.co/api/datasets/{spec['repo']}/tree/{revision}")
        entry = next(f for f in files if f['path'] == spec['file'])
        manifest = {
            'repo': spec['repo'], 'revision': revision, 'file': spec['file'],
            'bytes': entry['size'], 'sha256': entry['lfs']['oid'],
            'url': f"https://huggingface.co/datasets/{spec['repo']}/resolve/{revision}/{spec['file']}",
        }
    target = raw / spec['file']
    if target.exists():
        if target.stat().st_size != manifest['bytes'] or digest(target) != manifest['sha256']:
            raise ValueError(f'{target}: existing file does not match source checksum')
        print(f'{name}: existing download verified', flush=True)
    else:
        partial = target.with_suffix(target.suffix + '.partial')
        count = 0
        with urlopen(manifest['url'], timeout=120) as response, partial.open('wb') as stream:
            while block := response.read(8 * 1024 * 1024):
                stream.write(block)
                count += len(block)
                if count % (64 * 1024 * 1024) == 0:
                    print(f'{name}: {count / 1e6:.0f}/{manifest["bytes"] / 1e6:.0f} MB', flush=True)
        if count != manifest['bytes'] or digest(partial) != manifest['sha256']:
            raise ValueError(f'{name}: download checksum or size mismatch')
        partial.replace(target)
        print(f'{name}: download complete; SHA-256 verified', flush=True)
    write_json(manifest_path, manifest)
    for filename in ['README.md']:
        destination = raw / filename
        if not destination.exists():
            url = f"https://huggingface.co/datasets/{spec['repo']}/resolve/{manifest['revision']}/{filename}"
            with urlopen(url, timeout=90) as response:
                destination.write_bytes(response.read())


def prepare(name, spec):
    import numpy as np
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq

    source = ROOT / 'data' / 'raw' / name / spec['file']
    manifest = json.loads((source.parent / 'manifest.json').read_text())
    if source.stat().st_size != manifest['bytes'] or digest(source) != manifest['sha256']:
        raise ValueError(f'{name}: raw file integrity failed')
    output = ROOT / 'data' / 'processed' / f'{name}.parquet'
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.parquet.partial')
    dtypes = {c: ('float64' if c in spec['floats'] else 'int64') for c in spec['columns']}
    report = {'dataset': name, 'source_sha256': manifest['sha256'], 'rows': 0,
              'nulls': {c: 0 for c in spec['columns']}, 'nonfinite': {c: 0 for c in spec['columns']},
              'min': {}, 'max': {}, 'binary_counts': {}, 'group_counts': {}}
    writer = None
    try:
        for i, chunk in enumerate(pd.read_csv(source, sep=spec['sep'], dtype=dtypes, chunksize=250_000)):
            if list(chunk.columns) != spec['columns']:
                raise ValueError(f'{name}: unexpected column names or order: {list(chunk.columns)}')
            if i == 0:
                report['dtypes'] = {c: str(t) for c, t in chunk.dtypes.items()}
                preview = ROOT / 'data' / 'previews'
                preview.mkdir(parents=True, exist_ok=True)
                chunk.head(20).to_parquet(preview / f'{name}_first20.parquet', index=False)
            for c in spec['columns']:
                report['nulls'][c] += int(chunk[c].isna().sum())
                report['nonfinite'][c] += int((~np.isfinite(chunk[c].to_numpy())).sum())
                report['min'][c] = min(report['min'].get(c, float('inf')), chunk[c].min().item())
                report['max'][c] = max(report['max'].get(c, float('-inf')), chunk[c].max().item())
            for c in spec['binary']:
                if not chunk[c].isin([0, 1]).all():
                    raise ValueError(f'{name}: nonbinary values in {c}')
                counts = report['binary_counts'].setdefault(c, {'0': 0, '1': 0})
                for value, count in chunk[c].value_counts().items():
                    counts[str(value)] += int(count)
            if name == 'uplift':
                for keys, count in chunk.groupby(['treatment', 'exposure', 'visit', 'conversion']).size().items():
                    key = ','.join(map(str, keys))
                    report['group_counts'][key] = report['group_counts'].get(key, 0) + int(count)
            table = pa.Table.from_pandas(chunk, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(temporary, table.schema, compression='zstd')
            writer.write_table(table)
            report['rows'] += len(chunk)
            if (i + 1) % 8 == 0:
                print(f'{name}: prepared {report["rows"]:,} rows', flush=True)
    finally:
        if writer is not None:
            writer.close()
    if report['rows'] != spec['rows']:
        raise ValueError(f'{name}: unexpected row count {report["rows"]}')
    if any(report['nulls'].values()) or any(report['nonfinite'].values()):
        raise ValueError(f'{name}: missing or nonfinite values found; inspect raw input')
    if pq.ParquetFile(temporary).metadata.num_rows != report['rows']:
        raise ValueError(f'{name}: Parquet row count mismatch')
    temporary.replace(output)
    report['parquet_bytes'] = output.stat().st_size
    report['binary_rates'] = {c: counts['1'] / report['rows'] for c, counts in report['binary_counts'].items()}
    write_json(ROOT / 'outputs' / 'validation' / f'{name}.json', report)
    print(f'{name}: validated {report["rows"]:,} rows, {len(dtypes)} columns; saved {output}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['download', 'prepare'], required=True)
    parser.add_argument('--dataset', choices=['all', *SPECS], default='all')
    args = parser.parse_args()
    for name, spec in SPECS.items():
        if args.dataset in ('all', name):
            (download if args.stage == 'download' else prepare)(name, spec)
