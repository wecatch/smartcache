from setuptools import setup


version = __import__('smartcache').version


install_requires = [

]

for k in ['redis', 'docopt']:
    try:
        __import__(k)
    except ImportError:
        install_requires.append(k)

setup(
    name="smartcache",
    version=version,
    author="Wecatch.me",
    author_email="wecatch.me@gmail.com",
    url="http://github.com/wecatch/smartcache",
    license="http://www.apache.org/licenses/LICENSE-2.0",
    description="smartcache is friendly redis api",
    packages=['smartcache'],
    install_requires=install_requires
)
