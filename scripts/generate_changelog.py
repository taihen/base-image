import json
import os
import sys
import requests

def get_latest_release_sboms(repo, token):
    """Download and parse SBOMs from the latest GitHub release."""
    headers = {'Authorization': f'token {token}'}
    releases_url = f"https://api.github.com/repos/{repo}/releases/latest"
    response = requests.get(releases_url, headers=headers)
    if response.status_code == 404:
        print("No previous release found.")
        return {}, {}, {}
    release = response.json()
    print(f"Found previous release: {release['tag_name']}")
    base_packages = {}
    glibc_packages = {}
    debug_packages = {}
    for asset in release.get('assets', []):
        if asset['name'].endswith('.json') and 'sbom' in asset['name'].lower():
            download_url = asset['browser_download_url']
            asset_response = requests.get(download_url, headers=headers)
            try:
                sbom = json.loads(asset_response.content)
                packages = parse_cyclonedx_sbom(sbom)
                if asset['name'].startswith('debug_'):
                    debug_packages.update(packages)
                elif asset['name'].startswith('base_') or asset['name'].startswith('main_'):
                    base_packages.update(packages)
                elif asset['name'].startswith('glibc_'):
                    glibc_packages.update(packages)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from asset {asset['name']}")
                continue
    return base_packages, glibc_packages, debug_packages

def parse_cyclonedx_sbom(sbom):
    """Extract package information from a single CycloneDX SBOM, supporting both old and new formats."""
    packages = {}
    if not sbom:
        return packages

    component_list = sbom.get('components', [])
    if not component_list:
        # Handle the older SPDX format where packages are in the 'packages' list
        component_list = sbom.get('packages', [])

    for component in component_list:
        # To be considered a package for the changelog, the component must have a PURL
        # indicating it was installed from the Wolfi APK repository.
        is_wolfi_package = False
        for ref in component.get('externalRefs', []):
            if ref.get('referenceCategory') == 'PACKAGE-MANAGER' and ref.get('referenceLocator', '').startswith('pkg:apk/wolfi/'):
                is_wolfi_package = True
                break
        
        if not is_wolfi_package:
            continue

        name = component.get('name', 'unknown')
        version = component.get('version', component.get('versionInfo', 'unknown'))

        license_str = 'unknown'
        if 'licenses' in component and component.get('licenses'):
            license_info = component['licenses'][0].get('license', {})
            license_str = license_info.get('name', 'unknown')
        elif 'licenseDeclared' in component:
            license_str = component['licenseDeclared']

        packages[name] = {'version': version, 'license': license_str}
    return packages

def compare_sboms(old_packages, new_packages):
    """Compare two sets of packages and return differences."""
    if not old_packages:
        return {
            'added': [(name, info['version'], info['license']) for name, info in new_packages.items()],
            'removed': [],
            'updated': [],
            'total_packages': len(new_packages),
            'is_first_release': True
        }
    added = []
    removed = []
    updated = []
    for name, info in new_packages.items():
        if name not in old_packages:
            added.append((name, info['version'], info['license']))
        elif old_packages[name]['version'] != info['version']:
            updated.append((name, old_packages[name]['version'], info['version']))
    for name, info in old_packages.items():
        if name not in new_packages:
            removed.append((name, info['version']))
    return {
        'added': added,
        'removed': removed,
        'updated': updated,
        'total_packages': len(new_packages),
        'is_first_release': False
    }

def generate_changelog(base_changes, glibc_changes, debug_changes):
    """Generate markdown changelog."""
    changelog = []
    if base_changes.get('is_first_release', False):
        changelog.append("### 🎉 Initial Release\n")
        changelog.append(f"- **Base Image**: {base_changes['total_packages']} packages")
        changelog.append(f"- **glibc Image**: {glibc_changes.get('total_packages', 0)} packages")
        changelog.append(f"- **Debug Image**: {debug_changes.get('total_packages', 0)} packages")
        return '\n'.join(changelog)
    has_base_changes = bool(base_changes['added'] or base_changes['removed'] or base_changes['updated'])
    has_glibc_changes = bool(glibc_changes['added'] or glibc_changes['removed'] or glibc_changes['updated'])
    has_debug_changes = bool(debug_changes['added'] or debug_changes['removed'] or debug_changes['updated'])
    if not has_base_changes and not has_glibc_changes and not has_debug_changes:
        changelog.append("### 📦 Package Changes\n")
        changelog.append("ℹ️ **No package changes detected** (metadata or rebuild only)")
        return '\n'.join(changelog)
    changelog.append("### 📦 Package Changes\n")
    
    if has_base_changes:
        changelog.append("#### Base Image (musl libc)\n")
        if base_changes['updated']:
            changelog.append(f"**🔄 Updated ({len(base_changes['updated'])} packages)**")
            for name, old_ver, new_ver in sorted(base_changes['updated']):
                changelog.append(f"- `{name}`: {old_ver} → {new_ver}")
        if base_changes['added']:
            changelog.append(f"**➕ Added ({len(base_changes['added'])} packages)**")
            for name, version, license in sorted(base_changes['added']):
                changelog.append(f"- `{name}` v{version} (License: {license})")
        if base_changes['removed']:
            changelog.append(f"**➖ Removed ({len(base_changes['removed'])} packages)**")
            for name, version in sorted(base_changes['removed']):
                changelog.append(f"- `{name}` v{version}")
    else:
        changelog.append("#### Base Image (musl libc)\nNo changes\n")
    
    if has_glibc_changes:
        changelog.append("\n#### glibc Image\n")
        if glibc_changes['updated']:
            changelog.append(f"**🔄 Updated ({len(glibc_changes['updated'])} packages)**")
            for name, old_ver, new_ver in sorted(glibc_changes['updated']):
                changelog.append(f"- `{name}`: {old_ver} → {new_ver}")
        if glibc_changes['added']:
            changelog.append(f"**➕ Added ({len(glibc_changes['added'])} packages)**")
            for name, version, license in sorted(glibc_changes['added']):
                changelog.append(f"- `{name}` v{version} (License: {license})")
        if glibc_changes['removed']:
            changelog.append(f"**➖ Removed ({len(glibc_changes['removed'])} packages)**")
            for name, version in sorted(glibc_changes['removed']):
                changelog.append(f"- `{name}` v{version}")
    else:
        changelog.append("\n#### glibc Image\nNo changes\n")
        
    if has_debug_changes:
        changelog.append("\n#### Debug Image\n")
        if debug_changes['updated']:
            changelog.append(f"**🔄 Updated ({len(debug_changes['updated'])} packages)**")
            for name, old_ver, new_ver in sorted(debug_changes['updated']):
                changelog.append(f"- `{name}`: {old_ver} → {new_ver}")
        if debug_changes['added']:
            changelog.append(f"**➕ Added ({len(debug_changes['added'])} packages)**")
            for name, version, license in sorted(debug_changes['added']):
                changelog.append(f"- `{name}` v{version} (License: {license})")
        if debug_changes['removed']:
            changelog.append(f"**➖ Removed ({len(debug_changes['removed'])} packages)**")
            for name, version in sorted(debug_changes['removed']):
                changelog.append(f"- `{name}` v{version}")
    else:
        changelog.append("\n#### Debug Image\nNo changes\n")
    changelog.append("\n### 📊 Summary")
    changelog.append(f"- **Base**: {base_changes['total_packages']} total packages")
    changelog.append(f"- **glibc**: {glibc_changes.get('total_packages', 0)} total packages")
    changelog.append(f"- **Debug**: {debug_changes.get('total_packages', 0)} total packages")
    return '\n'.join(changelog)

def main():
    repo = os.environ.get('GITHUB_REPOSITORY')
    token = os.environ.get('GH_TOKEN')
    if not repo or not token:
        print("Error: GITHUB_REPOSITORY and GH_TOKEN env vars are required.")
        sys.exit(1)

    # Load current SBOMs
    current_base_packages = {}
    current_glibc_packages = {}
    current_debug_packages = {}
    for root, _, files in os.walk('sbom-output'):
        for file in files:
            if file.endswith('.json'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    try:
                        sbom_content = json.load(f)
                        # Parse the SBOM content to extract packages
                        packages = parse_cyclonedx_sbom(sbom_content)
                        if file.startswith('debug_'):
                            current_debug_packages.update(packages)
                        elif file.startswith('base_') or file.startswith('main_'):
                            current_base_packages.update(packages)
                        elif file.startswith('glibc_'):
                            current_glibc_packages.update(packages)
                    except json.JSONDecodeError:
                        print(f"Warning: Could not decode JSON from {filepath}")
                        continue
    if not current_base_packages:
        print("Error: Could not find any current base SBOMs.")
        sys.exit(1)

    # Get previous release SBOMs
    prev_base_packages, prev_glibc_packages, prev_debug_packages = get_latest_release_sboms(repo, token)

    # Compare SBOMs
    base_changes = compare_sboms(prev_base_packages, current_base_packages)
    glibc_changes = compare_sboms(prev_glibc_packages, current_glibc_packages)
    debug_changes = compare_sboms(prev_debug_packages, current_debug_packages)

    # Generate changelog
    changelog = generate_changelog(base_changes, glibc_changes, debug_changes)
    with open('sbom-changelog.md', 'w') as f:
        f.write(changelog)
    changes_data = {'base': base_changes, 'glibc': glibc_changes, 'debug': debug_changes}
    with open('sbom-changes.json', 'w') as f:
        json.dump(changes_data, f, indent=2)
    print("SBOM comparison completed successfully.")
    print("\nChangelog Preview:\n" + "="*50)
    print(changelog)
    print("="*50)

if __name__ == '__main__':
    main()
