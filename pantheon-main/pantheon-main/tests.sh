#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

python -m pytest --cov --cov-report=xml
git fetch origin main:refs/remotes/origin/main
diff-cover --version
diff-cover coverage.xml --include-untracked --exclude test_data/* --fail-under=75
