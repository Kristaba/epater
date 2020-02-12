#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

#with open('HISTORY.rst') as history_file:
#history = history_file.read()
history = ''

# Should the web-related dependencies should not be a hard-dependency of the package?
requirements = [
    'ply==3.11',
]

setup_requirements = [ ]

test_requirements = [ ]

setup(
    # NOTE to change if it is merged upstream ;)
    author="Léo Grange",
    author_email='leo.grange@irit.fr',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="An ARM emulator in Python for educational purposes with a web GUI.",
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='epater',
    name='epater',
    packages=find_packages(include=['epater', 'epater.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/kristaba/epater',
    version='0.1.0',
    zip_safe=False,
)
