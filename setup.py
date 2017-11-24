from setuptools import setup

setup(
    name='ehex',
    description='EHEX program parser and solver',
    url='https://github.com/hexhex/ehex',
    author='Tonico Strasser',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='epistemic hex logic answerset programming asp',
    install_requires=['grako==3.18.1'],
    python_requires='>=3.4',
    entry_points={
        'console_scripts': [
            'ehex=ehex.app:main'
        ],
    },
)
