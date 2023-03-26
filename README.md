# Warning
This is a personal **unofficial** project. I have no affiliation with Bitwarden. Use at your own risk. Issues and feedback are welcome.

# Python wrapper for [Bitwarden Secrets Manager](https://bitwarden.com/help/secrets-manager-overview/) CLI
This module contains the `BWS` class, which is a Python wrapper for the `bws` [CLI application](https://bitwarden.com/help/secrets-manager-cli/). The class allows users to retrieve secrets stored in a Bitwarden Secrets Manager project. The module uses `subprocess` to call the `bws` CLI. The `bws` CLI application must be [downloaded separately](https://github.com/bitwarden/sdk/releases) and already present on your system (ideally in a `PATH` directory).

You must also have opted-in to the Bitwarden Secrets Manager beta and have generated a project, secret(s) and service account.

# How to use the `BWS` class

## Install
1. Activate your environment of choice.
2. Download [bws_python](https://github.com/jdhalbert/bitwarden_secrets_manager_python/releases).
3. Navigate to the folder containing `pyproject.toml` and run `pip install ./`

## Import
```
from bws import BWS
```

Optionally use `logging` to see useful information, especially if using in a Jupyter Notebook or troubleshooting:
```import logging
logging.basicConfig(format='%(message)s', level=logging.INFO)
```

## Initialization
Initialize a `BWS` object with:
 - The project name as it appears in Bitwarden Secrets Manager.
 - If the BWS_ACCESS_TOKEN environment variable has not been set in your environment, provide the token as a string.
 - By default, the class uses the `bws` or `bws.exe` application found in a `PATH` directory, but a direct path to the application can also be supplied.

Example if `bws` is not in your `PATH` and a token is not set as an environment variable:
```
my_bws = BWS(project_name='my_project_name', bws_access_token='my_token', bws_path='path/to/bws')
```

Example if `bws` is in your `PATH` and a token is set as an environment variable:
```
my_bws = BWS(project_name='my_project_name')
```

Note that each `BWS` object corresponds to a single project and service account. If you have multiple projects and/or service accounts to access, create separate `BWS` objects for each one.

## Accessing individual secrets
Access secrets from the BWS object as a key/value dictionary.
```
secret_value = my_bws['key']
all_secrets = my_bws.items()
```

## Other functions
See docstrings in `bws.py` for other functionality.
