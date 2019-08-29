from codecs import open
from os.path import abspath, dirname, join

from setuptools import setup

here = abspath(dirname(__file__))

packages = ["sqlite3_to_mysql"]

requires = [
    "Click>=7.0",
    "mysql-connector-python>=8.0.17",
    "protobuf>=3.9.1",
    "six>=1.12.0",
    "tqdm>=4.35.0",
]

test_requirements = [
    "atomicwrites>=1.3.0",
    "attrs>=19.1.0",
    "backports.ssl-match-hostname>=3.7.0.1",
    "certifi>=2019.6.16",
    "chardet>=3.0.4",
    "Click>=7.0",
    "codecov>=2.0.15",
    "configparser>=3.8.1",
    "contextlib2>=0.5.5",
    "coverage>=4.5.4",
    "docker>=4.0.2",
    "factory-boy>=2.12.0",
    "Faker>=2.0.1",
    "funcsigs>=1.0.2",
    "idna>=2.8",
    "importlib-metadata>=0.19",
    "ipaddress>=1.0.22",
    "mock>=3.0.5",
    "more-itertools>=5.0.0",
    "mysql-connector-python>=8.0.17",
    "packaging>=19.1",
    "pathlib2>=2.3.4",
    "pluggy>=0.12.0",
    "protobuf>=3.9.1",
    "py>=1.8.0",
    "pyparsing>=2.4.2",
    "pytest>=4.6.5",
    "pytest-cov>=2.7.1",
    "pytest-faker>=2.0.0",
    "pytest-mock>=1.10.4",
    "python-dateutil>=2.8.0",
    "requests>=2.22.0",
    "scandir>=1.10.0",
    "six>=1.12.0",
    "SQLAlchemy>=1.3.7",
    "SQLAlchemy-Utils>=0.34.2",
    "text-unidecode>=1.2",
    "tqdm>=4.35.0",
    "urllib3>=1.25.3",
    "wcwidth>=0.1.7",
    "websocket-client>=0.56.0",
    "zipp>=0.6.0",
]

about = {}
with open(join(here, "sqlite3_to_mysql", "__version__.py"), "r", "utf-8") as fh:
    exec(fh.read(), about)

with open(join(here, "README.md"), "r", "utf-8") as fh:
    readme = fh.read()

setup(
    name=about["__title__"],
    version=about["__version__"],
    description=about["__description__"],
    long_description=readme,
    long_description_content_type="text/markdown",
    author=about["__author__"],
    author_email=about["__author_email__"],
    url=about["__url__"],
    packages=packages,
    include_package_data=True,
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*",
    install_requires=requires,
    license=about["__license__"],
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Database",
    ],
    tests_require=test_requirements,
    project_urls={"Source": about["__url__"]},
    entry_points="""
        [console_scripts]
        sqlite3mysql=sqlite3_to_mysql.cli:cli
    """,
)
