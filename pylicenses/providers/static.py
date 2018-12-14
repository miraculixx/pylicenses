import requests

from pylicenses.providers import PackageProvider


class StaticProvider(PackageProvider):
    """
    Map packages to static file or url references
    """
    LICENSE_MAP = {
        'blas': 'https://raw.githubusercontent.com/xianyi/OpenBLAS/develop/LICENSE',
        'intel-openmp': 'https://software.intel.com/en-us/license/intel-simplified-software-license',
        'yaml': 'https://raw.githubusercontent.com/yaml/pyyaml/master/LICENSE',
    }

    def get_license(self, package):
        license = {}
        if package in self.LICENSE_MAP:
            license_source = self.LICENSE_MAP[package]
            resp = requests.get(license_source)
            text = resp.content
            license = {
                'license_text': text,
                'license_trace': 'static license link',
                'license_source': license_source,
            }
        return license

    def get_packages_info(self, packages):
        infos = {}
        for pkg, data in packages.items():
            license = self.get_license(pkg)
            infos[pkg] = license
        return infos