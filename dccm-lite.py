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
from PIL import Image, ImageTk

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
import hashlib
from kellanb_cryptography import aes, key
import shutil
from shutil import which
import base64


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
# Get the data location, required for the config file etc
app_home = Path(os.path.dirname(os.path.realpath(__file__)))
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
                     '"Default Connection" , is assumed', default=None)

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
                help="""Used to specify the run-mode. This is either "command" (command-line) or "plugin" (editor
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
                """, dest='sql_script', default=None)

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
tunnelling = args_list["tunnelling"]
sql_script = ' '.join(sql_script)

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


valid_modes = ["plugin", "command"]
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

        if not tunnelling:
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
        if connection_banner and connection_banner !='None':
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
    just_fix_windows_console()

    controller = DCCMControl(app_home, mode=run_mode, db_file_path=db_file, connection_identifier=connection_identifier)
