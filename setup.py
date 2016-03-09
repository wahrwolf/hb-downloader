from distutils.core import setup

import configuration

setup(
    name='hb-downloader',
    version=configuration.VERSION,
    packages=['hb-downloader'],
    url='https://github.com/talonius/hb-downloader',
    license='MIT',
    author='Brian Schkerke',
    author_email='bmschkerke@gmail.com',
    description='Automated download tool for Humble Bundle purchases.', requires=['requests']
)
