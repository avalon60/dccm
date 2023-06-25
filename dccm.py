"""Database Client Connection Manager"""
# Control
__title__ = 'Database Client\nConnection Manager'
__author__ = 'Clive Bostock'
__version__ = "2.4.0"

import argparse
from colorama import just_fix_windows_console
# import cx_Oracle as cx
import oracledb as odb
from operator import attrgetter

import tkinter as tk
from tkinter import filedialog as fd
import customtkinter as ctk
import dccm_v as vew

from argparse import HelpFormatter
from pathlib import Path
import json
import sqlite3
import platform
import pyfiglet
import pyperclip
import os
import sys
from os.path import exists
from os.path import expanduser
import dccm_m as mod

from zipfile import ZipFile
import cbtk_kit as cbtk
# from tkfontawesome import icon_to_image
import re
import socket
import subprocess
import oci
from oci.config import from_file
from kellanb_cryptography import aes, key
import shutil
from shutil import which
import base64
from CTkMessagebox import CTkMessagebox

ENCODING = 'utf-8'

# Constants
HEADING1 = 'Roboto 16'
HEADING2 = 'Roboto 14'
HEADING3 = 'Roboto 12'
HEADING4 = 'Roboto 11'
HEADING_UL = 'Roboto 11 underline'
REGULAR_TEXT = 'Roboto 10'
SMALL_TEXT = 'Roboto 7'

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
app_home = Path(os.path.dirname(os.path.realpath(__file__)))
# Get the data location, required for the config file etc
data_location = mod.data_location
images_location = mod.images_location
temp_location = mod.temp_location

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


class SortingHelpFormatter(HelpFormatter):
    def add_arguments(self, actions):
        actions = sorted(actions, key=attrgetter('option_strings'))
        super(SortingHelpFormatter, self).add_arguments(actions)


ap = argparse.ArgumentParser(formatter_class=SortingHelpFormatter
                             , description=f"""{prog}: The dccm.py tool allows you to maintain database connection
                              details and uses these to launch a database client, and connect to the database. A
                              default connection can be set, for which the primary purpose is to use DCCM in a command
                              line mode, to act as an editor plugin.""")

ap.add_argument("-c", "--connection-identifier", required=False, action="store",
                help='The connection identifier, to be used to resolve the connection credentials. If omitted, the '
                     '"Default Connection" , is assumed. This flag is ignored when invoked with mode set as "gui".',
                dest='connection_identifier', default=None)

ap.add_argument("-e", "--export-connection", required=False, action="store",
                help='Specify "all" to perform a full export, or specify a specific Connection Id. A list of '
                     'Connection Ids can be obtained with the -l option. '
                     'If specified, any mode based operation request is ignored.'
                     ' The -e and -i options are mutually exclusive. Also see the -f option.',
                dest='export_connection', default=None)

ap.add_argument("-E", "--export-options", required=False, action="store",
                help='The only options here are "wallets-on" or "wallets-off". These control, respectively, '
                     'whether or not wallets are to be included as part of the connection(s) export.',
                dest='export_options', default="remap-on merge-off wallets-off")

ap.add_argument("-f", "--export-file", required=False, action="store",
                help=f'Specifies the file to export/import connections to/from. Use in conjunction with -e, -i or -P. '
                     f'If not specified {connection_export_default} is assumed for connection exports, and '
                     f'{settings_export_default} is the default for preferences. ',
                dest='export_file', default=connection_export_default)

ap.add_argument("-i", "--import-match", required=False, action="store",
                help='Specify "all" to perform a full import, or specify a specific Connection Id. '
                     'If specified, any mode based operation request is ignored. The -e and -i options are mutually '
                     'exclusive. Also see the -f option.',
                dest='import_connection', default=None)

ap.add_argument("-I", "--import-options", required=False, action="store",
                help='A space of comma, separated list of one or more keywords, enclosed within quotes. Valid options '
                     'are, "merge-on", "merge-off", "remap-on", "remap-off", "wallets-on" and "wallets-off". '
                     'Use "remap-on" to remap wallet locations to the default location specified in your '
                     'preferences ("remap-on" is the default). Use "merge-on" to cause updates of existing connections '
                     'during the import. The default is to skip over, pre-existing entries. Also see the -f option.'
                     'Use "wallets-on" to import any wallets included to the export. These are placed in your default'
                     'wallet location. The "wallets-on" option, must be specified in conjunction with "remap-on".',
                dest='import_options', default="remap-on merge-off wallets-off")

ap.add_argument("-l", "--list-connections", required=False, action="store_true",
                help="""List all connections. If specified, any mode based operation request is ignored.""",
                dest='list_connections', default=False)

ap.add_argument("-m", "--mode", required=False, action="store", default="command",
                help="""Used to specify the run-mode. This is either "gui", "command" (command-line) or "plugin" (editor
                  plugin). The command-line mode is the default, and is designed for interactive invocations or batch 
                  work. The "plugin" mode is similar to "command", except that it reads content from stdin, 
                  for execution against the target database.""", dest='mode')

ap.add_argument("-p", "--password", required=False, action="store",
                help="""Password to use for the encryption/decryption of passwords contained in export files.""",
                dest='password', default='')

ap.add_argument("-P", "--preferences", required=False, action="store",
                help="""This option controls the backup/restore of user preferences. The -P / --preferences option 
                must be accompanied by the keyword "backup" or "restore". Use the -f option to specify the file to 
                backup to / restore from. Do not use in conjunction with the export/import connection options.
                Also see the -f option.""",
                dest='prefs_operation', default='')

ap.add_argument("-s", "--sql-script", required=False, action="store", nargs="+",
                help="""Used to specify the pathname of a sql script to executed. This is only used in "command" mode. 
                "It is ignored for gui" and "plugin" modes.""", dest='sql_script', default=None)

ap.add_argument("-t", "--establish-tunnel", required=False, action="store_true",
                help="""Used in conjunction with -c flag. However, instead of launching the specified connection, the 
                ssh tunneling command, associated with the the specified connection is launched.""",
                dest='tunnelling', default=None)

args_list = vars(ap.parse_args())

connection_identifier = args_list["connection_identifier"]
export_connection = args_list["export_connection"]
export_file = args_list["export_file"]
export_options = args_list["export_options"].lower()
import_connection = args_list["import_connection"]
import_options = args_list["import_options"].lower()
list_connections = args_list["list_connections"]
password = args_list["password"]
prefs_operation = args_list["prefs_operation"].lower()
run_mode = args_list["mode"]
sql_script = args_list["sql_script"]
# The add_argument call for sql_script includes nargs="+",
# so argparse returns a list.  So here we convert the list
# into a string. This allows the passing of a script name
# along with any parameters.
if sql_script is not None:
    sql_script = ' '.join(sql_script)
tunnelling = args_list["tunnelling"]

import_options_list = import_options.split()
valid_import_options = 'merge-on, merge-off, remap-on, remap-off wallets-on wallets-off'
import_options_valid = True

# Check for conflicting file operations
file_operation_count = 0
if import_connection: file_operation_count += 1
if export_connection: file_operation_count += 1
if prefs_operation:  file_operation_count += 1

if file_operation_count > 1:
    print(f'Conflicting file operations. You cannot mix connection export, import, preferences backup or restore '
          f'operations.')
    exit(1)

if file_operation_count and tunnelling:
    print(f'Conflicting operations. You cannot mix connection export, import, preferences backup / restore '
          f'operations, with the SSH tunnelling option.')
    exit(1)

# If -f flag not specified then the default file name is based on that
# expected for a connections export. For preferences exports we need to
# set a different default name.
if prefs_operation and export_file == connection_export_default:
    export_file = settings_export_default

for option in import_options_list:
    if option.lower() not in valid_import_options:
        print(f'Invalid import option specified: {option}')
        import_options_valid = False

if not import_options_valid:
    print(f'{prog}: Bailing out!')
    exit(1)

if not connection_identifier and tunnelling:
    print(f'{prog}: You must specify a connection identifier ( use -c connection_id) to accompany the tunneling '
          f'option (-t).')
    exit(1)

merge_connections = False
remap_wallets = False
if 'merge-on' in import_options and 'merge-off' in import_options:
    print(f'{prog}: Conflicting import options specified: "merge-on" and "merge-off".')
    print(f'{prog}: Bailing out!')
    exit(1)
if 'remap-on' in import_options and 'remap-off' in import_options:
    print(f'{prog}: Conflicting import options specified: "remap-on" and "remap-off".')
    print(f'{prog}: Bailing out!')
    exit(1)

if ('wallets-on' in import_options and 'wallets-off' in import_options) or \
        ('wallets-on' in export_options and 'wallets-off' in export_options):
    print(f'{prog}: Conflicting export options specified: "wallets-on" and "wallets-off".')
    print(f'{prog}: Bailing out!')
    exit(1)

if 'wallets-on' in import_options or 'wallets-on' in export_options:
    include_wallets = True
else:
    include_wallets = True

if import_connection and 'wallets-on' in import_options and 'remap-on' not in import_options:
    print('You must specify "remap-on" as an import option, when requesting with "wallets-on".')
    print("Please rectify and try again.")
    exit(1)

valid_modes = ["gui", "plugin", "command"]
valid_modes_str = ', '.join(valid_modes)
if run_mode not in valid_modes:
    print(f'ERROR: Invalid run mode specified: {run_mode}')
    print(f'Valid modes are {valid_modes_str}')
    exit(1)

b_prog = prog.replace(".py", "")

db_file = mod.db_file


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


class DCCMControl:
    """Class to instantiate our DCCM controller."""

    def __init__(self, app_home: Path, mode: str, db_file_path: Path, connection_identifier: str = None):

        self.app_home = app_home
        self.app_images = self.app_home / 'images'
        self.app_configs = self.app_home / 'config'
        self.etc = self.app_home / 'etc'

        self.db_file_path = db_file_path
        self.wallet_pathname = ''
        self.import_pathname = None
        self.import_json = None
        self.connect_strings = []

        self.client_launch_directory = Path(os.getcwd())

        self.mvc_module = mod.DCCMModule(app_home=app_home, db_file_path=db_file_path)
        self.app_theme = self.mvc_module.app_theme()
        self.app_appearance_mode = self.mvc_module.app_appearance_mode()
        self.enable_tooltips = self.mvc_module.tooltips_enabled()
        self.default_wallet_directory = preference(db_file_path=db_file_path,
                                                   scope="preference",
                                                   preference_name="default_wallet_directory")

        self.oci_config = preference(db_file_path=db_file_path,
                                     scope="preference",
                                     preference_name="oci_config")

        self.enable_ancillary_ssh_window = preference(db_file_path=db_file,
                                                      scope='preference',
                                                      preference_name='enable_ancillary_ssh_window')

        if self.enable_ancillary_ssh_window is None:
            self.enable_ancillary_ssh_window = 0
        else:
            self.enable_ancillary_ssh_window = int(self.enable_ancillary_ssh_window)

        self.default_connection_type = self.mvc_module.default_connection_type
        self.client_tools_name_list = self.mvc_module.client_tools_name_list()

        if list_connections:
            ul = "="
            conn_str_len = 30
            print("\n   DCCM CONNECTIONS LISTING")
            print(f"   {ul * 24}\n")
            default_connection = preference(db_file_path=self.db_file_path,
                                            scope='preference',
                                            preference_name='default_connection')
            for connection_dict in self.mvc_module.connections_dict().values():
                this_length = len(connection_dict["connect_string"])
                if this_length > conn_str_len:
                    conn_str_len = this_length

            print(f'{"   Connection Id":<25}       {"DB Account":<30}    '
                  f'Connect String{" " * (conn_str_len - 14)}    {"Database Type":<14}    '
                  f'{"Management Type":<15}    SSH')
            print(f'   {ul * 25}    {ul * 30}    '
                  f'{ul * conn_str_len}    {ul * 14}    '
                  f'{ul * 15}    {ul * 3}')
            for connection_id, connection_dict in self.mvc_module.connections_dict().items():
                if connection_id == default_connection:
                    pad_length = 25 - len(connection_id)
                    # connection_id = f'{connection_id}(*)'
                    star = ' *'
                else:
                    star = '  '

                print(f'{star} {connection_id:<25}    {connection_dict["db_account_name"]:<30}    '
                      f'{connection_dict["connect_string"]}' + " " * (
                              conn_str_len - len(connection_dict["connect_string"]) + 4) +
                      f'{connection_dict["database_type"]:<14}    '
                      f'{connection_dict["connection_type"]:<15}     {connection_dict["ssh_tunnel_required_yn"]}')

            print('\n   * => Default connection')
            print("\n   Done.")
        if export_connection and import_connection:
            print(f'{prog} ERROR: Export and Import operations are mutually exclusive.')
            print('Bailing out!')
            exit(1)

        if export_connection:
            messages = self.mvc_module.export_connections(dump_file=export_file,
                                                          run_mode=run_mode,
                                                          connection_match=export_connection,
                                                          password=password,
                                                          include_wallets=include_wallets)
            for message in messages:
                print(message)

        if import_connection:
            messages = self.mvc_module.import_connections(dump_file=export_file,
                                                          run_mode=run_mode,
                                                          password=password,
                                                          connection_match=import_connection,
                                                          merge_connections=merge_connections,
                                                          remap_wallet_locations=remap_wallets,
                                                          import_wallets=include_wallets
                                                          )
            for message in messages:
                print(message)

        if prefs_operation == 'backup':
            feedback = backup_preferences(save_file_name=export_file)
            for line in feedback:
                print(f'{line}')
        elif prefs_operation == 'restore':
            feedback = restore_preferences(restore_file_name=export_file)
            for line in feedback:
                print(f'{line}')
        elif prefs_operation == '':
            pass
        else:
            print(f'Invalid preferences backup/restore request: {prefs_operation}')
            exit(1)

        if list_connections or export_connection or import_connection or prefs_operation:
            exit()

        if mode == 'gui':
            self.ROOT_WIDTH = 520
            self.ROOT_HEIGHT = 570
            ctk.set_appearance_mode(self.app_appearance_mode)  # Modes: "System" (standard), "Dark", "Light"
            ctk.set_default_color_theme(str(themes_location / f'{self.app_theme}.json'))
            self.mvc_view = vew.DCCMView(mvc_controller=self)
            self.app_themes_list = self.mvc_view.app_themes_list()
            self.mvc_view.iconbitmap = images_location / 'dccm.ico'

            # self.mvc_view.attributes("-alpha", 0.892)

            self.restore_geometry(window_category='root')
            self.mvc_view.geometry(f'{self.ROOT_WIDTH}x{self.ROOT_HEIGHT}')
            self.mvc_view.launch_in_gui_mode()
            self.update_opm_connections()

            self.status_bar = cbtk.CBtkStatusBar(master=self.mvc_view)
            self.mvc_view.bind("<Configure>", self.status_bar.auto_size_status_bar)

            self.mvc_view.enable_tool_tips = True

            self.mvc_view.mainloop()
        elif not tunnelling:
            connection_id = connection_identifier
            default_connection = ''
            if connection_id is None:
                default_connection = preference(db_file_path=self.db_file_path,
                                                scope='preference',
                                                preference_name='default_connection')
                if default_connection is None:
                    print('ERROR: You must specify a default connection, via the GUI, or explicitly specify '
                          'a connection, via use of the -c flag.')
                    exit(1)
                connection_id = default_connection
                print(f'Connecting to the default connection: "{connection_id}"')

            if mode == "command":
                self.launch_in_command_mode(connection_identifier=connection_id,
                                            sql_script_nane=sql_script)
            elif mode == "plugin":
                self.launch_in_plugin_mode(connection_identifier=connection_id)
        elif tunnelling:
            connection_id = connection_identifier
            if connection_id is None:
                default_connection = preference(db_file_path=self.db_file_path,
                                                scope='preference',
                                                preference_name='default_connection')
                if default_connection is None:
                    print('ERROR: You must configure a default connection, or use the -c flag.')
                    exit(1)
                else:
                    connection_id = default_connection
            self.launch_ssh_tunnel(connection_id=connection_id)

    def banner_colours(self):
        return self.mvc_module.colour_list()

    def banner_options(self):
        return self.mvc_module.banner_options()

    def connection_type_list(self):
        """The connection_type_list method acts as a broker, to obtain connection/management types from the module
        class. These are used to present details via the view class.

        :return: list"""
        return self.mvc_module.connection_type_list()

    def default_connection(self):
        """The default_connection method acts as a broker, to obtain default connection from the module class. This
        is used to present details via the view class.

        :return: str"""
        return self.mvc_module.default_connection()

    def connections_dict(self):
        """The connections_dict method acts as a broker, to obtain a dictionary of connections from the module class.
        This is used to present details via the view class.

        :return: dict"""
        return self.mvc_module.connections_dict()

    def connection_record(self, connection_identifier: str):
        """The connection_record method acts as a broker, to obtain a dictionary associated with the presented
        connection identifier, from the module class. This is used to present details via the view class.

        :param connection_identifier:
        :return: dict"""
        return self.mvc_module.connection_record(connection_identifier=connection_identifier)

    def launch_in_command_mode(self, connection_identifier: str, sql_script_nane: str = None):
        """As the name suggests, the launch_in_command_mode method, launches DCCM in command line mode."""
        connection_name = connection_identifier
        connection_record = self.mvc_module.connection_record(connection_identifier=connection_name)
        if connection_record is None:
            print(f'Invalid connection identifier: "{connection_identifier}"')
            exit(1)
        wallet_location = connection_record["wallet_location"]

        if connection_record["wallet_required_yn"] == "Y":
            if not exists(wallet_location):
                print(f'The associated wallet, {wallet_location}, for the "{connection_name}", cannot be found. '
                      f'Please rectify and try again.')
                return
        hostname, port_number = self.mvc_module.resolve_connect_host_port(connection_name)
        if connection_record["wallet_required_yn"] == "Y":
            if not port_is_open(host=hostname,
                                port_number=port_number):
                print(
                    f'Database server cannot be reached via host "{hostname}" on port {port_number}.\nThe connection may '
                    f"require ssh tunnel, VPN, Listener startup etc, to be established.")
                return
        else:
            if not port_is_open(host=hostname,
                                port_number=int(port_number)):
                print(
                    f'{prog}: Database server cannot be reached via host "{hostname}" on port {port_number}.\n'
                    f'Ensure that there are no network connectivity issues and that the database, and database listener'
                    f" are started.")
                return

        return_status, client_command = self.mvc_module.formulate_connection_launch(
            connection_identifier=connection_name,
            mode="command",
            script_name=sql_script_nane)

        if return_status:
            print(return_status)
            exit(1)
        # input(f'Press ENTER to continue...\c')

        connection_text_colour = connection_record["connection_text_colour"]
        colour_sequence = self.mvc_module.color_code(colour=connection_text_colour)
        colour_off = self.mvc_module.color_code(colour='None')
        connection_banner = connection_record["connection_banner"]
        if connection_banner is None:
            connection_banner = ''
        if connection_banner and connection_banner != 'None':
            ascii_banner = pyfiglet.figlet_format(connection_banner)
            print(f'{colour_sequence}{ascii_banner}{colour_off}')

        connection_message = connection_record["connection_message"]
        if connection_message:
            print(f'{colour_sequence}{connection_message}{colour_off}')

        # For some reason, this flush call is only required for GIT bash.
        sys.stdout.flush()
        status = os.system(client_command)
        if status:
            print(f'Client command, "{client_command}", returned with a status of: {status}')

    def launch_in_plugin_mode(self, connection_identifier: str):
        """The launch_in_plugin_mode method, launches DCCM in command line plugin mode. This mode is a little like
        the "command" mode, except that it expects input to be piped in from stdin.

        :param connection_identifier:
        :return: None"""
        connection_name = connection_identifier
        connection_record = self.mvc_module.connection_record(connection_identifier=connection_name)
        hostname, port_number = self.mvc_module.resolve_connect_host_port(connection_name)
        if connection_record["wallet_required_yn"] == "Y":
            if not port_is_open(host=hostname,
                                port_number=port_number):
                try:
                    ip = socket.gethostbyname(hostname)
                except socket.gaierror:
                    ip = 'Unresolved IP'
                print(f"Database server, {hostname} ({ip}), cannot be reached via port {port_number}.\nThe connection "
                      f"may require ssh tunnel, VPN, Listener startup etc, to be established.")
                return
        else:
            if not port_is_open(host=hostname,
                                port_number=int(port_number)):
                try:
                    ip = socket.gethostbyname(hostname)
                except socket.gaierror:
                    ip = 'Unresolved IP'
                print(
                    f"{prog}: Database server, {hostname} ({ip}), cannot be reached on port {port_number}.\nEnsure that "
                    f"there are no network connectivity issues and that the database, and database listener "
                    f"are started.")
                return
        # print(f'{prog}: Launching "{connection_name}" connection...')
        script = []
        try:
            for line in sys.stdin:
                script.append(line)
        except KeyboardInterrupt:
            sys.stdout.flush()
        with open('dccm.buf', 'w') as b:
            for line in script:
                b.write(f'{line}')
        return_status, client_command = self.mvc_module.formulate_connection_launch(
            connection_identifier=connection_name,
            mode="plugin",
            script_name='dccm.buf')

        if return_status:
            print(return_status)
            exit(1)

        status = os.system(client_command)
        if status:
            print(f"Client returned with a status of: {status}")

    def database_type_descriptors(self):
        """The database_type_descriptors method acts as a broker, to obtain a list of supported database types
        from the module class. This is used to present details via the view class object."""

        return self.mvc_module.valid_database_types

    def connection_type_descriptors(self):
        """The connection_type_descriptors function acts as a broker, to obtain a list of supported database
        connection/management types from the module class. This is used to present details via the view class object."""
        return self.mvc_module.connection_type_list()

    def launch_client_connection(self, connection_name: str = None):
        """The launch_client_connection method, marshals the required details, required to launch a client tool
        via a terminal window. The function leans on the module class to pull much of the detail together. Once
        the command is formulated, it is executed directly by launch_client_connection."""
        if connection_name is None:
            connection_name = self.mvc_view.opm_connections.get()
        connection_record = self.mvc_module.connection_record(connection_identifier=connection_name)
        start_directory = connection_record["start_directory"]
        wallet_location = Path(connection_record["wallet_location"])
        position_geometry = self.retrieve_geometry(window_category='root')
        geometry_offset = cbtk.geometry_offset(position_geometry, 50, 100)
        if start_directory is not None:
            if exists(start_directory):
                os.chdir(start_directory)
            else:
                confirm = CTkMessagebox(master=self.mvc_view,
                                        title='Action Required',
                                        message=f'The start directory, {start_directory}, for the '
                                                f'"{connection_name}", does not '
                                                f'exist. Please rectify and try again.',
                                        option_1='OK')
                if confirm.get() == 'OK':
                    return

        if connection_record["wallet_required_yn"] == "Y":
            if not exists(wallet_location):
                confirm = CTkMessagebox(master=self.mvc_view,
                                        title='Action Required',
                                        message=f'The associated wallet, {wallet_location}, for the '
                                                f'"{connection_name}", cannot be found. '
                                                f'Please rectify and try again.',
                                        option_1='OK')
                if confirm.get() == 'OK':
                    return
        hostname, port_number = self.mvc_module.resolve_connect_host_port(connection_name)
        if connection_record["wallet_required_yn"] == "Y":
            connect_string_record = self.mvc_module.connection_wallet_connect_string_dict(
                connection_identifier=connection_name)
            if not port_is_open(host=connect_string_record["host"],
                                port_number=int(connect_string_record["listener_port"])):
                try:
                    ip = socket.gethostbyname(hostname)
                except socket.gaierror:
                    ip = 'Unresolved IP'

                confirm = CTkMessagebox(master=self.mvc_view,
                                        title='Action Required',
                                        message=f"Database server, {hostname} ({ip}), cannot be reached on port "
                                                f"{port_number}. The connection may require ssh tunnel, VPN etc, "
                                                f"to be established.",
                                        option_1='OK')
                if confirm.get() == 'OK':
                    return
        else:
            if hostname is None or port_number is None:
                confirm = CTkMessagebox(master=self.mvc_view,
                                        title='Action Required',
                                        message=f"The selected connection, \"{connection_name}\", is no longer "
                                                f"valid. Possibly caused by an associated tnsnames.ora file entry, "
                                                f"which has been deleted, since this connection was created.",
                                        option_1='OK')
                if confirm.get() == 'OK':
                    return

            if not port_is_open(host=hostname,
                                port_number=int(port_number)):
                try:
                    ip = socket.gethostbyname(hostname)
                except socket.gaierror:
                    ip = 'Unresolved IP'

                confirm = CTkMessagebox(master=self.mvc_view,
                                        title='Action Required',
                                        message=f"Database server, {hostname} ({ip}), cannot be reached on port "
                                                f"{port_number}. Ensure that there are no network connectivity "
                                                "issues and that the database, and database listener are "
                                                "started.",
                                        option_1='OK')
                print(f'Database server cannot be reached. Connection may require ssh tunnel, VPN etc, '
                      f'to be established.')
                if confirm.get() == 'OK':
                    return

        return_status, client_command = self.mvc_module.formulate_connection_launch(
            connection_identifier=connection_name)
        if return_status:
            confirm = CTkMessagebox(master=self.mvc_view,
                                    title='Action Required',
                                    message=f'{return_status}',
                                    option_1='OK')
            print(f'Database server cannot be reached. Connection may require ssh tunnel, VPN etc, '
                  f'to be established.')
            if confirm.get() == 'OK':
                return

        status = os.system(client_command)
        if status:
            confirm = CTkMessagebox(master=self.mvc_view,
                                    title='Action Required',
                                    message=f'Client command, "{client_command}", returned with a status of: '
                                            f'{status}',
                                    option_1='OK')
            if confirm.get() == 'OK':
                return

    def launch_mod_connection(self):
        """The launch_mod_connection method, lunches the maintain_connection method in "Modify" mode. This creates
         the CTkTopLevel, used to update an existing  connection record."""
        self.mvc_view.maintain_connection(operation='Modify')
        self.present_connection_details()
        self.mvc_view.ent_mod_connection_identifier.configure(state=tk.DISABLED)
        self.toggle_mod_tunnel_widgets()

    def launch_new_connection(self):
        """The launch_mod_connection method, lunches the maintain_connection method in "Add New" mode. This creates
         the CTkTopLevel, used to create a new connection record."""
        self.wallet_pathname = ''
        self.client_launch_directory = ''
        self.mvc_view.maintain_connection(operation='Add New')
        self.toggle_mod_tunnel_widgets()

    def launch_ssh_tunnel(self, connection_id: str = None):
        """The launch_ssh_tunnel method, marshals the required details, required to launch a terminal window, with
        the command required to forge an ssh tunnel for a specified connection id. The function leans on the module
        class to pull much of the detail together. Once the command is formulated, it is executed directly by
        launch_client_connection."""
        if connection_id is None:
            connection_id = self.mvc_view.opm_connections.get()

        if run_mode == 'plugin':
            # Treat plugin mode as if it is command mode
            mode = 'command'
        else:
            mode = run_mode

        status_text, ssh_command = self.mvc_module.formulate_ssh_launch(connection_id=connection_id, mode=run_mode)
        if status_text and mode == 'gui':
            position_geometry = self.retrieve_geometry(window_category='root')

            confirm = CTkMessagebox(master=self.mvc_view,
                                    title='Action Required',
                                    message=status_text,
                                    option_1='OK')
            if confirm.get() == 'OK':
                return
        elif status_text:
            # We are in "command" or "plugin mode", so issue a message via print statement and exit.
            print(status_text)
            return

        if mode != 'gui':
            print(f'\nEstablishing ssh tunnel for connection "{connection_id}" using: {ssh_command}\n')
        status = os.system(ssh_command)
        if status:
            print(f'Client command, "{ssh_command}", returned with a status of: {status}')

    def preview_launch_command(self):
        connection_name = self.mvc_view.opm_connections.get()
        return_status, client_command = self.mvc_module.formulate_connection_launch(
            connection_identifier=connection_name,
            mode="command")
        if return_status:
            pyperclip.copy(return_status)
        else:
            pyperclip.copy(client_command)
        self.status_bar.set_status_text(
            status_text='Command copied to clipboard.')

    def resolve_connect_host_port(self, connection_name: str):
        """The resolve_connect_host_port method acts as a broker, to obtain a tuple of host, port, required by the
        specified connection id. This is used to check connectivity as well as present details via the view class
        object."""
        host, port = self.mvc_module.resolve_connect_host_port(connection_name=connection_name)
        return host, port

    def retrieve_geometry(self, window_category: str):
        """The retrieve_geometry method acts as a broker, to obtain a string containing the previously saved window
        geometry, of the specified window_category (name). This provided by the module class. This is primarily used
        to control window positioning, upon subsequent program / window launches.

        :param window_category (str): The window category - root, or toplevel
        :return geometry (str)"""
        geometry = self.mvc_module.retrieve_geometry(window_category=window_category)
        return geometry

    def set_ssh_button_state(self):
        """The set_ssh_button_state method, controls the 'Establish SSH Tunnel' button state associated with the
        selected connection on the root window.. If ssh is not required for the current connection, then we disable
        the button."""
        connection_id = self.mvc_view.opm_connections.get()
        connection_record = self.connection_record(connection_identifier=connection_id)
        # Connection record is None at this stage, if there is no preferred connection.
        if connection_record is None:
            self.mvc_view.btn_launch_ssh.configure(state=tk.DISABLED)
            self.mvc_view.file_menu.entryconfig('Establish SSH Tunnel', state="disabled")
        elif connection_record["ssh_tunnel_required_yn"] == "N":
            self.mvc_view.btn_launch_ssh.configure(state=tk.DISABLED)
            self.mvc_view.file_menu.entryconfig('Establish SSH Tunnel', state="disabled")
        else:
            self.mvc_view.btn_launch_ssh.configure(state=tk.NORMAL)
            self.mvc_view.file_menu.entryconfig('Establish SSH Tunnel', state="normal")

    def update_opm_connections(self):
        """The update_opm_connections function, updates the connections' widget, following the addition/deletion of
        connection entries."""
        connections = self.mvc_module.connection_identifiers_list()
        self.mvc_view.update_opm_connections(connections)

    def save_geometry(self, window_category):
        """The save_geometry method acts as a broker, to save a string of the window geometry, for the
        specified window_category (name). Handing this over to the module class. This is primarily used to control
        window positioning, upon subsequent program / window launches."""
        geometry = None
        if window_category == 'root':
            geometry = self.mvc_view.geometry()
        elif window_category == 'toplevel':
            geometry = self.mvc_view.top_mod_connection.geometry()
        self.mvc_module.save_geometry(window_category=window_category, geometry=geometry)

    def save_preferences(self):
        """The save_preference method acts as a broker, to obtain the widget selections/entries in from the
        preferences window, amd submit them to the module class, to be saved to the DCCM database."""
        self.app_theme = self.mvc_view.opm_app_theme.get()
        self.app_appearance_mode = self.mvc_view.tk_appearance_mode_var.get()
        ctk.set_appearance_mode(
            self.app_appearance_mode)
        cbtk.CBtkStatusBar.update_widgets_mode()
        self.status_bar.update_text_colour()
        self.enable_tooltips = self.mvc_view.swt_enable_tooltips.get()
        self.enable_ancillary_ssh_window = self.mvc_view.swt_enable_ancillary_ssh_window.get()

        preferences_dict = {"app_theme": self.app_theme,
                            "app_appearance_mode": self.app_appearance_mode,
                            "enable_tooltips": self.enable_tooltips,
                            "default_wallet_directory": self.default_wallet_directory,
                            "oci_config": self.oci_config,
                            "enable_ancillary_ssh_window": self.enable_ancillary_ssh_window}

        self.mvc_module.save_preferences(preferences=preferences_dict)
        self.status_bar.set_status_text(
            status_text='Preferences saved!')

    def restore_geometry(self, window_category: str):
        """The restore_geometry method acts as a broker, obtaining from the module class, a string of the window
        geometry, for the specified window_category (name). Handing this over to the module class.
        This is primarily used to control window positioning, upon subsequent program / window launches."""
        ROOT_WIDTH = 400
        ROOT_HEIGHT = 450
        MOD_WIDTH = 820
        MOD_HEIGHT = 760
        geometry = self.mvc_module.retrieve_geometry(window_category=window_category)
        if window_category == 'root':
            self.mvc_view.geometry(geometry)
            self.mvc_view.geometry(f'{ROOT_WIDTH}x{ROOT_HEIGHT}')
        elif window_category == 'toplevel':
            self.mvc_view.top_mod_connection.geometry(geometry)
            self.mvc_view.top_mod_connection.geometry(f"{MOD_WIDTH}x{MOD_HEIGHT}")

    def root_delete_connection(self):
        """The mod_delete_connection function, obtains the currently selected connection name, from the root window,
        and asks for confirmation, before deleting it from the DCCM database. This function is called from the
        root window, or from the menu."""
        connection_name = self.mvc_view.opm_connections.get()
        position_geometry = self.retrieve_geometry(window_category='root')
        geometry_offset = cbtk.geometry_offset(position_geometry, 50, 100)
        confirm = CTkMessagebox(title='Confirm Action',
                                message=f'Are you sure you wish to delete the "{connection_name}" entry?',
                                options=['Yes', 'No'],
                                master=self.mvc_view)

        if confirm == 'No':
            return

        self.mvc_module.mod_delete_connection(connection_identifier=connection_name)
        self.update_opm_connections()
        connections_list = self.mvc_module.connection_identifiers_list()
        default_connection = self.mvc_module.default_connection()
        if default_connection:
            self.mvc_view.opm_connections.set(default_connection)
        else:
            self.mvc_view.opm_connections.set(connections_list[0])
        self.status_bar.set_status_text(
            status_text=f'Database connection, "{connection_name}", deleted.')

    def set_connection_as_current(self):
        """When invoked, the set_connection_as_current method, determines the currently selected connection in the
        application root window, and sets it as the default connection in the user preferences. The selected
        connection also becomes the default selection in subsequent application launches. With the default set, and
        when running in non-GUI mode, the default connection is assumed when the -c / --connection-identifier flag is
        not specified."""
        prev_current = self.default_connection()
        connection_name = self.mvc_view.opm_connections.get()
        upsert_preference(db_file_path=self.db_file_path,
                          scope='preference',
                          preference_name='default_connection',
                          preference_value=connection_name,
                          preference_label='Default working connection.')
        default_connection = f'Default: {connection_name}'
        self.mvc_view.lbl_default_connection.configure(text=default_connection)
        self.mvc_view.btn_set_current.configure(state=tk.DISABLED)
        self.mvc_view.file_menu.entryconfig('Set as Default', state="disabled")
        self.status_bar.set_status_text(
            status_text=f'Default working connection, now set to: {connection_name}.')

    def selected_connection_record(self):
        """The selected_connection_record method, queries the connections selection widget from the root window, and
        and returns the associated connection record, via the module class."""
        connection_identifier = self.mvc_view.opm_connections.get()
        connection_record = self.mvc_module.connection_record(connection_identifier=connection_identifier)
        return connection_record

    def display_connection_attributes(self, event=None):
        """The display_connection_attributes method, is used to query the connection record associated with the
        connection selected on the root window. It then goes on to have the main record details, displayed in the
        Connection Details frame."""
        default_connection = self.default_connection()
        connection_identifier = self.mvc_view.opm_connections.get()
        connection_record = self.selected_connection_record()
        self.mvc_view.frm_connection_type.grid()
        self.mvc_view.frm_root_database_account.grid()
        self.mvc_view.frm_root_connect_string.grid()
        self.mvc_view.frm_root_client_tool.grid()
        self.mvc_view.frm_root_initial_dir.grid()
        self.mvc_view.frm_root_ssh_tunnel.grid()

        self.mvc_view.lbl_root_connection_type.grid()
        self.mvc_view.lbl_root_database_account.grid()
        self.mvc_view.lbl_root_connect_string.grid()
        self.mvc_view.lbl_root_client_tool.grid()
        self.mvc_view.lbl_root_initial_dir.grid()
        self.mvc_view.lbl_root_ssh_tunnel.grid()

        if connection_record:
            max_len = max(len(connection_record["db_account_name"]), len(connection_record["connect_string"]))
            self.mvc_view.geometry(f'{int(self.ROOT_WIDTH) + (5 * max_len)}x{self.ROOT_HEIGHT}')

        if connection_identifier != '-- Connections --':
            self.mvc_view.btn_modify.configure(state=tk.NORMAL)
            self.mvc_view.btn_delete.configure(state=tk.NORMAL)
            self.mvc_view.btn_launch_client.configure(state=tk.NORMAL)
            self.mvc_view.file_menu.entryconfig('Modify Connection', state="normal")
            self.mvc_view.file_menu.entryconfig('Delete Connection', state="normal")
            self.mvc_view.file_menu.entryconfig('Launch Connection', state="normal")
            self.mvc_view.file_menu.entryconfig('Copy Command', state="normal")

        if default_connection is None:
            default_connection = ''

        if default_connection == connection_identifier:
            self.mvc_view.btn_set_current.configure(state=tk.DISABLED)
            self.mvc_view.file_menu.entryconfig('Set as Default', state="disabled")
        elif connection_identifier == '-- Connections --':
            self.mvc_view.btn_set_current.configure(state=tk.DISABLED)
            self.mvc_view.file_menu.entryconfig('Set as Default', state="disabled")
        else:
            self.mvc_view.btn_set_current.configure(state=tk.NORMAL)
            self.mvc_view.file_menu.entryconfig('Set as Default', state="normal")

        if connection_record:
            self.mvc_view.lbl_root_connection_type_disp.configure(
                text=f'{connection_record["database_type"]} / {connection_record["connection_type"]}')

            self.mvc_view.lbl_root_database_account_disp.configure(
                text=f'{connection_record["db_account_name"]}')

            self.mvc_view.lbl_root_connect_string_disp.configure(
                text=f'{connection_record["connect_string"]}')

            self.mvc_view.lbl_root_client_tool_disp.configure(
                text=f'{connection_record["client_tool"]}')

            self.mvc_view.lbl_root_initial_dir_disp.configure(
                text=f'{connection_record["start_directory"]}')

            if connection_record["ssh_tunnel_code"]:
                ssh_connection_disp = connection_record["ssh_tunnel_code"]
            else:
                ssh_connection_disp = 'Not configured.'
            self.mvc_view.lbl_root_ssh_tunnel_disp.configure(text=ssh_connection_disp)

        self.set_ssh_button_state()

    def modify_connection(self):
        """The modify_connection method, is the first stage of call in updating/inserting connection details from
        the connections maintenance window. It performs some basic validation, via the module class object, ensuring
        that there isn't already a connection of the same identifier."""
        connection_identifier = self.mvc_view.ent_mod_connection_identifier.get()
        check_exists = connection_record = self.mvc_module.connection_record(connection_identifier)
        if check_exists and self.mvc_view.maintain_operation == 'Add New':
            confirm = CTkMessagebox(title='Action Required',
                                    message=f'A connection, "{connection_identifier}", already exists. Please '
                                            f'choose another name or cancel.',
                                    option_1='OK',
                                    master=self.mvc_view.top_mod_connection)
            return

        oci_config = preference(db_file_path=self.db_file_path, scope='preference',
                                preference_name='oci_config')
        if not oci_config and self.mvc_view.opm_mod_connection_type.get() == 'OCI Vault':
            confirm = CTkMessagebox(title='Action Required',
                                    message=f'To use the "OCI Vault" Management Type, you must first set your '
                                            f'OCI Config Locn (directory) in Tools / Preferences',
                                    option_1='OK',
                                    master=self.mvc_view.top_mod_connection)
            return
        # Now Insert (if Add New and doesn't exist already) or Update the record
        self.upsert_connection()
        self.mvc_view.btn_set_current.configure(state=tk.NORMAL)
        self.display_connection_attributes()

    def validate_mod_entries(self):
        """Validate a connections row. We create a dictionary, which reflects the table column names and their
        value assignments. This method is called from the modify_connection method. If validations are successful,
        we return a tuple of status message and connections table record. The status message is empty of there are
        no errors detected."""
        if self.wallet_pathname is None:
            self.wallet_pathname = ''

        connections_record = {}
        # We don't presently deal with the description.
        connections_record["description"] = ''

        connections_record["database_type"] = self.mvc_view.opm_mod_database_type.get()
        self.mvc_view.ent_mod_connection_identifier.configure(state=tk.NORMAL)
        connections_record["connection_identifier"] = self.mvc_view.ent_mod_connection_identifier.get().strip()
        connections_record["connection_type"] = self.mvc_view.opm_mod_connection_type.get()
        connections_record["db_account_name"] = self.mvc_view.ent_mod_db_account_name.get().strip()
        connections_record["connect_string"] = self.mvc_view.cmo_mod_connect_string.get().strip()
        connections_record["oci_profile"] = self.mvc_view.cmo_mod_oci_profile.get().strip()
        connections_record["ocid"] = self.mvc_view.ent_mod_ocid.get().strip()
        connections_record["wallet_required_yn"] = self.mvc_view.swt_mod_wallet_required.get()
        connections_record["connection_banner"] = self.mvc_view.opm_mod_connection_banner.get()
        connections_record["connection_message"] = self.mvc_view.tk_mod_connection_message.get()
        connections_record["connection_text_colour"] = self.mvc_view.opm_mod_connection_text_colour.get()
        status_text = ''

        if not connections_record["connection_identifier"]:
            status_text = 'You must enter a Connection Id.'
            return status_text, connections_record

        if not connections_record["db_account_name"]:
            status_text = 'You must enter a database Username.'
            return status_text, connections_record

        if not connections_record["ocid"] and connections_record["connection_type"] == 'OCI Vault':
            status_text = 'You must enter an OCID for an "OCI Vault" managed connection.'
            self.mvc_view.mod_status_bar.set_status_text(
                status_text=status_text)
            return status_text, connections_record

        if not connections_record["ocid"] and connections_record["connection_type"] == 'Legacy':
            status_text = 'Please enter a password for the connection.'
            self.mvc_view.mod_status_bar.set_status_text(
                status_text=status_text)
            return status_text, connections_record

        if not connections_record["connect_string"]:
            status_text = 'You must enter/select a database connect string.'
            return status_text, connections_record

        if connections_record["wallet_required_yn"] == 'N':
            connections_record["wallet_location"] = ''
        else:
            connections_record["wallet_location"] = str(self.wallet_pathname)

        if connections_record["wallet_required_yn"] == 'Y' and not connections_record["wallet_location"]:
            status_text = 'Please select a wallet location.'
            self.status_bar.set_status_text(
                status_text=status_text)
            return status_text, connections_record

        connections_record["client_tool"] = self.mvc_view.opm_mod_client_tool.get()
        if connections_record["client_tool"] == 'SQLcl':
            connections_record["client_tool_options"] = self.mvc_view.ent_mod_client_tool_options.get()
        else:
            connections_record["client_tool_options"] = ''

        if self.client_launch_directory is None:
            connections_record["start_directory"] = os.getcwd()
        else:
            connections_record["start_directory"] = str(self.client_launch_directory)

        connections_record["ssh_tunnel_required_yn"] = self.mvc_view.swt_mod_ssh_tunnel_required_yn.get()
        if connections_record["ssh_tunnel_required_yn"] == 'Y':
            connections_record["ssh_tunnel_code"] = self.mvc_view.opm_mod_tunnel_code.get()
        else:
            connections_record["ssh_tunnel_code"] = ''

        connections_record["listener_port"] = self.mvc_view.ent_mod_listener_port.get()

        if len(connections_record["ssh_tunnel_code"]) == 0 and connections_record["ssh_tunnel_required_yn"] == 'Y':
            status_text = 'Please select an SSH tunnel.'
            self.mvc_view.mod_status_bar.set_status_text(
                status_text=status_text)
            return status_text, connections_record

        if len(connections_record["listener_port"]) == 0 and connections_record["ssh_tunnel_required_yn"] == 'Y':
            status_text = 'Please enter the database listener port number.'
            self.mvc_view.mod_status_bar.set_status_text(
                status_text=status_text)
            return status_text, connections_record

        if len(connections_record["listener_port"]) > 0:
            try:
                listener_port = self.mvc_view.ent_mod_listener_port.get()
                connections_record["listener_port"] = int(listener_port)
            except ValueError:
                status_text = 'Please enter a positive integer for the database listener port number.'
                self.mvc_view.mod_status_bar.set_status_text(
                    status_text=status_text)
                return status_text, connections_record

        invalid_tns_message = self.mvc_module.validate_tns_connect(
            tns_connect_string=connections_record["connect_string"],
            wallet_pathname=connections_record["wallet_location"])

        if invalid_tns_message:
            status_text = invalid_tns_message
            return status_text, connections_record

        connections_record["description"] = self.mvc_view.ent_mod_description.get()

        return '', connections_record

    def test_connection(self):
        position_geometry = self.retrieve_geometry(window_category='toplevel')
        geometry_offset = cbtk.geometry_offset(position_geometry, 30, 50)
        popup_geometry = f"300x170{geometry_offset}"

        validation_status, connections_record = self.validate_mod_entries()
        if validation_status:
            confirm = CTkMessagebox(master=self.mvc_view,
                                    title='PAction Required',
                                    message=validation_status,
                                    option_1='OK')
            if confirm.get() == 'OK':
                return

        oci_config = Path(preference(db_file_path=self.db_file_path,
                                     scope='preference',
                                     preference_name='oci_config'))
        if connections_record["connection_type"] == 'OCI Vault':
            try:
                password = oci_secret(config_file_pathname=oci_config,
                                      oci_profile=connections_record['oci_profile'],
                                      secret_id=connections_record['ocid'])
            except Exception as e:
                confirm = CTkMessagebox(master=self.mvc_view,
                                        title='OCI Error Encountered',
                                        icon='warning',
                                        message=f'OCI Error encounter: {repr(e)}',
                                        option_1='OK')
                if confirm.get() == 'OK':
                    pass
        else:
            password = connections_record['ocid']

        connect_string = connections_record["connect_string"]
        wallet_required = connections_record["wallet_required_yn"]
        wallet_location = connections_record["wallet_location"]
        if wallet_location:
            wallet_pathname = wallet_location
        else:
            wallet_pathname = ''
        host, port = self.mvc_module.host_port_from_connect_str(connection_string=connect_string,
                                                                wallet_pathname=wallet_pathname)
        tk_state = None
        stale_connection = False
        port_open = False
        port_open = port_is_open(host=host, port_number=port)
        position_geometry = self.retrieve_geometry(window_category='toplevel')

        if wallet_required == "Y" and not port_open:
            confirm = CTkMessagebox(master=self.mvc_view,
                                    title='PAction Required',
                                    message=f"Database server, {host}, cannot be reached on port "
                                            f"{port} Connection may require ssh tunnel, VPN etc, to be "
                                            "established.",
                                    option_1='OK')
            if confirm.get() == 'OK':
                return
        elif not port_open:
            confirm = CTkMessagebox(master=self.mvc_view,
                                    title='PAction Required',
                                    message=f"Database server, {host}, cannot be reached on port "
                                            f"{port}. Please check that the database server is contactable and "
                                            f"that the database, and database listener are started.",
                                    option_1='OK')
            if confirm.get() == 'OK':
                return

        # TODO: Complete the hook in function test_db_connection and handling of returned messages (needs a status bar).
        if wallet_required == 'Y':
            wallet_pathname = connections_record["wallet_location"]
        else:
            wallet_pathname = ''
        connect_result = test_db_connection(username=connections_record["db_account_name"],
                                            password=password,
                                            connect_string=connect_string,
                                            wallet_pathname=wallet_pathname)

        self.mvc_view.mod_status_bar.set_status_text(status_text=connect_result)

    def upsert_connection(self):
        """Update/Insert a new/modified connections row. We require a dictionary, which reflects the table column names
        and their value assignments. This method is called from the modify_connection method."""
        validation_status, connections_record = self.validate_mod_entries()
        if validation_status:
            confirm = CTkMessagebox(master=self.mvc_view.top_mod_connection,
                                    title='Action Required',
                                    message=validation_status,
                                    option_1='OK')
            if confirm.get() == 'OK':
                return
        status = status_text = self.mvc_module.upsert_connection(connections_record=connections_record)
        position_geometry = self.retrieve_geometry(window_category='toplevel')

        geometry_offset = cbtk.geometry_offset(position_geometry, 50, 100)
        if validation_status:
            confirm = CTkMessagebox(master=self.mvc_view.top_mod_connection,
                                    title='Action Required',
                                    message=status_text,
                                    option_1='OK')
            if confirm.get() == 'OK':
                return

        geometry_offset = cbtk.geometry_offset(position_geometry, 50, 100)
        if status:
            self.status_bar.set_status_text(
                status_text=status_text)

            confirm = CTkMessagebox(master=self.mvc_view.top_mod_connection,
                                    title='Action Required',
                                    message=status_text,
                                    option_1='OK')
            if confirm.get() == 'OK':
                return

        self.update_opm_connections()
        self.mvc_view.opm_connections.set(self.mvc_view.ent_mod_connection_identifier.get())
        self.mvc_view.btn_modify.configure(state=tk.NORMAL)
        self.mvc_view.on_close_connections_maintenance()
        self.status_bar.set_status_text(
            status_text=f'Connection {connections_record["connection_identifier"]} saved.')

    def present_connection_details(self):
        """This function is used to load the selected connection's details to the modification frames."""
        connection_record = self.selected_connection_record()
        self.mvc_view.ent_mod_connection_identifier.insert(0, connection_record["connection_identifier"])
        self.mvc_view.opm_mod_database_type.set(connection_record["database_type"])
        self.mvc_view.opm_mod_connection_type.set(connection_record["connection_type"])
        self.mvc_view.ent_mod_db_account_name.insert(0, connection_record["db_account_name"])
        self.mvc_view.cmo_mod_oci_profile.set(connection_record["oci_profile"])
        self.mvc_view.ent_mod_ocid.insert(0, connection_record["ocid"])
        self.mvc_view.cmo_mod_connect_string.set(connection_record["connect_string"])
        self.mvc_view.tk_mod_ssh_tunnel_required_yn.set(connection_record["ssh_tunnel_required_yn"])
        self.mvc_view.opm_mod_tunnel_code.set(connection_record["ssh_tunnel_code"])
        self.mvc_view.tk_mod_listener_port.set(str(connection_record["listener_port"]))
        self.mvc_view.opm_mod_connection_banner.set(str(connection_record["connection_banner"]))
        if connection_record["connection_message"]:
            self.mvc_view.tk_mod_connection_message.set(str(connection_record["connection_message"]))
        self.mvc_view.opm_mod_connection_text_colour.set(str(connection_record["connection_text_colour"]))
        if connection_record["client_tool_options"] is not None:
            self.mvc_view.ent_mod_client_tool_options.insert(0, connection_record["client_tool_options"])

        wallet_location = connection_record["wallet_location"]
        self.wallet_pathname = wallet_location
        wallet_name = os.path.basename(wallet_location)
        self.mvc_view.lbl_mod_wallet_name.configure(text=wallet_name)
        start_directory = connection_record["start_directory"]
        if start_directory is None:
            start_directory = ''
        if len(start_directory) > 41:
            launch_dir = start_directory
            launch_dir = f'... {launch_dir[-41:]}'
        else:
            launch_dir = start_directory
        self.mvc_view.lbl_mod_disp_launch_directory.configure(text=launch_dir)
        self.mvc_view.opm_mod_client_tool.set(connection_record["client_tool"])
        templates = preferences_scope_names(db_file_path=self.db_file_path, scope='client_tools')
        self.mvc_view.opm_mod_client_tool.configure(values=templates)
        self.set_client_options_state()
        self.mvc_view.tk_mod_wallet_required.set(connection_record["wallet_required_yn"])
        if connection_record["connection_type"] == 'OCI Vault':
            self.mvc_view.cmo_mod_oci_profile.configure(state=tk.NORMAL)
            self.mvc_view.lbl_mod_oci_profile.configure(state=tk.NORMAL)
        else:
            self.mvc_view.swt_mod_wallet_required.grid()
            self.mvc_view.cmo_mod_oci_profile.configure(state=tk.DISABLED)
            self.mvc_view.lbl_mod_oci_profile.configure(state=tk.DISABLED)
        if not exists(connection_record["wallet_location"]) and connection_record["wallet_required_yn"] == 'Y':
            position_geometry = self.retrieve_geometry(window_category='toplevel')
            geometry_offset = cbtk.geometry_offset(position_geometry, 50, 50)

            confirm = CTkMessagebox(master=self.mvc_view,
                                    title='Action Required',
                                    message=f'The associated wallet, {wallet_location}, for this '
                                            f'connection, cannot be found. '
                                            f'Please rectify.',
                                    option_1='OK')
            if confirm.get() == 'OK':
                return
        if connection_record["wallet_required_yn"] == 'Y':
            tns_connect_dict = self.mvc_module.wallet_tns_connect_dict(
                wallet_pathname=connection_record["wallet_location"])

            tns_connect_list = []
            for connect_str in tns_connect_dict.keys():
                tns_connect_list.append(connect_str)
        else:
            tns_connect_list = self.mvc_module.tns_names_alias_list()
        self.mvc_view.cmo_mod_connect_string.configure(values=tns_connect_list)

    def ask_default_wallet_directory(self):
        """The ask_default_wallet_directory method is launched from the DCCM Preferences dialog. It in turn, launches
        a navigation window, allowing the user to navigate to, and select the user's wallet location. Once selected
        the selection is updated to the dialog window."""
        default_wallet_directory_ = preference(db_file_path=db_file,
                                               scope='preference',
                                               preference_name='default_wallet_directory')
        home_directory = Path(expanduser("~"))
        if default_wallet_directory_:
            initial_directory = default_wallet_directory_
        else:
            initial_directory = home_directory
        default_wallet_directory_ = fd.askdirectory(initialdir=initial_directory)
        if default_wallet_directory_:
            self.default_wallet_directory = default_wallet_directory_
            self.mvc_view.lbl_default_wallet_name.configure(text=f'{self.default_wallet_directory}')

    def ask_client_launch_directory(self):
        """The ask_client_launch_directory method is launched from the Connections maintenance dialog. It in turn,
        launches a navigation window, allowing the user to navigate to, and select an initial directory, from which
        the connection's client tool will be launched. Once selected the selection is updated to the dialog window."""
        client_launch_directory = fd.askdirectory(initialdir=self.client_launch_directory)
        if client_launch_directory:
            self.client_launch_directory = client_launch_directory
            if len(self.client_launch_directory) > 41:
                launch_dir = self.client_launch_directory
                launch_dir = f'... {launch_dir[-41:]}'
            else:
                launch_dir = f'{self.client_launch_directory}'
            self.mvc_view.lbl_mod_disp_launch_directory.configure(text=f'{launch_dir}')

    def get_oci_config(self):
        """The get_oci_config method is launched from the DCCM Preferences dialog. It in turn, launches
        a navigation window, allowing the user to navigate to, and select the user's wallet location. Once selected
        the selection is updated to the dialog window."""
        home_directory = Path(expanduser("~"))
        if exists(home_directory / '.oci'):
            initial_directory = home_directory / '.oci'
        else:
            initial_directory = home_directory

        oci_config = fd.askopenfilename(initialdir=initial_directory)
        if oci_config:
            self.oci_config = oci_config
            self.mvc_view.lbl_oci_config.configure(text=f'{self.oci_config}')

    def oci_config_profiles_list(self):
        """The oci_config_profiles_list method, acts as a broker, interacting with the module class and returning a
        list of OCI profiles from the users OCI  config file."""
        db_file_path = db_file
        return self.mvc_module.oci_config_profiles_list(db_file_path=db_file_path)

    def ask_import_file(self):
        """The ask_import_file method, is called from the import (GUI) dialog, allowing the user to select a JSON file
        from which to import connections."""
        self.import_json = None
        import_pathname = fd.askopenfilename(filetypes=[('JSON', '*.json')])
        if len(import_pathname) == 0:
            return
        import_pathname = Path(import_pathname)
        connect_strings = []
        if import_pathname == Path('.'):
            return
        import_file = import_pathname
        position_geometry = self.retrieve_geometry(window_category='toplevel')
        geometry_offset = cbtk.geometry_offset(position_geometry, 50, 50)
        with open(import_file) as json_file:
            try:
                import_json = json.load(json_file)
            except ValueError:
                position_geometry = self.retrieve_geometry(window_category='toplevel')
                geometry_offset = cbtk.geometry_offset(position_geometry, 50, 50)
                confirm = CTkMessagebox(master=self.mvc_view,
                                        title='Bad Import File',
                                        message=f'The file, "{import_file}", does not appear to be a valid '
                                                f'export file (JSON parse error).',
                                        option_1='OK')
                if confirm.get() == 'OK':
                    return
            except IOError:
                feedback = f'Failed to read file {import_file} - possible permissions issue.'
                position_geometry = self.retrieve_geometry(window_category='toplevel')
                geometry_offset = cbtk.geometry_offset(position_geometry, 50, 50)
                confirm = CTkMessagebox(master=self.mvc_view.top_import,
                                        title='Bad Import File',
                                        message=f'Failed to open, "{import_file}" - possible permissions of '
                                                f'disk space issue.',
                                        option_1='OK')
                if confirm.get() == 'OK':
                    return

        source = None
        if len(import_json) == 2:
            if import_json[0]["data_source"] == f'{prog}':
                source = 'native'
        elif "connections" in import_json:
            source = "sql_developer"
        else:
            confirm = CTkMessagebox(master=self.mvc_view.top_import,
                                    title='Bad Import File',
                                    message=f'The file, "{import_file}", is not a recognised export format '
                                            f'export file.',
                                    option_1='OK')
            if confirm.get() == 'OK':
                return

        self.mvc_view.lbl_imp_import_file.configure(text=import_file)
        password_hash = ''
        connection_id_list = []
        if source == 'native':
            header = import_json[0]
            body = import_json[1]
            for connection_name in body.keys():
                connection_id_list.append(connection_name)
            password_hash = header["password_hash"]
            if password_hash:
                self.mvc_view.imp_status_bar.set_status_text(
                    status_text='Connection passwords are password encrypted, within the selected export file.')
        else:
            connections = import_json["connections"]
            for entry_dict in connections:
                connection_name = entry_dict["name"]
                connection_id_list.append(connection_name)
            self.mvc_view.imp_status_bar.set_status_text(
                status_text='Selected file is a SQL Developer export - passwords will not be included during import.')

        self.mvc_view.lbx_imp_import_connections.set_values(values=connection_id_list)

        if password_hash:
            self.mvc_view.lbl_imp_import_password.grid()
            self.mvc_view.ent_imp_import_password.grid()
        else:
            self.mvc_view.lbl_imp_import_password.grid_remove()
            self.mvc_view.ent_imp_import_password.grid_remove()

        self.import_pathname = import_pathname

    def ask_wallet_location(self):
        """The ask_wallet_location method, is called from the connections maintenance dialog. It allows the user to
        select a wallet (zip file), for a connection requiring cloud database access."""
        wallets_dir = self.default_wallet_directory
        wallet_pathname = Path(fd.askopenfilename(initialdir=wallets_dir, initialfile=self.wallet_pathname))

        position_geometry = self.retrieve_geometry(window_category='toplevel')
        geometry_offset = cbtk.geometry_offset(position_geometry, 50, 50)
        connect_strings = []
        if wallet_pathname == Path('.'):
            return

        self.connect_strings = []
        self.port_mappings_dict = {}
        self.wallet_pathname = wallet_pathname
        self.mvc_view.lbl_mod_wallet_name.configure(text=f'{os.path.basename(self.wallet_pathname)}')
        with ZipFile(self.wallet_pathname, 'r') as zip:
            try:
                tns = zip.read('tnsnames.ora').decode(encoding="utf-8")
            except KeyError:
                confirm = CTkMessagebox(master=self.mvc_view.top_mod_connection,
                                        title='Template in Use',
                                        message=f"Failed to find tnsnames.ora in the wallet file: "
                                                f"{wallet_pathname}. This doesn't look like a valid wallet "
                                                f"file.",
                                        option_1='OK')
                if confirm.get() == 'OK':
                    return
        tns = tns.replace('\r', '')
        for line in tns.split('\n'):
            if len(line) == 0:
                continue
            # line = lines.split(' ')
            # print(f'DBX: Line = {line}')
            connect_string = re.findall("^[\S]+", line)
            connect_string = connect_string[0]
            self.connect_strings.append(connect_string)
            connect_strings.append(connect_string)
            port = re.findall("port=\d{1,5}", line, re.IGNORECASE)
            port = port[0]
            port = str(port).split('=')[1]
            self.port_mappings_dict[connect_string] = port
            # self.port_list.append(port)
            self.mvc_view.cmo_mod_connect_string.configure(values=connect_strings)
            self.mvc_view.cmo_mod_connect_string.set(connect_strings[0])

    def mod_ssh_listener_port(self):
        ssh_tunnel_required_yn = self.mvc_view.tk_mod_ssh_tunnel_required_yn.get()

        if ssh_tunnel_required_yn == 'Y':
            ssh_template_code = self.mvc_view.opm_mod_tunnel_code.get()
            ssh_template = preference(db_file_path=db_file, scope='ssh_templates', preference_name=ssh_template_code)
            if ssh_template is None:
                return None
            if "#listener_port#" in ssh_template:
                return "#listener_port#"
            # Get the port and host/ip segment...
            # address = ssh_template.split(' ')[-2]
            address_pattern = r'\d.*:.*:\d*'
            pattern = re.compile(address_pattern)
            match = re.search(pattern, ssh_template)

            if match is not None:
                address = match.group()
            else:
                return 'ERROR'
            # Get the port from the 3rd component...
            template_listener_port = address.split(':')[2]
            try:
                int(template_listener_port)
            except ValueError:
                # If we fail to obtain a port number...
                template_listener_port = ''
        else:
            return ''

        current_listener_port = self.mvc_view.ent_mod_listener_port.get()
        if current_listener_port:
            try:
                int(current_listener_port)
            except ValueError:
                # If we fail to obtain a port number...
                current_listener_port = ''

        if template_listener_port:
            return template_listener_port
        elif current_listener_port:
            return current_listener_port
        else:
            return 0

    def toggle_mod_ssh_port(self, event=None):
        """The toggle_mod_ssh_port method, works in conjunction with the mod_ssh_listener_port method, to resolve
        the database listener port. If the ssh tunnelling template has the port hard-coded (doesn't use #listener_port#)
         then we need to store the hard-wired value. However, we need to ensure that the widget reflects the latest
        port number, whenever we visit the maintenance dialog, in case the template is modified at any point."""
        listener_port = self.mod_ssh_listener_port()

        if listener_port is not None and "#listener_port#" in listener_port:
            self.mvc_view.lbl_mod_listener_port.configure(state=tk.NORMAL)
            self.mvc_view.ent_mod_listener_port.configure(state=tk.NORMAL)
        elif listener_port is not None:
            self.mvc_view.tk_mod_listener_port.set(listener_port)
            self.mvc_view.lbl_mod_listener_port.configure(state=tk.DISABLED)
            self.mvc_view.ent_mod_listener_port.configure(state=tk.DISABLED)

    def toggle_mod_wallet_display(self):
        """The toggle_mod_wallet_display method, is called when the state of the "wallet required" widget changes. It
        is responsible for showing / hiding wallet related widgets."""
        switch = self.mvc_view.swt_mod_wallet_required.get()
        if switch == 'Y':
            self.mvc_view.lbl_mod_wallet_location.grid()
            self.mvc_view.btn_mod_wallet_location.grid()
            # self.mvc_view.lbl_mod_wallet_name.grid()
            connection_id = self.mvc_view.ent_mod_connection_identifier.get()
            tns_connect_list = self.mvc_module.wallet_connect_string_list(connection_identifier=connection_id)
            self.mvc_view.cmo_mod_connect_string.configure(values=tns_connect_list)
        else:
            self.mvc_view.lbl_mod_wallet_location.grid_remove()
            self.mvc_view.btn_mod_wallet_location.grid_remove()
            self.mvc_view.lbl_mod_wallet_name.configure(text='')
            self.wallet_pathname = ''
            tns_connect_list = self.mvc_module.tns_names_alias_list()
            self.mvc_view.cmo_mod_connect_string.configure(values=tns_connect_list)

    def toggle_import_wallets(self):
        default_wallet_directory = preference(db_file_path=db_file,
                                              scope='preference',
                                              preference_name='default_wallet_directory')
        if default_wallet_directory is not None:
            default_wallet_directory = Path(default_wallet_directory)
        else:
            default_wallet_directory = ''

        if default_wallet_directory == 'None':
            self.mvc_view.tk_imp_import_wallets.set('N')
            self.mvc_view.swt_imp_remap_wallet.deselect()
            self.mvc_view.swt_imp_import_wallets.configure(state=tk.DISABLED)

        remap_wallets_yn = self.mvc_view.tk_remap_wallets.get()
        if remap_wallets_yn == 'Y':
            self.mvc_view.swt_imp_import_wallets.configure(state=tk.NORMAL)
        else:
            self.mvc_view.tk_imp_import_wallets.set('N')
            self.mvc_view.swt_imp_import_wallets.configure(state=tk.DISABLED)

    def toggle_mod_cloud_widgets(self, event=None):
        """The toggle_mod_cloud_widgets method, is called when the "connection/management type" selector changes. It
        is responsible for showing / hiding / re-presenting OCI Vault related widgets."""
        connection_type = self.mvc_view.opm_mod_connection_type.get()

        if connection_type == 'OCI Vault':
            self.mvc_view.show_vault_mod_widgets()
            self.mvc_view.lbl_mod_ocid.configure(text='Cloud Secret OCID:')
        else:
            self.mvc_view.hide_vault_mod_widgets()
            self.mvc_view.cmo_mod_connect_string.configure(values=self.mvc_module.tns_names_alias_list())
            self.mvc_view.lbl_mod_ocid.configure(text='Password:')

        self.toggle_mod_wallet_display()

        connection_identifier = self.mvc_view.opm_connections.get()
        wallet_required = self.mvc_view.tk_mod_wallet_required.get()
        if wallet_required and self.wallet_pathname and self.mvc_view.ent_mod_db_account_name.get():
            connect_list = self.mvc_module.wallet_connect_string_list(connection_identifier=connection_identifier)
            self.mvc_view.cmo_mod_connect_string.configure(values=connect_list)

    def cancel_tunnel_operation(self):
        """The cancel_tunnel_operation method, is called when the Cancel button is activated in the SSH Tunnelling
         Templates dialog. It is responsible for managing widget states within the dialog. Note that the Cancel button
         is not used to close the dialog, but rather to cancel an operation, such as adding a new template or modifying
         a selected template."""
        self.mvc_view.tk_tunnel_ssh_tunnel_code.set('')
        self.mvc_view.tk_tunnel_command_template.set('')
        self.mvc_view.opm_tunnel_templates.configure(state=tk.NORMAL)
        self.mvc_view.btn_tunnel_new.configure(state=tk.NORMAL)
        self.mvc_view.btn_tunnel_save.configure(state=tk.DISABLED)
        self.mvc_view.lbl_tunnel_ssh_tunnel_code.configure(state=tk.DISABLED)
        self.mvc_view.lbl_tunnel_command_template.configure(state=tk.DISABLED)
        self.mvc_view.btn_tunnel_delete.configure(state=tk.DISABLED)
        self.mvc_view.btn_tunnel_cancel.configure(state=tk.DISABLED)
        self.mvc_view.ent_tunnel_ssh_tunnel_code.configure(state=tk.DISABLED)
        self.mvc_view.ent_tunnel_command_template.configure(state=tk.DISABLED)
        self.set_opm_tunnel_templates()

        self.mvc_view.tunnel_status_bar.set_status_text(
            status_text='Operation cancelled.')

    def launch_import_dialog(self):
        """The launch_import_dialog is the entry point to the GUI import interface."""
        self.mvc_view.launch_import_dialog()
        connections_list = []
        self.mvc_view.lbx_imp_import_connections.set_values(values=connections_list)

    def launch_export_dialog(self):
        """The launch_export_dialog is the entry point to the GUI export interface."""
        self.mvc_view.launch_export_dialog()
        connections_list = self.mvc_module.connection_identifiers_list()
        # self.mvc_view.lbx_export_connections.configure(values=connections_list)
        self.mvc_view.lbx_export_connections.set_values(values=connections_list)

    def begin_connection_import(self):
        """The begin_connection_import is called from the GUI import dialog. It performs some initial checks, ensuring
        for example, that an export file has been selected to import from, before going on to request of the module
        class instance, that the import request be actioned."""
        import_connections = self.mvc_view.lbx_imp_import_connections.get()

        if self.import_pathname is None:
            self.mvc_view.imp_status_bar.set_status_text(status_text='You must select the Import File to import from.')
            return

        if import_connections is None:
            self.mvc_view.imp_status_bar.set_status_text(status_text='You must select at least one connection to import.')
            return

        import_file = self.import_pathname
        password = self.mvc_view.ent_imp_import_password.get()
        merge_connections = self.mvc_view.tk_imp_merge.get()
        if merge_connections == 'Y':
            merge_connections = True
        else:
            merge_connections = False
        remap_wallets_yn = self.mvc_view.tk_remap_wallets.get()
        import_wallets_yn = self.mvc_view.tk_imp_import_wallets.get()

        if remap_wallets_yn == 'Y':
            remap_wallets = True
        else:
            remap_wallets = False

        if import_wallets_yn == 'Y':
            import_wallets = True
        else:
            import_wallets = False

        feedback = self.mvc_module.import_connections_list(dump_file=str(import_file),
                                                           run_mode=run_mode,
                                                           connections_list=import_connections,
                                                           password=password,
                                                           merge_connections=merge_connections,
                                                           remap_wallet_locations=remap_wallets,
                                                           import_wallets=import_wallets)
        self.mvc_view.imp_status_bar.set_status_text(status_text=feedback)
        self.update_opm_connections()

    def begin_connection_export(self):
        """The begin_connection_export is called from the GUI export dialog. When called it in turn has the user
        navigate to a directory, via a dialog, and enter an export filename to export to, before going on to request
        of the module class instance, that the import request be actioned."""
        exp_connections_list = self.mvc_view.lbx_export_connections.get()
        if exp_connections_list is None:
            self.mvc_view.export_status_bar.set_status_text(
                status_text=f'You must select, at least one connection to export.')
            return

        exp_password = self.mvc_view.ent_export_password.get()

        exp_password_confirm = self.mvc_view.ent_export_password2.get()
        if exp_password != exp_password_confirm:
            self.mvc_view.export_status_bar.set_status_text(
                status_text=f'The passwords do not match - please re-enter.')
            return

        export_wallets_yn = self.mvc_view.tk_export_wallets.get()
        if export_wallets_yn == 'Y' and not exp_password:
            self.mvc_view.export_status_bar.set_status_text(
                status_text=f'Wallets can only be shipped where an export password is supplied.')
            return

        if export_wallets_yn == 'Y':
            include_wallets = True
        else:
            include_wallets = False

        exp_file = fd.asksaveasfile(filetypes=[('JSON', '*.json')], defaultextension=".json")
        if exp_file is None:
            return

            return

        feedback = self.mvc_module.export_connections_list(dump_file=exp_file.name,
                                                           run_mode=run_mode,
                                                           connections_list=exp_connections_list,
                                                           password=exp_password,
                                                           include_wallets=include_wallets)
        self.mvc_view.export_status_bar.set_status_text(
            status_text=feedback)

    def launch_client_tool_templates(self):
        """The launch_client_tool_templates method, is responsible for getting the DCCM Client Tool Templates dialog
        to launch."""
        self.mvc_view.launch_client_tool_templates()
        self.set_opm_client_tool_templates()

    def launch_tunnel_templates(self):
        """The launch_tunnel_templates method, is responsible for getting the DCCM Tunneling Templates to launch."""
        self.mvc_view.launch_tunnel_templates()
        self.set_opm_tunnel_templates()

    def set_client_options_state(self, event=None):
        """The set_client_options_state method, is responsible for setting the states of the SQLcl command line
         options widgets. We only enable these where the selected client tool is SQLcl."""
        client_tool = self.mvc_view.opm_mod_client_tool.get()

        if client_tool == 'SQLcl':
            self.mvc_view.lbl_mod_client_tool_options.configure(state=tk.NORMAL)
            self.mvc_view.ent_mod_client_tool_options.configure(state=tk.NORMAL)
        else:
            self.mvc_view.lbl_mod_client_tool_options.configure(state=tk.DISABLED)
            self.mvc_view.ent_mod_client_tool_options.configure(state=tk.DISABLED)

    def set_opm_tunnel_templates(self):
        """The set_opm_tunnel_templates method, is used to initialise the tunnel selection widget within the DCCM
        Tunneling Templates dialog. It is responsible for obtaining the list of tunnelling templates to be presented."""
        templates = preferences_scope_names(db_file_path=self.db_file_path, scope='ssh_templates')
        if templates:
            select_template = '-- Select Template --'
            select = [select_template]
            self.mvc_view.opm_tunnel_templates.set(select_template)
            templates = select + templates
            self.mvc_view.opm_tunnel_templates.configure(state=tk.NORMAL, values=templates)
        else:
            self.mvc_view.opm_tunnel_templates.set('Nothing to select')

    def delete_tunnel_template(self):
        """The delete_tunnel_template method is called to delete an ssh tunnelling template. It is called via the
        DCCM Tunneling Templates dialog."""
        template_code = self.mvc_view.opm_tunnel_templates.get()
        usage_list = self.mvc_module.tunnel_template_usage(ssh_tunnel_code=template_code)
        usage_count = len(usage_list)

        position_geometry = self.retrieve_geometry(window_category='toplevel')
        geometry_offset = cbtk.geometry_offset(position_geometry, 50, 50)

        if usage_list:
            confirm = CTkMessagebox(master=self.mvc_view.top_tunnel,
                                    title='Template in Use',
                                    message=f'The template named "{template_code}", is currently, '
                                            f'referenced by {usage_count} connections, and so cannot be deleted.',
                                    option_1='OK')
            if confirm.get() == 'OK':
                return

        confirm = CTkMessagebox(master=self.mvc_view.top_tunnel,
                                title='Confirm Action',
                                message=f'Are you sure you wish to delete the "{template_code}" template entry?',
                                options=['Yes', 'No'])
        if confirm.get() == 'No':
            return

        delete_preference(db_file_path=db_file, scope='ssh_templates', preference_name=template_code)
        self.mvc_view.btn_tunnel_delete.configure(state=tk.DISABLED)
        self.mvc_view.btn_tunnel_save.configure(state=tk.DISABLED)
        self.mvc_view.tk_tunnel_ssh_tunnel_code.set('')
        self.mvc_view.tk_tunnel_command_template.set('')
        self.set_opm_tunnel_templates()
        self.mvc_view.tunnel_status_bar.set_status_text(
            status_text=f'SSH template, "{template_code}", deleted.')

    def save_tunnel_template(self, event=None):
        """The save_tunnel_template method is called to insert or update an ssh tunnelling template. It is called
        via the DCCM Tunneling Templates dialog."""
        template_code = self.mvc_view.tk_tunnel_ssh_tunnel_code.get().strip()
        command_template = self.mvc_view.tk_tunnel_command_template.get()

        position_geometry = self.retrieve_geometry(window_category='toplevel')
        geometry_offset = cbtk.geometry_offset(position_geometry, 50, 50)

        if not template_code:
            confirm = CTkMessagebox(master=self.mvc_view.top_tunnel,
                                    title='Action Required',
                                    message=f'You must enter a Template Name.',
                                    option_1='OK')
            if confirm.get() == 'OK':
                return
        if self.tunnel_operation == 'add':
            already_exists = preference(db_file_path=db_file,
                                        scope='ssh_templates',
                                        preference_name=template_code)
            if already_exists:
                confirm = CTkMessagebox(master=self.mvc_view.top_tunnel,
                                        title='Action Required',
                                        message=f'A template named "{template_code}", already exists, '
                                                f'"please chose a different name.',
                                        option_1='OK')
                if confirm.get() == 'OK':
                    return
            self.mvc_view.btn_tunnel_save.configure(state=tk.DISABLED)
        upsert_preference(db_file_path=db_file, scope='ssh_templates',
                          preference_name=template_code,
                          preference_value=command_template,
                          preference_label='SSH Tunnelling Template')
        self.mvc_view.btn_tunnel_delete.configure(state=tk.DISABLED)
        if self.tunnel_operation == 'add':
            self.mvc_view.btn_tunnel_save.configure(state=tk.DISABLED)
            self.mvc_view.btn_tunnel_new.configure(state=tk.NORMAL)
            self.mvc_view.tunnel_status_bar.set_status_text(
                status_text=f'SSH template, "{template_code}", inserted to database.')
        else:
            self.mvc_view.tunnel_status_bar.set_status_text(
                status_text=f'SSH template, "{template_code}", updated to database.')
        self.set_opm_tunnel_templates()

    def new_client_tool_template(self):
        """The new_tunnel_template method, sets the widget states accordingly, for a new template, within the DCCM
        Tunneling Templates dialog, whenever the "New Template" button is activated."""
        self.cltool_operation = 'add'
        command_template = '<example-command> -u #db_account_name# -p #password# -s #connect_string#'
        self.mvc_view.tk_cltool_command_template.set(command_template)
        self.mvc_view.lbl_cltool_client_tool_code.configure(state=tk.NORMAL)
        self.mvc_view.ent_cltool_client_tool_code.configure(state=tk.NORMAL)
        self.mvc_view.btn_cltool_save.configure(state=tk.NORMAL)
        self.mvc_view.btn_cltool_cancel.configure(state=tk.NORMAL)
        self.mvc_view.lbl_cltool_command_template.configure(state=tk.NORMAL)
        self.mvc_view.ent_cltool_command_template.configure(state=tk.NORMAL)
        self.mvc_view.opm_client_tool_templates.configure(state=tk.DISABLED)
        self.mvc_view.btn_cltool_delete.configure(state=tk.DISABLED)
        self.mvc_view.btn_cltool_new.configure(state=tk.DISABLED)
        self.mvc_view.tk_cltool_client_tool_code.set('')
        self.mvc_view.ent_cltool_client_tool_code.focus_set()

    def save_client_tool_template(self, event=None):
        """The save_client_tool_template method is called to insert or update a client tool template. It is called
        via the DCCM Client Tool Templates dialog."""
        template_code = self.mvc_view.tk_cltool_client_tool_code.get().strip()
        command_template = self.mvc_view.tk_cltool_command_template.get()

        position_geometry = self.retrieve_geometry(window_category='toplevel')
        geometry_offset = cbtk.geometry_offset(position_geometry, 50, 50)

        if not template_code:
            confirm = CTkMessagebox(master=self.mvc_view.top_client_tool,
                                    title='Action Required',
                                    message=f'You must enter a Template Name.',
                                    option_1='OK')
            if confirm.get() == 'OK':
                return
        if self.cltool_operation == 'add':
            already_exists = preference(db_file_path=db_file,
                                        scope='client_tools',
                                        preference_name=template_code)
            if already_exists:
                confirm = CTkMessagebox(master=self.mvc_view.top_client_tool,
                                        title='Action Required',
                                        message=f'A template named "{template_code}", already exists, '
                                                f'"please chose a different name.',
                                        option_1='OK')
                if confirm.get() == 'OK':
                    return
            self.mvc_view.btn_cltool_save.configure(state=tk.DISABLED)
        upsert_preference(db_file_path=db_file, scope='client_tools',
                          preference_name=template_code,
                          preference_value=command_template,
                          preference_label='')
        self.mvc_view.btn_cltool_delete.configure(state=tk.DISABLED)
        if self.cltool_operation == 'add':
            self.mvc_view.btn_cltool_save.configure(state=tk.DISABLED)
            self.mvc_view.btn_cltool_new.configure(state=tk.NORMAL)
            self.mvc_view.client_tool_status_bar.set_status_text(
                status_text=f'Client tool template, "{template_code}", inserted to database.')
        else:
            self.mvc_view.client_tool_status_bar.set_status_text(
                status_text=f'Client tool template, "{template_code}", updated to database.')
        self.set_opm_client_tool_templates()

    def delete_client_tool_template(self):
        """The delete_client_tool_template method is called to delete an client tool template. It
        is called via the DCCM Client Tool Templates dialog."""
        template_code = self.mvc_view.opm_client_tool_templates.get()
        usage_list = self.mvc_module.client_tool_template_usage(client_tool_code=template_code)
        usage_count = len(usage_list)

        position_geometry = self.retrieve_geometry(window_category='toplevel')
        geometry_offset = cbtk.geometry_offset(position_geometry, 50, 50)

        if usage_list:
            confirm = CTkMessagebox(master=self.mvc_view.top_client_tool,
                                    title='Template in Use',
                                    message=f'The template named "{template_code}", is currently, '
                                            f'referenced by {usage_count} connections, and so cannot be deleted.',
                                    option_1='OK')
            if confirm.get() == 'OK':
                return
        confirm = CTkMessagebox(master=self.mvc_view.top_client_tool,
                                title='Template in Use',
                                message=f'Are you sure you wish to delete the "{template_code}" template entry?',
                                options=['Yes', 'No'])
        if confirm == 'No':
            return
        delete_preference(db_file_path=db_file, scope='client_tools', preference_name=template_code)
        self.mvc_view.btn_cltool_delete.configure(state=tk.DISABLED)
        self.mvc_view.btn_cltool_save.configure(state=tk.DISABLED)
        self.mvc_view.tk_cltool_client_tool_code.set('')
        self.mvc_view.tk_cltool_command_template.set('')
        self.set_opm_client_tool_templates()
        self.mvc_view.client_tool_status_bar.set_status_text(
            status_text=f'Client tool template, "{template_code}", deleted.')

    def on_close_client_tools(self):
        """The on_close_client_tools method, tidies up when we close the client tools templates maintenance dialog."""
        try:
            self.mvc_view.client_tool_status_bar.cancel_message_timer()
        except ValueError:
            # We get a value error if we haven't issued a message and incurred an "after",
            # since there is no "after" event to cancel.
            pass
        self.mvc_view.top_client_tool.destroy()
        cbtk.raise_tk_window(self)

    def cancel_client_tool_operation(self):
        """The cancel_client_tool_operation method, is called when the Cancel button is activated in the Client Tool Templates
         dialog. It is responsible for managing widget states within the dialog. Note that the Cancel button
         is not used to close the dialog, but rather to cancel an operation, such as adding a new template or modifying
         a selected template."""
        self.mvc_view.tk_cltool_client_tool_code.set('')
        self.mvc_view.tk_cltool_command_template.set('')
        self.mvc_view.opm_client_tool_templates.configure(state=tk.NORMAL)
        self.mvc_view.btn_cltool_new.configure(state=tk.NORMAL)
        self.mvc_view.btn_cltool_save.configure(state=tk.DISABLED)
        self.mvc_view.lbl_cltool_client_tool_code.configure(state=tk.DISABLED)
        self.mvc_view.lbl_cltool_command_template.configure(state=tk.DISABLED)
        self.mvc_view.lbl_cltool_templates.configure(state=tk.DISABLED)
        self.mvc_view.btn_cltool_delete.configure(state=tk.DISABLED)
        self.mvc_view.btn_cltool_cancel.configure(state=tk.DISABLED)
        self.mvc_view.ent_cltool_client_tool_code.configure(state=tk.DISABLED)
        self.mvc_view.ent_cltool_command_template.configure(state=tk.DISABLED)
        self.set_opm_client_tool_templates()

        self.mvc_view.client_tool_status_bar.set_status_text(
            status_text='Operation cancelled.')

    def set_opm_client_tool_templates(self):
        """The set_opm_client_tool_templates method, is used to initialise the client tool selection widget within the DCCM
        Client Tool Templates dialog. It is responsible for obtaining the list of client tool templates to be presented."""
        templates = preferences_scope_names(db_file_path=self.db_file_path, scope='client_tools')

        # The SQLcl entry is a special entry, and we don't want anyone
        # monkeying around with it - so we hide it...
        templates.remove('SQLcl')
        if templates:
            select_template = '-- Select Template --'
            select = [select_template]
            self.mvc_view.opm_client_tool_templates.set(select_template)
            templates = select + templates
            self.mvc_view.opm_client_tool_templates.configure(state=tk.NORMAL, values=templates)
        else:
            self.mvc_view.opm_client_tool_templates.set('Nothing to select')

    def new_tunnel_template(self):
        """The new_tunnel_template method, sets the widget states accordingly, for a new template, within the DCCM
        Tunneling Templates dialog, whenever the "New Template" button is activated."""
        self.tunnel_operation = 'add'
        command_template = 'ssh -L #local_port#:#database_host#:#listener_port# <jump-host-entry>'
        self.mvc_view.tk_tunnel_command_template.set(command_template)
        self.mvc_view.lbl_tunnel_ssh_tunnel_code.configure(state=tk.NORMAL)
        self.mvc_view.ent_tunnel_ssh_tunnel_code.configure(state=tk.NORMAL)
        self.mvc_view.btn_tunnel_save.configure(state=tk.NORMAL)
        self.mvc_view.btn_tunnel_cancel.configure(state=tk.NORMAL)
        self.mvc_view.lbl_tunnel_command_template.configure(state=tk.NORMAL)
        self.mvc_view.ent_tunnel_command_template.configure(state=tk.NORMAL)
        self.mvc_view.opm_tunnel_templates.configure(state=tk.DISABLED)
        self.mvc_view.btn_tunnel_delete.configure(state=tk.DISABLED)
        self.mvc_view.btn_tunnel_new.configure(state=tk.DISABLED)
        self.mvc_view.tk_tunnel_ssh_tunnel_code.set('')
        self.mvc_view.ent_tunnel_ssh_tunnel_code.focus_set()

    def select_client_tool_template(self, event=None):
        """The select_client_tool_template method, sets the widget states accordingly, for a selected template, within
        the DCCM Client Tool Templates dialog, whenever an existing template is selected."""
        self.cltool_operation = 'select'
        template_code = self.mvc_view.opm_client_tool_templates.get()
        if template_code == '-- Select Template --':
            return

        self.mvc_view.btn_cltool_delete.configure(state=tk.NORMAL)
        templates = preferences_scope_names(db_file_path=self.db_file_path, scope='client_tools')
        self.mvc_view.opm_client_tool_templates.configure(state=tk.NORMAL, values=templates)
        self.mvc_view.btn_cltool_cancel.configure(state=tk.NORMAL)
        self.mvc_view.lbl_cltool_templates.configure(state=tk.NORMAL)
        self.mvc_view.lbl_cltool_client_tool_code.configure(state=tk.NORMAL)
        self.mvc_view.lbl_cltool_command_template.configure(state=tk.NORMAL)
        self.mvc_view.ent_cltool_command_template.configure(state=tk.NORMAL)
        command_template = preference(db_file_path=db_file, scope='client_tools', preference_name=template_code)
        self.mvc_view.tk_cltool_client_tool_code.set(template_code)
        self.mvc_view.tk_cltool_command_template.set(command_template)
        self.mvc_view.btn_cltool_save.configure(state=tk.NORMAL)
        self.mvc_view.client_tool_status_bar.set_status_text(
            status_text=f'Template, "{template_code}", selected for update.')

    def select_tunnel_template(self, event=None):
        """The select_tunnel_template method, sets the widget states accordingly, for a selected template, within the
        DCCM Tunneling Templates dialog, whenever an existing template is selected."""
        self.tunnel_operation = 'select'
        template_code = self.mvc_view.opm_tunnel_templates.get()
        if template_code == '-- Select Template --':
            return

        self.mvc_view.btn_tunnel_delete.configure(state=tk.NORMAL)
        templates = preferences_scope_names(db_file_path=self.db_file_path, scope='ssh_templates')
        self.mvc_view.opm_tunnel_templates.configure(state=tk.NORMAL, values=templates)
        self.mvc_view.lbl_tunnel_ssh_tunnel_code.configure(state=tk.DISABLED)
        self.mvc_view.ent_tunnel_ssh_tunnel_code.configure(state=tk.DISABLED)
        self.mvc_view.btn_tunnel_cancel.configure(state=tk.NORMAL)
        self.mvc_view.lbl_tunnel_command_template.configure(state=tk.NORMAL)
        self.mvc_view.ent_tunnel_command_template.configure(state=tk.NORMAL)
        command_template = preference(db_file_path=db_file, scope='ssh_templates', preference_name=template_code)
        self.mvc_view.lbl_tunnel_ssh_tunnel_code.configure(state=tk.NORMAL)
        self.mvc_view.tk_tunnel_ssh_tunnel_code.set(template_code)
        self.mvc_view.tk_tunnel_command_template.set(command_template)
        self.mvc_view.btn_tunnel_save.configure(state=tk.NORMAL)
        self.mvc_view.tunnel_status_bar.set_status_text(
            status_text=f'Template, "{template_code}", selected for update.')

    def toggle_mod_tunnel_widgets(self):
        """The toggle_mod_tunnel_widgets method, modifies the states of widgets in the connection maintenance dialog,
        which are dependent upon whether ssh tunnelling is required for the connection being maintained/created."""
        ssh_required = self.mvc_view.swt_mod_ssh_tunnel_required_yn.get()
        if ssh_required == 'Y':
            self.mvc_view.lbl_mod_tunnel_templates.configure(state=tk.NORMAL)
            self.mvc_view.opm_mod_tunnel_code.configure(state=tk.NORMAL)
            self.mvc_view.lbl_mod_listener_port.configure(state=tk.NORMAL)
            self.mvc_view.ent_mod_listener_port.configure(state=tk.NORMAL)
        else:
            self.mvc_view.lbl_mod_tunnel_templates.configure(state=tk.DISABLED)
            self.mvc_view.opm_mod_tunnel_code.configure(state=tk.DISABLED)
            self.mvc_view.lbl_mod_listener_port.configure(state=tk.DISABLED)
            self.mvc_view.ent_mod_listener_port.configure(state=tk.DISABLED)

        # Here, using toggle_mod_ssh_port, we do some tinkering to ensure that the port number is reflected accurately,
        # depending on whether the SSH template has the listener port hard-wired (so we extract and update the display
        # read-only) or alternatively the #listener_port# string is in use by the template, and we allow the user to
        # enter and maintain the port number.
        self.toggle_mod_ssh_port()


if __name__ == "__main__":

    default_wallet_directory = preference(db_file_path=db_file,
                                          scope='preference',
                                          preference_name='default_wallet_directory')
    if 'merge-on' in import_options:
        merge_connections = True
    elif 'merge-off' in import_options:
        merge_connections = False

    remap_wallets = True
    if default_wallet_directory == 'None' and import_connection and 'remap-on' in import_options:
        print("WARNING: Wallet remapping (remap-on') option ignored - you need to set a default wallet location via "
              "the preferences in GUI mode.")
        remap_wallets = False
    elif 'remap-on' in import_options:
        remap_wallets = True
    elif 'remap-off' in import_options:
        remap_wallets = False

    if not exists(db_file):
        print(f'Could not locate the DCCM repository ({db_file}). Did you forget to run dccm-setup.py?')
        exit(1)
    if run_mode != 'gui':
        just_fix_windows_console()

    controller = DCCMControl(app_home, mode=run_mode, db_file_path=db_file, connection_identifier=connection_identifier)
