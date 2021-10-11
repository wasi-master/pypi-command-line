import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pypi-command-line",
    version="0.4.0",
    author="Wasi Master",
    author_email="arianmollik323@gmail.com",
    description="A beautiful command line interface for the Python Package Index",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://wasi-master.github.io/pypi-command-line/",
    project_urls={
        "Bug Tracker": "https://github.com/wasi-master/pypi-command-line/issues",
        "Source": "https://github.com/wasi-master/pypi-command-line",
        "Documentation": "https://wasi-master.github.io/pypi-command-line/",
        "Say Thanks": "https://saythanks.io/to/arianmollik323@gmail.com",
    },
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Natural Language :: English",
        "Topic :: Terminals",
    ],
    packages=["pypi_cli"],
    python_requires=">=3.6",
    install_requires=[
        "typer",
        "rich",
        "questionary",
        "rich-rst",
        "beautifulsoup4",
        "requests",
        "packaging",
        "humanize",
    ],
    extras_require={
        "speedups": [
            "shellingham",  # For automatic terminal detection for typer
            "lxml",  # For faster html and xml parsing
            "requests_cache",  # For faster web requests
        ]
    },
    entry_points={
        "console_scripts": ["pypi=pypi_cli.__main__:run"],
    },
    keywords=[
        "pypi",
        "pypi cli",
        "pypi-cli",
        "pypi command line",
        "pypi-command-line",
        "pypi command line interface",
        "pypi-command-line-interface",
        "pypi command line application",
        "pypi-command-line-application",
        "command line interface",
        "command-line-interface",
        "command line application",
        "command-line-application",
    ],
)
