from collections import defaultdict
from unittest import TestCase

from pylicenses import PyPiProvider, CondaProvider, CondaChannelProvider, PyLicenses, PipProvider


class PyLicensesTests(TestCase):
    def test_pypi_get_packages_info(self):
        packages = {
            'requests': {
                'name': 'requests'
            }
        }
        prov = PyPiProvider()
        infos = prov.get_packages_info(packages)
        for pkg, info in infos.items():
            self.assertIn('author_email', info)
            self.assertIn('author', info)
            self.assertIn('license_text', info)
            self.assertIn('license_trace', info)
            self.assertEqual(info['license_trace'], 'pypi')

    def test_conda(self):
        prov = CondaProvider()
        packages = {
            'requests': {
                'name': 'requests'
            },
            'wheel': {
                'name': 'wheel'
            }
        }
        subset = list(packages.keys())
        infos = prov.get_packages_info(packages, subset=subset)
        for pkg in subset:
            info = infos[pkg]
            self.assertIn('license', info)
            self.assertIn('license_trace', info)
            self.assertIn('license_text', info)
            self.assertEqual(info['license_trace'], 'conda local package')

    def test_conda_channel(self):
        prov = CondaChannelProvider()
        packages = {
            'requests': {
                'name': 'requests',
                'build': 'py37_0',
            }
        }
        infos = prov.get_packages_info(packages)
        for pkg, info in infos.items():
            self.assertIn('license', info)
            self.assertEqual(info['license_trace'], 'conda channel repository')

    def test_pip(self):
        packages = defaultdict(dict)
        packages.update({
            'requests': {
                'name': 'requests',
            }
        })
        prov = PipProvider()
        infos = prov.get_packages_info(packages, subset='requests')
        info = infos['requests']
        self.assertIn('license', info)
        self.assertIn('license_text', info)
        self.assertEqual(info['license_trace'], 'pip local package')
        
    def test_pylicenses_full(self):
        lic = PyLicenses()
        lic.discover(subset=['requests'])
        info = lic.packages['requests']
        self.assertIn('license', info)
        self.assertIn('license_trace', info)
        self.assertEqual(info['license_trace'], 'conda local package')
        self.assertIn('license_text', info)

    def test_discover_package_dependencies(self):
        lic = PyLicenses()
        lic.discover()
        lic.discover_package_dependencies()
        packages = lic.packages
        for pkg, data in packages.items():
            self.assertIn('required_by', data)


