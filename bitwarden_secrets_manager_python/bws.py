# pylint: disable=logging-format-interpolation, logging-fstring-interpolation, line-too-long, invalid-name

""" Module contains the BWS (Bitwarden Secrets Manager) class, a Python wrapper for the `bws` CLI application. """

import os
import json
import logging
import subprocess
from pathlib import Path
from copy import deepcopy

logger = logging.getLogger(__name__)


class BWS:
    """Bitwarden Secrets Manager Python wrapper."""

    _BWS_APPLICATION_PATH: Path
    _BWS_ACCESS_TOKEN: str
    _PROJECT_NAME: str

    PROJECT_ID: str

    _secrets: dict

    def __init__(self, project_name: str, bws_access_token: str = None, bws_path: str = "bws") -> None:
        """Initialize. Note: the given project MUST contain at least one secret.

        Args:
            project_name (str): Name of the project to get secrets for. The bws_access_token must have access
                to this project. To include secrets for multiple projects, use separate objects.
            bws_access_token (str, optional): If not provided, will check if the environment variable is set and use
                that. Supplied in CLI calls with the `-t` option. Defaults to None.
            bws_path (str, optional): Path to call `bws` or `bws.exe` application. Defaults to 'bws', which works if
                the parent directory is in your system's PATH variable.
        """
        self._PROJECT_NAME = project_name
        self._BWS_APPLICATION_PATH = Path(bws_path)
        self._set_token(bws_access_token=bws_access_token)
        self.PROJECT_ID = self._get_project_id()
        self.refresh_secrets_cache()

        logger.info(f"Using Bitwarden Secrets Manager application at: {bws_path}")

    def __getitem__(self, key: str) -> str:
        """When accessing the BWS object like a dictionary, only the 'value' field for the given key is returned.

        Args:
            key (str): Secret name.

        Returns:
            str: Secret 'value' field.
        """
        return self.get_secret(key=key, value_only=True)

    def __setitem__(self, key: str, value: str) -> None:
        """Adds or updates the provided key/value pair.

        Args:
            key (str): Secret name.
            value (str): Secret value.
        """
        if key in self:
            self.update_secret_value(key=key, value=value)
        else:
            self.add_secret(key=key, value=value)

    def __len__(self) -> int:
        return len(self._secrets)

    def __contains__(self, key) -> bool:
        return key in self._secrets

    def __delitem__(self, key) -> None:
        self.delete_secret(key=key)

    def _set_token(self, bws_access_token: str | None) -> None:
        """If a bws_access_token is not provided, check is one is already set as an environment variable.

        Args:
            bws_access_token (str | None): Provide if not already set as BWS_ACCESS_TOKEN environment variable.

        Raises:
            ValueError: No BWS_ACCESS_TOKEN provided or set as environment variable.
        """
        if bws_access_token:
            self._TOKEN = bws_access_token
        elif "BWS_ACCESS_TOKEN" in os.environ:
            logger.info("Using BWS_ACCESS_TOKEN already set as environment variable.")
            self._TOKEN = os.environ["BWS_ACCESS_TOKEN"]
        else:
            raise ValueError("No BWS_ACCESS_TOKEN provided or set as environment variable.")

    def _get_project_id(self, print_to_console: bool = False) -> str:
        """Gets the project's ID from the project name provided in the constructor.

        Args:
            print_to_console (bool, optional): Call print() on the stdout results. Defaults to False.

        Raises:
            ValueError: Project name not found.

        Returns:
            str: Project ID
        """
        projects: list[dict] = self.call_and_return_text(
            cl_args=["project", "list"], print_to_console=print_to_console, as_json=True
        )
        for project in projects:
            if project["name"] == self._PROJECT_NAME:
                return project["id"]
        raise ValueError(
            f'Project "{self._PROJECT_NAME}" not found. Choose from projects: ' f'{[p["name"] for p in projects]}'
        )

    def _make_call(self, cl_args: list[str], print_to_console: bool = False) -> str:
        """Make a call to `bws` with the provided args. Usually use self.call_and_return_text() instead of this.

        Args:
            cl_args (list[str]): Args in list format (e.g. ['project', 'list'])
            print_to_console (bool, optional): Call print() on the stdout results. Defaults to False.

        Returns:
            str: Call results.
        """
        try:
            output = subprocess.check_output(
                [self._BWS_APPLICATION_PATH] + cl_args + ["-c", "no", "-t", self._TOKEN],
                text=True,
                stderr=subprocess.STDOUT,
            )
            if print_to_console:
                print(output)
            return output

        except subprocess.CalledProcessError as cpe:
            if print_to_console:
                print(cpe.output)
            logger.critical(
                f"CalledProcessError: {cpe.output}. Note: access_token value redacted from list of"
                "commands in exception raised below:"
            )
            cpe.cmd.pop()  # remove the access_token value so it doesn't get logged or displayed
            raise cpe

    def _get_secrets_from_bws(self) -> dict[str, dict[str, str]]:
        """Get list of all secrets from `bws` CLI.

        Returns:
            dict[str, dict[str, str]: Secert objects keyed by secret key name. E.g.:
            {'secret_1':
                {'id': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
                'organizationId': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
                'projectId': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
                'key': 'secret_1',
                'value': 'secret_1_value',
                'note': '',
                'creationDate': '2001-01-01T01:23:45.678901234Z',
                'revisionDate': '2001-01-01T01:23:45.678901234Z'},
            ...
            }
        """
        secrets = self.call_and_return_text(cl_args=["secret", "list", self.PROJECT_ID], as_json=True)
        secrets_keyed_by_key = {secret["key"]: secret for secret in secrets}
        if len(secrets_keyed_by_key) != len(secrets):
            raise ValueError(
                "Projects with multiple keys with the same name are not supported. Each key name in your "
                "project must be unique."
            )
        return secrets_keyed_by_key

    def refresh_secrets_cache(self) -> None:
        """Re-download all secrets from BWS."""
        self._secrets = self._get_secrets_from_bws()

    def call_and_return_text(
        self, cl_args: list, print_to_console: bool = False, as_json: bool = True
    ) -> str | dict | list:
        """Make a call to `bws` CLI. Be careful with this as it can break compatibility with the BWS class (e.g.
            deleting all secrets in a project or creating secrets with duplicate key names). See README.md for more
            information.

        Args:
            cl_args (list): Args in list format (e.g. ['project', 'list']). Supply each word or option as a separate
                list item.
            print_to_console (bool, optional): Call print() on the stdout results. Defaults to False.
            as_json (bool, optional): Return the results converted to JSON. Defaults to True.

        Returns:
            str|dict|list: stdout
        """
        text: str = self._make_call(cl_args=cl_args, print_to_console=print_to_console)
        return json.loads(text) if as_json else text

    def get_secret(self, key: str, value_only: bool = False) -> dict | str:
        """When accessing the BWS object like a dictionary, only the 'value' field for the given key is returned.

        Args:
            key (str): Secret name.
            value_only (bool): Return only the secret's 'value' field instead of the whole dict.

        Returns:
            dict | str: Entire secret dict if value_only, else just the secret 'value' field as string.
                E.g. if dict:
                    {'id': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
                    'organizationId': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
                    'projectId': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
                    'key': 'secret_1',
                    'value': 'secret_1_value',
                    'note': '',
                    'creationDate': '2001-01-01T01:23:45.678901234Z',
                    'revisionDate': '2001-01-01T01:23:45.678901234Z'}

                E.g. if str: 'secret_1_value'
        """
        return self._secrets[key]["value"] if value_only else self._secrets[key]

    def add_secret(self, key: str, value: str, print_to_console: bool = False) -> dict:
        """Add a new secret key/value pair. Adds to the internal cache without refreshing the whole thing.

        Args:
            key (str): Key to add.
            value (str): Secret value.
            print_to_console (bool, optional): Call print() on the stdout results. Defaults to False.

        Returns:
            dict: Full new secret dict. E.g.
                {'id': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
                'organizationId': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
                'projectId': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
                'key': 'secret_key',
                'value': 'secret_value',
                'note': '',
                'creationDate': '2001-01-01T01:23:45.678901234Z',
                'revisionDate': '2001-01-01T01:23:45.678901234Z'}
        """
        if key in self:
            raise RuntimeError(f"Key {key} already exists in the project. Did you mean to call update_secret_value()?")
        full_secret = self.call_and_return_text(
            cl_args=["secret", "create", key, value, self.PROJECT_ID], print_to_console=print_to_console
        )
        logger.info(f'Added secret "{key}" to project "{self._PROJECT_NAME}"')
        self._secrets[key] = full_secret
        return full_secret

    def update_secret_value(self, key: str, value: str, print_to_console: bool = False) -> dict:
        """Update the value of a given secret. Updates internal cache without refreshing the whole thing.

        Args:
            key (str): Key to update.
            value (str): Replacement value.
            print_to_console (bool, optional): Call print() on the stdout results. Defaults to False.

        Returns:
            dict: Full updated secret dict. E.g.
                {'id': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
                'organizationId': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
                'projectId': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
                'key': 'secret_key',
                'value': 'secret_value',
                'note': '',
                'creationDate': '2001-01-01T01:23:45.678901234Z',
                'revisionDate': '2001-01-01T01:23:45.678901234Z'}
        """
        secret_id = self._secrets[key]["id"]
        full_secret = self.call_and_return_text(
            cl_args=["secret", "edit", secret_id, "--value", value], print_to_console=print_to_console
        )
        logger.info(f'Updated value for secret "{key}" in project "{self._PROJECT_NAME}"')
        self._secrets[key] = full_secret
        return full_secret

    def delete_secret(self, key: str, print_to_console: bool = False) -> None:
        """Delete a secret. Updates internal cache without refreshing the whole thing.

        Args:
            key (str): Key to delete.
            print_to_console (bool, optional): Call print() on the stdout results. Defaults to False.
        """
        secret_id = self._secrets[key]["id"]
        self.call_and_return_text(
            cl_args=["secret", "delete", secret_id], print_to_console=print_to_console, as_json=False
        )
        del self._secrets[key]
        logger.info(f'Deleted secret "{key}" from project "{self._PROJECT_NAME}"')

    def items(self) -> list[tuple[str, dict]]:
        """Call .items() on the secrets cache.

        Returns:
            list[tuple[str, dict]]: List of secrets like [(key:str, value:dict)].
        """
        return self._secrets.items()

    def as_dict(self) -> dict[str, dict[str, dict]]:
        """Returns a deepcopy of the internal secrets cache containing all project secrets.

        Returns:
            dict[str, dict[str, dict]]: Deepcopy of internal _secrets object.
        """
        return deepcopy(self._secrets)

    def help(self, print_to_console=True) -> str:
        """`bws` -h (help) command.

        Args:
            print_to_console (bool, optional): Defaults to True.

        Returns:
            str: Console output as string.
        """
        return self.call_and_return_text(cl_args=["-h"], print_to_console=print_to_console, as_json=False)

    def version(self, print_to_console=True) -> str:
        """`bws` -V (version) command.

        Args:
            print_to_console (bool, optional): Defaults to True.

        Returns:
            str: Console output as string.
        """
        return self.call_and_return_text(cl_args=["-V"], print_to_console=print_to_console, as_json=False)
