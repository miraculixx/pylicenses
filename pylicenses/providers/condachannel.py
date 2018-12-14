import json

import sh

from pylicenses.providers import PackageProvider


class CondaChannelProvider(PackageProvider):
    """
    Use conda search to get package license type
    """

    def get_packages_info(self, packages):
        infos = {}
        for pkg, data in packages.items():
            if data.get('version', '--no-version--') in pkg:
                # ignore build names as package names, conda search does not like
                continue
            try:
                condadata = json.loads(str(sh.conda('search', pkg, '--info', '--json')))
            except Exception as e:
                condadata = {}
            else:
                license = {}
                for condainfo in condadata.get(pkg, []):
                    if condainfo.get('build') != data.get('build'):
                        # mismatch of build data
                        continue
                    license = {
                        'license': condainfo.get('license'),
                        'license_trace': 'conda channel repository',
                        'license_source': 'conda search {} --info'.format(pkg),
                    }
                infos[pkg] = license
        return infos
