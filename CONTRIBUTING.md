# Contributing

I greatly appreciate your interest in reading this message, as this project requires volunteer developers to assist
in developing and maintaining it.

Before making any changes to this repository, please first discuss the proposed modifications with the repository owners
through an issue, email, or any other appropriate communication channel.

Please be aware that a [code of conduct](CODE-OF-CONDUCT.md) is in place, and should be adhered to during all
interactions related to the project.

## Python version support

Ensuring backward compatibility is an imperative requirement.

Currently, the tool supports Python versions 3.9, 3.10, 3.11, 3.12, and 3.13.

## MySQL version support

This tool is intended to fully support MySQL versions 5.5, 5.6, 5.7, and 8.0, including major forks like MariaDB.
We should prioritize and be dedicated to maintaining compatibility with these versions for a smooth user experience.

## Testing

As this project/tool involves the critical process of transferring data between different database types, it is of
utmost importance to ensure thorough testing. Please remember to write tests for any new code you create, utilizing the
[pytest](https://docs.pytest.org/en/latest/) framework for all test cases.

### Running the test suite

In order to run the test suite run these commands using a Docker MySQL image.

**Requires a running Docker instance!**

```bash
git clone https://github.com/techouse/sqlite3-to-mysql
cd sqlite3-to-mysql                   
python3 -m venv env
source env/bin/activate
pip install -e .
pip install -r requirements_dev.txt
tox
```

## Submitting changes

To contribute to this project, please submit a
new [pull request](https://github.com/techouse/sqlite3-to-mysql/pull/new/master) and provide a clear list of your
modifications. For guidance on creating pull requests, you can refer
to [this resource](http://help.github.com/pull-requests/).

When sending a pull request, we highly appreciate the inclusion of [pytest](https://docs.pytest.org/en/latest/) tests,
as we strive to enhance our test coverage. Following our coding conventions is essential, and it would be ideal if you
ensure that each commit focuses on a single feature.

For commits, please write clear log messages. While concise one-line messages are suitable for small changes, more
substantial modifications should follow a format similar to the example below:

```bash
git commit -m "A brief summary of the commit
> 
> A paragraph describing what changed and its impact."
```

## Coding standards

It is essential to prioritize code readability and conciseness. To achieve this, we recommend
using [Black](https://github.com/psf/black) for code formatting.

Once your work is deemed complete, it is advisable to run the following command:

```bash
tox -e flake8,linters
```

This command executes various linters and checkers to identify any potential issues or inconsistencies in your code. By
following these guidelines, you can ensure a high-quality codebase.

Thanks,

Klemen Tusar
