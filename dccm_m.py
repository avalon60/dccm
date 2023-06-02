"""Database Client Connection Manager"""
# Control
__title__ = 'Database Client Connection Manager (Module Component: MVC)'
__author__ = 'Clive Bostock'
__version__ = "2.4.0"

from configparser import ConfigParser
import oracledb as odb
from pathlib import Path
import json
import sqlite3
import platform
import os
from os.path import exists
from os.path import expanduser

from zipfile import ZipFile
# from tkfontawesome import icon_to_image
import re
import socket
import subprocess
import oci
from oci.config import from_file
import hashlib
from kellanb_cryptography import aes, key
import shutil
from shutil import which
import base64

ENCODING = 'utf-8'

TOOLTIP_DELAY = 1

try:
    tns_admin = Path(os.environ["TNS_ADMIN"])
except KeyError:
    tns_admin = None

try:
    oracle_home = Path(os.environ["ORACLE_HOME"])
except KeyError:
    oracle_home = None

if tns_admin is None and oracle_home is not None:
    tns_admin = oracle_home / 'network/admin'

prog_path = os.path.realpath(__file__)
prog = os.path.basename(__file__)
# Get the data location, required for the config file etc
app_home = Path(os.path.dirname(os.path.realpath(__file__)))
data_location = app_home / 'data'
images_location = app_home / 'images'
temp_location = app_home / 'tmp'

# The temp_tns_admin folder is reserved for unpacking wallets, so that
# python-oracledb can be used to test database connections.
temp_tns_admin = temp_location / 'tns_admin'
themes_location = app_home / 'themes'

# Set the default export file names for connection and settings exports respectively.
base_prog = prog.replace(".py", "")
connection_export_default = f'{base_prog}_exp.json'
settings_export_default = f'{base_prog}_preferences_backup.json'

if not exists(data_location):
    os.mkdir(data_location)

if not exists(temp_location):
    os.mkdir(temp_location)

if not exists(temp_tns_admin):
    os.mkdir(temp_tns_admin)


def base64_file(file_path: str):
    """Generate a base64, UTF8 string from binary file content."""
    with open(file_path, 'rb') as open_file:
        byte_content = open_file.read()
    base64_bytes = base64.b64encode(byte_content)
    # Convert to a character string
    base64_string = base64_bytes.decode(ENCODING)
    return base64_string


def unpack_base64_to_file(base64_string: str, file_pathname: str):
    """Take a string which wraps base64, and convert it back to binary, then write it to the specified file.
    :param base64_string: str
    :param file_pathname: str
    """
    # Convert our string back to our raw base64 bytes
    base64_bytes = bytes(base64_string, ENCODING)
    # Decode the base64 to raw bytes
    file_bytes = base64.decodebytes(base64_bytes)
    with open(file_pathname, 'wb') as binary_file:
        binary_file.write(file_bytes)


def kb_encrypt(data: str, kb_password: str):
    """The kb_encrypt function accepts a data string and encrypts it based upon a password, returning the encrypted
    string. """
    encryption_key = key.gen_key_from_password(kb_password)  # generate a key
    encrypted = aes.encrypt_aes(data, encryption_key)  # encrypt text
    return encrypted


def kb_decrypt(encrypted_data: str, kb_password: str):
    """The kb_encrypt function accepts an encrypted data string (encrypted using the kb_encrypt function) and
    decrypts it using the supplied password, returning the decrypted string.

    :param encrypted_data:
    :param kb_password:
    :return: decrypted data string"""
    encryption_key = key.gen_key_from_password(kb_password)  # generate a key
    decrypted_data = aes.decrypt_aes(encrypted_data, encryption_key)  # decrypt
    return decrypted_data


b_prog = prog.replace(".py", "")
db_file = Path(f'{data_location}' + f'/.dccm.db')


def command_found(command: str):
    """Check whether command is on the PATH O/S variable or that it can be found directly.
    :param command: (str) Command or pathname to a command
    :return: bool
    """
    # If this is a full-blown command, with arguments, separate out the command.
    cmd = command.split(' ')[0]
    cmd = cmd.strip()
    if cmd == 'start':
        operating_system = platform.system()
        if operating_system == 'Windows':
            return True
    if exists(cmd):
        return True
    return which(cmd) is not None


def sqlite_dict_factory(cursor, row):
    """The sqlite_dict_factory (SQL dictionary factory) method converts a row from a returned sqlite3  dataset
    into a dictionary, keyed on column names.

    :param cursor: sqlite3 cursor
    :param row: list
    :return: dict"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def dict_substitutions(string: str, dictionary: dict, none_substitution: str = ''):
    """The dict_substitutions function, accepts a string, which includes substitution placeholders (strings enclosed
    by 2 # characters) along with a dictionary of values. It scans the keys of the dictionary, and we assume that at
    least one of these is included as a substitution string in the string supplied, It replaces the delimited string
    with the corresponding value from the dictionary.

    :param string: String which includes substitution placeholders.
    :param dictionary: Dictionary used to match substitution placeholders and source the substitution values.
    :return: substituted (edited) string
    :param none_substitution: str"""
    for variable in dictionary.keys():
        substitution_string = str(dictionary[variable])
        if substitution_string == 'None':
            substitution_string = none_substitution
        string = string.replace(f'#{variable}#', substitution_string)
    return string


def system_id():
    operating_system = platform.system()
    if operating_system == 'Darwin':
        command = "ioreg -d2 -c IOPlatformExpertDevice"
        ioreg_cmd = subprocess.run(["ioreg", "-d2", "-c", "IOPlatformExpertDevice"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #  awk -F\" '/IOPlatformUUID/{print $(NF-1)}'
        awk_cmd = subprocess.run(["awk", '-F\"', "'/IOPlatformUUID/{print $(NF-1)}'"],
                                 input=ioreg_cmd.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        system_uid = awk_cmd.stdout.decode()
    elif operating_system == 'Windows':
        # wmic path win32_computersystemproduct get UUID
        wmic_cmd = subprocess.run(["wmic", "path", "win32_computersystemproduct", "get", "UUID"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        system_uid = str(wmic_cmd.stdout.decode())
        system_uid = system_uid.replace('UUID ', '').replace('\r', '').replace('\n', '').replace(' ', '')
    elif operating_system == 'Linux':
        cat_cmd = subprocess.run(["cat", "/etc/machine-id"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        system_uid = cat_cmd.stdout.decode()
    else:
        system_uid = '&8*00ae0)19GfsBEAFA987612'
    return system_uid


def oci_secret(config_file_pathname: Path, oci_profile: str, secret_id: str):
    """The oci_secret function, accepts the pathname to the user's OCI config file, along with the OCI Profile,
    and a secret OCID,  required to retrieve the secret (password) from an OCI vault.

    :param config_file_pathname: User's OCI config file pathname.
    :param oci_profile: User's OCI profile (entry in the config file)
    :param secret_id: The OCID associated with the required secret.
    :return: A string - the secret/password."""
    config = from_file(file_location=config_file_pathname, profile_name=oci_profile)
    secrets_client = oci.secrets.SecretsClient(config)
    secret_base64 = secrets_client.get_secret_bundle(secret_id).data.secret_bundle_content
    secret = secret_base64.__getattribute__("content")
    content_type = secret_base64.__getattribute__("content_type")
    if content_type == "BASE64":
        # Include a decode, otherwise we get a byte string, which upsets oracledb.
        return base64.b64decode(secret).decode()
    else:
        return secret


def port_is_open(host: str, port_number: int):
    """Function to check port, to see whether it is open. We can use this to check,
    whether a database host is reachable.

    :param host: Host / IP Address of the database listener (localhost for ssh tunnelling).
    :param port_number: The port used to access the database (listener or local ssh port).
    :return: Returns boolean True if the server is accessible via the specified port."""

    # Create a new socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if host == 'localhost':
        host = '127.0.0.1'
    # Attempt to connect to the given host and port
    try:
        if sock.connect_ex((host, port_number)) == 0:
            return True
        else:
            return False
    except socket.gaierror:
        # print(f'ERROR: Socket error: socket.gaierror: {host} / {port_number}')
        return False
    # Close the connection
    sock.close()


def dump_preferences(db_file_path: Path):
    """The dump_preferences function is here for debugging purposes."""
    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()
    cur.execute("select preference_name, "
                "preference_value, "
                "preference_attr1, "
                "preference_attr2, "
                "preference_attr3, "
                "preference_attr4, "
                "preference_attr5 "
                "from preferences;")
    preferences = cur.fetchall()
    db_conn.close()
    print(f'DBG: Preferences dump: {preferences}')


def backup_preferences(save_file_name: Path):
    """The backup_preferences function, creates a JSON file containing all user preferences, including anyfInitial Di
    SSH tunnelling templates etc, created by the user."""
    prefs_list = preferences_dict_list(db_file_path=db_file)
    entry_count = len(prefs_list)
    feedback = []
    feedback.append(f'Starting preferences backup to {save_file_name}.')
    feedback.append(f'Exporting {entry_count} preference rows.')
    # os.chdir(app_home)
    try:
        with open(save_file_name, "w") as f:
            json.dump(prefs_list, f, indent=2)
        feedback.append(f'Export complete.')
    except IOError:
        feedback = f'Failed to write file {save_file_name} - possible a permissions or free space issue.'
    return feedback


def restore_preferences(restore_file_name: Path):
    """The restore_preferences function, reads a JSON preferences backup file, containing user
    preferences. It then updates them to the DCCM database preferences table."""
    with open(restore_file_name) as json_file:
        try:
            import_json = json.load(json_file)
        except ValueError:
            print(f'The file, "{restore_file_name}", does not appear to be a valid '
                  f'export file (JSON parse error).')
            exit(1)
        except IOError:
            feedback = f'Failed to read file {restore_file_name} - possible permissions issue.'

    entry_count = len(import_json)
    feedback = [f'Starting preferences restore from  {restore_file_name}.', f'Restoring {entry_count} preference rows.']
    for row in import_json:
        scope = row["scope"]
        preference_name = row["preference_name"]
        preference_value = row["preference_value"]
        preference_label = row["preference_label"]
        upsert_preference(db_file_path=db_file,
                          scope=scope,
                          preference_name=preference_name,
                          preference_value=preference_value,
                          preference_label=preference_label)
    feedback.append(f'Restore complete.')
    return feedback


def test_db_connection(username: str, password: str, connect_string: str, wallet_pathname: str = ''):
    """Accept a  database connect string and credentials, and test a database connection. We optionally accept a wallet,
    in which case we unpack it and make a call to init_oracle_client, to set a temporary TNS Admin location, for the
    purposes of the test."""
    if wallet_pathname:
        unpack_wallet(wallet_pathname)
        # init_oracle_client can only be called once per program session,
        # otherwise we get:
        #    cx_Oracle.ProgrammingError: Oracle Client library has already been initialized
        try:
            odb.init_oracle_client(config_dir=str(temp_tns_admin))
        except odb.ProgrammingError:
            pass
    try:
        connection = odb.connect(user=username, password=password,
                                 dsn=connect_string, encoding="UTF-8")
    except odb.DatabaseError as db_error:
        return 'Connection failed: ' + str(db_error)
    connection.close()
    return 'Connection succeeded!'


def unpack_wallet(wallet_pathname: Path):
    """"The unpack_wallet function, is provided for testing the database connections via a cloud wallet. In
    such cases the wallet must be unpacked for use by python-oracledb.
    The wallet is unpacked to the program's temp TNS admin directory, defined by temp_tns_admin.
    :param wallet_pathname: Path
    """
    with ZipFile(wallet_pathname, 'r') as zip_ref:
        zip_ref.extractall(temp_tns_admin)

    # We now need to edit the temporary sqlnet.ora file, to reflect our temporary config dir:
    sqlnet = Path(f'{temp_tns_admin}/sqlnet.ora').read_text()
    sqlnet = sqlnet.replace('DIRECTORY="?/network/admin"', f'DIRECTORY="{temp_tns_admin}"')
    with open(f'{temp_tns_admin}/sqlnet.ora', 'w') as f:
        f.write(sqlnet)


def preferences_dict_list(db_file_path: Path):
    """The preferences_dict_list function, extracts all preferences entries as a list of dictionary entries. Each
    dictionary entry represents a row from the preferences table.

    :param db_file_path: Pathname to the sqlite3 database.
    :return list: List of preferences dictionaries.
    """
    db_conn = sqlite3.connect(db_file_path)
    db_conn.row_factory = sqlite_dict_factory
    cur = db_conn.cursor()
    cur.execute("select scope, "
                "preference_name, "
                "preference_value, "
                "preference_label, "
                "preference_attr1, "
                "preference_attr2, "
                "preference_attr3, "
                "preference_attr4, "
                "preference_attr5 "
                "from preferences "
                "order by scope, preference_name;")
    preferences = cur.fetchall()
    db_conn.close()
    return preferences


def preference(db_file_path: Path, scope: str, preference_name):
    """The preference function accepts a preference scope and preference name, and returns the associated preference
    value.
    :param db_file_path (Path): Pathname to the DCCM database file.
    :param scope (str): Preference scope / domain code.
    :param preference_name (str): Preference name.
    :return (str): The preference value"""
    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()

    cur.execute("select preference_value "
                "from preferences "
                "where scope = :scope "
                "and preference_name = :preference_name;", {"scope": scope, "preference_name": preference_name})
    preference_value = cur.fetchone()
    if preference_value is not None:
        preference_value, = preference_value
    db_conn.close()
    return preference_value


def purge_temp_tns_admin():
    """The purge_temp_location function, clears down the contents of the DCCM temp_location/tns_admin folder."""
    try:
        shutil.rmtree(temp_tns_admin, ignore_errors=False, onerror=None)
    except FileNotFoundError:
        # We found no files to delete, so do nothing.
        pass


def delete_preference(db_file_path: Path, scope: str, preference_name):
    """The preference function accepts a preference scope and preference name, and deleted the associated preference
    record from the DCCM database.

    :param db_file_path: Database file pathname.
    :param scope: Preference scope / domain code.
    :param preference_name: Preference name."""
    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()

    cur.execute("delete "
                "from preferences "
                "where scope = :scope "
                "and preference_name = :preference_name;", {"scope": scope, "preference_name": preference_name})
    db_conn.commit()
    db_conn.close()


def preferences_scope_list(db_file_path: Path, scope: str):
    """The preferences function, returns a list of lists. The inner lists, each represent a row from the preferences
    table, which are matched based on the scope passed to the function.

    :param db_file_path:
    :param scope: The scope/domain to base the list of preferences upon.
    :return: List - each entry is in turn a list, representing a returned row."""
    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()
    cur.execute("select preference_name, "
                "preference_value, "
                "preference_attr1, "
                "preference_attr2, "
                "preference_attr3, "
                "preference_attr4, "
                "preference_attr5 "
                "from preferences "
                "where scope = :scope "
                "order by preference_name;", {"scope": scope})
    preferences = cur.fetchall()
    db_conn.close()
    list_of_preferences = []
    # We have a list of tuples; each tuple, representing a row.
    for row in preferences:
        record = []
        for column in row:
            record.append(column)
        list_of_preferences.append(record)
    return list_of_preferences


def preferences_scope_names(db_file_path: Path, scope: str):
    """The preferences function, returns a list of lists. The inner lists, each represent a row from the preferences
    table, which are matched based on the scope/domain passed to the function.

    :param db_file_path: Pathname to the DCCM database file.
    :param scope: A string, defining the preference scope/domain.
    :return: List"""
    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()
    cur.execute("select preference_name "
                "from preferences "
                "where scope = :scope "
                "order by preference_name;", {"scope": scope})
    preferences = cur.fetchall()
    db_conn.close()
    list_of_preferences = []
    # We have a list of tuples; each tuple, representing a row.
    for row in preferences:
        list_of_preferences.append(row[0])
    return list_of_preferences


def upsert_preference(db_file_path: Path,
                      scope: str,
                      preference_name: str,
                      preference_value: str,
                      preference_label: str = ''):
    """The upsert_preference function operates as an UPSERT mechanism. Inserting where the preference does not exists,
    but updating where it already exists.

    :param db_file_path: Pathname to the DCCM database file.
    :param scope: A string, defining the preference scope/domain.
    :param preference_name: The preference withing the specified scope, to be inserted/updated.
    :param preference_value: The new value to set.
    :param preference_label: A label which is associated with the preference entry."""
    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()

    # Check to see if the preference exists.
    pref_exists = preference(db_file_path=db_file_path, scope=scope, preference_name=preference_name)

    if preference_label == '':
        preference_label = preference_name.replace('_', ' ').title()

    if pref_exists is None:
        # The preference does not exist
        if preference_label:
            cur.execute("insert  "
                        "into preferences (scope, preference_name, preference_value, preference_label) "
                        "values "
                        "(:scope, :preference_name, :preference_value, :preference_label);",
                        {"scope": scope, "preference_name": preference_name,
                         "preference_value": preference_value,
                         "preference_label": preference_label})
        else:
            cur.execute("insert  "
                        "into preferences (scope, preference_name, preference_value) "
                        "values "
                        "(:scope, :preference_name, :preference_value);",
                        {"scope": scope, "preference_name": preference_name,
                         "preference_value": preference_value})
    elif preference_label is None:
        # The preference does exist, so update it.
        cur.execute("update preferences  "
                    "set preference_value = :preference_value "
                    "where scope = :scope and preference_name = :preference_name;",
                    {"scope": scope, "preference_name": preference_name, "preference_value": preference_value})
    else:
        cur.execute("update preferences  "
                    "set preference_value = :preference_value, "
                    "    preference_label = :preference_label "
                    "where scope = :scope and preference_name = :preference_name;",
                    {"scope": scope,
                     "preference_name": preference_name,
                     "preference_value": preference_value,
                     "preference_label": preference_label})

    db_conn.commit()
    db_conn.close()


class DCCMModule:
    """Class to control our data management."""

    def __init__(self, app_home: Path, db_file_path: Path):

        # Set up the colours. These are optionally used for banner/connection text,
        # when connecting in command line mode.
        self.COLOUR_RESET = '\033[0m'
        self.BOLD = '\033[1m'
        self.UNDERLINE = '\033[4m'
        self.colours_dict = {
            "None": self.COLOUR_RESET,
            "Red": '\033[91m',
            "Green": '\033[92m',
            "Yellow": '\033[93m',
            "Blue": '\033[94m',
            "Magenta": '\033[95m',
            "Cyan": '\033[96m'
        }

        self.banner_options_list = ['None', 'WARNING !', 'INFO :']

        self.app_home = app_home
        self.app_images = self.app_home / 'images'
        self.app_configs = self.app_home / 'config'
        self.app_themes_dir = self.app_home / 'themes'
        self.etc = self.app_home / 'etc'
        self.db_file_path = db_file_path
        self.db_conn = sqlite3.connect(db_file_path)
        # NOTE: Unlike the preferences table interactions, here we use a cursor factory.
        #       This allows us to manifest connections row data as dictionary objects.
        self.db_conn.row_factory = sqlite_dict_factory
        self.cur = self.db_conn.cursor()

        self.valid_database_types = ["Oracle"]
        self.valid_connection_types = self.connection_type_list()

        self.client_tools_dict = self.client_tools_as_dict()
        pass

    def color_code(self, colour):
        if colour is None:
            return self.colours_dict['None']
        else:
            return self.colours_dict[colour]

    def colour_list(self):
        return list(self.colours_dict.keys())

    def banner_options(self):
        return self.banner_options_list

    def connection_type_list(self):
        """The connection_type_list method, returns a list of all the database connection/management types/categories.
        This is used in the DCCM connection creation/modification window."""
        config_pathname = preference(db_file_path=self.db_file_path,
                                     scope="preference",
                                     preference_name="oci_config")
        if config_pathname:
            self.default_connection_type = "OCI Vault"
            valid_connection_types = ["OCI Vault", "Legacy"]
        else:
            self.default_connection_type = "Legacy"
            valid_connection_types = ["Legacy"]
        return valid_connection_types

    def app_theme(self):
        """The app_theme method retrieves and returns the name of the theme, stored in the app preferences table.

        :return: String - the preferred app theme.
        """
        app_theme = preference(db_file_path=self.db_file_path,
                               scope='preference',
                               preference_name="app_theme")
        if app_theme is None:
            app_theme = 'GreyGhost'

        return app_theme

    def app_appearance_mode(self):
        """Determines the application (CustomTkinter compliant) theme appearance mode (Dark/Light/System....) to use.

        :return: String - the preferred app appearance mode.
        """
        app_appearance_mode = preference(db_file_path=self.db_file_path, scope="preference",
                                         preference_name="app_appearance_mode")

        if app_appearance_mode is None:
            app_appearance_mode = 'System'
        return app_appearance_mode

    def tooltips_enabled(self):
        """The tooltips_enable, is used to determine whether tooltips are enabled, based on user preference.

        :return: integer - 0 implies tooltips are disabled, and 1 implied that tooltips are enabled.
        """
        enable_tooltips = preference(db_file_path=self.db_file_path, scope="preference",
                                     preference_name="enable_tooltips")

        if enable_tooltips is None:
            enable_tooltips = 1
        return int(enable_tooltips)

    def connection_password(self, connection_id):
        """For a given connection identifier, resolve the database password and return it as a string.
        :param connection_id: str
        :return password: str
        """
        connection_record = self.connection_record(connection_id)
        connection_type = connection_record['connection_type']
        db_account_name = connection_record['db_account_name']
        connect_string = connection_record['connect_string']
        oci_profile = connection_record['oci_profile']
        ocid = connection_record['ocid']

        if connection_type == 'OCI Vault':
            oci_config = Path(preference(db_file_path=self.db_file_path,
                                         scope='preference',
                                         preference_name='oci_config'))

            password = oci_secret(config_file_pathname=oci_config,
                                  oci_profile=oci_profile,
                                  secret_id=ocid)
            password = str(password, encoding='ascii')
        else:
            password = ocid
        return password

    def formulate_connection_launch(self, connection_identifier, mode="gui", script_name=None):
        """The formulate_connection_launch method, accepts a connection identifier and formulates the command
        required to launch the SQL client, taking into account, whether we are running in GUI mode / O/S etc. The
        command, once formulated, is returned as the 2nd string component of two piece tuple. The first component is
        a status message string. This only contains text if an error is detected.

        :param connection_identifier:
        :param mode:  string ("command", "gui" or "plugin")
        :param script_name: Optional SQL script pathname, to execute.
        :return: String - the formulated command."""
        operating_system = platform.system()
        connection_record = self.connection_record(connection_identifier)
        database_type = connection_record["database_type"]
        connection_type = connection_record['connection_type']
        db_account_name = connection_record['db_account_name']
        connect_string = connection_record['connect_string']
        oci_profile = connection_record['oci_profile']
        ocid = connection_record['ocid']

        return_status = ''

        if connection_type == 'OCI Vault':
            if not ocid:
                return f'No OCID defined for connection "{connection_identifier}, please rectify."', ''
            oci_config = Path(preference(db_file_path=self.db_file_path,
                                         scope='preference',
                                         preference_name='oci_config'))

            password = oci_secret(config_file_pathname=oci_config,
                                  oci_profile=oci_profile,
                                  secret_id=ocid)
            # password = str(password, encoding='ascii')
        else:
            if not ocid:
                return f'No password defined for connection "{connection_identifier}, please rectify."', ''
            password = ocid
        wallet_required_yn = connection_record['wallet_required_yn']
        wallet_location = connection_record['wallet_location']
        client_tool = connection_record["client_tool"]

        # We have the client tool (user friendly) name, now look up the associated command
        client_command = self.client_command(client_tool_name=client_tool)

        if not client_command:
            return_status = f'Client command, "{client_tool}", referenced by this connectionn has not been configured.' \
                            f'\nPerhaps this connection was imported from another DCCM repository?\nYou can ' \
                            f'configure bespoke client tools, via the Tools > Client Tools dialog.'
            return return_status, client_command

        # Grab the command from the command line and check whether we can find it.
        if not command_found(client_command):
            return_status = f'ERROR: The configured client command, "{client_command}", for this connection cannot be ' \
                            f'located.\nPlease ensure that the client tool is locatable via the O/S PATH variable or' \
                            f'if using a full pathname, that it is valid.'
            return return_status, client_command

        if client_command is None:
            return_status = f'The connection id, {connection_identifier}, has no valid client tool association. ' \
                            f'Incomplete migration?'
            return return_status, client_command
        # Add a username synonym for db_account_name
        connection_record["username"] = connection_record["db_account_name"]

        # Add the password to the connection record, in case it's needed for substitution.
        connection_record["password"] = password

        # Add the script_name to the connection record, in case it's needed for substitution.
        if script_name is not None:
            connection_record["script_name"] = script_name

        # Now make any placeholder / keyword substitutions
        client_command = dict_substitutions(string=client_command, dictionary=connection_record, none_substitution='')
        if operating_system == 'Darwin':
            client_command = '`which ' + client_command + '`'

        if wallet_required_yn == 'Y':
            # wallet_pathname = Path('./tmp') / os.path.basename(wallet_location)
            wallet_pathname = Path(wallet_location)
            cloudconfig = f'-cloudconfig {wallet_pathname}'
        else:
            cloudconfig = ''

        if client_tool == 'SQLcl' and mode != 'plugin':
            client_command = f'{client_command} {cloudconfig} {db_account_name}/{password}@{connect_string}'
        elif client_tool == 'SQLcl':
            client_command = f'{client_command} -S {cloudconfig} {db_account_name}/{password}@{connect_string}'

        if script_name is not None:
            if client_tool == 'SQLcl':
                client_command = f'{client_command} @{script_name}'

        if mode == 'gui':
            if operating_system == 'Darwin':
                temp_file = f'{temp_location}/sql.sh'
                with open(temp_file, "w") as f:
                    f.write(client_command)
                os.system(f'chmod 750 {temp_file}')
                return '', f'open -a Terminal.app {temp_file}'
            elif operating_system == 'Windows':
                client_command = f'start cmd /c {client_command}'
                return '', client_command
            elif operating_system == 'Linux':
                client_command = f'gnome-terminal -- bash -c "{client_command}"'
                return '', client_command
            else:
                print(f'WARNING: Unrecognised operating system: {operating_system}')
                print(f'Attempting a basic launch...')
        return '', client_command

    def formulate_ssh_launch(self, connection_id: str, mode: str = 'command'):
        """The formulate_ssh_launch method, accepts a connection identifier and formulates the command
        required to launch the ssh tunnelling command. The ssh command is based upon an ssh template associated with the
        supplied connection_id. This works in a similar fashion, to the formulate_connection_launch function. The
        function returns a two part tuple, of status text (empty string if no errors are encountered) and the formulated
        ssh command.

        :param connection_id:
        :param mode: str ('command' / 'gui')
        :return: A string containing the ssh tunneling command."""
        operating_system = platform.system()
        connection_record = self.connection_record(connection_identifier=connection_id)
        if connection_record is None:
            return_status = f'Invalid connection identifier: "{connection_id}"'
            return return_status, ''
        host, listener_port = self.resolve_connect_host_port(connection_name=connection_id)

        if not command_found('ssh'):
            return_status = f'ERROR: The ssh command, required for this connection cannot be ' \
                            f'located.\nPlease ensure that ssh is installed and is locatable via the O/S PATH variable.'
            return return_status, ''
        connection_record = self.connection_record(connection_identifier=connection_id)
        template_code = connection_record["ssh_tunnel_code"]
        database_host, local_port = self.resolve_connect_host_port(connection_name=connection_id)
        listener_port = connection_record["listener_port"]
        ssh_dict = {"database_host": database_host, "listener_port": listener_port, "local_port": local_port}
        template = preference(db_file_path=db_file,
                              scope='ssh_templates',
                              preference_name=template_code)
        if template is None:
            status_text = f'The SSH tunneling template, "{template_code}", referenced by "{connection_id}", ' \
                          f'no longer exists. This may be as a result of an incomplete executed migration ' \
                          f'(preferences not restored). Please rectify and try again.'
            return status_text, ''
        ssh_command = dict_substitutions(template, ssh_dict)

        if mode == 'gui':
            if operating_system == 'Darwin':
                temp_file = f'{temp_location}/ssh.sh'
                with open(temp_file, "w") as f:
                    f.write(ssh_command)
                os.system(f'chmod 750 {temp_file}')
                return '', f'open -a Terminal.app {temp_file}'
            elif operating_system == 'Windows':
                ssh_command = f'start cmd /c {ssh_command}'
                return '', ssh_command
            else:  # operating_system == 'Linux'
                ssh_command = f'gnome-terminal -- bash -c "{ssh_command}"'
                return '', ssh_command

        enable_ancillary_ssh_window = preference(db_file_path=db_file,
                                                 scope='preference',
                                                 preference_name='enable_ancillary_ssh_window')

        # We need to take extra care here. The user may not have visited the Preferences yet and saved the
        # 'enable_ancillary_ssh_window' setting, and so we need to handle the NoneType which may have been
        # returned above.
        if enable_ancillary_ssh_window is None:
            enable_ancillary_ssh_window = 0
        else:
            enable_ancillary_ssh_window = int(enable_ancillary_ssh_window)

        # If we get to this point, we are either in "command" or "plugin" mode.
        if operating_system == 'Windows' and enable_ancillary_ssh_window:
            # If this is Windows, there are no options for backgrounding SSH tunnelling commands,
            # and so we provide second command window to launch a dccm client connection.
            ssh_command = f'start; {ssh_command}'
        elif operating_system == 'Linux' and enable_ancillary_ssh_window:
            working_directory = os.getcwd()
            ssh_command = f'gnome-terminal; {ssh_command}'
        elif operating_system == 'Darwin' and enable_ancillary_ssh_window:
            working_directory = os.getcwd()
            ssh_command = f'open -a Terminal.app {working_directory}; {ssh_command}'
        return '', ssh_command


    def default_connection(self):
        """Get the user's default connection identifier.
        :return string:
        """
        default_connection = preference(db_file_path=self.db_file_path,
                                        scope='preference',
                                        preference_name='default_connection')

        # Check that the current connection still exists (it may have been deleted,
        # since it was set as the preferred connection.
        connection_exists = self.connection_record(default_connection)
        if connection_exists:
            return default_connection
        else:
            return None

    def client_command(self, client_tool_name: str):
        """Formulate, and return, the client command associated with the specified client tool name. We store 
        the client tools as hidden preferences (scope = "client_tools")

        :param client_tool_name: str
        :return: str"""
        client_tool = preference(db_file_path=self.db_file_path, scope='client_tools', preference_name=client_tool_name)
        return client_tool

    def client_tools_as_dict(self):
        """Obtain and return a dictionary the client tools (stored in preferences under the domain of "client_tools").
        The dictionary is keyed upon the client tool id, which is the displayable value in dropdown lists.

        :return: dict"""
        records = preferences_scope_list(db_file_path=self.db_file_path, scope='client_tools')
        client_identifiers_dict = {}
        for record in records:
            client_identifiers_dict[record[0]] = record[1]
        return client_identifiers_dict

    def client_tools_name_list(self):
        """The client_tools_name_list method, returns a list of all the SQL client tool names stored as
        preference entries.

        :return: list"""
        self.client_tools_dict = self.client_tools_as_dict()
        client_tools_names = list(self.client_tools_dict.keys())
        return client_tools_names

    def connection_identifiers_list(self):
        """The connection_identifiers_list method, returns a list of all the connection identifiers. These are
        retrieved from the connections table.

        :return: list"""
        self.cur.execute("select connection_identifier "
                         "from connections "
                         "order by connection_identifier;")
        connections = self.cur.fetchall()
        connection_identifiers_list = []
        # Our records come back as a list of tuples.
        # Let's unpack them...
        for connection in connections:
            connection_name = connection["connection_identifier"]
            connection_identifiers_list.append(connection_name)
        return connection_identifiers_list

    def connections_dict(self):
        """The connections dict method, generates a dictionary, of all connections, keyed on connection_identifier.

        :return dict:
        """
        connections_dict = {}
        for connection in self.connection_identifiers_list():
            connection_record = self.connection_record(connection)
            # Remove the connection key from the record, since this
            # will be used as our new dictionary key.
            connection_record.pop("connection_identifier")
            connections_dict[connection] = connection_record
        return connections_dict

    def export_connections(self, dump_file: str,
                           run_mode: str,
                           connection_match: str = 'all',
                           password: str = '',
                           include_wallets: bool = False):

        """The export_connections method, services any export requests, either from the command line/plugin modes or
        more likely the gui interface.  A logfile is written, based upon the name of the specified import filename,
        where the (.json) file extension is replaced with "_exp.log".
        In non-GUI mode, feedback is returned in the form of a list of actions/decisions, whereas a terse summary
        (or error text)  is returned in GUI mode. Irrespective of whether the export is run in GUI mode or not, the
        feedback is written to the logfile.

        :param dump_file: Pathname to write the export file (str).
        :param run_mode: (str) defines whether DCCM is running in "command", "gui", or "plugin" mode.
        :param connection_match: (str) Exact match of connection name or 'all' (str)
        :param password: str
        :param include_wallets: (bool) Include wallet files in export (bool)
        :return: list (non-gui mode) / str (gui mode)"""
        connections_dict = {}
        export_count = 0
        feedback = []
        logfile = dump_file.replace('.json', '_exp.log')
        password_hash = None
        if str(connection_match).lower() == 'all':
            connections_dict = self.connections_dict()
        else:
            connections_dict = self.connection_record(connection_match)
            # Convert the dictionary to the same format as a multi-connection (ie "all")
            # dictionary. This is to make the import process easier.
            connection_name = connections_dict.pop("connection_identifier")
            connections_dict = {connection_name: connections_dict}
            feedback.append(f'Including connection, {connection_name}, to export...')

        feedback.append(f'Matching connections for: {connection_match}')
        if password:
            password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            feedback.append('Password supplied - connection passwords / secrets included and encrypted.')
        else:
            password_hash = ''
            feedback.append('Password not supplied - connection passwords / secrets, not included to export.')

        feedback.append('')
        # If a password is supplied, encrypt the secrets.
        if password:
            for connection, connection_dict in connections_dict.items():
                ocid = connections_dict[connection]["ocid"]
                # We need to first decrypt the ocid / password, which is encrypted
                # in our DCCM database. We can then encrypt based
                system_uid = system_id()
                connections_dict[connection]["ocid"] = kb_encrypt(data=ocid,
                                                                  kb_password=password)

                if include_wallets and connections_dict[connection]["wallet_location"] and password:
                    base64_wallet = base64_file(file_path=connections_dict[connection]["wallet_location"])
                    base64_wallet = kb_encrypt(data=base64_wallet,
                                               kb_password=password)
                else:
                    base64_wallet = ''
                connections_dict[connection]["base64_wallet"] = base64_wallet

                feedback.append(f'Connection, "{connection}", successfully exported...')
                export_count += 1
        else:
            for connection, connection_dict in connections_dict.items():
                ocid = connections_dict[connection]["ocid"]
                connections_dict[connection]["ocid"] = ''

                if include_wallets and connections_dict[connection]["wallet_location"] and password:
                    base64_wallet = base64_file(file_path=connections_dict[connection]["wallet_location"])
                else:
                    base64_wallet = ''
                connections_dict[connection]["base64_wallet"] = base64_wallet

                export_count += 1

        export_header = {"data_source": 'dccm.py',
                         "version": __version__,
                         "export_match": connection_match,
                         "password_hash": password_hash}
        export_dict = [export_header, connections_dict]
        try:
            with open(dump_file, "w") as f:
                json.dump(export_dict, f, indent=2)
        except IOError:
            feedback.append(f'Failed to write file {dump_file} - possible a permissions or free space issue.')
            return
        feedback.append('')
        feedback.append(f'Export completed with {export_count} connections, and written to {dump_file}.')

        with open(logfile, 'w') as lf:
            for item in feedback:
                # write each item on a new line
                lf.write("%s\n" % item)

        if run_mode == 'gui':
            return f'{export_count} connections exported, logfile written to {logfile}.'
        else:
            return feedback

    def import_connections(self, dump_file: str,
                           run_mode: str,
                           password: str,
                           connection_match: str = 'all',
                           merge_connections: bool = False,
                           remap_wallet_locations: bool = True,
                           import_wallets: bool = False):
        """The import_connections method, services any import requests, either from the command line/plugin modes or
        more likely the gui interface. A logfile is written, based upon the name of the specified import filename, where
        the (.json) file extension is replaced with "_imp.log".

        Wallets are only imported where a default wallet location has been configured via the preferences option.

        In non-GUI mode, feedback is returned in the form of a list of actions/decisions, whereas a terse summary
        (or error text)  is returned in GUI mode. Irrespective of whether the import is run in GUI mode or not, the
        feedback is written to the logfile.


        :param dump_file: str
        :param run_mode: (str) defines whether DCCM is running in "command", "gui", or "plugin" mode.
        :param connection_match: str
        :param password: str
        :param merge_connections: bool
        :param remap_wallet_locations: bool
        :param import_wallets: (bool)
        :return: list (non-gui mode) / str (gui mode)"""

        feedback = []
        if not exists(dump_file):
            feedback.append(f'The connections export file, "{dump_file}", cannot be found.')
            feedback.append(f'Please rectify and try again.')
            return feedback
        logfile = dump_file.replace('.json', '_imp.log')
        with open(dump_file) as json_file:
            connection_record = {}
            import_count = 0
            password_hash = ''
            try:
                import_json = json.load(json_file)
            except ValueError:
                feedback.append(f'The file, "{json_file}", does not appear to be a valid '
                                f'export file (JSON parse error).')
                return feedback
            except IOError:
                feedback = f'Failed to read export file {dump_file} - possible permissions issue.'

        # Now determine whether this is a native export or taken from SQL*Developer
        # The format of a native export, differs starkly from that of
        # SQl*Developer. A native export, appears as a list of 2 dictionaries (a header and body),
        # whereas that of SQL Developer is one dictionary.
        if len(import_json) == 2:
            password_hash = None
            if import_json[0]["data_source"] == 'dccm.py':
                source = 'native'
                header = import_json[0]
                exp_version = header["version"]
                body = import_json[1]
                if password_hash and not password:
                    feedback.append(
                        'Export is password protected and no password supplied - import operation terminated!')
                    return feedback

                password_hash = header["password_hash"]
                expected_password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
                if password_hash and expected_password_hash != password_hash:
                    if run_mode == 'gui':
                        return 'Invalid password supplied - import terminated!'
                    elif password_hash:
                        feedback.append('Invalid password supplied - import terminated!')
                        return feedback
        elif "connections" in import_json:
            source = "sql_developer"
            body = import_json
        else:
            feedback.append(f'The file {json_file} has an unrecognised format.')
            feedback.append('Deploying chute and bailing out!')
            if run_mode == 'gui':
                return f'The file {json_file} has an unrecognised format.'
            else:
                return feedback

        feedback.append(f'Matching connections for: {connection_match}')
        if merge_connections:
            feedback.append('Merge connections: enabled.')
        else:
            feedback.append('Merge connections: disabled.')

        if remap_wallet_locations:
            feedback.append('Wallet location remapping: enabled.')
        else:
            feedback.append('Wallet location remapping: disabled.')

        feedback.append('')
        if source == 'native':
            for connection_name, connection_dict in body.items():
                check_record = self.connection_record(connection_identifier=connection_name)
                if check_record and not merge_connections:
                    feedback.append(f'Connection, "{connection_name}", skipped - entry already exists, and '
                                    f'merge option not specified.')
                    continue
                connection_dict["connection_identifier"] = connection_name
                if connection_match.lower() != 'all' and connection_match != connection_name:
                    continue

                wallet_location = connection_dict["wallet_location"]
                default_wallet_directory = default_wallet_directory = preference(db_file_path=db_file,
                                                                                 scope='preference',
                                                                                 preference_name='default_wallet_directory')
                if remap_wallet_locations:
                    wallet_location = Path(os.path.basename(wallet_location.replace('\\', '/')))
                    wallet_location = default_wallet_directory / wallet_location
                else:
                    wallet_location = connection_dict["wallet_location"]

                if not default_wallet_directory and remap_wallet_locations:
                    feedback.append(
                        'ERROR: Cannot perform a default import without the default wallet location.')
                    feedback.append(
                        'ACTION: Either setup a default wallet location, via the application GUI, under '
                        'Tools > Preferences,')
                    feedback.append('        or use the "-I remap-off" option.')

                    if run_mode == 'gui':
                        return 'ERROR: Cannot perform a default import without the default wallet location.'
                    else:
                        return feedback

                if password and password_hash:
                    ocid = connection_dict["ocid"]
                    ocid = kb_decrypt(encrypted_data=ocid, kb_password=password)
                    connection_dict["ocid"] = ocid

                if remap_wallet_locations and connection_dict["wallet_required_yn"] == 'Y':
                    default_wallet_directory = default_wallet_directory.replace('\\', '/')
                    # Include replace here for dealing with '\\' in Windows paths - these break basename
                    wallet_basename = Path(os.path.basename(wallet_location))
                    wallet_location = default_wallet_directory / wallet_basename
                    connection_dict["wallet_location"] = str(wallet_location)
                    # We only allow wallets to be unpacked to a default wallet location, so we do this here.
                    base64_wallet = connection_dict["base64_wallet"]
                    if base64_wallet and import_wallets:
                        base64_wallet = kb_decrypt(encrypted_data=base64_wallet, kb_password=password)
                        feedback.append(f'Decoding wallet for connection, "{connection_name}", to default wallet '
                                        f'location, {default_wallet_directory}.')
                        unpack_base64_to_file(file_pathname=str(wallet_location), base64_string=base64_wallet)
                else:
                    connection_dict["wallet_location"] = ''

                if exp_version == '1.0.0':
                    connection_dict["ssh_tunnel_required_yn"] = 'N'
                    connection_dict["listener_port"] = ''
                    connection_dict["ssh_tunnel_code"] = ''
                    connection_dict["client_tool_options"] = ''

                self.upsert_connection(connections_record=connection_dict)
                feedback.append(f'Connection, "{connection_name}", successfully imported...')
                import_count += 1
        elif source == 'sql_developer':
            connections = import_json["connections"]
            for entry_dict in connections:
                info = entry_dict["info"]
                name = entry_dict["name"]
                check_record = self.connection_record(connection_identifier=name)
                if check_record and not merge_connections:
                    feedback.append(f'Connection, "{name}", skipped - entry exists and merge option '
                                    f'not specified.')
                    continue

                if info["RaptorConnectionType"] != 'Oracle':
                    print(f'Unsupported connection of type, {info["RaptorConnectionType"]} - skipped')
                    continue

                if not (connection_match.lower() == 'all' or connection_match == name):
                    continue
                connection_type = info.get("OracleConnectionType", '')
                connection_record["ssh_tunnel_required_yn"] = 'N'
                connection_record["listener_port"] = ''

                if connection_type == 'TNS':
                    connection_record["connect_string"] = info.get("customUrl", "")
                    connection_record["wallet_required_yn"] = "N"
                    connection_record["wallet_location"] = ''
                elif connection_type == 'CLOUD':
                    connection_record["wallet_required_yn"] = "Y"
                    connection_record["connect_string"] = info.get("customUrl", "")

                    wallet_location = info.get("sqldev.cloud.configfile", "")
                    if remap_wallet_locations:
                        default_wallet_directory = Path(preference(db_file_path=db_file,
                                                                   scope='preference',
                                                                   preference_name='default_wallet_directory'))
                        wallet_basename = Path(os.path.basename(wallet_location))
                        wallet_location = default_wallet_directory / wallet_basename
                    connection_record["wallet_location"] = str(wallet_location)
                else:
                    connection_record["wallet_required_yn"] = "N"
                    connection_record["wallet_location"] = ''
                    service_name = info.get("serviceName", "")
                    port = info.get("port", "")
                    hostname = info.get("hostname", "")
                    hostname = hostname.strip()
                    connect_string = f'{hostname}:{port}/{service_name}'
                    connection_record["connect_string"] = connect_string

                connection_record["client_tool"] = 'SQLcl'
                connection_record["connection_identifier"] = name
                connection_record["database_type"] = "Oracle"
                connection_record['connection_type'] = 'Legacy'
                connection_record['db_account_name'] = info["user"]
                connection_record['ocid'] = ''
                connection_record['oci_profile'] = ''
                connection_record["start_directory"] = ''
                connection_record["client_tool_options"] = ''
                connection_record["ssh_tunnel_code"] = ''
                connection_record["description"] = ''
                connection_record["ocid"] = 'Pwd update required.'

                status = self.upsert_connection(connections_record=connection_record)
                if status:
                    feedback.append(status)
                else:
                    import_count += 1
                    feedback.append(f'Connection, "{name}", successfully imported...')

        feedback.append('')
        feedback.append(f'Import from file, {dump_file} completed with {import_count} connections inserted / updated.')

        with open(logfile, 'w') as lf:
            for item in feedback:
                # write each item on a new line
                lf.write("%s\n" % item)

        if run_mode == 'gui':
            return f'{import_count} connections imported, logfile written to {logfile}.'
        else:
            return feedback

    def tns_names_alias_list(self):
        """The tns_names_alias_list method, interrogates the discovered tnsnames.ora file and produces a list of all
        the connection aliases, defined therein.

        :return: list"""
        if tns_admin is None:
            return []

        tns_dict = self.tns_names_aliases(tns_names_pathname=Path(tns_admin) / 'tnsnames.ora')
        return list(tns_dict.keys())

    def client_tool_template_usage(self, client_tool_code):
        """The client_tool_template_usage method, returns a list of all the connection identifiers which depend upon the
        presented client_tool_code. We use this to ensure we don't delete a tunnelling template which is in use.

        :return: list"""
        self.cur.execute("select connection_identifier "
                         "from connections "
                         "where client_tool = :client_tool_code "
                         "order by connection_identifier;", {"client_tool_code": client_tool_code})
        connections = self.cur.fetchall()
        connection_identifiers_list = []
        # Our records come back as a list of tuples.
        # Let's unpack them...
        for connection in connections:
            connection_name = connection["connection_identifier"]
            connection_identifiers_list.append(connection_name)
        return connection_identifiers_list

    def tunnel_template_usage(self, ssh_tunnel_code):
        """The tunnel_template_usage method, returns a list of all the connection identifiers which depend upon the
        presented ssh_tunnel_code. We use this to ensure we don't delete a tunnelling template which is in use.

        :return: list"""
        self.cur.execute("select connection_identifier "
                         "from connections "
                         "where ssh_tunnel_code = :ssh_tunnel_code "
                         "order by connection_identifier;", {"ssh_tunnel_code": ssh_tunnel_code})
        connections = self.cur.fetchall()
        connection_identifiers_list = []
        # Our records come back as a list of tuples.
        # Let's unpack them...
        for connection in connections:
            connection_name = connection["connection_identifier"]
            connection_identifiers_list.append(connection_name)
        return connection_identifiers_list

    def tns_names_aliases(self, tns_names_pathname: Path):
        """The tns_names_aliases method, takes a tnsnames.ora file and scans it, returning a dictionary containing a
        key for each TNS alias, which resolves to a string containing the full TNS entry. This can then be used to
        resolve hosts, ports etc.

        :param tns_names_pathname:
        :return: dict"""
        with open(tns_names_pathname, 'r') as tns:
            lines = tns.readlines()
        tns_aliases = []
        tns_line = ''
        count = 0
        for line in lines:
            line = line.strip()
            count += 1
            if len(line) > 0:
                tns_line = f'{tns_line} {line}'
            elif len(lines) == count or len(line) == 0:
                tns_aliases.append(tns_line)
                tns_line = ''
        if len(tns_line) > 0:
            tns_aliases.append(tns_line)

        # Strip out the empty list entries caused by extra blank lines
        tns_aliases = [entry for entry in tns_aliases if len(entry) > 0]

        aliases_dict = {}
        for connect_string in tns_aliases:
            alias = re.findall('[\w\d._-]+[\s]?=', connect_string)
            if alias is not None and len(alias) > 0:
                alias = alias[0].replace('=', '').strip()
            aliases_dict[alias] = connect_string

        return aliases_dict

    def tns_names_entry(self, tns_names_pathname: Path, tns_alias: str):
        """The tns_names_entry method, takes a tnsnames.ora file and a tns_alias. It then returns the associated
        entry, from the tns_names.ora file.

        :param tns_names_pathname:
        :param tns_alias:
        :return: str (or None if key not found in aliases dict)"""
        tns_dict = self.tns_names_aliases(tns_names_pathname=tns_names_pathname)
        try:
            tns_entry = tns_dict[tns_alias]
        except KeyError:
            tns_entry = None
        return tns_entry

    def connect_string_dict(self, connection_string: str):
        """The connect_string_dict method accepts a TNS connect string and extracts the key details
        for the "connect string and returns them as a dictionary."""
        connect_str_dict = {}

        try:
            port = re.findall("port[\s]?=[\s]?\d{1,5}", connection_string, re.IGNORECASE)
            port = port[0]
            port = str(port).split('=')[1]
        except IndexError:
            port = None
        connect_str_dict["listener_port"] = port

        try:
            host = re.findall("host[\s]?=[\s]?[\w.\d-]+", connection_string, re.IGNORECASE)
            host = host[0]
            host = str(host).split('=')[1]
        except IndexError:
            host = None
        connect_str_dict["host"] = host

        try:
            service_name = re.findall("service_name[\s]?=[\s]?[\w.\d_-]+", connection_string, re.IGNORECASE)
            service_name = service_name[0]
            service_name = str(service_name).split('=')[1]
        except IndexError:
            service_name = None
        connect_str_dict["service_name"] = service_name

        return connect_str_dict

    def wallet_tns_connect_dict(self, wallet_pathname: Path):
        """The wallet_tns_connect_dict method accepts a wallet pathname and opens the associated
        wallet. It then extracts the primary tnsnames.ora details and returns the
        as a dictionary, keyed on connect string."""
        connect_str_dict = {}
        if not wallet_pathname:
            print(f'ERROR: Wallet not found: {wallet_pathname}')
            raise FileNotFoundError

        connection_dictionary = {}
        if not exists(wallet_pathname):
            print(f'ERROR: Wallet file, {wallet_pathname}, does not exist!')
            raise FileNotFoundError
        with ZipFile(wallet_pathname, 'r') as zip:
            try:
                tns = zip.read('tnsnames.ora').decode(encoding="utf-8")
            except KeyError:
                print(f'ERROR: Failed to find tnsames.ora in the wallet file: {wallet_pathname}')
                raise
        tns = tns.replace('\r', '')
        for line in tns.split('\n'):
            if len(line) == 0:
                continue
            connect_str = re.findall("^[\S]+", line)
            connect_str = connect_str[0]

            port = re.findall("port[\s]?=\d{1,5}", line, re.IGNORECASE)
            port = port[0]
            port = str(port).split('=')[1]

            host = re.findall("host[\s]?=[\w.\d-]+", line, re.IGNORECASE)
            host = host[0]
            host = str(host).split('=')[1]
            connect_str_dict["host"] = host
            service_name = re.findall("service_name[\s]?=[\w.\d_-]+", line, re.IGNORECASE)
            service_name = service_name[0]
            service_name = str(service_name).split('=')[1]

            connect_str_dict[connect_str] = {}
            connect_str_dict[connect_str]["listener_port"] = port
            connect_str_dict[connect_str]["host"] = host
            connect_str_dict[connect_str]["service_name"] = service_name
        return connect_str_dict

    def wallet_connect_string_dict(self, wallet_pathname: str, connect_string: str):
        """The wallet_connect_strings_dict method accepts a wallet pathname and connect string and retrieves the
        associated wallet tnsnames.ora entry. It then extracts the primary details for the entry  and
        returns them as a dictionary.
        :param wallet_pathname: str
        :param connect_string:  str
        :return dict:  primary connect string attributes"""
        tns_connections_dict = self.wallet_tns_connect_dict(wallet_pathname=Path(wallet_pathname))
        connect_str_dict = {"connect_string": connect_string,
                            "host": tns_connections_dict[connect_string]["host"],
                            "listener_port": tns_connections_dict[connect_string]["listener_port"],
                            "service_name": tns_connections_dict[connect_string]["service_name"]}

        return connect_str_dict

    def connection_wallet_connect_string_dict(self, connection_identifier: str):
        """The connection_wallet_connect_string_dict method accepts a connection_identifier and retrieves the
        associated wallet and connect string. It then extracts the primary details for the connect string and
        returns them as a dictionary.
        :param connection_identifier: str
        :return dict:  primary connect string attributes """
        connect_str_dict = {}
        connection_record = self.connection_record(connection_identifier=connection_identifier)
        wallet_location = connection_record["wallet_location"]
        connect_string = connection_record["connect_string"]
        if not wallet_location:
            print(f'ERROR: Wallet not found: {wallet_location}')
            raise FileNotFoundError

        connect_str_dict = self.wallet_connect_string_dict(wallet_pathname=wallet_location,
                                                           connect_string=connect_string)
        return connect_str_dict

    def wallet_connect_string_list(self, connection_identifier: str):
        """Return a complete list of connect strings from the wallet associated with the supplied
        connection identifier."""
        if not connection_identifier:
            return []

        connection_record = self.connection_record(connection_identifier=connection_identifier)
        if not connection_record:
            return []

        wallet_pathname = connection_record["wallet_location"]
        connect_string = connection_record["connect_string"]

        if not wallet_pathname:
            return []

        wallet_tns_dict = self.wallet_tns_connect_dict(wallet_pathname=wallet_pathname)
        connect_str_list = []
        for connect_str in wallet_tns_dict.keys():
            connect_str_list.append(connect_str)
        return connect_str_list

    def connection_record(self, connection_identifier):
        self.cur.execute("select "
                         "database_type, "
                         "connection_identifier, "
                         "connection_type, "
                         "db_account_name, "
                         "connect_string, "
                         "oci_profile, "
                         "ocid, "
                         "wallet_required_yn, "
                         "wallet_location, "
                         "client_tool, "
                         "client_tool_options, "
                         "start_directory, "
                         "ssh_tunnel_required_yn, "
                         "ssh_tunnel_code, "
                         "listener_port, "
                         "description,  "
                         "connection_banner, "
                         "connection_message, "
                         "connection_text_colour "
                         "from connections "
                         "where connection_identifier = :connection_identifier;",
                         {"connection_identifier": connection_identifier})
        connection_record = self.cur.fetchone()
        if connection_record is not None:
            ocid = connection_record["ocid"]
            system_uid = system_id()
            connection_record["ocid"] = kb_decrypt(encrypted_data=ocid, kb_password=system_uid)
        return connection_record

    def mod_delete_connection(self, connection_identifier):
        """Delete the connections table row, associated with the supplied connection_identifier."""
        self.cur.execute("delete "
                         "from connections "
                         "where connection_identifier = :connection_identifier;",
                         {"connection_identifier": connection_identifier})
        self.db_conn.commit()

    def database_type_descriptors(self):
        """The database_type_descriptors returns a list of supported database types."""
        return self.valid_database_types

    def insert_connection(self, connections_record: dict):
        """Insert a new connections row. We expect a dictionary, which reflects the table column names and their
        value assignments. This method should not be called directly - only via the upsert_connection method."""
        for column_name in ["database_type", "connection_identifier", "connection_type",
                            "db_account_name", "wallet_required_yn"]:
            if not connections_record[column_name]:
                print(f'ERROR: {column_name} cannot be null or empty string!')
                raise sqlite3.IntegrityError

        if 'ssh_tunnel_required_yn' not in connections_record.keys():
            connections_record['ssh_tunnel_required_yn'] = 'N'

        if 'ssh_tunnel_code' not in connections_record.keys():
            connections_record['ssh_tunnel_code'] = ''

        if 'listener_port' not in connections_record.keys():
            connections_record['listener_port'] = ''

        if 'connection_banner' not in connections_record.keys():
            connections_record['connection_banner'] = 'None'

        if 'connection_message' not in connections_record.keys():
            connections_record['connection_message'] = ''

        if 'connection_text_colour' not in connections_record.keys():
            connections_record['connection_text_colour'] = 'None'

        self.cur.execute("insert into connections ("
                         "database_type, "
                         "connection_identifier, "
                         "connection_type, "
                         "db_account_name, "
                         "connect_string, "
                         "oci_profile, "
                         "ocid, "
                         "wallet_required_yn, "
                         "wallet_location, "
                         "client_tool, "
                         "client_tool_options, "
                         "start_directory, "
                         "ssh_tunnel_required_yn, "
                         "ssh_tunnel_code, "
                         "listener_port, "
                         "description, "
                         "connection_banner, "
                         "connection_message, "
                         "connection_text_colour "
                         " ) "
                         "values ("
                         ":database_type, "
                         ":connection_identifier, "
                         ":connection_type, "
                         ":db_account_name, "
                         ":connect_string, "
                         ":oci_profile, "
                         ":ocid, "
                         ":wallet_required_yn, "
                         ":wallet_location, "
                         ":client_tool, "
                         ":client_tool_options, "
                         ":start_directory, "
                         ":ssh_tunnel_required_yn, "
                         ":ssh_tunnel_code, "
                         ":listener_port, "
                         ":description,  "
                         ":connection_banner, "
                         ":connection_message, "
                         ":connection_text_colour) "
                         , connections_record)
        self.db_conn.commit()

    def save_geometry(self, window_category: str, geometry: str):
        """The save_geometry method, stores the window geometry, of window  category/name, primarily to record
        the window's screen position, so that it can be restored, when subsequently re-launched. This works in
        partnership with the retrieve_geometry function"""
        upsert_preference(db_file_path=self.db_file_path,
                          scope='auto',
                          preference_name=f'{window_category}_geometry',
                          preference_value=geometry,
                          preference_label='Auto-saved Geometry')

    def host_port_from_connect_str(self, connection_string, wallet_pathname):
        host = None
        port = None
        if wallet_pathname:
            connect_string_record = self.wallet_connect_string_dict(connect_string=connection_string,
                                                                    wallet_pathname=wallet_pathname)
            host = connect_string_record["host"]
            port = int(connect_string_record["listener_port"])
        elif ":" in connection_string:  # Assume EZConnect
            port = re.findall(":\d{1,5}", connection_string)
            host = re.findall("[\s]?[\w.\d-]+:", connection_string)
            port = port[0].replace(':', '')
            host = host[0].replace('//', '')
            host = host.replace(':', '')
        elif "=" in connection_string:  # Assume the string is fully specified
            connect_string_record = self.connect_string_dict(
                connection_string=connection_string)
            host = connect_string_record["host"]
            port = int(connect_string_record["listener_port"])
        elif tns_admin is not None:
            tns_record = self.tns_names_entry(tns_names_pathname=tns_admin / 'tnsnames.ora',
                                              tns_alias=connection_string)
            if tns_record is None:
                return None, None
            connect_string_record = self.connect_string_dict(connection_string=tns_record)
            host = connect_string_record["host"]
            port = int(connect_string_record["listener_port"])

        return host.strip(), int(port)

    def resolve_connect_host_port(self, connection_name):
        """Given a connection identifier, resolve its type: wallet based tns_names.ora, EZConnect, connect string or
        tns_names.ora connection entry. Then obtain the host and port number, returning them as a tuple (host, port).
        :param connection_name:
        :return: tuple (host, port)"""
        # TODO: Update to delegate some processing to method host_port_from_connect_str
        host = None
        port = None
        connection_record = self.connection_record(connection_identifier=connection_name)
        if connection_record["wallet_required_yn"] == "Y":
            connect_string_record = self.connection_wallet_connect_string_dict(connection_identifier=connection_name)
            host = connect_string_record["host"]
            port = int(connect_string_record["listener_port"])
        elif ":" in connection_record["connect_string"]:  # Assume EZConnect
            port = re.findall(":\d{1,5}", connection_record["connect_string"])
            host = re.findall("[\s]?[\w.\d-]+:", connection_record["connect_string"])
            port = port[0].replace(':', '')
            host = host[0].replace('//', '')
            host = host.replace(':', '')
        elif "=" in connection_record["connect_string"]:  # Assume the string is fully specified
            connect_string_record = self.connect_string_dict(
                connection_string=connection_record["connect_string"])
            host = connect_string_record["host"]
            port = int(connect_string_record["listener_port"])
        elif tns_admin is not None:
            tns_record = self.tns_names_entry(tns_names_pathname=tns_admin / 'tnsnames.ora',
                                              tns_alias=connection_record["connect_string"])
            if tns_record is None:
                return None, None
            connect_string_record = self.connect_string_dict(connection_string=tns_record)
            host = connect_string_record["host"]
            port = int(connect_string_record["listener_port"])

        return host.strip(), int(port)

    def validate_tns_connect(self, tns_connect_string: str, wallet_pathname: str = ''):
        """Given a TNS connect string and optionally a wallet, check whether the entry is in the tnsnames.ora file.
        If the wallet pathname is empty (no wallet in play) we assume this is meant to be EZConnect and validate its
        form. We return an appropriate error message, if we cannot validate the connect string.

        :param tns_connect_string: str
        :return: str"""

        if wallet_pathname:
            wallet_tns_connect = self.wallet_tns_connect_dict(wallet_pathname=wallet_pathname)
            service_list = []
            for service_name in wallet_tns_connect.keys():
                service_list.append(service_name)
            if tns_connect_string in service_list:
                return ''
            else:
                return f'The service_name, {tns_connect_string}, could not be found in tnsnames.ora, contained in ' \
                       f'the wallet: {wallet_pathname}'

        # Now look for a local tnsnames.ora and check there...
        tns_alias_list = self.tns_names_alias_list()
        if tns_connect_string in tns_alias_list:
            return ''

        # Now check for EZConnect
        if ":" in tns_connect_string:
            ez_pattern = r'[a-zA-Z0-9\.\/\?\:\-_]+:(\d)+[/][a-zA-Z0-9\.\/\?\:\-_]+'
            ez_match = re.search(pattern=ez_pattern, string=tns_connect_string, flags=re.IGNORECASE)
            if ez_match:
                return ''
            else:
                return 'This looks like a malformed EZ Connect string - please correct.'

        if "=" in tns_connect_string:  # Assume the string is fully specified and see if we can make sense
            connect_string_record = self.connect_string_dict(
                connection_string=tns_connect_string)
            try:
                host = connect_string_record["host"]
                port = connect_string_record["listener_port"]
                service_name = connect_string_record["service_name"]
            except KeyError:
                return 'Cannot parse (verbose) connect string - please check syntax'

            if host is None or port is None or service_name is None:
                return 'Cannot parse, what appears to be, a verbose connect string - please check syntax'
            else:
                return ''

        return 'TNS Connect String not resolved / recognised.'

    def retrieve_geometry(self, window_category: str):
        """The retrieve_geometry method, restores the window geometry, of window  category/name, primarily to restore
        the window's screen position, after a subsequent re-launch. This works in partnership with the save_geometry
        function.

        :param window_category: str
        :return: str"""
        geometry = preference(db_file_path=self.db_file_path,
                              scope='auto',
                              preference_name=f'{window_category}_geometry')
        return geometry

    def save_preferences(self, preferences: dict):
        """The save_preference method, receives a dictionary containing a preference entry, and upserts the data to the
        DCCM database.

        :param preferences: dict"""

        for pref, pref_value in preferences.items():
            if str(pref_value):
                upsert_preference(db_file_path=self.db_file_path, scope='preference',
                                  preference_name=pref, preference_value=str(pref_value),
                                  preference_label='')

    def oci_config_profiles_list(self, db_file_path: Path):
        """Accept an OCI config file pathname, and return the associated value list of profiles, defined in
        the config.

        :param db_file_path:
        :return: list"""
        config_pathname = preference(db_file_path=db_file_path,
                                     scope="preference",
                                     preference_name="oci_config")
        if not config_pathname:
            return []
        config = ConfigParser()
        config.read(config_pathname)
        profiles_list = []
        for section in config.sections():
            profiles_list.append(section)

        profiles_list.sort()
        return profiles_list

    def upsert_connection(self, connections_record: dict):
        """Insert a new connections row. We expect a dictionary, which reflects the table column names and their
        value assignments.

        :param connections_record (
        :return str: Error string, if encountered"""

        database_type = connections_record["database_type"]
        connection_identifier = connections_record["connection_identifier"]
        connection_type = connections_record["connection_type"]
        db_account_name = connections_record["db_account_name"].upper()
        connect_string = connections_record["connect_string"]
        oci_profile = connections_record["oci_profile"]
        if not connections_record["start_directory"]:
            home_directory = expanduser("~")
            connections_record["start_directory"] = home_directory

        ocid = connections_record["ocid"]

        system_uid = system_id()
        ocid = kb_encrypt(data=ocid, kb_password=system_uid)
        connections_record["ocid"] = ocid
        wallet_required_yn = connections_record["wallet_required_yn"]

        wallet_location = connections_record["wallet_location"]
        connection_id = self.connection_record(connection_identifier=connection_identifier)

        # Validate the submitted data
        if not connection_identifier:
            return f'You must enter a Connection Identifier.'
        elif not db_account_name:
            return f'You must specify a Database Username for the connection.'
        elif connection_type == 'Legacy' and not ocid:
            return f'You must supply a Password for a {connection_type} type entry.'
        elif connection_type == 'OCI Vault' and not ocid:
            return f'You must supply an OCID, for an {connection_type} type entry.'
        elif connection_type == 'OCI Vault' and not oci_profile:
            return f'You must supply an OCI Profile, for an {connection_type} type entry.'
        elif wallet_required_yn == 'Y' and not wallet_location:
            return f'You must supply a Wallet Location for the database connection.'
        elif not connect_string:
            return f'You must supply/select a Connect String for the database connection.'

        for column_name in ["database_type", "connection_identifier", "connection_type",
                            "db_account_name", "wallet_required_yn"]:
            if not connections_record[column_name]:
                print(f'ERROR: {column_name} cannot be null or empty string!')
                raise sqlite3.IntegrityError

        if not connection_id:
            self.insert_connection(connections_record=connections_record)
        else:
            if wallet_location is None:
                wallet_location = ''
            self.cur.execute("update connections set "
                             "database_type = :database_type, "
                             "connection_type = :connection_type, "
                             "db_account_name = :db_account_name, "
                             "connect_string = :connect_string, "
                             "oci_profile = :oci_profile, "
                             "ocid = :ocid, "
                             "wallet_required_yn = :wallet_required_yn, "
                             "wallet_location = :wallet_location, "
                             "client_tool = :client_tool, "
                             "client_tool_options = :client_tool_options, "
                             "start_directory = :start_directory, "
                             "ssh_tunnel_required_yn = :ssh_tunnel_required_yn, "
                             "ssh_tunnel_code = :ssh_tunnel_code, "
                             "listener_port = :listener_port, "
                             "description = :description, "
                             "connection_banner = :connection_banner, "
                             "connection_message = :connection_message, "
                             "connection_text_colour = :connection_text_colour "
                             "where connection_identifier = :connection_identifier;"
                             , connections_record)
            self.db_conn.commit()
            return ''

if __name__ == "__main__":
    pass
