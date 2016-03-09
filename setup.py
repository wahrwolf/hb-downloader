from distutils.core import setup

setup(
    name='hb-downloader',
    version='0.10',
    packages=['requests'],
    url='https://github.com/talonius/hb-downloader',
    license='MIT',
    author='Brian Schkerke',
    author_email='bmschkerke@gmail.com',
    description='Automated download tool for Humble Bundle purchases.', requires=['requests']
)
