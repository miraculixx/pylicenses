import argparse

from tabulate import tabulate

from pylicenses import PyLicenses

args = argparse.ArgumentParser()
args.add_argument('--github',
                  help='specify github user,password')
args.add_argument('--stats',
                  help='print statistics')

def print_license_stats(lic):
    counts, by_license = lic.get_license_stats()
    print("License counts by type\n")
    print(tabulate(counts.items(), headers=('License family', 'Count')))
    print("\n\nPackages by license\n")
    print(tabulate(by_license.items(), headers=('Licency family', 'Packages')))

def print_missing(lic):
    rows = []
    columns = 'name', 'version', 'license', 'url'
    missing = lic.missing_licenses()
    if missing:
        print(missing)
        for pkg, data in missing.items():
            values = [data.get(k) for k in columns]
            rows.append(values)
        print("\n\n**WARNING** Packages with missing license texts\n")
        print(tabulate(rows, headers=columns))
    else:
        print("\n**SUCCESS** Good news. There are no packages without license texts\n")


def print_catalog(lic):
    primary_rows = []
    secondary_rows = []
    columns = 'name', 'author', 'license', 'url'
    for pkg, data in lic.packages.items():
        if pkg != data.get('name'):
            # ignore versioned entries
            continue
        values = [data.get(k) for k in columns]
        if data.get('is_primary'):
            primary_rows.append(values)
        else:
            secondary_rows.append(values)
    print("Packages directly required:\n")
    print(tabulate(primary_rows, headers=columns))
    print("\nPackages pulled in through other requirements:\n")
    print(tabulate(secondary_rows, headers=columns))
    print_missing(lic)

def save_license_trail(lic):
    reportfn = 'THIRDPARTY-LICENSES'
    with open(reportfn, 'w') as fout:
        fout.write('\n-- ** THIRDPARTY LICENSES **\n')
        fout.write('-- report produced by pylicenses [use at your own risk]')
        fout.write('--')
        for pkg, data in lic.packages.items():
            if pkg != data.get('name'):
                continue
            license_text = data.get('license_text')
            if isinstance(license_text, bytes):
                license_text = license_text.decode('utf8')
            fout.write('--\n')
            fout.write('Package: {}\n'.format(pkg))
            fout.write('Version: {}\n'.format(data.get('version', 'latest')))
            fout.write('Author: {}\n'.format(data.get('author')))
            fout.write('License: {}\n'.format(data.get('license')))
            fout.write('Home-page: {}\n'.format(data.get('home_page')))
            fout.write('Source: {}\n'.format(data.get('url')))
            fout.write('Licence Text:\n{}\n'.format(license_text))
        fout.write('\n-- ** end of report **\n')
    print("**SUCCESS** The full license report is available in {}\n".format(reportfn))

if __name__ == '__main__':
    # parse args
    options = args.parse_args()
    github_auth = None
    if options.github:
        github_auth = options.github.split(',')
    # run
    lic = PyLicenses(github_auth=github_auth)
    lic.discover()
    if options.stats:
        print_license_stats(lic)
        print_missing(lic)
    else:
        lic.discover_package_dependencies()
        print_catalog(lic)
    save_license_trail(lic)
