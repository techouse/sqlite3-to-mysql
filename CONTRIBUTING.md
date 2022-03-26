# Contributing

I'm really glad you're reading this, because we need volunteer developers to help this project come to fruition.

When contributing to this repository, please first discuss the change you wish to make via issue, email, or any other 
method with the owners of this repository before making a change.

Please note we have a code of conduct, please follow it in all your interactions with the project.

## Python version support

Backwards compatibility is a must.

Currently, the tool supports Python versions 2.7, 3.5, 3.6, 3.7, 3.8, 3.9 and 3.10.

Even though Python 2.7 has reached the end of its life at the beginning of 2020, a lot of people still rely on it. 
Therefore, we should continue to support it as long as the underlying tools do not completely drop support for it.

## MySQL version support

This tool supports and should continue to support MySQL versions 5.5, 5.6, 5.7 and 8.0. This includes any includes major
forks of MySQL, e.g. MariaDB.

## Testing

Since this project/tool deals with transferring data from one database type to another it is crucial that it is
thoroughly tested. Please write tests for any new code you create. All tests must be written using [pytest](https://docs.pytest.org/en/latest/).

### Running the test suite

In order to run the test suite run these commands using a Docker MySQL image.

**Requires a running Docker instance!**

- using Python 2.7
```bash
git clone https://github.com/techouse/sqlite3-to-mysql
cd sqlite3-to-mysql
virtualenv -p $(which python2) env
source env/bin/activate
pip install -e .
pip install -r requirements_dev.txt
tox
```

- using Python 3.5+
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

Send a new [pull request](https://github.com/techouse/sqlite3-to-mysql/pull/new/master) with a clear list of what
you've done (read more about [pull requests](http://help.github.com/pull-requests/)). When you send a pull request, 
we will love you forever if you include [pytest]((https://docs.pytest.org/en/latest/)) tests. We can always use more 
test coverage. Please follow our coding conventions (below) and make sure all of your commits are atomic (one feature 
per commit).

Always write a clear log message for your commits. One-line messages are fine for small changes, but bigger changes 
should look like this:

```bash
git commit -m "A brief summary of the commit
> 
> A paragraph describing what changed and its impact."
```
    
## Coding standards

Your code should be readable and concise. Always use [Black](https://github.com/psf/black) to format your code.
Additionally, once you feel you're done, run 

```bash
tox -e flake8,linters
``` 

in order to run all various linters and checkers against it.



Thanks,

Klemen Tusar