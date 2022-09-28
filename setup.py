from setuptools import find_packages, setup

setup(
    name="ehex-solver",
    version="0.3",
    author="Tonico Strasser",
    author_email="tonico.strasser@gmail.com",
    description="Epistemic logic program solver using HEX programs",
    url="https://github.com/hexhex/ehex",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    install_requires=["tatsu>=5.8.0"],
    python_requires=">=3.10",
    entry_points={"console_scripts": ["ehex=ehex.__main__:main"]},
)
