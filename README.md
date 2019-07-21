PyLicenses
==========

Find license types and texts for all installed packages in conda and pip
environments, producing a distribution-ready file THIRDPARTY-LICENSES
with required details on all packages, including their respective license texts.

Why yet another tool?
---------------------

There are several packages with similar intents, however I did not find any
to match the particular usecase PyLicenses covers. Specifically to produce
a complete set of licenses for all installed packages, at the package level
(as opposed to the file level as many other such tools do).Also I wanted to have
a focused tool that is easily extensible to any framework, in any language.

Features
--------

PyLicense

* produces the THIRDPARTY-LICENSES file as a report on all packages
* collects data from conda, pip, pypi and github to retrieve information
  on authorship, package homepage, license style and - most importantly -
  the actual license text.
* uses a pipeline of scanners/data collectors. Adding a new framework to
  scan (e.g. to include npm modules) is a matter of writing a new PackageProvider
  class with a single method.
* produces reports and statistics on primary packages (direct dependency) and
  secondary packages (pulled-in through a dependency), notably this works across
  conda and pip. Statistics currently include counts per license type.
* highlights packages were the license information or license text is missing
* can map packages to a fixed license URL for packages that do not include
  the license text or where the LICENSE file is difficult to find by automated
  means.


How to use
----------

Within your conda or pip virtualenv, run

    $ python -m pylicenses

To see options

    $ python -m pylicenses -h
    usage: __main__.py [-h] [--github GITHUB] [--stats STATS]

    optional arguments:
      -h, --help       show this help message and exit
      --github GITHUB  specify github user,password
      --stats STATS    print statistics

Sample output
-------------

See the THIRDPARTY-LICENSES file in this repository for the full license
collection report of this package.

The direct output looks something like this

    $ python -m pylicenses
    Packages directly required:

    name        author                      license
    ----------  --------------------------  -----------------------
    pylicenses  Patrick Senti               Apache 2.0
    wheel       Daniel Holth                Other
    urllib3     Andrey Petrov               MIT
    tabulate    Sergey Astanin              MIT
    sh          Andrew Moffat               MIT
    setuptools  Python Packaging Authority  MIT License
    requests    Kenneth Reitz               Apache Software License
    pip         The pip developers          MIT
    certifi     Kenneth Reitz               MPL-2.0
    libedit                                 NetBSD
    python                                  PSF

    Packages pulled in through other requirements:

    name             author            license
    ---------------  ----------------  --------------------------------------
    idna             Kim Davies        BSD Like
    chardet          Daniel Blanchard  GNU Lesser General Public License v2.1
    ca-certificates                    ISC
    libffi                             MIT
    libgcc-ng                          GPL
    libstdcxx-ng                       GPL3 with runtime exception
    ncurses                            Free software - X11 License
    openssl                            OpenSSL
    readline                           GPL3
    sqlite                             Public-Domain
    xz                                 Public-Domain, GPL
    zlib                               zlib

    **SUCCESS** Good news. There are no packages without license texts

    **SUCCESS** The full license report is available in THIRDPARTY-LICENSES


How to implement a new scanner
------------------------------

1. Add a class in `pylicenses.provider`, e.g.

        class MyPackageScanner(PackageProvider):
            def get_packages_info(self, packages, subset=None)
                ... your code to update packages ...
                return packages

   `packages` is a dictionary mapping `name=>data`, where `name` is either
   the package's canonical name or the full distribution name (name-version-type),
   and `data` is the data collected so far. For programming convenience all mapping
   of the same package, independent of the key, reference the same `data` object.

   Currently there are only very few conventions for the contents of data:

    * `name` is the name of package without version or distribution type
    * `dist_name` is the full distribution name (name-version or name-version-type)
    * `license` is the canonical license name (e.g. MIT, Apache-2.0 etc.)
    * `license_text` is the actual license text
    * `license_source` is the filename/URL to the source of the license text
    * `license_trace` is the last scanner to update the data

   Any other data can be stored by the scanners as they see fit. Note the
   dependency on `PackageProvider` as a base class is a convenience only.

2. Add the new scanner class to PyLicenses.PROVIDERS

3. Add unit tests

License
-------

MIT License - Copyright (c) 2018 Patrick Senti, productaize.io
See LICENSE file
