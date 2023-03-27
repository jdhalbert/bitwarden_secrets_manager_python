# pylint: disable=logging-format-interpolation, logging-fstring-interpolation, line-too-long, invalid-name

""" Module contains the BWS (Bitwarden Secrets Manager) class, a Python wrapper for the `bws` CLI application. """

import os
import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

class BWS:
    """ Bitwarden Secrets Manager Python wrapper. """

    _BWS_APPLICATION_PATH:Path
    _BWS_ACCESS_TOKEN:str
    _PROJECT_NAME:str
    _PROJECT_ID:str
    _SECRETS:dict

    def __init__(self, project_name:str, bws_access_token:str=None, bws_path:str='bws') -> None:
        """ Initialize.

        Args:
            project_name (str): Name of the project to get secrets for. The bws_access_token must have access
                to this project. To include secrets for multiple projects, use separate objects. 
            bws_access_token (str, optional): If not provided, will check if the environment variable is set and use
                that. Supplied in CLI calls with the `-t` option. Defaults to None.
            bws_path (str, optional): Path to call `bws` or `bws.exe` application. Defaults to 'bws', which works if
                the parent directory is in your system's PATH variable.
        """
        self._set_token(bws_access_token=bws_access_token)
        self._BWS_APPLICATION_PATH = Path(bws_path)
        self._PROJECT_NAME = project_name
        self._PROJECT_ID = self._get_project_id()
        self._SECRETS = self._get_secrets_from_bws()

        logger.info(f'Using Bitwarden Secrets Manager application at: {bws_path}')

    def __getitem__(self, key):
        return self._SECRETS[key]

    def __len__(self):
        return len(self._SECRETS)

    def __contains__(self, item):
        return item in self._SECRETS

    def _set_token(self, bws_access_token:str|None) -> None:
        """ If a bws_access_token is not provided, check is one is already set as an environment variable.

        Args:
            bws_access_token (str | None): Provide if not already set as BWS_ACCESS_TOKEN environment variable.

        Raises:
            ValueError: No BWS_ACCESS_TOKEN provided or set as environment variable.
        """
        if bws_access_token:
            self._TOKEN = bws_access_token
        elif 'BWS_ACCESS_TOKEN' in os.environ:
            logger.info('Using BWS_ACCESS_TOKEN already set as environment variable.')
            self._TOKEN = os.environ['BWS_ACCESS_TOKEN']
        else:
            raise ValueError('No BWS_ACCESS_TOKEN provided or set as environment variable.')

    def _get_project_id(self) -> str:
        """ Gets the project's ID from the project name provided in the constructor.

        Raises:
            ValueError: Project name not found.

        Returns:
            str: Project ID
        """
        projects:list[dict] = self.call_and_return_text(cl_args=['list', 'projects'], #print_to_console=True,
                                                        as_json=True)
        for project in projects:
            if project['name'] == self._PROJECT_NAME:
                return project['id']
        raise ValueError(f'Project "{self._PROJECT_NAME}" not found. Choose from projects: '
                         f'{[p["name"] for p in projects]}')

    def _make_call(self, cl_args:list, check:bool=True) -> subprocess.CompletedProcess:
        """ Make a call to `bws` with the provided args. Usually use self.call_and_return_text() instead of this.

        Args:
            cl_args (list): Args in list format (e.g. ['list', 'projects'])
            check (bool, optional): If true, raises exception on failure. Defaults to True.

        Returns:
            subprocess.CompletedProcess: Call results. (Use .stdout and .stderr to get text results.)
        """
        try:
            return subprocess.run([self._BWS_APPLICATION_PATH] + cl_args + ['-t', self._TOKEN], capture_output=True,
                                  text=True, check=check)
        except subprocess.CalledProcessError as cpe:
            logger.critical(f'CalledProcessError: {cpe.stderr}')
            logger.critical('Note: access_token value redacted from list of commands in exception raised below:')
            cpe.cmd.pop() # remove the access_token value
            raise cpe

    def _get_secrets_from_bws(self, full_detail:bool=False) -> list[dict] | dict[str,str]:
        """ Get list of all secrets from `bws` CLI.

        Returns:
            list[dict] | dict[str,str]: List of "secret" objects if full_detail=True, else dict[key,value].
        """
        secrets = self.call_and_return_text(cl_args=['list', 'secrets', self._PROJECT_ID], as_json=True)
        return secrets if full_detail else {secret['key']: secret['value'] for secret in secrets}

    def call_and_return_text(self, cl_args:list, print_to_console=False, as_json:bool=False) -> str|dict|list:
        """ Make a call to `bws`.

        Args:
            cl_args (list): Args in list format (e.g. ['list', 'projects']). Supply each word or option as a separate
                list item.
            print_to_console (bool, optional): Call print() on the stdout results. Defaults to False.
            as_json (bool, optional): Return the results converted to JSON. Defaults to False.

        Returns:
            str|dict|list: stdout
        """
        text:str = self._make_call(cl_args=cl_args).stdout
        if print_to_console:
            print(text)
        return json.loads(text) if as_json else text

    def items(self) -> list[tuple[str,str]]:
        """ Get all secret key/values in a dict-like items() call. 

        Returns:
            list[tuple[str,str]]: List of secrets like [(key, value)].
        """
        return self._SECRETS.items()

    def as_dict(self) -> dict[str,str]:
        """ Get the internal _secrets dict containing all project secrets.

        Returns:
            dict[str,str]: Internal _secrets object.
        """
        return self._SECRETS

    def help(self, print_to_console=True) -> str:
        """ `bws` -h (help) command.

        Args:
            print_to_console (bool, optional): Defaults to True.

        Returns:
            str: Console output as string.
        """
        return self.call_and_return_text(cl_args=['-h'], print_to_console=print_to_console)

    def version(self, print_to_console=True) -> str:
        """ `bws` -V (version) command.

        Args:
            print_to_console (bool, optional): Defaults to True.

        Returns:
            str: Console output as string.
        """
        return self.call_and_return_text(cl_args=['-V'], print_to_console=print_to_console)
