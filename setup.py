from setuptools import setup, find_packages
import sys

version = __import__('smartcache').version


install_requires = []

for k in ['hash_ring', 'redis', 'docopt']:
    try:
        __import__(k)
    except ImportError:
        install_requires.append(k)

if sys.version_info < (2, 7):
    install_requires.append('unittest2')

setup(
    name="smartcache",
    version=version,
    author="Wecatch.me",
    author_email="wecatch.me@gmail.com",
    url="http://github.com/wecatch/smartcache",
    license="http://www.apache.org/licenses/LICENSE-2.0",
    description="smartcache is a friendly redis api",
    packages=find_packages(),
    install_requires=install_requires
)
