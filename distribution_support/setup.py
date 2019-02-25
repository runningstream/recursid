import setuptools
from distutils.core import setup

setup(
    name='Recursid',
    version='0.1.0',
    author='Running Stream',
    author_email='runningstreamllc@gmail.com',
    packages=['recursid', 'recursid.modules'],
    scripts=['bin/recursid.py','bin/recursid_multithread.py'],
    url='https://github.com/runningstream/recursid/',
    license='LICENSE.md',
    description='Recursive data processing framework.',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "requests >= 2.20.0",
        "python3-logstash >= 0.4.80",
        "boto3 >= 1.9.0",
        "pyzmq >= 17.1.2",
        "msgpack >= 0.6.0",
    ],
)
