# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

version_dict = dict()
exec(open(os.path.join(os.path.dirname(__file__),
                       '_version.py')).read(),
     version_dict)

setup(
    name="repairweb",
    version=version_dict['__version__'],
    description="GDSE Dummy",
    #url='https://maxbo.github.io/cythonarrays/',
    author='Christoph Franke',
    author_email='franke@ggr-planung.de',
    classifiers=[
        # How mature is this project? Common values are
        #'Development Status :: 5 - Production/Stable',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish (should match "license" above)
         'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python',
        #'Programming Language :: Cython',

    ],
    #keywords='cython setuptools',

    packages=find_packages('.', exclude=['ez_setup']),

    package_dir={'': '.'},
    #package_data={'': ['*.pxd']},
    include_package_data=True,
    zip_safe=False,
    data_files=[],
    install_requires=[
        #'setuptools',
        ],
)

