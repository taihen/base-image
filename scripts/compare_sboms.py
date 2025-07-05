import json
import os
import sys

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
    packages = {}
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, 'r') as f:
            try:
                sbom = json.load(f)
                # Support both 'components' (new) and 'packages' (old)
                component_list = sbom.get('components')
                if component_list is None:
                    component_list = sbom.get('packages')
                
                if component_list:
                    for component in component_list:
                        name = component.get('name', 'unknown')
                        # Support both 'version' (new) and 'versionInfo' (old)
                        version = component.get('version')
                        if version is None:
                            version = component.get('versionInfo', 'unknown')
                        packages[name] = version
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from {path}")
    return packages

def compare_packages(old_pkgs, new_pkgs):
    if not old_pkgs and not new_pkgs:
        return False
    if not old_pkgs and new_pkgs:
        print("No previous SBOM found. Assuming changes.")
        return True
    return old_pkgs != new_pkgs

def main():
    prev_main_files = get_sbom_files('previous-sbom', 'main_')
    prev_debug_files = get_sbom_files('previous-sbom', 'debug_')
    curr_main_files = get_sbom_files('sbom-output', 'main_')
    curr_debug_files = get_sbom_files('sbom-output', 'debug_')
    print(f"Previous main SBOMs: {prev_main_files}")
    print(f"Previous debug SBOMs: {prev_debug_files}")
    print(f"Current main SBOMs: {curr_main_files}")
    print(f"Current debug SBOMs: {curr_debug_files}")
    prev_main_pkgs = parse_sboms(prev_main_files)
    curr_main_pkgs = parse_sboms(curr_main_files)
    prev_debug_pkgs = parse_sboms(prev_debug_files)
    curr_debug_pkgs = parse_sboms(curr_debug_files)
    main_changed = compare_packages(prev_main_pkgs, curr_main_pkgs)
    if main_changed:
        print("Main SBOM has changes.")
    debug_changed = compare_packages(prev_debug_pkgs, curr_debug_pkgs)
    if debug_changed:
        print("Debug SBOM has changes.")
    if main_changed or debug_changed:
        print("Changes detected in SBOMs.")
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write('sbom-changes=true\n')
    else:
        print("No changes detected in SBOMs.")
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write('sbom-changes=false\n')

if __name__ == "__main__":
    main()
