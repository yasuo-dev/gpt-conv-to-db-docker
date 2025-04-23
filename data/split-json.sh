#!/bin/bash

# ファイル引数の確認
if [ -z "$1" ]; then
  echo "Usage: $0 <json_file>"
  exit 1
fi

INPUT_FILE="$1"

# 分割処理（カレントディレクトリに出力）
jq -c '.[]' "$INPUT_FILE" | nl -n rz -w 4 -s '' | while read -r line; do
  num=$(echo "$line" | cut -c1-4)
  content=$(echo "$line" | cut -c5-)
  echo "$content" > "item_${num}.json"
done

echo "✅ Done: JSON objects saved as item_XXXX.json"

