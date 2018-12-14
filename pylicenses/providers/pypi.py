import base64
import json
import warnings

import requests

from pylicenses.providers import PackageProvider


class PyPiProvider(PackageProvider):
    """
    Use pypi.org and github to retrieve package data (pypi) and license content (github)
    """
    init_kwargs = ['github_auth']

    def __init__(self, github_auth=None):
        self.github_auth = github_auth
        self._github_licenses = {}  # cache for queried github licenses (repo or verbatim)
        self._pypi_data = {}  # cache for queried pypi data

    def get_github_repo_license(self, ref):
        if ref in self._github_licenses:
            return self._github_licenses[ref]
        url = 'https://api.github.com/repos/{ref}/license'.format(ref=ref)
        resp = requests.get(url, auth=self.github_auth)
        error_text = lambda resp: {'error': 'github /repos/{}/license returned {}'.format(ref, resp.content)}
        try:
            license = json.loads(resp.content)
            license['license_text'] = base64.b64decode(license['content'])
        except:
            license = error_text(resp)
            warnings.warn(str(license))
        else:
            if resp.status_code != 200:
                license['error'] = error_text(resp)
        license = {
            k: v for k, v in license.items() if k in ('license', 'license_text', 'spdx_id', 'error')
        }
        if 'license' in license:
            license['license_spdx_id'] = license['license'].get('spdx_id')
            license['license'] = license['license']['name']
        if 'error' in license:
            license['github_error'] = license['error']
        license['license_trace'] = 'github-repository-license'
        license['license_source'] = url
        self._github_licenses[ref] = license
        return license

    def _run_github_license_query(self, name):
        if name in self._github_licenses:
            return self._github_licenses[name]
        url = 'https://api.github.com/licenses/{name}'.format(name=name)
        resp = requests.get(url, auth=self.github_auth)
        error_text = lambda resp: {'error': 'github /licenses/{} returned {}'.format(name, resp.content)}
        try:
            license = json.loads(resp.content)
        except:
            license = error_text(resp)
            warnings.warn(str(license))
        else:
            if resp.status_code != 200:
                license['error'] = error_text(resp)
            license['license_trace'] = 'github-license-query'
            license['license_source'] = url
        KEY_MAP = {
            'body': 'license_text',
            'html_url': 'license_url',
            'error': 'github_error'
        }
        license = {
            KEY_MAP.get(k): v for k, v in license.items() if k in KEY_MAP
        }
        self._github_licenses[name] = license
        return self._github_licenses[name]

    def get_github_license(self, name, family):
        license = {}
        for ref in (name, family):
            NAME_MAP = {
                'lgpl': 'lgpl-3.0',
                'lgpl3': 'lgpl-3.0',
                'lgpl3.0': 'lgpl-3.0',
                'lgpl2.1': 'lgpl-2.1',
                'gpl': 'gpl-2.0',
                'gpl2': 'gpl-2.0',
                'gpl3': 'gpl-3.0',
                'gnugpl3withgccruntimelibrary': 'gpl-3.0',
                'gpl3withruntimeexception': 'gpl-3.0',
                'bsd': 'bsd-2-clause',
                'bsdstyle': 'bsd-2-clause',
                'bsd2': 'bsd-2-clause',
                'bsd2.0': 'bsd-2-clause',
                'bsd3': 'bsd-3-clause',
                'bsd3.0': 'bsd-3-clause',
                'bsd3clause': 'bsd-3-clause',
                'newbsd': 'bsd-3-clause',
                'apache2.0': 'apache-2.0',
            }
            ref = ref.lower().strip()  # remove leading and trailing blanks
            ref = ref.replace('-', '').replace(' ', '')  # remove any blanks, dashes
            ref = ref.split('/')[0]  # split on something like GPL/MIT, take just the first
            ref = ref.replace('license', '')  # reduce something like "mit license" to "mit"
            ref = NAME_MAP.get(ref) or ref  # map to the actual name on github
            if ref:
                license.update(self._run_github_license_query(ref))
                if license.get('license_text'):
                    break
        return license

    def get_pypi_info(self, package):
        if package in self._pypi_data:
            return self._pypi_data[package]
        url = 'https://pypi.org/pypi/{package}/json'.format(package=package)
        resp = requests.get(url)
        try:
            info = json.loads(resp.content).get('info')
        except:
            info = {}
        else:
            info = {
                k: v for k, v in info.items() if k in ('author', 'home_page', 'bugtrack_url', 'license',
                                                       'author_email', 'project_urls', 'license_family',
                                                       'summary')
            }
            info['license_trace'] = 'pypi'
            info['license_source'] = url
        self._pypi_data[package] = info
        return info

    def get_packages_info(self, packages):
        """
        get all information from pypi + github available for the packages

        :param packages: (dict) mapping name => information
        :return:
        """
        infos = {}
        for data in packages.values():
            # query from pypi
            pkg = data['name']
            infos[pkg] = data
            infos[pkg].update(self.get_pypi_info(pkg))
            homepage = infos[pkg].get('home_page')
            project_urls = infos[pkg].get('project_urls') or {}
            project_homepage = project_urls.get('Homepage')
            # query from github if we know github repo/name
            found = False
            for hp in (homepage, project_homepage):
                if hp and 'github' in hp:
                    # strip trailing slash, get repo ref as user/repo
                    github_ref = '/'.join(hp.strip('/').split('/')[-2:])
                    # query repo license, if available update info
                    repo_license = self.get_github_repo_license(github_ref)
                    if repo_license and 'license_text' in repo_license:
                        infos[pkg].update(repo_license)
                        found = True
                        break
            # last fall back, get verbatim license text from github
            if not found:
                license_family = infos[pkg].get('license_family', '')
                license_name = infos[pkg].get('license', '')
                if license_name or license_family:
                    license = self.get_github_license(license_name, license_family)
                    infos[pkg].update(license)
        return infos
