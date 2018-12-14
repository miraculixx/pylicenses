class PackageProvider(object):
    init_kwargs = []

    def get_packages_info(self):
        raise NotImplementedError
