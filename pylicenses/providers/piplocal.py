import email

import os
from glob import glob

import sys
from pip._internal.utils.misc import get_installed_distributions

from pylicenses.providers import PackageProvider


class PipProvider(PackageProvider):
    def get_package_metadata(self, pkg):
        # adopted from https://stackoverflow.com/a/19086260
        # PKG-INFO is in email format. since Metadata 2.1 format description may
        #          be in the body or header.
        # see https://www.python.org/dev/peps/pep-0314/#including-metadata-in-packages
        #     https://packaging.python.org/specifications/core-metadata/
        data = None
        for metakind in ('PKG-INFO', 'METADATA'):
            try:
                pkginfo = pkg.get_metadata(metakind)
            except:
                pass
            else:
                message = email.message_from_string(pkginfo)
                data = {
                    k.replace('-', '_').lower(): v for
                    k, v in dict(message).items()
                }
                # description may be in the body since Metadata 2.1
                if data['metadata_version'] != '1.2':
                    data['description'] = message.get_payload()
                break
        return data

    def find_license_files(self):
        files = []
        for path in sys.path:
            if not 'site-packages' in path:
                continue
            for fnkind in ('COPYING*', 'LICENSE*'):
                pattern = os.path.join(path, '**', fnkind)
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
            # installed package with license
            # e.g. /usr/local/anaconda3/lib/python3.6/site-packages/tornado-5.1.1.dist-info/LICENSE.txt
            dist_name = parts[-2].replace('.dist-info', '')
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
                'license_trace': 'pip local package',
                'license_source': license_file,
            }
            licenses[dist_name] = license
            licenses[name] = license
        return licenses

    def get_packages_info(self, packages, subset=None):
        pkgsdata = get_installed_distributions()
        for pkg in pkgsdata:
            pkgmeta = self.get_package_metadata(pkg)
            name = pkgmeta['name']
            distname = '{}-{}'.format(pkgmeta['name'], pkgmeta['version'])
            packages[name].update(pkgmeta)
            packages[distname].update(pkgmeta)
        # get licenses
        licenses = self.get_licenses()
        # combine packages + licenses
        for pkg, data in packages.items():
            # filter on requested packages
            if subset and not pkg in subset:
                continue
            license = licenses.get(pkg)
            data.update(license) if license else None
        return packages
