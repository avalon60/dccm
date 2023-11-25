"""Class Container for Oracle connection maintenance dialogue."""
import customtkinter as ctk
import tkinter as tk
import lib.cbtk_kit as cbtk
import libm.dccm_m as mod
from tktooltip import ToolTip
from PIL import Image

# Constants
HEADING1 = mod.HEADING1
HEADING2 = mod.HEADING2
HEADING3 = mod.HEADING3
HEADING4 = mod.HEADING4
HEADING5 = mod.HEADING5

# HEADING_UL = 'Roboto 11 underline'
REGULAR_TEXT = mod.REGULAR_TEXT
SMALL_TEXT = mod.SMALL_TEXT

TOOLTIP_DELAY = mod.TOOLTIP_DELAY

app_home = mod.app_home
app_assets = mod.app_assets
data_location = mod.data_location
from os.path import expanduser
images_location = mod.images_location
temp_location = mod.temp_location
db_file = mod.db_file

class OraConnectionMaintenanceDialog(ctk.CTkToplevel):
    def __init__(self, controller, operation, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = controller
        DIALOG_WIDTH = 820
        DIALOG_HEIGTH = 760

        default_padx = 5
        default_pady = 10
        position_geometry = self.controller.retrieve_geometry(window_name='maintain_connection')
        self.geometry(position_geometry)
        self.geometry(f'{DIALOG_WIDTH}x{DIALOG_HEIGTH}')
        # self.controller.restore_geometry(window_name='maintain_connection')

        self.maintain_operation = operation

        if operation == 'Modify':
            connection_record = self.controller.selected_connection_record()
            connection_type = connection_record["connection_type"]
            wallet_required_yn = connection_record["wallet_required_yn"]
        else:
            connection_type = self.controller.default_connection_type
            wallet_required_yn = 'Y'

        # Frames
        self.title(f'{operation} Connection')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=0)

        # This is our top widgets region, where we render the primary widgets,
        # oriented around connection and client type details
        self.frm_mod_connection_body = ctk.CTkFrame(master=self)
        self.frm_mod_connection_body.grid(row=0, column=0, padx=5, pady=5, sticky='nsew', columnspan=3)

        lbl_mod_connection_type = ctk.CTkLabel(master=self.frm_mod_connection_body, text='Connection Name / Type',
                                               font=HEADING4)
        lbl_mod_connection_type.grid(row=0, column=0, padx=(10, 5), pady=0, sticky='w', columnspan=2)

        self.frm_mod_conn_type = ctk.CTkFrame(master=self.frm_mod_connection_body)
        self.frm_mod_conn_type.grid(row=1, column=0, padx=5, pady=0, sticky='ew', columnspan=2)

        lbl_mod_credentials = ctk.CTkLabel(master=self.frm_mod_connection_body, text='Credentials              ',
                                           font=HEADING4)
        lbl_mod_credentials.grid(row=2, column=0, padx=5, pady=(5, 0), sticky='w', columnspan=2)

        self.frm_mod_credentials = ctk.CTkFrame(master=self.frm_mod_connection_body)
        self.frm_mod_credentials.grid(row=3, column=0, padx=5, pady=5, sticky='new', columnspan=2)

        lbl_mod_tns_properties = ctk.CTkLabel(master=self.frm_mod_connection_body, text='Connection Properties',
                                              font=HEADING4)
        lbl_mod_tns_properties.grid(row=4, column=0, padx=5, pady=(5, 0), sticky='w')

        self.frm_mod_tns_properties = ctk.CTkFrame(master=self.frm_mod_connection_body)
        self.frm_mod_tns_properties.grid(row=5, column=0, padx=5, pady=5, sticky='new', columnspan=2)

        lbl_mod_gui_session_init = ctk.CTkLabel(master=self.frm_mod_connection_body,
                                                text='Cmd Mode Session Intialisation',
                                                font=HEADING4)
        lbl_mod_gui_session_init.grid(row=6, column=0, padx=5, pady=(5, 0), sticky='w')

        self.frm_mod_cmd_session = ctk.CTkFrame(master=self.frm_mod_connection_body)
        self.frm_mod_cmd_session.grid(row=7, column=0, padx=5, pady=5)

        lbl_mod_gui_session_init = ctk.CTkLabel(master=self.frm_mod_connection_body,
                                                text='GUI Mode Session Intialisation',
                                                font=HEADING4)
        lbl_mod_gui_session_init.grid(row=6, column=1, padx=5, pady=5, sticky='w')
        # Frame to render GUI session initialisation widgets
        self.frm_mod_gui_session = ctk.CTkFrame(master=self.frm_mod_connection_body)
        self.frm_mod_gui_session.grid(row=7, column=1, padx=5, pady=5, sticky='nsew')

        lbl_mod_ssh_settings = ctk.CTkLabel(master=self.frm_mod_connection_body,
                                            text='SSH Settings         ',
                                            font=HEADING4)
        lbl_mod_ssh_settings.grid(row=8, column=0, padx=5, pady=(5, 0), sticky='w')

        self.frm_mod_ssh_settings = ctk.CTkFrame(master=self.frm_mod_connection_body)
        self.frm_mod_ssh_settings.grid(row=9, column=0, padx=5, pady=5, sticky='new', columnspan=2)

        self.frm_mod_buttons = ctk.CTkFrame(master=self)
        self.frm_mod_buttons.grid(row=10, column=0, padx=5, pady=5, columnspan=3, sticky='ew')

        # Widgets
        column = 0
        row = 0
        self.lbl_mod_connection_identifier = ctk.CTkLabel(master=self.frm_mod_conn_type,
                                                          text='Connection Id:', anchor='e')
        self.lbl_mod_connection_identifier.grid(row=row, column=column, padx=default_padx, pady=5, sticky='e')
        if self.controller.enable_tooltips:
            self.connection_identifier_tooltip = ToolTip(self.frm_mod_conn_type,
                                                         'A unique identifier for this connection.',
                                                         TOOLTIP_DELAY)
        column += 1
        self.ent_mod_connection_identifier = ctk.CTkEntry(master=self.frm_mod_conn_type,
                                                          placeholder_text='Unique identifier')
        self.ent_mod_connection_identifier.grid(row=row, column=column, padx=default_padx, pady=default_pady,
                                                sticky='sw')
        row += 1
        column = 0

        lbl_mod_database_type = ctk.CTkLabel(master=self.frm_mod_conn_type, text='Database Type:', anchor='e')
        lbl_mod_database_type.grid(row=row, column=column, padx=default_padx, pady=default_pady)
        column += 1

        self.opm_mod_database_type = ctk.CTkOptionMenu(master=self.frm_mod_conn_type,
                                                       values=self.controller.database_type_descriptors())
        self.opm_mod_database_type.grid(row=row, column=column, padx=default_padx, pady=default_pady, sticky='sw')

        column += 1
        lbl_mod_connection_type = ctk.CTkLabel(master=self.frm_mod_conn_type, text='Management Type:', anchor='e')
        lbl_mod_connection_type.grid(row=row, column=column, padx=(25, 5), pady=default_pady, sticky='e')

        column += 1
        self.controller.valid_connection_types = self.controller.connection_type_list()
        if self.controller.enable_tooltips:
            self.connection_type_tooltip = ToolTip(lbl_mod_connection_type,
                                                   'Select a password management type. The "OCI Vault" management type '
                                                   'relies on OCI Vault being configured and the use of secrets '
                                                   'OCIDs to retrieve passwords from the OCI vault. "Legacy" '
                                                   'management type, causes the password to be encrypted and '
                                                   'stored locally.', TOOLTIP_DELAY)

        self.opm_mod_connection_type = ctk.CTkOptionMenu(master=self.frm_mod_conn_type,
                                                         command=self.controller.toggle_mod_cloud_widgets,
                                                         values=self.controller.connection_type_descriptors())
        self.opm_mod_connection_type.grid(row=row, column=column, padx=default_padx, pady=default_pady, sticky='sw')
        self.opm_mod_connection_type.set(connection_type)

        self.tk_mod_wallet_required = ctk.StringVar(master=self.frm_mod_tns_properties, value=wallet_required_yn)
        self.swt_mod_wallet_required = ctk.CTkSwitch(master=self.frm_mod_tns_properties,
                                                     text='Wallet Required',
                                                     variable=self.tk_mod_wallet_required,
                                                     onvalue='Y',
                                                     offvalue='N',
                                                     command=self.toggle_mod_wallet_display)

        self.swt_mod_wallet_required.grid(row=row, column=column, padx=default_padx, pady=default_pady, sticky='w')
        if self.controller.enable_tooltips:
            self.wallet_required_tooltip = ToolTip(self.swt_mod_wallet_required,
                                                   'Wallets are required for Cloud database connections.',
                                                   TOOLTIP_DELAY)

        column = 0
        row += 1
        self.lbl_mod_wallet_location = ctk.CTkLabel(master=self.frm_mod_tns_properties, text='Select Wallet:',
                                                    anchor='e')
        self.lbl_mod_wallet_location.grid(row=row, column=column, padx=default_padx, pady=(5, 0), sticky='e')
        if self.controller.enable_tooltips:
            lbl_theme_tooltip = ToolTip(self.lbl_mod_wallet_location,
                                        f"Select a wallet for this connection. This is most commonly required for "
                                        f"cloud database connections.",
                                        TOOLTIP_DELAY)
        column += 1
        wallet_image = ctk.CTkImage(light_image=Image.open(images_location / 'wallet_lm.png'),
                                    dark_image=Image.open(images_location / 'wallet_dm.png'),
                                    size=(30, 30))
        self.btn_mod_wallet_location = ctk.CTkButton(master=self.frm_mod_tns_properties,
                                                     text='',
                                                     bg_color="transparent",
                                                     fg_color="transparent",
                                                     width=60,
                                                     height=30,
                                                     border_width=0,
                                                     image=wallet_image,
                                                     command=self.controller.ask_wallet_location)
        self.btn_mod_wallet_location.grid(row=row, column=column, padx=0, pady=(10, 5), sticky='sw')
        # self.btn_mod_wallet_location.place(x=100, y=-100)

        column += 1

        self.lbl_mod_connect_string = ctk.CTkLabel(master=self.frm_mod_tns_properties, text='Connect String:',
                                                   anchor='e')
        self.lbl_mod_connect_string.grid(row=row, column=column, padx=0, pady=(5, 0), sticky='w')
        if self.controller.enable_tooltips:
            self.connection_identifier_toolt9ip = ToolTip(self.lbl_mod_connect_string,
                                                          'The connect string or service name to connect'
                                                          'to the database with. Entries from a '
                                                          'tnsnames.ora may be specified/selected, '
                                                          'EZConnect or a Wallet service name.',
                                                          TOOLTIP_DELAY)
        column += 1
        self.cmo_mod_connect_string = ctk.CTkComboBox(master=self.frm_mod_tns_properties,
                                                      width=450,
                                                      values=[])
        self.cmo_mod_connect_string.grid(row=row, column=column, padx=default_padx, pady=(5, 0), sticky='w')
        self.cmo_mod_connect_string.set('')

        row += 1
        column = 0

        self.lbl_mod_wallet_name = ctk.CTkLabel(master=self.frm_mod_tns_properties, font=SMALL_TEXT,
                                                text='')
        self.lbl_mod_wallet_name.grid(row=row, column=column, padx=(75, 5), pady=(0, 5), sticky='w', columnspan=2)

        row += 1
        column = 0

        lbl_mod_client_tool = ctk.CTkLabel(master=self.frm_mod_conn_type, text='Client Tool:', anchor='e')
        lbl_mod_client_tool.grid(row=row, column=column, padx=default_padx, pady=default_pady, sticky='e')
        if self.controller.enable_tooltips:
            self.lbl_mod_client_tool_tooltip = ToolTip(lbl_mod_client_tool,
                                                       'Select the required client tool to use when connecting to the '
                                                       'database. You can add new clients (other than the SQLcl), '
                                                       'via the Tools/Client Tools menu option.',
                                                       TOOLTIP_DELAY)
        column += 1

        # TODO: Cater for non SQLcl command selection
        self.opm_mod_client_tool = ctk.CTkOptionMenu(master=self.frm_mod_conn_type,
                                                     command=self.controller.set_client_options_state,
                                                     values=self.controller.client_tools_name_list)
        self.opm_mod_client_tool.grid(row=row, column=column, padx=default_padx, pady=default_pady, sticky='w')

        if 'SQLcl' in self.controller.client_tools_name_list:
            self.opm_mod_client_tool.set('SQLcl')
        if self.controller.enable_tooltips:
            lbl_theme_tooltip = ToolTip(self.opm_mod_client_tool,
                                        f"The client tool which you wish to launch, when launching this "
                                        f"connection.",
                                        TOOLTIP_DELAY)
        column += 1

        self.lbl_mod_client_tool_options = ctk.CTkLabel(master=self.frm_mod_conn_type,
                                                        text='SQLcl Options:', anchor='e')
        self.lbl_mod_client_tool_options.grid(row=row, column=column, padx=default_padx, pady=default_pady, sticky='e')

        if self.controller.enable_tooltips:
            lbl_theme_tooltip = ToolTip(self.lbl_mod_client_tool_options,
                                        f'The SQLcl command line options to include on client launch. Example: '
                                        f'"-S" for silent (no SQLcl banner upon start)',
                                        TOOLTIP_DELAY)

        column += 1
        self.ent_mod_client_tool_options = ctk.CTkEntry(master=self.frm_mod_conn_type,
                                                        placeholder_text='SQLcl option flags')
        self.ent_mod_client_tool_options.grid(row=row, column=column, sticky='w', padx=default_padx, pady=default_pady)

        # Render the buttons.
        button_width = 95
        btn_close = ctk.CTkButton(master=self.frm_mod_buttons, command=self.on_close_connections_maintenance,
                                  text='Cancel', width=button_width)
        btn_close.grid(row=0, column=0, padx=15, pady=(10, 10), sticky='s')

        self.btn_mod_test = ctk.CTkButton(master=self.frm_mod_buttons, command=self.controller.test_connection,
                                          text='Test Connection', width=button_width)
        self.btn_mod_test.grid(row=0, column=1, padx=180, pady=(10, 10), sticky='s')

        btn_mod_save = ctk.CTkButton(master=self.frm_mod_buttons, command=self.controller.modify_connection,
                                     text='Save', width=button_width)
        btn_mod_save.grid(row=0, column=2, padx=15, pady=(10, 10), sticky='s')

        self.render_connection_widgets()
        home_directory = expanduser("~")
        self.lbl_mod_disp_launch_directory.configure(text=home_directory)

        self.toggle_mod_wallet_display()

        self.mod_status_bar = cbtk.CBtkStatusBar(master=self)

        self.grab_set()

    def db_account_caps(self, event):
        """The db_account_caps function, is a callback function, used to convert the database account name to
        uppercase, as the user types in the name."""
        self.tk_mod_db_account_name.set(self.tk_mod_db_account_name.get().upper())

    def hide_vault_mod_widgets(self):
        self.lbl_mod_oci_profile.configure(state=tk.DISABLED)
        self.cmo_mod_oci_profile.configure(state=tk.DISABLED)
        self.ent_mod_ocid.configure(placeholder_text='Password')
        self.swt_mod_wallet_required.grid()

    def show_vault_mod_widgets(self):
        self.lbl_mod_oci_profile.configure(state=tk.NORMAL)
        self.cmo_mod_oci_profile.configure(state=tk.NORMAL)
        self.tk_mod_wallet_required.set('Y')

    def render_connection_widgets(self, connection_type: str = None):
        """Method to render the Connection Create / Modify Widgets"""
        default_padx = (5, 5)
        default_pady = 10

        row = 0
        column = 0

        self.lbl_mod_db_account_name = ctk.CTkLabel(master=self.frm_mod_credentials,
                                                    text='Username:', anchor='e')
        self.lbl_mod_db_account_name.grid(row=row, column=column, padx=default_padx, pady=default_pady, sticky='e')
        column += 1
        if self.controller.enable_tooltips:
            self.db_account_name_tooltip = ToolTip(self.lbl_mod_db_account_name,
                                                   'The database account, to connect as.',
                                                   TOOLTIP_DELAY)

        # TODO: reinstate the textvariable. Waiting on CustomTkinter fix for placeholder text.
        self.tk_mod_db_account_name = tk.StringVar(master=self.frm_mod_credentials)
        self.ent_mod_db_account_name = ctk.CTkEntry(master=self.frm_mod_credentials,
                                                    # textvariable=self.tk_mod_db_account_name,
                                                    placeholder_text='Database username')
        self.ent_mod_db_account_name.grid(row=row, column=column, padx=default_padx, pady=default_pady, sticky='s')

        self.ent_mod_db_account_name.bind("<KeyRelease>", self.db_account_caps)

        column += 1

        self.lbl_mod_ocid = ctk.CTkLabel(master=self.frm_mod_credentials,
                                         text='Cloud Secret OCID:', anchor='e')
        self.lbl_mod_ocid.grid(row=row, column=column, padx=default_padx, pady=default_pady, sticky='w')
        column += 1
        if self.controller.enable_tooltips:
            self.lbl_mod_ocid_tooltip = ToolTip(self.lbl_mod_ocid,
                                                'Cloud Secret OCID / Password.',
                                                TOOLTIP_DELAY)

        self.ent_mod_ocid = ctk.CTkEntry(master=self.frm_mod_credentials)
        self.ent_mod_ocid.grid(row=row, column=column, padx=5, pady=5)

        column += 1

        eye_image = ctk.CTkImage(light_image=Image.open(images_location / 'eye_lm.png'),
                                 dark_image=Image.open(images_location / 'eye_dm.png'),
                                 size=(30, 30))
        btn_eye = ctk.CTkButton(master=self.frm_mod_credentials, bg_color="transparent", fg_color="transparent",
                                command=self.toggle_password_display,
                                width=40,
                                height=20,
                                image=eye_image,
                                border_width=0,
                                text=None)
        btn_eye.grid(row=row, column=column, padx=(0, 5), pady=5)
        if self.controller.enable_tooltips:
            lbl_theme_tooltip = ToolTip(btn_eye,
                                        f"Poke my eye, to make me show you the secret / password. Poke the eye again, "
                                        f"to hide the password.",
                                        TOOLTIP_DELAY)

        row += 1
        column = 0
        self.lbl_mod_oci_profile = ctk.CTkLabel(master=self.frm_mod_tns_properties,
                                                text='OCI Profile:',
                                                anchor='e')
        self.lbl_mod_oci_profile.grid(row=row, column=column, padx=default_padx, pady=default_pady, sticky='w')
        if self.controller.enable_tooltips:
            self.lbl_mod_oci_profile_tooltip = ToolTip(self.lbl_mod_oci_profile,
                                                       'The OCI profile (from the OCI config file) to '
                                                       'use when connecting to the OCI Vault. Note that '
                                                       'you need to set up public/private keys for the '
                                                       'vault access.',
                                                       TOOLTIP_DELAY)
        column += 1

        self.cmo_mod_oci_profile = ctk.CTkComboBox(master=self.frm_mod_tns_properties,
                                                   values=self.controller.oci_config_profiles_list())
        self.cmo_mod_oci_profile.grid(row=row, column=column, padx=0, pady=default_pady, sticky='w')

        # btn_eye.bind("<Enter>", self.show_password)
        # btn_eye.bind("<ButtonRelease-1>", self.hide_password)

        column = 0
        row = 0

        self.password_hidden = True
        self.ent_mod_ocid.configure(show="*")

        # The second settings frame widgets start here:
        self.ent_mod_description = ctk.CTkEntry(master=self.frm_mod_ssh_settings,
                                                placeholder_text='Connection comments/description')
        # self.ent_mod_description.grid(row=row, column=0, padx=default_padx, pady=default_pady)

        row = 1

        self.lbl_mod_client_launch_directory = ctk.CTkLabel(master=self.frm_mod_gui_session, text='Initial Directory:')
        self.lbl_mod_client_launch_directory.grid(row=row, column=0, padx=(5, 30), pady=default_pady, sticky='w')
        if self.controller.enable_tooltips:
            self.new_client_launch_directory_tooltip = ToolTip(self.lbl_mod_client_launch_directory,
                                                               'The directory from which to launch the client tool. '
                                                               '\nThis is only used when launching in GUI mode. '
                                                               '\n'
                                                               '\nNote that when launching in command line mode, the '
                                                               '\ninitial working directory, is assumed to be the'
                                                               '\ndirectory from which the command was launched.',
                                                               TOOLTIP_DELAY)
        column += 1

        folder_image = ctk.CTkImage(light_image=Image.open(images_location / 'folder.png'),
                                    dark_image=Image.open(images_location / 'folder.png'),
                                    size=(25, 25))
        self.btn_mod_launch_directory = ctk.CTkButton(master=self.frm_mod_gui_session,
                                                      text='',
                                                      bg_color="transparent",
                                                      fg_color="transparent",
                                                      width=40,
                                                      height=20,
                                                      border_width=0,
                                                      command=self.controller.ask_client_launch_directory,
                                                      image=folder_image
                                                      )
        self.btn_mod_launch_directory.grid(row=row, column=0, padx=(120, 0), pady=0, sticky='w')
        if self.controller.enable_tooltips:
            opm_app_theme_tooltip = ToolTip(self.btn_mod_launch_directory,
                                            f"Set the starting directory, when launched in GUI mode.",
                                            TOOLTIP_DELAY)
        row += 1

        self.lbl_mod_disp_launch_directory = ctk.CTkLabel(master=self.frm_mod_gui_session, font=SMALL_TEXT,
                                                          text='')
        self.lbl_mod_disp_launch_directory.grid(row=row, column=0, padx=(20, 5), pady=0, sticky='w')

        column = 0
        row = 0
        self.lbl_mod_connection_banner = ctk.CTkLabel(master=self.frm_mod_cmd_session,
                                                      text='Connection Banner:', anchor='e')
        self.lbl_mod_connection_banner.grid(row=row, column=column, padx=default_padx, pady=default_pady, sticky='e')
        if self.controller.enable_tooltips:
            lbl_theme_tooltip = ToolTip(self.lbl_mod_connection_banner,
                                        f"Select a banner type, to be displayed when launching the client tool in "
                                        f"command line mode.",
                                        TOOLTIP_DELAY)

        # TODO: Hook up the next 3 widgets with the controller

        column += 1
        banner_values = self.controller.banner_options()
        self.opm_mod_connection_banner = ctk.CTkOptionMenu(master=self.frm_mod_cmd_session,
                                                           values=banner_values,
                                                           width=15)
        self.opm_mod_connection_banner.grid(row=row, column=column, padx=default_padx, pady=default_pady)
        self.opm_mod_connection_banner.set(value='None')

        column += 1
        self.lbl_mod_connection_text_colour = ctk.CTkLabel(master=self.frm_mod_cmd_session,
                                                           text='Message Colour:', anchor='e')
        self.lbl_mod_connection_text_colour.grid(row=row, column=column, padx=default_padx,
                                                 pady=default_pady, sticky='e')
        if self.controller.enable_tooltips:
            lbl_theme_tooltip = ToolTip(self.lbl_mod_connection_text_colour,
                                        'Select a colour for the connection message.',
                                        TOOLTIP_DELAY)

        column += 1
        colour_values = self.controller.banner_colours()
        self.opm_mod_connection_text_colour = ctk.CTkOptionMenu(master=self.frm_mod_cmd_session,
                                                                values=colour_values)
        self.opm_mod_connection_text_colour.grid(row=row, column=column, padx=default_padx, pady=default_pady,
                                                 sticky='w')
        self.opm_mod_connection_text_colour.set(value='None')

        row += 1
        column = 0
        self.lbl_mod_connection_message = ctk.CTkLabel(master=self.frm_mod_cmd_session,
                                                       text='Connection Message:', anchor='e')
        self.lbl_mod_connection_message.grid(row=row, column=column, padx=default_padx,
                                             pady=(default_pady, 10), sticky='e')
        if self.controller.enable_tooltips:
            lbl_theme_tooltip = ToolTip(self.lbl_mod_connection_message,
                                        'Enter a connection message, to be displayed when invoking command line '
                                        'based connections.',
                                        TOOLTIP_DELAY)
        column += 1

        self.tk_mod_connection_message = tk.StringVar(master=self.frm_mod_cmd_session, value='')
        self.ent_mod_connection_message = ctk.CTkEntry(master=self.frm_mod_cmd_session,
                                                       placeholder_text='Cmd line connection message',
                                                       textvariable=self.tk_mod_connection_message,
                                                       width=400)
        self.ent_mod_connection_message.grid(row=row, column=column, padx=(5, 5), pady=(default_pady, 5),
                                             sticky='w', columnspan=3)

        row = 0
        column = 0
        self.tk_mod_ssh_tunnel_required_yn = tk.StringVar(master=self.frm_mod_ssh_settings, value='N')
        self.swt_mod_ssh_tunnel_required_yn = ctk.CTkSwitch(master=self.frm_mod_ssh_settings,
                                                            text='SSH Tunnel',
                                                            variable=self.tk_mod_ssh_tunnel_required_yn,
                                                            onvalue='Y',
                                                            offvalue='N',
                                                            command=self.controller.toggle_mod_tunnel_widgets)
        if self.controller.enable_tooltips:
            opm_app_theme_tooltip = ToolTip(self.swt_mod_ssh_tunnel_required_yn,
                                            f"Enable, if SSH is required for this connection.",
                                            TOOLTIP_DELAY)
        self.swt_mod_ssh_tunnel_required_yn.grid(row=row, column=column, padx=(10, 5), pady=default_pady,
                                                 sticky='w')
        column += 1

        self.lbl_mod_tunnel_templates = ctk.CTkLabel(master=self.frm_mod_ssh_settings,
                                                     text='Select Tunnel:', anchor='e')
        self.lbl_mod_tunnel_templates.grid(row=row, column=column, padx=default_padx, pady=default_pady, sticky='w')
        if self.controller.enable_tooltips:
            lbl_theme_tooltip = ToolTip(self.lbl_mod_tunnel_templates,
                                        f"Select the SSH tunnelling entry, required for this connection.",
                                        TOOLTIP_DELAY)
        column += 1
        ssh_templates = mod.preferences_scope_names(db_file_path=db_file, scope='ssh_templates')
        self.opm_mod_tunnel_code = ctk.CTkOptionMenu(master=self.frm_mod_ssh_settings,
                                                     values=ssh_templates,
                                                     command=self.controller.toggle_mod_ssh_port,
                                                     width=150)
        self.opm_mod_tunnel_code.grid(row=row, column=column, padx=(5, 5), pady=default_pady)

        column += 1
        self.lbl_mod_listener_port = ctk.CTkLabel(master=self.frm_mod_ssh_settings,
                                                  text='Listener Port:',
                                                  anchor='e')
        self.lbl_mod_listener_port.grid(row=row, column=column, padx=(5, 5), pady=default_pady, sticky='w')
        if self.controller.enable_tooltips:
            lbl_theme_tooltip = ToolTip(self.lbl_mod_listener_port,
                                        f"Enter the database listener port number",
                                        TOOLTIP_DELAY)
        column += 1
        self.tk_mod_listener_port = tk.StringVar(master=self.frm_mod_ssh_settings)
        self.ent_mod_listener_port = ctk.CTkEntry(master=self.frm_mod_ssh_settings,
                                                  state=tk.DISABLED,
                                                  textvariable=self.tk_mod_listener_port,
                                                  placeholder_text='Listener Port#')
        self.ent_mod_listener_port.grid(row=row, column=column, padx=(5, 5), pady=default_pady, sticky='w')

    def toggle_mod_wallet_display(self):
        """The toggle_mod_wallet_display method, is called when the state of the "wallet required" widget changes. It
        is responsible for showing / hiding wallet related widgets."""
        switch = self.swt_mod_wallet_required.get()
        if switch == 'Y':
            self.lbl_mod_wallet_location.grid()
            self.btn_mod_wallet_location.grid()
            # self.mvc_view.lbl_mod_wallet_name.grid()
            connection_id = self.ent_mod_connection_identifier.get()
            tns_connect_list = self.controller.wallet_connect_string_list(connection_identifier=connection_id)
            tns_connect_list = self.controller.wallet_connect_string_list(connection_identifier=connection_id)
            self.cmo_mod_connect_string.configure(values=tns_connect_list)
        else:
            self.lbl_mod_wallet_location.grid_remove()
            self.btn_mod_wallet_location.grid_remove()
            self.lbl_mod_wallet_name.configure(text='')
            self.wallet_pathname = ''
            tns_connect_list = self.controller.tns_names_alias_list()
            self.cmo_mod_connect_string.configure(values=tns_connect_list)

    def toggle_password_display(self, event=None):
        if self.password_hidden:
            self.password_hidden = False
            self.ent_mod_ocid.configure(show="")
        else:
            self.password_hidden = True
            self.ent_mod_ocid.configure(show="*")

    def on_close_connections_maintenance(self):
        """The on_close_connections_maintenance method, tidies up when we close the connections maintenance dialog."""
        geometry = self.geometry()
        self.controller.save_geometry(window_name='maintain_connection', geometry=geometry)
        mod.purge_temp_tns_admin()
        self.deiconify()
        self.destroy()
