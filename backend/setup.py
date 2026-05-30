# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""Installer for Markanm package."""

from setuptools import setup, find_packages

from blend_core.version import VERSION_TAG, GIT_URL
from blend_core import get_setting

with open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = [l.strip() for l in f.readlines()]

with open('requirements-dev.txt') as f:
    dev_requirements = [l.strip() for l in f.readlines()]

setup(
    name='markanm',
    description="Markanm is a metasearch engine. Users are neither tracked nor profiled.",
    long_description=long_description,
    license="Apache-2.0",
    author='Markanm',
    author_email='contact@markanm.org',
    python_requires=">=3.10",
    version=VERSION_TAG,
    keywords='metasearch searchengine search web http',
    url=get_setting('brand.docs_url'),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    project_urls={"Code": GIT_URL, "Issue tracker": get_setting('brand.issue_url')},
    entry_points={
        'console_scripts': [
            'markanm-run = blend_core.webapp:run',
            'blend-run = blend.webapp:run',
        ]
    },
    packages=find_packages(
        include=[
            'blend',
            'blend.*',
            'blend',
            'blend_core.*',
            'blend_core.*.*',
            'blend_core.*.*.*',
        ]
    ),
    package_data={
        'blend': [
            'blend_config.yml',
            '*.toml',
            '*.msg',
            'data/*.json',
            'data/*.txt',
            'data/*.ftz',
            'favicons/*.toml',
            'infopage/**',
            'static/**',
            'templates/**',
            'translations/**',
        ],
    },
    install_requires=requirements,
    extras_require={'test': dev_requirements},
)
