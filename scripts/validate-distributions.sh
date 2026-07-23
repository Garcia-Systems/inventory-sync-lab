#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

rm -rf build dist .release-venv
expected_version=$(PYTHONPATH=src python -c 'import inventory_sim; print(inventory_sim.__version__)')
python -m build
python -m twine check dist/*

sdist=(dist/*.tar.gz)
wheel=(dist/*.whl)
test "${#sdist[@]}" -eq 1
test "${#wheel[@]}" -eq 1

# Confirm the source archive carries the material needed to inspect, test, and
# rebuild the project, without relying on the current checkout.
tar -tzf "${sdist[0]}" > /tmp/inventory-sync-lab-sdist-files.txt
for path in pyproject.toml README.md LICENSE CONTRIBUTING.md src/inventory_sim tests book docs diagrams; do
  grep -Eq "^[^/]+/${path}(/|$)" /tmp/inventory-sync-lab-sdist-files.txt
done

python -m venv .release-venv
release_python=.release-venv/bin/python
release_cli=.release-venv/bin/inventory-sim
"$release_python" -m pip install --disable-pip-version-check "${wheel[0]}"

"$release_cli" doctor | tee /tmp/inventory-sync-lab-doctor.txt
grep -F "version ${expected_version}" /tmp/inventory-sync-lab-doctor.txt
"$release_cli" --help >/dev/null
"$release_cli" inventory --on-hand 10 --reserved 3 >/dev/null
"$release_cli" laboratory >/dev/null
"$release_python" -c 'import importlib.metadata as m, inventory_sim; assert m.version("inventory-sync-lab") == inventory_sim.__version__'

# Installing the sdist exercises an isolated rebuild and confirms that it is a
# usable distribution, not merely a complete-looking archive.
"$release_python" -m pip uninstall --yes inventory-sync-lab >/dev/null
"$release_python" -m pip install --disable-pip-version-check "${sdist[0]}"
"$release_cli" doctor >/dev/null
