#!/usr/bin/env bash
# Regenerate all M1 documents with YOUR numbers/names:
#   GROUP_NUM=7 GROUP_ID=07 M1_NAME="Ali (2021xxxx)" M2_NAME="..." M3_NAME="..." ./make_docs.sh
# needs: pip install reportlab matplotlib openpyxl pillow
set -euo pipefail
cd "$(dirname "$0")"
python3 build_m1_a.py && python3 build_m1_b.py
echo "M1 documents written to docs/M1/"
