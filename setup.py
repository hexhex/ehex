from setuptools import setup, find_packages

setup(
    name="ehex-solver",
    version="0.1",
    author="Tonico Strasser",
    author_email="tonico.strasser@gmail.com",
    description="Epistemic logic program solver using HEX programs",
    url="https://github.com/hexhex/ehex",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
    ],
    install_requires=["tatsu>=5.5.0"],
    python_requires=">=3.8",
    entry_points={"console_scripts": ["ehex=ehex.__main__:main"]},
)
