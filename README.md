# mysolenso library

![PyPI](https://img.shields.io/pypi/v/mysolenso) ![TestPyPI](https://img.shields.io/badge/dynamic/json?label=TestPyPI&url=https%3A%2F%2Ftest.pypi.org%2Fpypi%2Fmysolenso%2Fjson&query=$.info.version) ![License](https://img.shields.io/pypi/l/mysolenso) 

[![Docs](https://img.shields.io/badge/docs-online-brightgreen)](https://thanatos-vf-2000.github.io/mysolenso/) [![Workflow Status](https://github.com/thanatos-vf-2000/mysolenso/actions/workflows/docs.yml/badge.svg?branch=main)](https://github.com/thanatos-vf-2000/mysolenso/actions)

![Python Versions](https://img.shields.io/pypi/pyversions/mysolenso)
![Downloads](https://img.shields.io/pypi/dm/mysolenso)


MySolenso library for Python 3. The library was created to call api from your https://monitor.solenso.net/platform/.

To recover your encrypted password, please use the project [pwdsolenso](https://github.com/thanatos-vf-2000/pwdsolenso)


## Document

[Document](https://thanatos-vf-2000.github.io/mysolenso/)

## Example usage

### Generic example

See [example.py](./example.py) for a basic usage and tests

```code
PYTHONPATH=./src/ python3 example.py --username <USER> --password <PASSWORD_CRYPT>
```

### Report example

See [example_reports.py](./example_reports.py) for a report usage and tests

```code
PYTHONPATH=./src/ python3 example_reports.py --username <USER> --password <PASSWORD_CRYPT>
```

## https://www.solenso.fr/ - mysolenso

This library can read information from https://monitor.solenso.net/platform/. The project is independent of Solenso.

## Help

- You must use your crypt password or a token, not your password directly. To do this, use the project [pwdsolenso](https://github.com/thanatos-vf-2000/pwdsolenso).


## Issues

You can create issues in this repository to plan, discuss, and track work. Issues can track bug reports, new features and ideas, and anything else you need to write down or discuss. [➡️ Go to issues ⬅️](https://github.com/thanatos-vf-2000/mysolenso/issues)

## Contributing

We welcome contributions of all kinds to this repository. For instructions on how to get started and
descriptions of our development workflows, please see our [contributing guide][contrib].

[contrib]: https://github.com/thanatos-vf-2000/mysolenso/blob/main/CONTRIBUTING.md

## License

Copyright 2026 @Franck VANHOUCKE

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.


For the full license text see [`LICENSE`](LICENSE).