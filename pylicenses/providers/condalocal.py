import json

import os
import sh

from glob import glob

from pylicenses.providers import PackageProvider


class CondaProvider(PackageProvider):
    """
    Use the conda and pip environment to find local LICENSE files included in packages
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._conda_prefix_path = None

    @property
    def prefix_path(self):
        if not self._conda_prefix_path:
            info = json.loads(str(sh.conda('info', '--json')))
            self._conda_prefix_path = os.path.join(info['sys.prefix'], 'pkgs')
        return self._conda_prefix_path

    def get_packages_list(self):
        """
        return dict of packages indexed by name and dist_name
        """
        # get all packages
        packages = json.loads(str(sh.conda('list', '--json')))
        idx_by_name = {p['dist_name']: p for p in packages}
        idx_by_distname = {p['name']: p for p in packages}
        packages = dict(**idx_by_name, **idx_by_distname)
        return packages

    def get_packages_info(self, packages, subset=None):
        # get all locally available packages
        packages.update(self.get_packages_list())
        # build info from conda
        names = [data['name'] for data in packages.values()]
        infos = json.loads(str(sh.conda('info', '--json', names)))
        infos_by_distname = {}
        for name, builds in infos.items():
            for build in builds:
                dist_name = '{name}-{version}.{build}'.format(**build)
                name = build['name']
                infos_by_distname[dist_name] = build
                infos_by_distname[name] = build
        # get licenses
        licenses = self.get_licenses()
        # combine packages, infos, licenses
        for pkg, data in packages.items():
            # filter on requested packages
            if subset and not pkg in subset:
                continue
            license = licenses.get(pkg)
            data.update(license) if license else None
            info = infos_by_distname.get(pkg)
            data.update(info) if info else None
        return packages

    def find_license_files(self):
        files = []
        for fnkind in ('COPYING*', 'LICENSE*'):
            pattern = os.path.join(self.prefix_path, '**', fnkind)
            files.extend(glob(pattern, recursive=True))
        return files

    def get_licenses(self):
        """
        get dict of licenses indexed by package name
        """
        licenses = {}
        files = self.find_license_files()
        for path in files:
            parts = path.split('/')
            # conda package source
            # e.g. '/usr/local/anaconda3/pkgs/mkl-service-1.1.2-py36h17a0993_4/info/LICENSE.txt',
            pkg_idx = parts.index('pkgs')
            dist_name = parts[pkg_idx + 1]
            name_parts = dist_name.split('-')
            # name can contain dash. reverse the string, take off build and version, reverse again
            # the remaining parts are the package name. if there is more than one part there is a dash
            if len(name_parts) > 2:
                name = '-'.join(name_parts[::-1][2:][::-1])
            else:
                name = name_parts[0]
            license_file = path
            with open(license_file, 'r') as fin:
                text = fin.read()
            license = {
                'dist_name': dist_name,
                'name': name,
                'license_text': text,
                'license_trace': 'conda local package',
                'license_source': license_file,
            }
            licenses[dist_name] = license
            licenses[name] = license
        return licenses
