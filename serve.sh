#!/usr/bin/env sh
set -eu

port="${1:-8765}"

case "$port" in
	*[!0-9]* | "")
		echo "Usage: $0 [port]" >&2
		exit 2
		;;
esac

script_dir=$(CDPATH= cd "$(dirname "$0")" && pwd)

echo "Pi study: http://127.0.0.1:${port}/index.html"
exec python3 -m http.server "$port" --bind 127.0.0.1 --directory "$script_dir"
