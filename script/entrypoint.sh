#!/bin/bash
set -euo pipefail

PROTO_FILES=(`find ./protos -name *.proto`)

mkdir temp
for proto_file in "${PROTO_FILES[@]}"; do
  ./filter.py ${proto_file} temp/`basename ${proto_file}`
done

# this is required because of the wildcard expansion. Passing protos/*.proto in CMD gets escaped -_-. So instead leaving
# off the [FILES] will put protos/*.proto in from here which will expand correctly.
args=("$@")
if [ "${#args[@]}" -lt 2 ]; then args+=(temp/*.proto); fi

exec protoc -Itemp --doc_out=/out "${args[@]}"
