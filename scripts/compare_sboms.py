import json
import os
import sys

VARIANTS = ['base', 'glibc', 'debug']

def get_sbom_files(directory, prefix):
    sbom_files = []
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return sbom_files
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith(prefix) and file.endswith('.json'):
                sbom_files.append(os.path.join(root, file))
    return sbom_files

def parse_sboms(paths):
    # apko emits SPDX SBOMs: package entries live under 'packages' with
    # 'versionInfo'. The index SBOM has no package list and contributes
    # nothing here; per-arch SBOMs carry the actual packages.
    packages = {}
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, 'r') as f:
            try:
                sbom = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from {path}")
                continue
        for package in sbom.get('packages') or []:
            name = package.get('name', 'unknown')
            packages[name] = package.get('versionInfo', 'unknown')
    return packages

def compare_packages(old_pkgs, new_pkgs):
    if not old_pkgs:
        print("No previous SBOM found. Assuming changes.")
        return True
    return old_pkgs != new_pkgs

def main():
    changed = False
    for variant in VARIANTS:
        curr_files = get_sbom_files('sbom-output', f'{variant}_')
        prev_files = get_sbom_files('previous-sbom', f'{variant}_')
        if variant == 'base' and not prev_files:
            # backward compatibility with the old 'main_' prefix
            prev_files = get_sbom_files('previous-sbom', 'main_')

        print(f"Previous {variant} SBOMs: {prev_files}")
        print(f"Current {variant} SBOMs: {curr_files}")

        # Fail closed: a missing or empty current SBOM is a build defect,
        # not "no change".
        if not curr_files:
            print(f"ERROR: no current SBOM files found for {variant}.")
            sys.exit(1)
        curr_pkgs = parse_sboms(curr_files)
        if not curr_pkgs:
            print(f"ERROR: current {variant} SBOMs contain no packages.")
            sys.exit(1)

        prev_pkgs = parse_sboms(prev_files)
        if compare_packages(prev_pkgs, curr_pkgs):
            print(f"{variant} SBOM has changes.")
            changed = True

    if changed:
        print("Changes detected in SBOMs.")
    else:
        print("No changes detected in SBOMs.")
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write(f"sbom-changes={'true' if changed else 'false'}\n")

if __name__ == "__main__":
    main()
