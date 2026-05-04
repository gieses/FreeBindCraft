#!/usr/bin/env python3
"""Download and extract AlphaFold weights."""
import argparse
import os
import tarfile
import urllib.request
from pathlib import Path

from loguru import logger

PARAMS_URL = "https://storage.googleapis.com/alphafold/alphafold_params_2022-12-06.tar"


def ensure_af_params_available(params_dir: str) -> str:
    """Check that AlphaFold weights exist in *params_dir*; download if missing.

    Args:
        params_dir: Directory that should contain the weight ``.npz`` files.

    Returns:
        Resolved absolute path to the params directory.
    """
    params_dir = os.path.abspath(os.path.expanduser(params_dir))

    # The extracted tar contains *.npz weight files — presence of any is sufficient
    has_weights = any(Path(params_dir).glob("*.npz"))

    if has_weights:
        logger.info(f"AlphaFold weights found in {params_dir}")
    else:
        logger.info(f"No AlphaFold weights found in {params_dir}, downloading …")
        download_alphafold_weights(params_dir)
        # Verify after download
        if not any(Path(params_dir).glob("*.npz")):
            logger.error(f"Download finished but no .npz files found in {params_dir}. "
                         "Check the directory contents.")
            sys.exit(1)
        logger.info(f"AlphaFold weights ready in {params_dir}")

    return params_dir


def download_alphafold_weights(out_dir: str) -> None:
    """Download AlphaFold params tarball and extract into out_dir."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tar_path = out_dir / "alphafold_params.tar"

    # Download
    logger.info(f"Downloading AlphaFold weights to {tar_path} ...")
    urllib.request.urlretrieve(PARAMS_URL, str(tar_path))

    # Extract
    logger.info(f"Extracting to {out_dir} ...")
    with tarfile.open(tar_path) as tar:
        tar.extractall(path=str(out_dir))

    # Clean up tarball
    tar_path.unlink()
    logger.info("Done preparing weights.")


def main():
    parser = argparse.ArgumentParser(description="Download AlphaFold weights.")
    parser.add_argument("--param_dir", required=False, help="Output directory for weights.", default=None)
    args = parser.parse_args()

    if args.param_dir is None:
        param_dir = Path().home() / ".bindcraft" / "weights"
    else:
        param_dir = Path(args.param_dir)
    ensure_af_params_available(param_dir)


if __name__ == "__main__":
    main()
