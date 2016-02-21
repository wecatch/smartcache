from setuptools import setup, find_packages
import sys
import os

version = __import__('smartcache').version


install_requires = []

for k in ['redis', 'docopt']:
    try:
        __import__(k)
    except ImportError:
        install_requires.append(k)

if sys.version_info < (2, 7):
    install_requires.append('unittest2')

kwargs = {}

readme_path = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(readme_path, 'README.rst')) as f:
    kwargs['long_description'] = f.read()

setup(
    name="smartcache",
    version=version,
    author="Wecatch.me",
    author_email="wecatch.me@gmail.com",
    url="http://github.com/wecatch/smartcache",
    license="http://www.apache.org/licenses/LICENSE-2.0",
    description="smartcache is friendly redis api",
    keywords='cache redis objectcache',
    packages=find_packages(),
    install_requires=install_requires,
    **kwargs
)
