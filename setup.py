from setuptools import setup

setup(
    name='Python Transfer',
    description='An easy way to fetch and store data from and to key-value databases like Redis.',
    version="0.2",
    url='https://github.com/arrrlo/python-transfer',

    author='Ivan Arar',
    author_email='ivan.arar@gmail.com',

    packages=['python_transfer'],
    install_requires=[
        'redis~=2.10',
        'ujson~=1.35'
    ],

    entry_points={
        'console_scripts': [
            'pythontransfer=python_transfer.cli:cli'
        ],
    },
)
