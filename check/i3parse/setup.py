
import sys
try:
    # setuptools entry point is slow
    #  if we have festentrypoint use
    #  a fast entry point
    import fastentrypoints
except ImportError:
    sys.stdout.write('Not using fastentrypoints\n')
    pass

import setuptools.command.test
import os

HERE = os.path.dirname(__file__)

class ToxTest(setuptools.command.test.test):
    user_options = []

    def initialize_options(self):
        setuptools.command.test.test.initialize_options(self)

    def run_tests(self):
        import tox
        tox.cmdline()
        tox.cmdline(['-c', 'tox-minimal.ini'])


setuptools.setup(
    name='i3parse',
    cmdclass = {'test': ToxTest},
    version="0.1.0",
    author='Tal Wrii',
    author_email='talwrii@gmail.com',
    description='',
    license='GPLv3',
    keywords='',
    url='',
    packages=['i3parse'],
    long_description='See https://github.com/talwrii/i3parse',
    entry_points={
        'console_scripts': ['i3parse=i3parse.i3parse:main']
    },
    classifiers=[
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)"
    ],
    install_requires=['parsimonious', 'graphviz', 'mock']
)
