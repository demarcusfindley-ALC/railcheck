#!/bin/sh
set -e
cd "$(dirname "$0")"
export PYTHONPATH=src
python3 -m unittest tests/test_fixtures.py
python3 -m railcheck check --offline --fixtures fixtures --out examples
