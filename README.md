# Warning
This is a personal **unofficial** project. I have no affiliation with Bitwarden. Use at your own risk. Issues and feedback are welcome.

# Python wrapper for [Bitwarden Secrets Manager](https://bitwarden.com/help/secrets-manager-overview/) CLI
This module contains the `BWS` class, which is a Python wrapper for the `bws` [CLI application](https://bitwarden.com/help/secrets-manager-cli/). The `BWS` class allows users to retrieve secrets stored in a Bitwarden Secrets Manager project. The module uses `subprocess` to call the `bws` CLI. The `bws` CLI application (v.0.4.0+) must be [downloaded separately](https://github.com/bitwarden/sdk/releases) and already present on your system (ideally in a `PATH` directory). 

You must also have a Bitwarden Secrets Manager account with an existing project, secret(s) and machine account.

# How to use the `BWS` class

## Install
1. Activate your environment of choice.
2. Download [bitwarden_secrets_manager_python](https://github.com/jdhalbert/bitwarden_secrets_manager_python/releases).
3. Navigate to the folder containing `pyproject.toml` and run `pip install ./`

## Import
```
from bitwarden_secrets_manager_python import BWS
```

Optionally use `logging` to see useful information, especially if using in a Jupyter Notebook or troubleshooting. Secrets and keys will not be logged.
```import logging
logging.basicConfig(format='%(message)s', level=logging.INFO)
```

## Initialization
Initialize a `BWS` object with:
 - The project name as it appears in Bitwarden Secrets Manager.
 - If the BWS_ACCESS_TOKEN environment variable has not been set in your environment, provide the token as a string.
    - Your machine account that your access token is for must have at least `Read` access to your project (allowing get-like operations only). `Read and write` access is necessary to use functionality that adds, updates, or deletes secrets.
 - By default, the class uses the `bws` or `bws.exe` application found in a `PATH` directory, but a direct path to the application can also be supplied.
 - **Note: your project must already exist and contain at least one secret, otherwise initialization will fail.**
 - **Another note: your project *cannot* have any duplicate key names.** Although Bitwarden Secrets Manager does support duplicate key names (and keys instead by `id`), the `BWS` class mostly abstracts the `id` field for ease of use, keying on the key name (`key`) instead. This class will not allow creation of duplicate key names when using its CRUD interfaces. Be careful not to break compatibility by adding duplicate key names via the CLI, web interface, or other tools.

Example if `bws` is not in your `PATH` and a token is not set as an environment variable:
```python
my_bws = BWS(project_name='my_project_name', bws_access_token='my_token', bws_path='path/to/bws')
```

Example if `bws` is in your `PATH` and a token is set as an environment variable:
```python
my_bws = BWS(project_name='my_project_name')
```

Note that each `BWS` object corresponds to a single project and service account. If you have multiple projects and/or service accounts to access, create separate `BWS` objects for each one.

### Note on Caching Behavior
Upon initialization, all of the secrets in the given project are cached in the `BWS` instance. After initialization, get-like operations will read from the cache. Adds, updates, and deletes will update in your Bitwarden Secrets Manager account and incrementally update the cache, keeping the cache and online account in sync without unnecessary traffic. **Out-of-bound** changes to secrets made after initialization will not be reflected in the cache unless `refresh_secrets_cache()` is called on the instance.

## Interacting with secrets
Get a secret value:
```python
secret_value = my_bws['secret_key']
# or
secret_value = my_bws.get_secret('secret_key')['value']
# or
secret_value = my_bws.get_secret('secret_key', value_only=True)
```

Add a secret:
```python
my_bws['secret_key'] = 'secret_value' # same as updating
# or
my_bws.add_secret('secret_key', 'secret_value')
```

Update a secret:
```python
my_bws['secret_key'] = 'secret_value' # same as adding
# or
my_bws.update_secret_value('secret_key', 'secret_value')
```

Delete a secret:
```python
del my_bws['secret_key']
# or
my_bws.delete_secret('secret_key')
```

Get all secrets as a dictionary keyed by `key`:
```python
my_bws.as_dict()
```

Get all secrets as a list of tuples:
```python
my_bws.items()
```

Get number of secrets:
```python
len(my_bws)
```

Check if a secret exists:
```python
'secret_key' in my_bws
```

Other arbitrary calls to BWS CLI using your access token (but not your project name):
```python
my_bws.call_and_return_text(cl_args=['project', 'get', bws.PROJECT_ID], print_to_console=True, as_json=True)
```

## Other functions

```python
# use for making sure the CLI is working
my_bws.help()
my_bws.version()
```

See `bws.py` for more information.
