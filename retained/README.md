# Retained ESCI sources for the search lab

The `lab-sources-v1` release retains the exact source files used by the search
lab. Downloads do not depend on the original ESCI-S S3 bucket remaining available.
The full datasets are release assets, not files in Git history.

## Contents and attribution

| Original file | Source | Original bytes | Download bytes |
| --- | --- | ---: | ---: |
| `products.parquet` | Amazon Science ESCI | 1,108,857,465 | 919,638,615 |
| `examples.parquet` | Amazon Science ESCI | 51,286,808 | 20,931,574 |
| `esci-s.json.zst` | shuttie/ESCI-S | 3,620,467,456 | 3,620,467,456 |

Original sources and commit references are recorded in `original-sources.json`.
Both upstream repositories publish under Apache-2.0. Retain their attribution
when redistributing these copies:

- [Amazon Science ESCI](https://github.com/amazon-science/esci-data/tree/7916cdf6ab75a462e77f20ab40428a10923998d5)
- [ESCI-S](https://github.com/shuttie/esci-s/tree/99e849f387b6618a5e8641f28d7847f7cd6cf8ac)

The Parquet files have an additional Zstandard layer. ESCI-S keeps its existing
compression and is split into four ordered chunks below GitHub's asset size limit.
Join those chunks in manifest order to recover `esci-s.json.zst`. No records,
metadata, labels or compressed ESCI-S bytes have been altered.

`manifest.json` records hashes and sizes for both the assets and the reconstructed
originals. The lab keeps an accepted copy of that manifest and verifies both;
replacing a release asset cannot silently change its catalogue inputs.

## Reproduce the packages

With Python and `zstandard==0.23.0` installed, from this repository root:

```sh
python retained/package.py --source /path/to/verified-originals --output /path/to/assets
```

The source directory must contain all three original files. The command verifies
their pinned hashes, writes the assets and manifest, then reconstructs every
original in memory streams and verifies its size and hash again. Allow roughly
5 GB for packaged assets in addition to the originals. Publication is a separate
step; this script does not upload, change an existing release or download upstream
sources. Keep an accepted release unchanged and use a new tag for future bundles.
