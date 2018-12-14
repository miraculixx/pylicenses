from collections import defaultdict, Counter

from pylicenses.providers.condachannel import CondaChannelProvider
from pylicenses.providers.condalocal import CondaProvider
from pylicenses.providers.piplocal import PipProvider
from pylicenses.providers.pypi import PyPiProvider
from pylicenses.providers.static import StaticProvider

version = '0.1'


class PyLicenses(object):
    """
    Extensible dependencies license finder
    """
    PROVIDERS = {
        'primary': [PipProvider, CondaProvider],
        'fallback': [StaticProvider,
                     CondaChannelProvider,
                     PyPiProvider,
        ]
    }

    def __init__(self, github_auth=None):
        """

        :param github_auth: the tuple (user,password), defaults to None
        """
        # a pipeline of providers
        # TODO unify all providers into one pipeline and use an n-pass strategy to execute
        #      until no progress is made (progress = reduce #missing packages)
        self.github_auth = tuple(github_auth) if github_auth else None
        self._packages = defaultdict(dict)
        self.providers = defaultdict(list)
        # initialize providers, passing information
        for kind, provs in PyLicenses.PROVIDERS.items():
            for provCls in provs:
                kwargs = {
                    kwarg: getattr(self, kwarg) for kwarg in provCls.init_kwargs
                }
                self.providers[kind].append(provCls(**kwargs))

    @property
    def packages(self):
        return self._packages

    def discover(self, subset=None):
        """
        return dict of all packages including license files
        """
        # get packages and licenses dicts from primary providers
        packages = self._packages
        for prov in self.providers['primary']:
            prov.get_packages_info(packages, subset=subset)
        # find those with missing license files
        for prov in self.providers['fallback']:
            missing = self.missing_licenses(subset=subset)
            infos = prov.get_packages_info(missing)
            for pkg, missing_data in infos.items():
                if subset and not pkg in subset:
                    continue
                data = packages.get(pkg)
                data.update(missing_data) if infos else None
        return self

    def missing_licenses(self, subset=None):
        return {pkg: data for pkg, data in self.packages.items()
                if (subset is None or pkg in subset)
                and not any(data.get(k) for k in ('license_text', 'license_source'))
                }

    def resolved_licenses(self, subset=None):
        return {pkg: data for pkg, data in self.packages.items()
                if (subset is None or pkg in subset)
                and any(data.get(k) for k in ('license_source', 'license_text'))
                }

    def get_license_stats(self):
        c = Counter()
        by_license = defaultdict(set)
        for pkg, data in self.resolved_licenses().items():
            name = data['name']
            license = data.get('license_family') or data.get('license', 'unknown')
            c[license] += 1
            by_license[license].add(name)
        return c, by_license

    def get_package_dependencies(self, pkg):
        data = self.packages[pkg]
        depends = set()
        if 'requires_dist' in data:
            reqs = data['requires_dist']
            for dist in reqs.split(';'):
                dep_name = dist.split(' ')[0]
                depends.add(dep_name) if dep_name else None
        if 'depends' in data:
            for dist in data['depends']:
                dep_name = dist.split(' ')[0]
                depends.add(dep_name) if dep_name else None
        return depends

    def discover_package_dependencies(self):
        """
        for each package determine what required it, from package dependencies

        Note:
            The dependencies are derived from package meta data only. Any pip or
            conda requirements.txt is not taken into account. The dependencies
            are reported independent of versions and no correctness is done
            (i.e. no verification whether dependencies are satisfied)

        :return: .packages is updated to contain the required_by key for each
           package. If required_by is an empty set the package was not required
           by any (known) package.
        """
        packages = self.packages
        requireds = defaultdict(set)
        for pkg, data in packages.items():
            requireds[pkg]  # ensure we have an empty set for every pkg
            if pkg != data['name']:
                # only use basic package names, not versioned
                continue
            for dep in self.get_package_dependencies(pkg):
                requireds[dep].add(pkg)
        for pkg, required_by in requireds.items():
            if pkg in packages:
                # only add to known packages
                packages[pkg]['required_by'] = required_by
                packages[pkg]['is_primary'] = not required_by
        return self
