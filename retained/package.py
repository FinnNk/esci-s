"""Package verified original datasets for a GitHub release without changing their bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import zstandard


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def package(source, output, lock):
    output.mkdir(parents=True, exist_ok=True)
    result = {'schema_version': 1, 'repository': 'FinnNk/esci-s',
              'release': 'lab-sources-v1', 'files': []}
    for item in lock['files']:
        original = source / item['file']
        if original.stat().st_size != item['bytes'] or digest(original) != item['sha256']:
            raise ValueError('Original source differs: ' + item['file'])
        print('Packaging ' + item['file'], flush=True)
        packed = output / (item['file'] + '.zst' if item['file'].endswith('.parquet') else item['file'])
        if item['file'].endswith('.parquet'):
            with original.open('rb') as inp, packed.open('wb') as out:
                zstandard.ZstdCompressor(level=10).copy_stream(inp, out)
            parts = [packed]
        else:
            parts = []
            with original.open('rb') as inp:
                number = 1
                while True:
                    block = inp.read(1024 * 1024)
                    if not block:
                        break
                    part = output / (item['file'] + f'.part{number:02d}')
                    with part.open('wb') as out:
                        out.write(block)
                        remaining = 1024**3 - len(block)
                        while remaining:
                            block = inp.read(min(1024 * 1024, remaining))
                            if not block:
                                break
                            out.write(block)
                            remaining -= len(block)
                    parts.append(part)
                    number += 1
        result['files'].append({**item, 'encoding': 'zstd' if item['file'].endswith('.parquet') else 'identity',
            'assets': [{'name': part.name, 'bytes': part.stat().st_size, 'sha256': digest(part)} for part in parts]})
    # Verify every package reconstructs the original, not only its transport hashes.
    for item in result['files']:
        check = hashlib.sha256()
        total = 0
        for asset in item['assets']:
            with (output / asset['name']).open('rb') as inp:
                stream = zstandard.ZstdDecompressor().stream_reader(inp) if item['encoding'] == 'zstd' else inp
                with stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b''):
                        check.update(block)
                        total += len(block)
        if total != item['bytes'] or check.hexdigest() != item['sha256']:
            raise ValueError('Reconstruction differs: ' + item['file'])
    (output / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({item['file']: sum(a['bytes'] for a in item['assets']) for item in result['files']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    package(args.source, args.output, json.loads(Path(__file__).with_name('original-sources.json').read_text(encoding='utf-8')))
