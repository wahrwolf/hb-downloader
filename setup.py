from setuptools import setup

setup(name='hb_downloader',
      version='0.5.0',
      description='an unofficial api client for humblebundle',
      url='https://github.com/MayeulC/hb-downloader/releases',
      author='Brian Schkerke',
      license='MIT',
      packages=['hb_downloader'],
      test_suite='nose.collector',
      tests_require=['nose'],
      zip_safe=False)
