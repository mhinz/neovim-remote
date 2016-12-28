from setuptools import setup
from os         import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name             = 'neovim-remote',
    author           = 'Marco Hinz',
    author_email     = 'mh.codebro@gmail.com',
    url              = 'https://github.com/mhinz/neovim-remote',
    description      = 'Control Neovim instances using "nvr" commandline tool',
    long_description = long_description,
    install_requires = ['neovim'],
    scripts          = ['bin/nvr'],
    packages         = [],
    version          = '1.4.2',
    license          = 'MIT',
    keywords         = 'neovim nvim nvr remote helper',
    classifiers      = [
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)

