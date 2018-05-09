from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='DB Transfer',
    version="0.5.0",

    description='An easy way to fetch and store data from and store to key-value databases like Redis.',
    long_description=readme(),
    long_description_content_type='text/markdown',

    url='https://github.com/arrrlo/db-transfer',
    licence='MIT',

    author='Ivan Arar',
    author_email='ivan.arar@gmail.com',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='database, redis, transfer, migration',

    packages=['db_transfer'],
    install_requires=[
        'click~=6.3',
        'redis~=2.10',
        'ujson~=1.35',
        'six~=1.11.0',
        'PyYAML~=3.12'
    ],

    entry_points={
        'console_scripts': [
            'dbtransfer=db_transfer.cli:cli'
        ],
    },

    project_urls={
        'Source': 'https://github.com/arrrlo/db-transfer',
    },
)
