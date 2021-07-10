from codecs import open
from os.path import abspath, dirname, join

from setuptools import setup

here = abspath(dirname(__file__))

packages = ["sqlite3_to_mysql"]

requires = [
    "Click>=7.0,<8.0.0 ; python_version<'3.6'",
    "Click>=7.0 ; python_version>='3.6'",
    "mysql-connector-python>=8.0.18,<8.0.24 ; python_version<'3.6'",
    "mysql-connector-python>=8.0.18 ; python_version>='3.6'",
    "pytimeparse>=1.1.8",
    "six>=1.12.0",
    "simplejson>=3.16.0",
    "tqdm>=4.35.0",
    "packaging>=20.3",
    "tabulate<0.8.6 ; python_version<'3.5'",
    "tabulate ; python_version>='3.5'",
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
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Database",
    ],
    project_urls={"Source": about["__url__"]},
    entry_points="""
        [console_scripts]
        sqlite3mysql=sqlite3_to_mysql.cli:cli
    """,
)
