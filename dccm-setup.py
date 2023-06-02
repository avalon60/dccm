"""Database Client Connection Manager"""

import argparse
from operator import attrgetter
from argparse import HelpFormatter
from pathlib import Path
import json
import shutil
import platform
import sqlite3
import os
from os.path import exists
from os.path import expanduser
from zipfile import ZipFile
import zipfile


# from tkfontawesome import icon_to_image
import re

PRODUCT = 'DCCM'
__title__ = f'{PRODUCT} Setup'
__author__ = 'Clive Bostock'
__version__ = "1.1.0"

# Constants
KEY_INV_DIRS = ['themes', 'images', 'data']
KEY_INV_FILES = ['dccm.bat', 'dccm.sh', 'dccm.py', 'build_app.sh',
                       'build_app.bat', 'get-pip.py', 'requirements.txt',
                       'data/dccm_updates.json', 'themes/GreyGhost.json']
python_version = platform.python_version()

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

class SortingHelpFormatter(HelpFormatter):
    def add_arguments(self, actions):
        actions = sorted(actions, key=attrgetter('option_strings'))
        super(SortingHelpFormatter, self).add_arguments(actions)


ap = argparse.ArgumentParser(formatter_class=SortingHelpFormatter
                             , description=f"""{prog}: The {prog} tool is used to assist in the installation and with 
                             upgrades of {PRODUCT}.""")

ap.add_argument("-a", "--artefact", required=False, action="store",
                help=f"""Used for {PRODUCT} deployments & upgrades. Use -a along with the pathname to the {PRODUCT} 
                      artefact ZIP file.""", dest='artefact', default=None)

ap.add_argument("-H", "--dccm-home", required=False, action="store",
                help=f"""used to point to the install/upgrade location for {PRODUCT}. {PRODUCT} will be installed 
                in its own subdirectory below the base location provided. If not supplied, a default
                location will be used. The default is assumed to be the user's home directory. For example on MacOS this
                will equate to  $HOME/{PRODUCT.lower()} and on Windows it would be <system_drive>:\\Users\\<username>
                      file.""", dest='application_home', default=None)

operating_system = platform.system()
home_directory = expanduser("~")

args_list = vars(ap.parse_args())

artefact = args_list["artefact"]

if artefact is not None and not exists(artefact):
    print(f'ERROR: Cannot locate the specified artefact ZIP file: {artefact}')
    exit(1)

b_prog = prog.replace(".py", "")


def app_file_version(python_file:Path):
    """Given a Python program, find the version, as defined by __version__."""
    with open(python_file, 'r') as fp:
        # read all lines in a list
        lines = fp.readlines()
        for line in lines:
            # check if string present on a current line
            if '__version__' in line:
                version_line = line
                break
    version_list = version_line.split()
    if len(version_list) == 3:
        version = version_list[2]
    else:
        return 'unknown'
    return version.replace('"', '')

def apply_repo_updates(data_directory: Path, app_file_version: str):
    """Perform any system related data related migration steps required. This avoids the necessity of performing a
    complicated migration, where data structures require change."""
    db_file_path = data_directory / f'.{PRODUCT.lower()}.db'
    registered_app_version = preference(db_file_path=db_file_path, scope='system', preference_name='app_version')
    if registered_app_version is None:
        print('No record of current repo version, assuming 2.0...')
        registered_app_version = '2.0.0'
    print(f'Updating the {PRODUCT} repository:-')
    print(f'Existing repository appears to be version {registered_app_version}...')

    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()

    updates_json_file = data_directory / 'dccm_updates.json'
    updates_json_file = updates_json_file
    print(f'updates_json_file: {updates_json_file}')
    with open(updates_json_file) as json_file:
        try:
            updates_dict_list = json.load(json_file)
        except ValueError:
            print(f'ERROR: The file, "{updates_json_file}", does not appear to be a valid JSON file.')
            print('Bailing out!')
            raise
        except IOError:
            feedback = f'Failed to read file {updates_json_file} - possible permissions issue.'

    sql_to_apply = 0
    for sql_id in updates_dict_list:
        sql_apply_version = updates_dict_list[sql_id]["sql_apply_version"]
        if version_scalar(registered_app_version) < version_scalar(sql_apply_version) <= version_scalar(app_file_version):
            sql_to_apply += 1

    backup_repo = (f'{PRODUCT.lower()}-{registered_app_version}.db')
    if sql_to_apply > 0:
        print(f'There are {sql_to_apply} potential upgrade actions pending...')
        print(f'Backing up ${PRODUCT} repo to: {data_directory}/{backup_repo}')
        shutil.copy(db_file_path, Path(f'{data_directory}/{backup_repo}'))
    else:
        print(f'No upgrade actions pending.')


    sql_count = 0
    for sql_id in updates_dict_list:
        description = updates_dict_list[sql_id]["description"]
        sql_statement = updates_dict_list[sql_id]["sql_statement"]
        sql_apply_version = updates_dict_list[sql_id]["sql_apply_version"]
        if version_scalar(registered_app_version) < version_scalar(sql_apply_version) <= version_scalar(app_file_version):
            try:
                cur.execute(sql_statement)
                print(f'Applying SQL Id: {sql_id}  :- {description} (Succeeded)')
            except sqlite3.OperationalError:
                if version_scalar(sql_apply_version) == version_scalar(app_file_version):
                    # If it fails and the versions are the same, we assume that it's because a DDL
                    # script has been previously run.
                    print(f'Apply SQL Id: {sql_id}  :- {description} (Skipped)')
                else:
                    print(f'Apply SQL Id: {sql_id}  :- {description} (FAILED - OperationalError)')
            sql_count += 1
    print(f'Repo updates applied: {sql_count}')
    # Upsert preference opens the database, so ensure we close it here, to avoid a lock error,
    db_conn.commit()
    db_conn.close()

    upsert_preference(db_file_path=db_file,
                      scope='system',
                      preference_name='app_version',
                      preference_value=app_file_version,
                      preference_label='Application Version')



def version_scalar(version: str):
    """Version scalar, takes a version number (with dot notation) and converts it to a scalar. The number of components
    within the version, is by default assumed to be 3. If you specifiy a shorter version format (e.g. 3.1), then it will
    be augmented to 3 components (3.1.0), before converting and returning the scalar value."""
    dot_count = version.count('.')
    if dot_count > 2:
        print(f'Invalid number of dots in version string, {version}, a maximum of 2 is expected.')
        print('Bailing out!')
        exit(1)

    version_padded = version
    for i in range(3 - dot_count - 1):
        version_padded = version + '.0'
    version_list = version_padded.split('.')
    # Check version components are all integers...
    for component in version_list:
        try:
            comp = int(component)
        except ValueError:
            print(f'Invalid non-integer character, "{component}", found in version string, "{version}" ')
            print('Bailing out!')
            exit(1)
        if len(component) > 2:
            print(f'Invalid version component, "{component}", found in version string, "{version}"')
            print('Maximum version component length expected is 2 characters.')
            print('Bailing out!')
            exit(1)

    scalar_version = ''
    for component in version_list:
        component = component.zfill(2)
        scalar_version = scalar_version + component
    return int(scalar_version)

def initialise_database(db_file_path: Path):
    """The initialise_database function created the sqllite3 database, used to store DCCM settings. This is executed
    when the program is first run.

    :param db_file_path: Pathname of the sqllite3 database, to be created."""
    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()
    cur.execute("""create table if not exists
     application_control (
       application_version text primary key,
       previous_version text);
    """)
    cur.execute("""insert into application_control
    (application_version)
    values
    (:version);""", {"version": __version__})
    db_conn.commit()

    cur.execute("""create table if not exists
     connections (
       connection_identifier text primary key,
       database_type text not null,
       connection_type text not null,
       db_account_name text not null,
       connect_string  text,
       oci_profile     text not null,
       ocid            text not null,
       wallet_required_yn text not null,
       wallet_location text,
       client_tool     text,
       client_tool_options text,
       start_directory text,
       ssh_tunnel_required_yn  text,
       ssh_tunnel_code text,
       listener_port integer,
       description     text);
    """)
    db_conn.commit()

    cur.execute("""create table if not exists 
     preferences (
       scope           text not null,
       preference_name text not null,
       preference_value text not null,
       preference_label text not null,
       preference_attr1 text,
       preference_attr2 text,
       preference_attr3 text,
       preference_attr4 text,
       preference_attr5 text,
       primary key (scope, preference_name)
   );
    """)

    db_conn.commit()

    cur.execute("select preference_label, preference_value "
                "from preferences "
                "where preference_name = 'sql_client';")
    sql_client = cur.fetchone()
    if sql_client is None:
        print('Initialising database registry, with client tool SQLcl')
        cur.execute("insert into preferences "
                    "(scope, preference_name,  preference_value, preference_label)"
                    "values "
                    "('client_tools', 'SQLcl', 'sql', 'SQLcl');")

        # print('Initialising database registry, with client tool SQL*Plus')
        # cur.execute("insert into preferences "
        # cur.execute("insert into preferences "
        #            "(scope, preference_name,  preference_value, preference_label)"
        #            "values "
        #            "('client_tools', 'SQL*Plus', 'sqlplus', 'SQL*Plus');")
        db_conn.commit()

    db_conn.close()


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

def app_home_contents_ok(app_home: str):
    """Function to check the home contents, to ensure that it looks like a valid DCCM home directory. If components
    are missing we list (print) them and return False. Otherwise, we return True.
    :param app_home: Application home directory."""
    missing_dirs = []
    missing_files = []
    for dir in KEY_INV_DIRS:
        if not exists(dir):
            missing_dirs.append(dir)
    for file in KEY_INV_FILES:
        if not exists(file):
            missing_files.append(file)
    if len(missing_files) > 0 or len(missing_dirs) > 0:
        print(f'The specified application home directory, {app_home}, appears invalid.\nThe following components '
              f'are missing:')
        for directory in missing_dirs:
            print(f'{directory} (directory)')
        for file in missing_files:
            print(f'{file} (file)')
        return False
    else:
        return True


def unpack_artefact(zip_pathname: Path, install_location: str):
    """"The unpack_artefact function, is provided for when we need to perform a software upgrade.
    We unpack the wallet contents to the target application home directory, prior to initialisation of the Python
    virtual environment for the application.
    :param zip_pathname: Path
    """
    if not zipfile.is_zipfile(zip_pathname):
        print(f'unpack_artefact: Artefact file, {zip_pathname}, appears to be an invalid ZIP file. Unable to proceed!')
        exit(1)

    # https://realpython.com/python-zipfile/
    # with ZipFile(zip_pathname, 'r') as archive:
    #    archive.extract('dccm/requirements.txt', '.')

    with ZipFile(zip_pathname, 'r') as archive:
        extract_location = Path(install_location)
        archive.extractall(extract_location)


if __name__ == "__main__":
    if args_list["application_home"] is None:
        application_home = Path(home_directory) / 'dccm'
    else:
        application_home = args_list["application_home"]
        application_home = os.path.abspath(application_home)
    artefact = os.path.abspath(artefact)

    print(f'Starting {PRODUCT} deployment.')
    print(f'Application home: {str(application_home)}')

    # Perform initial checks
    print('Checking Python interpreter version...')
    if not (version_scalar('3.8.0') <= version_scalar(python_version) <= version_scalar('3.10.9')):
        print(f'ERROR: Python interpreter version, {python_version}, is unsupported.\n'
              f'Only Python versions between 3.8 and 3.10 are supported')
        exit(1)
    else:
        print(f'Python version, {python_version}, is a supported version.')

    if not exists(application_home) and artefact is not None:
        parent_folder = os.path.dirname(application_home)
        if exists(parent_folder):
            os.mkdir(application_home)
        else:
            print(f'ERROR: The parent directory, {parent_folder}, for the specified {PRODUCT} application home, '
                  f'does not exist.\nPlease correct the supplied pathname and retry.')
            exit(1)
    elif not exists(application_home) and artefact is None:
        print(f'ERROR: For the new application home, {application_home}, you must provide a deployment artefact via the '
              f'"-a/--artefact" command modifier.')
        print(f'Please correct and retry.')
        exit(1)
    else:
        print(f'Updating existing installation at: {application_home}')
    app_home = Path(os.path.abspath(application_home))
    # Switch working directory to the application home
    os.chdir(app_home)

    data_location = app_home / 'data'
    images_location = app_home / 'images'
    temp_location = app_home / 'tmp'
    themes_location = app_home / 'themes'

    db_file = data_location / f'.{PRODUCT.lower()}.db'

    if not exists(temp_location):
        os.mkdir(temp_location)

    if not exists(data_location):
        os.mkdir(data_location)

    print(f'Checking for repository: {db_file}')
    if not exists(db_file):
        new_database = True
        print("Greenfield installation - creating a new repository.")
        initialise_database(db_file_path=db_file)

    if artefact:
        print(f'Unpacking artefact: {artefact} to: {application_home}')
        unpack_artefact(zip_pathname=artefact, install_location=application_home)

    entry_point_script = PRODUCT.lower() + '.py'

    print(f'Inspecting {PRODUCT} application home directory...')
    if app_home_contents_ok(app_home=application_home):
        print(f'Application home, {str(os.path.abspath(application_home))}, looks fine.')
    else:
        print(f'The application home directory, {application_home}, does not appear to be correct.')
        exit(1)

    if operating_system == 'Windows':
        os.system('.\\build_app.bat')
    else:
        os.system('chmod 750 *.sh')
        os.system('./build_app.sh')

    app_version = app_file_version(app_home / f'{entry_point_script}')

    apply_repo_updates(data_directory=data_location, app_file_version=app_version)
    print(f'App Home for {PRODUCT}: ' + str(os.path.abspath(app_home)))
    print("Done.")
    # dump_preferences(db_file_path=db_file)
