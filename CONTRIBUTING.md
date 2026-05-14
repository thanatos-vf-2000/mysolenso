# Contributing to the mysolenso Python packages (PyPI)

Thanks for your interest in mysolenso.

- [Contributing to the mysolenso Python packages (PyPI)](#contributing-to-the-mysolenso-python-packages-pypi)
  - [Prerequisites](#prerequisites)
  - [Set up a development environment](#set-up-a-development-environment)
  - [Testing](#testing)
  - [Releasing](#releasing)

## Prerequisites

Before getting started, the following tools need to be installed:

1. [Git][get-git] to manage source code
[get-git]: https://git-scm.com/downloads
2. Clone depot:

```code
git clone https://github.com/thanatos-vf-2000/mysolenso.git
```

## Set up a development environment

1. Go to mysolenso directory ```cd mysolenso```
2. Install dependency: ```pip install -e .```

## Testing

Run [example.py](./example.py) for a basic usage and tests

```code
PYTHONPATH=./src/ python3 example.py --username <USER> --password <PASSWORD_CRYPT>
```

## Releasing

From a clean instance of main, perform the following actions to release a new version
of this plugin:

- Update the version number in [`pyproject.toml`](pyproject.toml),
- Update file [`CHANGELOG.md`](CHANGELOG.md)
    - Verify that all changes for this version in `CHANGELOG.md` are clear and accurate,
      and are followed by a link to their respective issue
    - Create a PR with these changes
