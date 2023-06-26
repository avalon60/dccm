"""Database Client Connection Manager"""
# Control
__title__ = 'Database Client\nConnection Manager'
__author__ = 'Clive Bostock'
__version__ = "2.4.0"

gui_enabled = True
try:
    from tktooltip import ToolTip
    import tkinter as tk
    import customtkinter as ctk
    from PIL import Image, ImageTk
except ModuleNotFoundError:
    gui_enabled = False

from pathlib import Path
import platform
import os
from os.path import expanduser
import dccm_m as mod
import cbtk_kit as cbtk
from CTkTable import *
from CTkListbox import *

# from tkfontawesome import icon_to_image

ENCODING = 'utf-8'

# Constants
# These aren't true sizes as per WEB design
HEADING1 = ('Roboto', 26)
HEADING2 = ('Roboto', 22)
HEADING3 = ('Roboto', 20)
HEADING4 = ('Roboto', 18)
HEADING5 = ('Roboto', 16)

CTK_VERSION = ctk.__version__

# HEADING_UL = 'Roboto 11 underline'
REGULAR_TEXT = ('Roboto', 10)
SMALL_TEXT = ('Roboto', 9)

TOOLTIP_DELAY = 1

valid_modes = ["gui", "plugin", "command"]
valid_modes_str = ', '.join(valid_modes)

prog_path = os.path.realpath(__file__)
prog = os.path.basename(__file__)
b_prog = prog.replace(".py", "")

# Get the data location, required for the config file etc
app_home = Path(os.path.dirname(os.path.realpath(__file__)))
images_location = mod.images_location
app_themes_dir = mod.themes_location

db_file = mod.db_file


def load_image(image_file: Path, image_size: int):
    """ load rectangular image from the file identified by the image_file pathname.

    :param image_file: Path (pathname to image file)
    :param image_size: integer
    :return: ImageTk.PhotoImage
    """
    return ImageTk.PhotoImage(Image.open(image_file).resize((image_size, image_size)))


class DCCMView(ctk.CTk):
    """Class to instantiate our DCCM visual interface."""

    def __init__(self, mvc_controller, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid_columnconfigure(1, weight=1)
        self.mvc_controller = mvc_controller
        self.grid_rowconfigure(0, weight=1)
        self.enable_tooltips = False

        self.top_skill_setting = None
        self.maintain_operation = None
        self.create_menu()
        self.default_connection_type = self.mvc_controller.default_connection_type
        icon_image = tk.PhotoImage(file=images_location / 'dccm.png')
        self.iconphoto(False, icon_image)

    def about(self):

        self.enable_tooltips = False

        widget_corner_radius = 5
        ABOUT_WIDTH = 391
        ABOUT_HEIGHT = 280
        position_geometry = self.mvc_controller.retrieve_geometry(window_category='toplevel')
        top_about = ctk.CTkToplevel(master=self)
        top_about.title('CTk Theme Builder')
        top_about.geometry(position_geometry)
        top_about.geometry(f'{ABOUT_WIDTH}x{ABOUT_HEIGHT}')
        logo_image = load_image(images_location / 'bear-logo-colour.jpg', 210)

        # Make preferences dialog modal
        top_about.rowconfigure(0, weight=1)
        top_about.rowconfigure(1, weight=0)
        top_about.columnconfigure(0, weight=1)

        frm_about_main = ctk.CTkFrame(master=top_about, corner_radius=widget_corner_radius)
        frm_about_main.grid(column=0, row=0, sticky='nsew')
        frm_about_main.columnconfigure(1, weight=1)
        frm_about_main.rowconfigure(0, weight=1)
        frm_about_main.rowconfigure(1, weight=0)

        frm_widgets = ctk.CTkFrame(master=frm_about_main, corner_radius=widget_corner_radius)
        frm_widgets.grid(column=0, row=0, padx=10, pady=10, sticky='nsew')

        frm_about_logo = ctk.CTkFrame(master=frm_about_main, corner_radius=widget_corner_radius)
        frm_about_logo.grid(column=1, row=0, padx=10, pady=10, sticky='nsew')

        lbl_title = ctk.CTkLabel(master=frm_widgets, text=f'{__title__}')
        lbl_title.grid(row=0, column=0, pady=(5, 0), sticky='ew')

        # dccm_icon = load_image(images_location / 'dccm.png', 50)
        dccm_icon = ctk.CTkImage(light_image=Image.open(images_location / 'dccm.png'),
                                 dark_image=Image.open(images_location / 'dccm.png'),
                                 size=(50, 50))
        btn_dccm_icon = ctk.CTkButton(master=frm_widgets,
                                      text='',
                                      width=60,
                                      height=30,
                                      bg_color="transparent",
                                      fg_color="transparent",
                                      image=dccm_icon)
        btn_dccm_icon.grid(row=1, column=0, sticky='ew')

        lbl_version = ctk.CTkLabel(master=frm_widgets, text=f'Version: {__version__}')
        lbl_version.grid(row=2, column=0, sticky='ew')

        lbl_ctk_version = ctk.CTkLabel(master=frm_widgets, text=f'CustomTkinter: {ctk.__version__}')
        lbl_ctk_version.grid(row=3, column=0, sticky='ew')

        lbl_author = ctk.CTkLabel(master=frm_widgets, text=f'Author: {__author__}')
        lbl_author.grid(row=4, column=0, padx=(10, 10), sticky='ew')

        lbl_logo = ctk.CTkLabel(master=frm_widgets, text=f'Logo: Jan Bajec')
        lbl_logo.grid(row=5, column=0, padx=(10, 10), sticky='ew')

        btn_logo = ctk.CTkButton(master=frm_about_logo, text='', height=50, width=50,
                                 corner_radius=widget_corner_radius,
                                 bg_color="transparent",
                                 fg_color="transparent",
                                 hover_color=None,
                                 border_color=None,
                                 image=logo_image)
        btn_logo.grid(row=0, column=1, sticky='ew')

        frm_buttons = ctk.CTkFrame(master=frm_about_main, corner_radius=widget_corner_radius)
        frm_buttons.grid(column=0, row=1, padx=(5, 5), pady=(0, 0), sticky='ew', columnspan=2)

        btn_ok = ctk.CTkButton(master=frm_buttons, text='OK', width=ABOUT_WIDTH - 20,
                               corner_radius=widget_corner_radius,
                               command=top_about.destroy)
        btn_ok.grid(row=0, column=0, padx=(5, 5), pady=10)

        top_about.grab_set()

    def app_themes_list(self):
        """The app_themes_list method, returns alist of available application themes, based upon the themes located
        in the application's themes sub-folder.

        :return: A list of theme names (these are JSON file name prefxes)."""
        themes = cbtk.themes_list(themes_dir=app_themes_dir)
        return themes

    def create_menu(self):
        # Set up the core of our menu
        # NOTE: On Windows and OSX, it isn't possible to change the Menu bar colour.
        self.des_menu = cbtk.CBtkMenu(self, tearoff=0)
        self.config(menu=self.des_menu)

        # Now add a File sub-menu option
        self.file_menu = cbtk.CBtkMenu(self.des_menu, tearoff=0)
        self.des_menu.add_cascade(label='File', menu=self.file_menu)
        self.file_menu.add_command(label='Set as Default', command=self.mvc_controller.set_connection_as_current)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='New Connection', command=self.mvc_controller.launch_new_connection)
        self.file_menu.add_command(label='Modify Connection', command=self.mvc_controller.launch_mod_connection)
        self.file_menu.add_command(label='Delete Connection', command=self.mvc_controller.root_delete_connection)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Launch Connection', command=self.mvc_controller.launch_client_connection)
        self.file_menu.add_command(label='Establish SSH Tunnel', command=self.mvc_controller.launch_ssh_tunnel)
        self.file_menu.add_command(label='Copy Command', command=self.mvc_controller.preview_launch_command)

        self.file_menu.add_separator()

        self.file_menu.add_command(label='Close', command=self.on_close)

        # Initialise states
        self.file_menu.entryconfig('Set as Default', state="disabled")
        self.file_menu.entryconfig('Modify Connection', state="disabled")
        self.file_menu.entryconfig('Delete Connection', state="disabled")
        self.file_menu.entryconfig('Launch Connection', state="disabled")
        self.file_menu.entryconfig('Establish SSH Tunnel', state="disabled")
        self.file_menu.entryconfig('Copy Command', state="disabled")

        # Now add a Tools sub-menu option
        self.tools_menu = cbtk.CBtkMenu(self.des_menu, tearoff=0)
        self.des_menu.add_cascade(label='Tools', menu=self.tools_menu)
        self.tools_menu.add_command(label='Preferences', command=self.launch_preferences)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label='Connectivity Scan', command=self.launch_connections_scan)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label='SSH Tunnels', command=self.mvc_controller.launch_tunnel_templates)
        self.tools_menu.add_command(label='Client Tools', command=self.mvc_controller.launch_client_tool_templates)

        self.tools_menu.add_separator()
        self.tools_menu.add_command(label='Export', command=self.mvc_controller.launch_export_dialog)
        self.tools_menu.add_command(label='Import', command=self.mvc_controller.launch_import_dialog)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label='About', command=self.about)

    def launch_preferences(self):
        """Launch the preferences window (CTkTopLevel)."""
        PREFS_WIDTH = 400
        PREFS_HEIGHT = 500
        position_geometry = self.mvc_controller.retrieve_geometry(window_category='toplevel')
        self.top_prefs = ctk.CTkToplevel(master=self)
        self.top_prefs.title('DCCM Preferences')
        self.top_prefs.geometry(position_geometry)
        self.top_prefs.geometry(f'{PREFS_WIDTH}x{PREFS_HEIGHT}')
        # Make preferences dialog modal
        self.top_prefs.rowconfigure(0, weight=1)
        self.top_prefs.rowconfigure(1, weight=0)
        self.top_prefs.columnconfigure(0, weight=1)

        frm_prefs_main = ctk.CTkFrame(master=self.top_prefs)
        frm_prefs_main.grid(column=0, row=0, sticky='nsew')
        frm_prefs_main.columnconfigure(0, weight=1)
        frm_prefs_main.rowconfigure(0, weight=1)

        frm_prefs_widgets = ctk.CTkFrame(master=frm_prefs_main)
        frm_prefs_widgets.grid(column=0, row=0, padx=10, pady=10, sticky='nsew')

        frm_buttons = ctk.CTkFrame(master=frm_prefs_main, corner_radius=0)
        frm_buttons.grid(column=0, row=1, padx=(0, 5), pady=(0, 0), sticky='ew')

        self.new_theme_json_dir = None

        frm_prefs_main = ctk.CTkFrame(master=self.top_prefs, corner_radius=10)
        frm_prefs_main.grid(column=0, row=0, sticky='nsew')
        frm_prefs_main.columnconfigure(0, weight=1)
        frm_prefs_main.rowconfigure(0, weight=1)

        frm_prefs_widgets = ctk.CTkFrame(master=frm_prefs_main)
        frm_prefs_widgets.grid(column=0, row=0, padx=10, pady=10, sticky='nsew')

        frm_buttons = ctk.CTkFrame(master=frm_prefs_main, corner_radius=0)
        frm_buttons.grid(column=0, row=1, padx=(0, 5), pady=(0, 0), sticky='ew')

        widget_start_row = 0

        lbl_theme = ctk.CTkLabel(master=frm_prefs_widgets, text='Theme', width=170, justify='right')
        lbl_theme.grid(row=widget_start_row, column=0, padx=(5, 0), pady=(15, 5), sticky='w')

        if self.tooltips_enabled():
            lbl_theme_tooltip = ToolTip(lbl_theme,
                                        f"Change the application colour theme. Requires an application restart to "
                                        f"realise the change.",
                                        TOOLTIP_DELAY)

        app_theme = os.path.splitext(self.mvc_controller.app_theme)[0]
        app_theme = os.path.splitext(self.mvc_controller.app_theme)[0]
        app_theme = os.path.basename(app_theme)
        self.tk_app_theme = tk.StringVar(value=self.mvc_controller.app_theme)
        self.opm_app_theme = ctk.CTkOptionMenu(master=frm_prefs_widgets,
                                               variable=self.tk_app_theme,
                                               values=self.mvc_controller.app_themes_list)
        self.opm_app_theme.grid(row=widget_start_row, column=1, padx=(0, 50), pady=(15, 10), sticky='w')
        widget_start_row += 1

        lbl_mode = ctk.CTkLabel(master=frm_prefs_widgets, text='Appearance Mode')
        lbl_mode.grid(row=widget_start_row, padx=5, column=0, sticky='w')

        # The app_mode holds the  CustomTkinter appearance mode (Dark / Light)
        self.tk_appearance_mode_var = tk.StringVar(value=self.mvc_controller.app_appearance_mode)
        rdo_light = ctk.CTkRadioButton(master=frm_prefs_widgets, text='Light', variable=self.tk_appearance_mode_var,
                                       value='Light')
        rdo_light.grid(row=widget_start_row, column=1, sticky='w')
        widget_start_row += 1
        if self.mvc_controller.app_appearance_mode == 'Light':
            rdo_light.select()

        rdo_dark = ctk.CTkRadioButton(master=frm_prefs_widgets, text='Dark', variable=self.tk_appearance_mode_var,
                                      value='Dark')
        rdo_dark.grid(row=widget_start_row, column=1, pady=5, sticky='w')
        widget_start_row += 1
        if self.mvc_controller.app_appearance_mode == 'Dark':
            rdo_dark.select()

        if platform.system() != 'Linux':
            rdo_system = ctk.CTkRadioButton(master=frm_prefs_widgets, text='System',
                                            variable=self.tk_appearance_mode_var,
                                            value='System')
            rdo_system.grid(row=widget_start_row, column=1, pady=5, sticky='w')
            widget_start_row += 1
            if self.mvc_controller.app_appearance_mode == 'System':
                rdo_system.select()

        # lbl_enable_tooltips = ctk.CTkLabel(master=frm_prefs_widgets, text='Enable tooltips')
        # lbl_enable_tooltips.grid(row=widget_start_row, column=0, padx=(90, 0), sticky='e')

        self.tk_enable_tooltips = tk.IntVar(master=frm_prefs_widgets, value=self.mvc_controller.enable_tooltips)
        self.swt_enable_tooltips = ctk.CTkSwitch(master=frm_prefs_widgets,
                                                 text='Tooltips',
                                                 variable=self.tk_enable_tooltips)
        self.swt_enable_tooltips.grid(row=widget_start_row, column=1, padx=(0, 0), pady=10, sticky='w')
        widget_start_row += 1

        self.tk_enable_new_ssh_window = tk.IntVar(master=frm_prefs_widgets,
                                                  value=self.mvc_controller.enable_tooltips)

        self.tk_enable_tooltips = tk.IntVar(master=frm_prefs_widgets, value=self.mvc_controller.enable_tooltips)

        self.tk_enable_ancillary_ssh_window = tk.IntVar(master=frm_prefs_widgets,
                                                        value=self.mvc_controller.enable_ancillary_ssh_window)
        self.swt_enable_ancillary_ssh_window = ctk.CTkSwitch(master=frm_prefs_widgets,
                                                             text='SSH Ancillary Window',
                                                             variable=self.tk_enable_ancillary_ssh_window)

        self.swt_enable_ancillary_ssh_window.grid(row=widget_start_row, column=1, padx=(0, 0), pady=10, sticky='w')
        if self.tooltips_enabled():
            opm_app_theme_tooltip = ToolTip(self.swt_enable_ancillary_ssh_window,
                                            f'This is a command mode related option. If enabled, a separate window '
                                            f'is launched whenever the "-t" flag is used to launch an SSH tunnel. '
                                            f'This saves having to manually open up another command window, to run '
                                            f'the associated database connection command.'
                                            , TOOLTIP_DELAY)
            widget_start_row += 1

        lbl_default_wallet_directory = ctk.CTkLabel(master=frm_prefs_widgets, text='Default Wallet Locn')
        lbl_default_wallet_directory.grid(row=widget_start_row, padx=5, column=0, sticky='w')
        if self.tooltips_enabled():
            opm_app_theme_tooltip = ToolTip(lbl_default_wallet_directory,
                                            f"Set the default cloud wallet location.", TOOLTIP_DELAY)

        folder_image = ctk.CTkImage(light_image=Image.open(images_location / 'wallet_lm.png'),
                                    dark_image=Image.open(images_location / 'wallet_dm.png'),
                                    size=(35, 35))
        self.btn_default_wallet_directory = ctk.CTkButton(master=frm_prefs_widgets,
                                                          text='',
                                                          bg_color="transparent",
                                                          fg_color="transparent",
                                                          width=60,
                                                          height=30,
                                                          border_width=0,
                                                          command=self.mvc_controller.ask_default_wallet_directory,
                                                          image=folder_image
                                                          )
        self.btn_default_wallet_directory.grid(row=widget_start_row, column=1, padx=(0, 15), pady=(15, 0), sticky='w')
        if self.tooltips_enabled():
            opm_app_theme_tooltip = ToolTip(self.btn_default_wallet_directory,
                                            f"Set the default cloud wallet location.",
                                            TOOLTIP_DELAY)
        widget_start_row += 1

        self.lbl_default_wallet_name = ctk.CTkLabel(master=frm_prefs_widgets, font=SMALL_TEXT,
                                                    text=f'{self.mvc_controller.default_wallet_directory}',
                                                    width=220, justify='right')
        self.lbl_default_wallet_name.grid(row=widget_start_row, columnspan=2, column=0, padx=(130, 0), pady=0,
                                          sticky='w')

        widget_start_row += 1
        lbl_oci_config = ctk.CTkLabel(master=frm_prefs_widgets, text='OCI Config Locn', width=120, justify='right')
        lbl_oci_config.grid(row=widget_start_row, padx=(10, 0), column=0, sticky='w')
        if self.tooltips_enabled():
            opm_app_theme_tooltip = ToolTip(lbl_oci_config,
                                            f"The pathname to your OCI configuration. You must configure OCI "
                                            f"CLI, and set this location, to use the OCI Vault type "
                                            f"connections.", TOOLTIP_DELAY)

        config_image = ctk.CTkImage(light_image=Image.open(images_location / 'cloud_settings_lm.png'),
                                    dark_image=Image.open(images_location / 'cloud_settings_dm.png'),
                                    size=(40, 40))
        self.btn_oci_config = ctk.CTkButton(master=frm_prefs_widgets,
                                            text='',
                                            width=60,
                                            bg_color="transparent",
                                            fg_color="transparent",
                                            height=30,
                                            border_width=0,
                                            command=self.mvc_controller.get_oci_config,
                                            image=config_image
                                            )
        self.btn_oci_config.grid(row=widget_start_row, column=1, pady=(5, 0), sticky='w')
        if self.tooltips_enabled():
            opm_app_theme_tooltip = ToolTip(self.btn_oci_config,
                                            f"The pathname to your OCI configuration. You must configure OCI "
                                            f'CLI, and set this location, to use the "OCI Vault" type '
                                            f"connections.", TOOLTIP_DELAY)

        widget_start_row += 1

        self.lbl_oci_config = ctk.CTkLabel(master=frm_prefs_widgets, font=SMALL_TEXT,
                                           text=f'{self.mvc_controller.oci_config}',
                                           width=60, justify='right')
        self.lbl_oci_config.grid(row=widget_start_row, columnspan=2, column=0, padx=(165, 0), pady=0, sticky='w')

        # Control buttons
        btn_close = ctk.CTkButton(master=frm_buttons, text='Cancel', command=self.top_prefs.destroy)
        btn_close.grid(row=0, column=0, padx=(15, 35), pady=5)

        btn_save = ctk.CTkButton(master=frm_buttons, text='Save', command=self.save_preferences)
        btn_save.grid(row=0, column=1, padx=(PREFS_WIDTH - 350, 15), pady=5)
        self.top_prefs.grab_set()

    def launch_export_dialog(self):
        """Launch the export connections dialog (CTkToplevel)."""
        EXPORT_WIDTH = 600
        EXPORT_HEIGHT = 310
        border_width = 2
        pad_y = (20, 0)
        pad_y_button_group = (10, 0)
        position_geometry = self.mvc_controller.retrieve_geometry(window_category='toplevel')
        self.top_export = ctk.CTkToplevel(master=self)
        self.top_export.title('DCCM Export')
        self.top_export.geometry(position_geometry)
        self.top_export.geometry(f'{EXPORT_WIDTH}x{EXPORT_HEIGHT}')
        # Make preferences dialog modal
        self.top_export.rowconfigure(0, weight=1)
        self.top_export.rowconfigure(1, weight=0)
        self.top_export.columnconfigure(0, weight=1)

        self.frm_exp_left = ctk.CTkFrame(master=self.top_export, border_width=border_width)
        self.frm_exp_left.grid(row=0, column=0, padx=(5, 10), pady=(10, 0), sticky='nsew')

        # self.frm_exp_top.grid_columnconfigure(1, weight=1)
        # self.frm_exp_top.grid_rowconfigure(0, weight=1)

        self.frm_exp_right = ctk.CTkFrame(master=self.top_export, border_width=border_width)
        self.frm_exp_right.grid(row=0, column=1, padx=(5, 10), columnspan=3, pady=(10, 0), sticky='nsew')

        self.top_export.grab_set()

        btn_close = ctk.CTkButton(master=self.frm_exp_right,
                                  command=self.on_close_exports,
                                  text='Close')

        button_gap = 98

        download_image = ctk.CTkImage(light_image=Image.open(images_location / 'download_lm.png'),
                                      dark_image=Image.open(images_location / 'download_dm.png'),
                                      size=(16, 16))
        self.btn_exp_start = ctk.CTkButton(master=self.frm_exp_right,
                                           image=download_image,
                                           command=self.mvc_controller.begin_connection_export,
                                           text='Export')
        self.btn_exp_start.grid(row=0, column=0, padx=10, pady=(10, button_gap), sticky='e')

        btn_close.grid(row=1, column=0, padx=10, pady=(button_gap, 20), sticky='w')

        self.lbl_export_connections = ctk.CTkLabel(master=self.frm_exp_left,
                                                   text='Connection to Export:')
        self.lbl_export_connections.grid(row=0, column=0, padx=20, pady=(10, 0), sticky='w')

        # self.lbx_export_connections = ctk.CTkOptionMenu(master=self.frm_exp_left,
        self.lbx_export_connections = CTkListbox(master=self.frm_exp_left,
                                                 width=160,
                                                 multiple_selection=True,
                                                 )
        self.lbx_export_connections.grid(row=1, column=0, rowspan=4, padx=(10, 10), pady=0)

        self.lbl_export_password = ctk.CTkLabel(master=self.frm_exp_left,
                                                text='Password:')
        self.lbl_export_password.grid(row=0, column=1, padx=20, pady=(10, 0), sticky='w')
        if self.tooltips_enabled():
            self.ent_export_password_tooltip = ToolTip(self.lbl_export_password,
                                                       'Enter a password, if you wish to include your connection '
                                                       'passwords to the export.',
                                                       TOOLTIP_DELAY)

        self.ent_export_password = ctk.CTkEntry(master=self.frm_exp_left, placeholder_text='Enter password')
        self.ent_export_password.grid(row=1, column=1, padx=(10, 10), pady=(2, 0), sticky='n')
        self.ent_export_password.configure(show="*")

        self.ent_export_password2 = ctk.CTkEntry(master=self.frm_exp_left, placeholder_text='Confirm password')
        self.ent_export_password2.grid(row=2, column=1, padx=(10, 10), pady=(0, 60), sticky='n')
        self.ent_export_password2.configure(show="*")

        self.tk_export_wallets = ctk.StringVar(master=self.frm_exp_left, value='N')
        self.swt_export_wallets = ctk.CTkSwitch(master=self.frm_exp_left,
                                                text='Ship Wallet File(s)',
                                                variable=self.tk_export_wallets,
                                                onvalue='Y',
                                                offvalue='N')

        self.swt_export_wallets.grid(row=2, column=1, padx=10, pady=(140, 5))
        if self.tooltips_enabled():
            self.swt_export_wallets_tooltip = ToolTip(self.swt_export_wallets,
                                                      'If enabled, connections which have an associated wallet, have '
                                                      'their wallet included to the export file.',
                                                      TOOLTIP_DELAY)

        self.export_status_bar = cbtk.CBtkStatusBar(master=self.top_export)

    def launch_client_tool_templates(self):
        """Launch the client tool templates dialog (CTkToplevel)."""
        CLTOOL_WIDTH = 770
        CLTOOL_HEIGHT = 320
        border_width = 2
        pad_y = (20, 0)
        pad_y_button_group = (10, 0)
        position_geometry = self.mvc_controller.retrieve_geometry(window_category='toplevel')
        self.top_client_tool = ctk.CTkToplevel(master=self)
        self.top_client_tool.title('Client Tool Templates')
        self.top_client_tool.geometry(position_geometry)
        self.top_client_tool.geometry(f'{CLTOOL_WIDTH}x{CLTOOL_HEIGHT}')
        # Make preferences dialog modal
        self.top_client_tool.rowconfigure(0, weight=1)
        self.top_client_tool.rowconfigure(1, weight=0)
        self.top_client_tool.columnconfigure(0, weight=1)

        frm_client_tool_control = ctk.CTkFrame(master=self.top_client_tool, border_width=0)
        frm_client_tool_control.grid(row=0, column=0, sticky='wns', padx=(10, 5), pady=(10, 0), rowspan=3)

        self.frm_client_tool_right = ctk.CTkFrame(master=self.top_client_tool, border_width=border_width)
        self.frm_client_tool_right.grid(row=0, column=1, padx=(5, 10), pady=(10, 0), sticky='nsew')
        self.frm_client_tool_right.grid_columnconfigure(1, weight=1)
        self.frm_client_tool_right.grid_rowconfigure(0, weight=1)

        self.frm_client_tool_setting = ctk.CTkFrame(master=self.frm_client_tool_right, border_width=border_width)
        self.frm_client_tool_setting.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
        self.top_client_tool.grab_set()

        row = 0
        self.lbl_cltool_templates = ctk.CTkLabel(master=frm_client_tool_control,
                                                 text='Modify Template:')
        self.lbl_cltool_templates.grid(row=row, column=0, padx=(0, 10), pady=(2, 0))

        row += 1
        self.opm_client_tool_templates = ctk.CTkOptionMenu(master=frm_client_tool_control,
                                                           width=160,
                                                           state=tk.DISABLED,
                                                           command=self.mvc_controller.select_client_tool_template)
        self.opm_client_tool_templates.grid(row=row, column=0, padx=(30, 10), pady=(2, 30))
        row += 1

        self.btn_cltool_new = ctk.CTkButton(master=frm_client_tool_control,
                                            command=self.mvc_controller.new_client_tool_template,
                                            text='New Template')
        self.btn_cltool_new.grid(row=row, column=0, padx=10, pady=pad_y_button_group)
        if self.tooltips_enabled():
            self._create_tooltip = ToolTip(self.btn_cltool_new,
                                           'Create a new tool command template',
                                           TOOLTIP_DELAY)
        row += 1

        self.btn_cltool_save = ctk.CTkButton(master=frm_client_tool_control,
                                             command=self.mvc_controller.save_client_tool_template,
                                             state=tk.DISABLED,
                                             text='Save Template')
        self.btn_cltool_save.grid(row=row, column=0, padx=10, pady=pad_y_button_group)
        if self.tooltips_enabled():
            self.modify_tooltip = ToolTip(self.btn_cltool_save,
                                          'Save changes to the selected and modified client tool template',
                                          TOOLTIP_DELAY)

        row += 1

        self.btn_cltool_delete = ctk.CTkButton(master=frm_client_tool_control,
                                               command=self.mvc_controller.delete_client_tool_template,
                                               state=tk.DISABLED,
                                               text='Delete Template')
        self.btn_cltool_delete.grid(row=row, column=0, padx=10, pady=pad_y_button_group)
        if self.tooltips_enabled():
            self.modify_tooltip = ToolTip(self.btn_cltool_delete,
                                          'Delete the currently selected client tool template',
                                          TOOLTIP_DELAY)
        row += 1

        btn_close = ctk.CTkButton(master=frm_client_tool_control,
                                  command=self.mvc_controller.on_close_client_tools,
                                  text='Close')
        btn_close.grid(row=row, column=0, padx=10, pady=(38, 10), sticky='s')
        row += 1

        self.lbl_cltool_client_tool_code = ctk.CTkLabel(master=self.frm_client_tool_setting,
                                                        bg_color="transparent",
                                                        fg_color="transparent",
                                                        state=tk.DISABLED,
                                                        text='Template Name:')
        self.lbl_cltool_client_tool_code.grid(row=row, column=0, padx=1, pady=(15, 0), sticky='w')
        if self.tooltips_enabled():
            lbl_theme_tooltip = ToolTip(self.lbl_cltool_client_tool_code,
                                        f"Enter a unique client tool command reference. You can optionally select "
                                        f"from these entries, in the connections maintenance window.",
                                        TOOLTIP_DELAY)
        row += 1

        self.tk_cltool_client_tool_code = tk.StringVar(master=self.frm_client_tool_setting)
        self.ent_cltool_client_tool_code = ctk.CTkEntry(master=self.frm_client_tool_setting,
                                                        state=tk.DISABLED,
                                                        textvariable=self.tk_cltool_client_tool_code,
                                                        placeholder_text='Unique Name')
        self.ent_cltool_client_tool_code.grid(row=row, column=0, padx=10, pady=(0, 10), sticky='w')
        row += 1

        self.lbl_cltool_command_template = ctk.CTkLabel(master=self.frm_client_tool_setting,
                                                        state=tk.DISABLED,
                                                        text='Client Command Template:')
        self.lbl_cltool_command_template.grid(row=row, column=0, padx=20, pady=(10, 0), sticky='w')
        if self.tooltips_enabled():
            lbl_theme_tooltip = ToolTip(self.lbl_cltool_command_template,
                                        f"For new templates, modify the <example-command> entry to match the required "
                                        f"command. The strings enclosed by hashes are auto-substituted at runtime. "
                                        f"There are more substitution options, including #wallet_location#, "
                                        f" #listener_port#, #wallet_location#... - see the 2.0.0 release notes "
                                        f"for more details.",
                                        TOOLTIP_DELAY)
        row += 1

        self.tk_cltool_command_template = tk.StringVar(master=self.frm_client_tool_setting)
        self.ent_cltool_command_template = ctk.CTkEntry(master=self.frm_client_tool_setting,
                                                        state=tk.DISABLED,
                                                        textvariable=self.tk_cltool_command_template,
                                                        placeholder_text='Command Template',
                                                        width=500)
        self.ent_cltool_command_template.grid(row=row, column=0, padx=10, pady=(0, 15))

        self.btn_cltool_cancel = ctk.CTkButton(master=self.frm_client_tool_right,
                                               command=self.mvc_controller.cancel_client_tool_operation,
                                               state=tk.DISABLED,
                                               text='Cancel')
        self.btn_cltool_cancel.grid(row=10, column=1, padx=10, pady=(0, 10), sticky='ew')
        if self.tooltips_enabled():
            self.btn_cltool_cancel_tooltip = ToolTip(self.btn_cltool_cancel,
                                                     'Cancel operation - resets the page.',
                                                     TOOLTIP_DELAY)

        row += 1
        self.client_tool_status_bar = cbtk.CBtkStatusBar(master=self.top_client_tool)


    def launch_import_dialog(self):
        """Launch the import connections dialog (CTkToplevel)."""
        IMPORT_WIDTH = 650
        IMPORT_HEIGHT = 480
        border_width = 2
        button_gap = 175

        position_geometry = self.mvc_controller.retrieve_geometry(window_category='toplevel')
        self.top_import = ctk.CTkToplevel(master=self)
        self.top_import.title('DCCM Import')
        self.top_import.geometry(position_geometry)
        self.top_import.geometry(f'{IMPORT_WIDTH}x{IMPORT_HEIGHT}')
        # Make preferences dialog modal
        self.top_import.rowconfigure(0, weight=1)
        self.top_import.rowconfigure(1, weight=0)
        self.top_import.columnconfigure(0, weight=1)

        self.frm_imp_left = ctk.CTkFrame(master=self.top_import, border_width=border_width)
        self.frm_imp_left.grid(row=0, column=0, padx=(5, 10), pady=(10, 0), sticky='nsew')

        # self.frm_imp_top.grid_columnconfigure(1, weight=1)
        # self.frm_imp_top.grid_rowconfigure(0, weight=1)

        self.frm_imp_right = ctk.CTkFrame(master=self.top_import, border_width=border_width)
        self.frm_imp_right.grid(row=0, column=1, padx=(5, 10), columnspan=3, pady=(10, 0), sticky='nsew')

        self.top_import.grab_set()

        self.btn_imp_start = ctk.CTkButton(master=self.frm_imp_right,
                                           command=self.mvc_controller.begin_connection_import,
                                           text='Import')
        self.btn_imp_start.grid(row=0, column=0, padx=10, pady=(15, button_gap), sticky='e')

        btn_close = ctk.CTkButton(master=self.frm_imp_right,
                                  command=self.on_close_imports,
                                  text='Close')
        btn_close.grid(row=1, column=0, padx=10, pady=(button_gap + 5, 10), sticky='w')

        # Rest of widgets start here
        row = 0
        self.lbl_imp_import_file = ctk.CTkLabel(master=self.frm_imp_left,
                                                text='Select Import File:')
        self.lbl_imp_import_file.grid(row=row, column=0, padx=10, pady=(10, 0), sticky='w')

        upload_image = ctk.CTkImage(light_image=Image.open(images_location / 'upload_lm.png'),
                                    dark_image=Image.open(images_location / 'upload_dm.png'),
                                    size=(40, 40))
        self.btn_imp_import_file = ctk.CTkButton(master=self.frm_imp_left,
                                                 text='',
                                                 bg_color="transparent",
                                                 fg_color="transparent",
                                                 width=30,
                                                 height=30,
                                                 image=upload_image,
                                                 command=self.mvc_controller.ask_import_file)
        self.btn_imp_import_file.grid(row=1, column=0, padx=20, pady=(0, 5), sticky='w')


        self.lbl_imp_import_file = ctk.CTkLabel(master=self.frm_imp_left, font=SMALL_TEXT,
                                                text='(Import not selected)')


        self.lbl_imp_import_file.grid(row=2, column=0, padx=(10, 10), pady=0, sticky='w')

        self.lbl_imp_import_connections = ctk.CTkLabel(master=self.frm_imp_left,
                                                       text='Connections to Import:')
        self.lbl_imp_import_connections.grid(row=3, column=0, padx=10, pady=(10, 0), sticky='w')

        self.lbx_imp_import_connections = CTkListbox(master=self.frm_imp_left,
                                                     width=160,
                                                     multiple_selection=True)

        self.lbx_imp_import_connections.grid(row=4, column=0, rowspan=3, padx=(10, 10), pady=(2, 10))


        self.tk_imp_merge = ctk.StringVar(master=self.frm_imp_left, value='N')
        self.swt_imp_merge = ctk.CTkSwitch(master=self.frm_imp_left,
                                           text='Merge Connections',
                                           variable=self.tk_imp_merge,
                                           onvalue='Y',
                                           offvalue='N')

        self.swt_imp_merge.grid(row=0, column=1, padx=(35, 5), pady=(50, 5), sticky='s')
        if self.tooltips_enabled():
            self.swt_imp_merge_tooltip = ToolTip(self.swt_imp_merge,
                                                 'If enabled, this option causes the import to overwrite any of your '
                                                 'connections matched by those being imported.',
                                                 TOOLTIP_DELAY)


        default_wallet_directory = default_wallet_directory = mod.preference(db_file_path=db_file,
                                                                             scope='preference',
                                                                             preference_name='default_wallet_directory')

        self.tk_remap_wallets = ctk.StringVar(master=self.frm_imp_left, value='Y')
        self.swt_imp_remap_wallet = ctk.CTkSwitch(master=self.frm_imp_left,
                                                  text='Remap Wallet Locns',
                                                  command=self.mvc_controller.toggle_import_wallets,
                                                  variable=self.tk_remap_wallets,
                                                  onvalue='Y',
                                                  offvalue='N')
        self.swt_imp_remap_wallet.grid(row=1, column=1, padx=(35, 5), pady=10, sticky='s')
        if default_wallet_directory == 'None' or not default_wallet_directory:
            self.tk_imp_merge.set('N')
            self.swt_imp_remap_wallet.deselect()
            self.swt_imp_remap_wallet.configure(state=tk.DISABLED)

        if self.tooltips_enabled():
            self.swt_imp_remap_wallet_tooltip = ToolTip(self.swt_imp_remap_wallet,
                                                        'If enabled, then causes the import to Remap any wallet '
                                                        'locations specified in the import file, to your default '
                                                        'wallet location.',
                                                        TOOLTIP_DELAY)

        row += 1

        self.tk_imp_import_wallets = ctk.StringVar(master=self.frm_imp_left, value='N')
        self.swt_imp_import_wallets = ctk.CTkSwitch(master=self.frm_imp_left,
                                                    text='Import Wallets',
                                                    variable=self.tk_imp_import_wallets,
                                                    onvalue='Y',
                                                    offvalue='N')
        self.swt_imp_import_wallets.grid(row=2, column=1, padx=0, pady=10, sticky='s')
        if self.tooltips_enabled():
            self.swt_imp_remap_wallet_tooltip = ToolTip(self.swt_imp_import_wallets,
                                                        'If enabled, this causes the import to import any wallets '
                                                        'shipped within the export file. When imported, these are '
                                                        'unpacked to the default wallet location, as defined in '
                                                        'Tools > Preferences.',
                                                        TOOLTIP_DELAY)

        self.lbl_imp_import_password = ctk.CTkLabel(master=self.frm_imp_left,
                                                    text='Password Required:')
        self.lbl_imp_import_password.grid(row=3, column=1, padx=(10, 20), pady=(10, 0))
        self.lbl_imp_import_password.grid_remove()

        self.ent_imp_import_password = ctk.CTkEntry(master=self.frm_imp_left, placeholder_text='Enter password')
        self.ent_imp_import_password.grid(row=4, column=1, padx=(30, 10), pady=(2, 10), sticky='n')

        self.ent_imp_import_password.grid_remove()
        self.ent_imp_import_password.configure(show="*")

        if self.tooltips_enabled():
            self.ent_imp_import_password_tooltip = ToolTip(self.lbl_imp_import_password,
                                                           'The export has password encrypted components. You must supply '
                                                           'the password, to successfully import any connections.',
                                                           TOOLTIP_DELAY)

        self.imp_status_bar = cbtk.CBtkStatusBar(master=self.top_import)

    def launch_tunnel_templates(self):
        """Launch the tunnel templates dialog (CTkToplevel)."""
        TUNNL_WIDTH = 770
        TUNNL_HEIGHT = 320
        border_width = 2
        pad_y = (20, 0)
        pad_y_button_group = (10, 0)
        position_geometry = self.mvc_controller.retrieve_geometry(window_category='toplevel')
        self.top_tunnel = ctk.CTkToplevel(master=self)
        self.top_tunnel.title('SSH Tunnelling Templates')
        self.top_tunnel.geometry(position_geometry)
        self.top_tunnel.geometry(f'{TUNNL_WIDTH}x{TUNNL_HEIGHT}')
        # Make preferences dialog modal
        self.top_tunnel.rowconfigure(0, weight=1)
        self.top_tunnel.rowconfigure(1, weight=0)
        self.top_tunnel.columnconfigure(0, weight=1)

        frm_tunnel_control = ctk.CTkFrame(master=self.top_tunnel, border_width=0)
        frm_tunnel_control.grid(row=0, column=0, sticky='wns', padx=(10, 5), pady=(10, 0), rowspan=3)

        self.frm_tunnel_right = ctk.CTkFrame(master=self.top_tunnel, border_width=border_width)
        self.frm_tunnel_right.grid(row=0, column=1, padx=(5, 10), pady=(10, 0), sticky='nsew')
        self.frm_tunnel_right.grid_columnconfigure(1, weight=1)
        self.frm_tunnel_right.grid_rowconfigure(0, weight=1)

        self.frm_tunnel_setting = ctk.CTkFrame(master=self.frm_tunnel_right, border_width=border_width)
        self.frm_tunnel_setting.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
        self.top_tunnel.grab_set()

        row = 0
        self.lbl_tunnel_templates = ctk.CTkLabel(master=frm_tunnel_control,
                                                 text='Modify Template:')
        self.lbl_tunnel_templates.grid(row=row, column=0, padx=(0, 10), pady=(2, 0))

        row += 1
        self.opm_tunnel_templates = ctk.CTkOptionMenu(master=frm_tunnel_control,
                                                      width=160,
                                                      state=tk.DISABLED,
                                                      command=self.mvc_controller.select_tunnel_template)
        self.opm_tunnel_templates.grid(row=row, column=0, padx=(30, 10), pady=(2, 30))
        row += 1

        self.btn_tunnel_new = ctk.CTkButton(master=frm_tunnel_control, command=self.mvc_controller.new_tunnel_template,
                                            text='New Template')
        self.btn_tunnel_new.grid(row=row, column=0, padx=10, pady=pad_y_button_group)
        if self.tooltips_enabled():
            self._create_tooltip = ToolTip(self.btn_tunnel_new,
                                           'Create a new SSH tunnelling command template',
                                           TOOLTIP_DELAY)
        row += 1

        self.btn_tunnel_save = ctk.CTkButton(master=frm_tunnel_control,
                                             command=self.mvc_controller.save_tunnel_template,
                                             state=tk.DISABLED,
                                             text='Save Template')
        self.btn_tunnel_save.grid(row=row, column=0, padx=10, pady=pad_y_button_group)
        if self.tooltips_enabled():
            self.modify_tooltip = ToolTip(self.btn_tunnel_save,
                                          'Save changes to the selected and modified tunnelling template',
                                          TOOLTIP_DELAY)

        row += 1

        self.btn_tunnel_delete = ctk.CTkButton(master=frm_tunnel_control,
                                               command=self.mvc_controller.delete_tunnel_template,
                                               state=tk.DISABLED,
                                               text='Delete Template')
        self.btn_tunnel_delete.grid(row=row, column=0, padx=10, pady=pad_y_button_group)
        if self.tooltips_enabled():
            self.modify_tooltip = ToolTip(self.btn_tunnel_delete,
                                          'Delete the currently selected tunnelling template',
                                          TOOLTIP_DELAY)
        row += 1

        btn_close = ctk.CTkButton(master=frm_tunnel_control,
                                  command=self.on_close_tunnels,
                                  text='Close')
        btn_close.grid(row=row, column=0, padx=10, pady=(38, 10), sticky='s')
        row += 1

        self.lbl_tunnel_ssh_tunnel_code = ctk.CTkLabel(master=self.frm_tunnel_setting,
                                                       bg_color="transparent",
                                                       fg_color="transparent",
                                                       state=tk.DISABLED,
                                                       text='Template Name:')
        self.lbl_tunnel_ssh_tunnel_code.grid(row=row, column=0, padx=1, pady=(15, 0), sticky='w')
        if self.tooltips_enabled():
            lbl_theme_tooltip = ToolTip(self.lbl_tunnel_ssh_tunnel_code,
                                        f"Enter a unique SSH tunneling command reference. You can optionally select "
                                        f"from these entries, in the connections maintenance window.",
                                        TOOLTIP_DELAY)
        row += 1

        self.tk_tunnel_ssh_tunnel_code = tk.StringVar(master=self.frm_tunnel_setting)
        self.ent_tunnel_ssh_tunnel_code = ctk.CTkEntry(master=self.frm_tunnel_setting,
                                                       state=tk.DISABLED,
                                                       textvariable=self.tk_tunnel_ssh_tunnel_code,
                                                       placeholder_text='Unique Name')
        self.ent_tunnel_ssh_tunnel_code.grid(row=row, column=0, padx=10, pady=(0, 10), sticky='w')
        row += 1

        self.lbl_tunnel_command_template = ctk.CTkLabel(master=self.frm_tunnel_setting,
                                                        state=tk.DISABLED,
                                                        text='SSH Command Template:')
        self.lbl_tunnel_command_template.grid(row=row, column=0, padx=20, pady=(10, 0), sticky='w')
        if self.tooltips_enabled():
            lbl_theme_tooltip = ToolTip(self.lbl_tunnel_command_template,
                                        f"For new templates, modify the <jump-host-entry> to match the required "
                                        f"jump host. The strings enclosed by hashes are auto-substituted at runtime.",
                                        TOOLTIP_DELAY)
        row += 1

        self.tk_tunnel_command_template = tk.StringVar(master=self.frm_tunnel_setting)
        self.ent_tunnel_command_template = ctk.CTkEntry(master=self.frm_tunnel_setting,
                                                        state=tk.DISABLED,
                                                        textvariable=self.tk_tunnel_command_template,
                                                        placeholder_text='Command Template',
                                                        width=500)
        self.ent_tunnel_command_template.grid(row=row, column=0, padx=10, pady=(0, 15))

        self.btn_tunnel_cancel = ctk.CTkButton(master=self.frm_tunnel_right,
                                               command=self.mvc_controller.cancel_tunnel_operation,
                                               state=tk.DISABLED,
                                               text='Cancel')
        self.btn_tunnel_cancel.grid(row=10, column=1, padx=10, pady=(0, 10), sticky='ew')
        if self.tooltips_enabled():
            self.cancel_tooltip = ToolTip(self.btn_tunnel_cancel,
                                          'Cancel operation - resets the page.',
                                          TOOLTIP_DELAY)

        row += 1
        self.tunnel_status_bar = cbtk.CBtkStatusBar(master=self.top_tunnel)

    def on_close_exports(self):
        """The on_close_exports method, tidies up when we close the connection exports dialog."""
        try:
            self.export_status_bar.cancel_message_timer()
        except ValueError:
            # We get a value error if we haven't issues a message and incurred an "after",
            # since there is no
            pass
        self.top_export.destroy()

    def on_close_imports(self):
        """The on_close_imports method, tidies up when we close the connection imports dialog."""
        try:
            self.imp_status_bar.cancel_message_timer()
        except ValueError:
            # We get a value error if we haven't issues a message and incurred an "after",
            # since there is no
            pass
        self.top_import.destroy()

    def on_close_tunnels(self):
        """The on_close_tunnels method, tidies up when we close the tunnelling templates maintenance dialog."""
        try:
            self.tunnel_status_bar.cancel_message_timer()
        except ValueError:
            # We get a value error if we haven't issues a message and incurred an "after",
            # since there is no
            pass
        self.top_tunnel.destroy()

    def launch_connections_scan(self):
        """The launch_connections_scan creates a CTkToplevel and reports the connection availability of the user
        connections. It also provides a launch option for each all connections which appear to be available."""
        CSCAN_WIDTH = 680
        CSCAN_HEIGHT = 470

        self.mvc_controller.status_bar.set_status_text(
            status_text='Scanning your connection ports, please wait...')
        position_geometry = self.mvc_controller.retrieve_geometry(window_category='toplevel')
        self.top_cscan = ctk.CTkToplevel(master=self)
        self.top_cscan.title('DCCM Connectivity Scan')
        self.top_cscan.geometry(position_geometry)
        self.top_cscan.geometry(f'{CSCAN_WIDTH}x{CSCAN_HEIGHT}')
        # Make preferences dialog modal
        self.top_cscan.rowconfigure(0, weight=1)
        self.top_cscan.rowconfigure(1, weight=0)
        self.top_cscan.columnconfigure(0, weight=1)

        frm_cscan_main = ctk.CTkFrame(master=self.top_cscan)
        frm_cscan_main.grid(column=0, row=0, sticky='nsew')
        frm_cscan_main.columnconfigure(0, weight=1)
        frm_cscan_main.rowconfigure(0, weight=1)

        frm_cscan_widgets = ctk.CTkScrollableFrame(master=frm_cscan_main)
        frm_cscan_widgets.grid(column=0, row=0, padx=10, pady=10, sticky='nsew')

        frm_buttons = ctk.CTkFrame(master=frm_cscan_main)
        frm_buttons.grid(column=0, row=1, padx=(10, 10), pady=(0, 10), sticky='ew')

        btn_ok = ctk.CTkButton(master=frm_buttons, text='OK', width=CSCAN_WIDTH - 30,
                               command=self.top_cscan.destroy)
        btn_ok.grid(row=0, column=0, padx=(5, 5), pady=10)

        connections = self.mvc_controller.connections_dict()
        row = 0
        self.launch_buttons = {}
        HEADING_UL = HEADING2 = ('Roboto', 14)

        connection_table = [['Connection Id', 'DB Account', 'Connect String', 'Contactable', 'Launch']]

        button_fg_color = cbtk.get_color_from_name(widget_type='CTkButton', widget_property='fg_color')
        button_hover_color = cbtk.get_color_from_name(widget_type='CTkButton', widget_property='hover_color')
        self.tbv_connections = CTkTable(master=frm_cscan_widgets,
                                        values=connection_table,
                                        hover=True,
                                        anchor='w',
                                        corner_radius=5,
                                        header_color=button_fg_color)
        self.tbv_connections.grid(row=0, column=0)

        row += 1
        for i, connection_name in enumerate(connections.keys(), start=1):
            db_account_name = connections[connection_name]["db_account_name"]
            connect_string = connections[connection_name]["connect_string"]
            start_directory = connections[connection_name]["start_directory"]
            table_row = [connection_name, db_account_name, connect_string, '', '']
            self.tbv_connections.add_row(values=table_row)
            self.tbv_connections.edit_row(i, state=ctk.DISABLED)

        # Second loop. We need this because we can't combine add_row and insert in
        # the same loop (current limitation on CTkTable).
        for i, connection_name in enumerate(connections.keys(), start=1):
            db_account_name = connections[connection_name]["db_account_name"]
            connect_string = connections[connection_name]["connect_string"]
            start_directory = connections[connection_name]["start_directory"]

            try:
                host, port = self.mvc_controller.resolve_connect_host_port(connection_name=connection_name)
            except FileNotFoundError:
                host = port = None
            tk_state = None
            stale_connection = False
            port_open = False
            if host is not None and port is not None:
                stale_connection = False
                port_open = mod.port_is_open(host=host, port_number=port)
            elif host is None or port is None:
                stale_connection = True
                port_open = False

            if not stale_connection:
                stale_icon = ctk.CTkImage(light_image=Image.open(images_location / 'launch_lm.png'),
                                          dark_image=Image.open(images_location / 'launch_dm.png'),
                                          size=(20, 20))
            else:
                stale_icon = ctk.CTkImage(light_image=Image.open(images_location / 'x_bones_lm.png'),
                                          dark_image=Image.open(images_location / 'x_bones_dm.png'),
                                          size=(20, 20))

            if port_open:
                tk_state = tk.NORMAL
                tooltip_text = 'Database server appears to be contactable.'
                hover_colour = button_hover_color
                icon_file_lm = 'tick_lm.png'
                icon_file_dm = 'tick_dm.png'
            elif not port_open and stale_connection:
                tk_state = tk.DISABLED
                hover_colour = button_fg_color
                icon_file_lm = 'q_mark_lm.png'
                icon_file_dm = 'q_mark_dm.png'
                tooltip_text = 'Connection entry appears to be stale. Has an associated tnsnames.ora entry been ' \
                               'deleted? '
            else:
                tooltip_text = 'Database server cannot be contacted.'
                hover_colour = button_fg_color
                tk_state = tk.DISABLED
                icon_file_lm = 'cross_lm.png'
                icon_file_dm = 'cross_dm.png'

            icon_image = ctk.CTkImage(light_image=Image.open(images_location / icon_file_lm),
                                      dark_image=Image.open(images_location / icon_file_dm),
                                      size=(16, 16))

            self.tbv_connections.insert(i, 3, '', width=40, image=icon_image, anchor='c')
            self.tbv_connections.insert(i, 4, '', width=40, image=stale_icon, anchor='c', state=tk_state,
                                        hover_color=hover_colour,
                                        command=lambda connection=connection_name:
                                        self.mvc_controller.launch_client_connection(connection_name=connection))

            if self.tooltips_enabled():
                self.probe_tooltip = ToolTip(self.tbv_connections.frame[i, 3], tooltip_text, TOOLTIP_DELAY)

            if self.tooltips_enabled() and port_open:
                tooltip_text = 'Click to launch connection.'
                self.launch_tooltip = ToolTip(self.tbv_connections.frame[i, 4], tooltip_text, TOOLTIP_DELAY)

            launch = ctk.CTkImage(light_image=Image.open(images_location / 'launch_lm.png'),
                                  dark_image=Image.open(images_location / 'launch_dm.png'),
                                  size=(16, 16))

            if tk_state == tk.DISABLED:
                availability = ' [ disabled ]'
            else:
                availability = ''

            row += 1
        self.tbv_connections.edit_column(3, width=40)
        self.tbv_connections.edit_column(4, width=40)
        self.top_cscan.grab_set()

    def save_tunnel(self):
        """Save the new/modified ssh tunnelling template."""
        self.mvc_controller.save_tunnel()
        self.top_tunnel.destroy()

    def save_preferences(self):
        """Save the new/modified preference record."""
        self.mvc_controller.save_preferences()
        self.top_prefs.destroy()

    def render_root_window_contents(self):
        """After the root window is instantiated by the controller, the render_root_window_contents method is used
        to create frames/widgets therein."""
        pad_y = (20, 0)
        pad_y_button_group = (10, 0)

        # Frames
        # TODO: Add a LabelFrame to CBTK module.
        # frm_connection_type = tk.LabelFrame(master=frm_root_widgets, text='Management Type')
        # frm_connection_type.grid(row=0, column=0)

        border_width = 1

        frm_root_buttons = ctk.CTkFrame(master=self, border_width=0)
        frm_root_buttons.grid(row=0, column=0, sticky='wns', padx=(10, 5), pady=(10, 10), rowspan=3)

        self.frm_right = ctk.CTkFrame(master=self, border_width=border_width)
        self.frm_right.grid(row=0, column=1, padx=(5, 10), pady=(10, 10), sticky='ewns')
        # self.frm_right.grid_columnconfigure(0, weight=1)

        self.frm_connection_type = ctk.CTkFrame(master=self.frm_right, border_width=border_width)
        self.frm_connection_type.grid(row=1, column=1, padx=10, pady=5, sticky='ew')
        self.frm_connection_type.grid_columnconfigure(0, weight=1)
        self.frm_connection_type.grid_columnconfigure(1, weight=1)
        self.frm_connection_type.grid_remove()

        self.frm_root_database_account = ctk.CTkFrame(master=self.frm_right, border_width=border_width)
        self.frm_root_database_account.grid(row=2, column=1, padx=10, pady=5, sticky='ew')
        self.frm_root_database_account.grid_remove()

        self.frm_root_connect_string = ctk.CTkFrame(master=self.frm_right, border_width=border_width)
        self.frm_root_connect_string.grid(row=3, column=1, padx=10, pady=5, sticky='ew')
        self.frm_root_connect_string.grid_remove()

        self.frm_root_client_tool = ctk.CTkFrame(master=self.frm_right, border_width=border_width)
        self.frm_root_client_tool.grid(row=4, column=1, padx=10, pady=(5, 10), sticky='ew')
        self.frm_root_client_tool.grid_remove()

        self.frm_root_initial_dir = ctk.CTkFrame(master=self.frm_right, border_width=border_width)
        self.frm_root_initial_dir.grid(row=5, column=1, padx=10, pady=(5, 10), sticky='ew')
        self.frm_root_initial_dir.grid_remove()

        self.frm_root_ssh_tunnel = ctk.CTkFrame(master=self.frm_right, border_width=border_width)
        self.frm_root_ssh_tunnel.grid(row=6, column=1, padx=10, pady=10, sticky='ew')
        self.frm_root_ssh_tunnel.grid_remove()

        # Widgets

        row = 0
        self.lbl_control = ctk.CTkLabel(master=frm_root_buttons,
                                        font=HEADING3,
                                        text='Control')
        self.lbl_control.grid(row=0, column=0, padx=10, pady=(5, 0))

        row += 1
        self.lbl_connections = ctk.CTkLabel(master=frm_root_buttons,
                                            text='Connections:')
        self.lbl_connections.grid(row=row, column=0, padx=5, pady=(10, 0))
        if self.tooltips_enabled():
            lbl_theme_tooltip = ToolTip(self.lbl_connections,
                                        f"Select a database connection to work with.",
                                        TOOLTIP_DELAY)
        row += 1

        default_connection = self.mvc_controller.default_connection()
        self.opm_connections = ctk.CTkOptionMenu(master=frm_root_buttons,
                                                 width=160,
                                                 command=self.mvc_controller.display_connection_attributes)
        self.opm_connections.grid(row=row, column=0, padx=(30, 10), pady=(2, 0))
        row += 1
        if default_connection is not None:
            self.opm_connections.set(default_connection)
        else:
            self.opm_connections.set('-- Connections --')

        self.btn_set_current = ctk.CTkButton(master=frm_root_buttons,
                                             command=self.mvc_controller.set_connection_as_current,
                                             state=tk.DISABLED,
                                             text='Set as Default')
        self.btn_set_current.grid(row=row, column=0, padx=10, pady=pad_y, sticky='s')
        row += 1
        default_connection = self.mvc_controller.default_connection()
        default_connection = f'( Default: {default_connection} )'
        self.lbl_default_connection = ctk.CTkLabel(master=frm_root_buttons,
                                                   font=SMALL_TEXT,
                                                   text=default_connection)
        self.lbl_default_connection.grid(row=row, column=0, padx=10, pady=(10, 0))
        row += 1

        btn_create = ctk.CTkButton(master=frm_root_buttons,
                                   command=self.mvc_controller.launch_new_connection,
                                   text='New Connection')
        btn_create.grid(row=row, column=0, padx=10, pady=pad_y_button_group)
        if self.tooltips_enabled():
            self.modify_tooltip = ToolTip(btn_create,
                                          'Create a new database / client connection.', TOOLTIP_DELAY)
        row += 1

        self.btn_modify = ctk.CTkButton(master=frm_root_buttons,
                                        command=self.mvc_controller.launch_mod_connection,
                                        state=tk.DISABLED,
                                        text='Modify Connection')
        self.btn_modify.grid(row=row, column=0, padx=10, pady=pad_y_button_group)
        if self.tooltips_enabled():
            self.modify_tooltip = ToolTip(self.btn_modify,
                                          'Modify the selected connection.', TOOLTIP_DELAY)
        row += 1

        self.btn_delete = ctk.CTkButton(master=frm_root_buttons, command=self.mvc_controller.root_delete_connection,
                                        state=tk.DISABLED,
                                        text='Delete Connection')
        self.btn_delete.grid(row=row, column=0, padx=15, pady=(10, 10), sticky='s')
        if self.tooltips_enabled():
            self.delete_tooltip = ToolTip(self.btn_delete,
                                          'Delete the selected connection.', TOOLTIP_DELAY)
        row += 1

        self.btn_launch_client = ctk.CTkButton(master=frm_root_buttons,
                                               state=tk.DISABLED,
                                               command=self.mvc_controller.launch_client_connection,
                                               text='Launch Connection')
        self.btn_launch_client.grid(row=row, column=0, padx=10, pady=(30, 5))
        if self.tooltips_enabled():
            lbl_theme_tooltip = ToolTip(self.btn_launch_client,
                                        f"Launch the currently selected client connection.",
                                        TOOLTIP_DELAY)
        row += 1
        self.btn_launch_ssh = ctk.CTkButton(master=frm_root_buttons,
                                            state=tk.DISABLED,
                                            command=self.mvc_controller.launch_ssh_tunnel,
                                            text='Establish SSH Tunnel')
        self.btn_launch_ssh.grid(row=row, column=0, padx=10, pady=(10, 0))
        if self.tooltips_enabled():
            lbl_theme_tooltip = ToolTip(self.btn_launch_ssh,
                                        f"When enabled, this button allows you to launch the SSH "
                                        f"command to create a an SSH tunnel, specific to the selected connection.",
                                        TOOLTIP_DELAY)
        row += 1

        btn_close = ctk.CTkButton(master=frm_root_buttons, command=self.on_close, text='Close')
        btn_close.grid(row=row, column=0, padx=10, pady=(40, 10), sticky='s')

        row = 0
        self.lbl_selected_connection = ctk.CTkLabel(master=self.frm_right,
                                                    font=HEADING3,
                                                    text='Connection Synopsis')
        self.lbl_selected_connection.grid(row=row, column=1, padx=10, pady=(5, 5), sticky='ew')

        row = 1
        self.lbl_root_connection_type = ctk.CTkLabel(master=self.frm_connection_type,
                                                     fg_color="transparent",
                                                     text='Management Type:')
        self.lbl_root_connection_type.grid(row=row, column=0, padx=(5, 15), pady=(5, 0), sticky='w')
        self.lbl_root_connection_type.grid_remove()

        row += 1

        self.lbl_root_connection_type_disp = ctk.CTkLabel(master=self.frm_connection_type,
                                                          fg_color="transparent",
                                                          text='')
        self.lbl_root_connection_type_disp.grid(row=row, column=0, padx=(30, 10), pady=(0, 5), sticky='ew')
        row += 1

        self.lbl_root_database_account = ctk.CTkLabel(master=self.frm_root_database_account,
                                                      fg_color="transparent",
                                                      text='DB Account:')
        self.lbl_root_database_account.grid(row=row, column=0, padx=(5, 10), pady=(5, 0), sticky='w')
        self.lbl_root_database_account.grid_remove()
        row += 1

        self.lbl_root_database_account_disp = ctk.CTkLabel(master=self.frm_root_database_account,
                                                           fg_color="transparent",
                                                           text='')
        self.lbl_root_database_account_disp.grid(row=row, column=0, padx=(30, 10), pady=(0, 5), sticky='w')
        row += 1

        self.lbl_root_connect_string = ctk.CTkLabel(master=self.frm_root_connect_string,
                                                    fg_color="transparent",
                                                    text='Connect String:')
        self.lbl_root_connect_string.grid(row=row, column=0, padx=(5, 10), pady=(5, 0), sticky='w')
        self.lbl_root_connect_string.grid_remove()
        row += 1

        self.lbl_root_connect_string_disp = ctk.CTkLabel(master=self.frm_root_connect_string,
                                                         fg_color="transparent",
                                                         text='')
        self.lbl_root_connect_string_disp.grid(row=row, column=0, padx=(30, 10), pady=(0, 5), sticky='w')
        row += 1

        self.lbl_root_client_tool = ctk.CTkLabel(master=self.frm_root_client_tool,
                                                 fg_color="transparent",
                                                 text='Client Tool:')
        self.lbl_root_client_tool.grid(row=row, column=0, padx=(5, 10), pady=(5, 0), sticky='w')
        self.lbl_root_client_tool.grid_remove()
        row += 1

        self.lbl_root_client_tool_disp = ctk.CTkLabel(master=self.frm_root_client_tool,
                                                      fg_color="transparent",
                                                      text='')
        self.lbl_root_client_tool_disp.grid(row=row, column=0, padx=(30, 10), pady=(0, 5), sticky='w')
        row += 1

        self.lbl_root_initial_dir = ctk.CTkLabel(master=self.frm_root_initial_dir,
                                                 fg_color="transparent",
                                                 text='Initial Directory:')
        self.lbl_root_initial_dir.grid(row=row, column=0, padx=(5, 10), pady=(5, 0), sticky='w')
        self.lbl_root_initial_dir.grid_remove()
        row += 1

        self.lbl_root_initial_dir_disp = ctk.CTkLabel(master=self.frm_root_initial_dir,
                                                      fg_color="transparent",
                                                      text='')
        self.lbl_root_initial_dir_disp.grid(row=row, column=0, padx=(30, 10), pady=(0, 5), sticky='w')
        row += 1

        # ===

        self.lbl_root_ssh_tunnel = ctk.CTkLabel(master=self.frm_root_ssh_tunnel,
                                                fg_color="transparent",
                                                text='SSH Tunnel:')
        self.lbl_root_ssh_tunnel.grid(row=row, column=0, padx=(5, 10), pady=(5, 0), sticky='w')
        self.lbl_root_ssh_tunnel.grid_remove()
        row += 1

        self.lbl_root_ssh_tunnel_disp = ctk.CTkLabel(master=self.frm_root_ssh_tunnel,
                                                     fg_color="transparent",
                                                     text='')
        self.lbl_root_ssh_tunnel_disp.grid(row=row, column=0, padx=(30, 10), pady=(0, 5), sticky='w')
        row += 1

        self.mvc_controller.display_connection_attributes()

    def tooltips_enabled(self):
        """The tooltips_enabled function gets the tooltips enabled status, from the DCCM controller."""
        return self.mvc_controller.enable_tooltips

    def maintain_connection(self, operation=None):
        default_padx = 5
        default_pady = 10

        self.maintain_operation = operation

        if operation == 'Modify':
            connection_identifier = self.opm_connections.get()
            connection_record = self.mvc_controller.selected_connection_record()
            connection_type = connection_record["connection_type"]
            wallet_required_yn = connection_record["wallet_required_yn"]
        else:
            connection_type = self.default_connection_type
            wallet_required_yn = 'Y'

        # Frames
        self.top_mod_connection = ctk.CTkToplevel(master=self)
        self.top_mod_connection.title(f'{operation} Connection')
        self.top_mod_connection.grid_rowconfigure(0, weight=1)
        self.top_mod_connection.grid_columnconfigure(2, weight=1)
        self.top_mod_connection.grid_columnconfigure(0, weight=0)
        self.mvc_controller.restore_geometry(window_category='toplevel')

        # This is our top widgets region, where we render the primary widgets,
        # oriented around connection and client type details
        self.frm_mod_connection_body = ctk.CTkFrame(master=self.top_mod_connection)
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

        self.frm_mod_buttons = ctk.CTkFrame(master=self.top_mod_connection)
        self.frm_mod_buttons.grid(row=10, column=0, padx=5, pady=5, columnspan=3, sticky='ew')

        # Widgets
        column = 0
        row = 0
        self.lbl_mod_connection_identifier = ctk.CTkLabel(master=self.frm_mod_conn_type,
                                                          text='Connection Id:', anchor='e')
        self.lbl_mod_connection_identifier.grid(row=row, column=column, padx=default_padx, pady=5, sticky='e')
        if self.tooltips_enabled():
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
                                                       values=self.mvc_controller.database_type_descriptors())
        self.opm_mod_database_type.grid(row=row, column=column, padx=default_padx, pady=default_pady, sticky='sw')

        column += 1
        lbl_mod_connection_type = ctk.CTkLabel(master=self.frm_mod_conn_type, text='Management Type:', anchor='e')
        lbl_mod_connection_type.grid(row=row, column=column, padx=(25, 5), pady=default_pady, sticky='e')

        column += 1
        self.mvc_controller.valid_connection_types = self.mvc_controller.connection_type_list()
        if self.tooltips_enabled():
            self.connection_type_tooltip = ToolTip(lbl_mod_connection_type,
                                                   'Select a password management type. The "OCI Vault" management type '
                                                   'relies on OCI Vault being configured and the use of secrets '
                                                   'OCIDs to retrieve passwords from the OCI vault. "Legacy" '
                                                   'management type, causes the password to be encrypted and '
                                                   'stored locally.', TOOLTIP_DELAY)

        self.opm_mod_connection_type = ctk.CTkOptionMenu(master=self.frm_mod_conn_type,
                                                         command=self.mvc_controller.toggle_mod_cloud_widgets,
                                                         values=self.mvc_controller.connection_type_descriptors())
        self.opm_mod_connection_type.grid(row=row, column=column, padx=default_padx, pady=default_pady, sticky='sw')
        self.opm_mod_connection_type.set(connection_type)

        self.tk_mod_wallet_required = ctk.StringVar(master=self.frm_mod_tns_properties, value=wallet_required_yn)
        self.swt_mod_wallet_required = ctk.CTkSwitch(master=self.frm_mod_tns_properties,
                                                     text='Wallet Required',
                                                     variable=self.tk_mod_wallet_required,
                                                     onvalue='Y',
                                                     offvalue='N',
                                                     command=self.mvc_controller.toggle_mod_wallet_display)

        self.swt_mod_wallet_required.grid(row=row, column=column, padx=default_padx, pady=default_pady, sticky='w')
        if self.tooltips_enabled():
            self.wallet_required_tooltip = ToolTip(self.swt_mod_wallet_required,
                                                   'Wallets are required for Cloud database connections.',
                                                   TOOLTIP_DELAY)

        column = 0
        row += 1
        self.lbl_mod_wallet_location = ctk.CTkLabel(master=self.frm_mod_tns_properties, text='Select Wallet:',
                                                    anchor='e')
        self.lbl_mod_wallet_location.grid(row=row, column=column, padx=default_padx, pady=(5, 0), sticky='e')
        if self.tooltips_enabled():
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
                                                     command=self.mvc_controller.ask_wallet_location)
        self.btn_mod_wallet_location.grid(row=row, column=column, padx=0, pady=(10, 5), sticky='sw')
        # self.btn_mod_wallet_location.place(x=100, y=-100)

        column += 1

        self.lbl_mod_connect_string = ctk.CTkLabel(master=self.frm_mod_tns_properties, text='Connect String:',
                                                   anchor='e')
        self.lbl_mod_connect_string.grid(row=row, column=column, padx=0, pady=(5, 0), sticky='w')
        if self.tooltips_enabled():
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
        if self.tooltips_enabled():
            self.lbl_mod_client_tool_tooltip = ToolTip(lbl_mod_client_tool,
                                                       'Select the required client tool to use when connecting to the '
                                                       'database. You can add new clients (other than the SQLcl), '
                                                       'via the Tools/Client Tools menu option.',
                                                       TOOLTIP_DELAY)
        column += 1

        # TODO: Cater for non SQLcl command selection
        self.opm_mod_client_tool = ctk.CTkOptionMenu(master=self.frm_mod_conn_type,
                                                     command=self.mvc_controller.set_client_options_state,
                                                     values=self.mvc_controller.client_tools_name_list)
        self.opm_mod_client_tool.grid(row=row, column=column, padx=default_padx, pady=default_pady, sticky='w')

        if 'SQLcl' in self.mvc_controller.client_tools_name_list:
            self.opm_mod_client_tool.set('SQLcl')
        if self.tooltips_enabled():
            lbl_theme_tooltip = ToolTip(self.opm_mod_client_tool,
                                        f"The client tool which you wish to launch, when launching this "
                                        f"connection.",
                                        TOOLTIP_DELAY)
        column += 1

        self.lbl_mod_client_tool_options = ctk.CTkLabel(master=self.frm_mod_conn_type,
                                                        text='SQLcl Options:', anchor='e')
        self.lbl_mod_client_tool_options.grid(row=row, column=column, padx=default_padx, pady=default_pady, sticky='e')

        if self.tooltips_enabled():
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

        btn_mod_delete = ctk.CTkButton(master=self.frm_mod_buttons, command=self.mvc_controller.test_connection,
                                       text='Test Connection', width=button_width)
        btn_mod_delete.grid(row=0, column=1, padx=180, pady=(10, 10), sticky='s')

        btn_mod_save = ctk.CTkButton(master=self.frm_mod_buttons, command=self.mvc_controller.modify_connection,
                                     text='Save', width=button_width)
        btn_mod_save.grid(row=0, column=2, padx=15, pady=(10, 10), sticky='s')

        self.render_connection_widgets()
        home_directory = expanduser("~")
        self.lbl_mod_disp_launch_directory.configure(text=home_directory)

        self.mvc_controller.toggle_mod_wallet_display()

        self.mod_status_bar = cbtk.CBtkStatusBar(master=self.top_mod_connection)

        self.top_mod_connection.grab_set()

    def db_account_caps(self, event):
        """The db_account_caps function, is a callback function, used to convert the database account name to 
        uppercase, as the user types in the name."""
        self.tk_mod_db_account_name.set(self.tk_mod_db_account_name.get().upper())

    def on_close_connections_maintenance(self):
        """The on_close_connections_maintenance method, tidies up when we close the connections maintenance dialog."""
        self.mvc_controller.save_geometry(window_category='toplevel')
        mod.purge_temp_tns_admin()
        self.top_mod_connection.destroy()
        self.deiconify()

    def on_close(self):
        """The on_close method, tidies up when we close the application."""
        self.mvc_controller.save_geometry(window_category='root')
        self.destroy()

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
        if self.tooltips_enabled():
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
        if self.tooltips_enabled():
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
        if self.tooltips_enabled():
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
        if self.tooltips_enabled():
            self.lbl_mod_oci_profile_tooltip = ToolTip(self.lbl_mod_oci_profile,
                                                       'The OCI profile (from the OCI config file) to '
                                                       'use when connecting to the OCI Vault. Note that '
                                                       'you need to set up public/private keys for the '
                                                       'vault access.',
                                                       TOOLTIP_DELAY)
        column += 1

        self.cmo_mod_oci_profile = ctk.CTkComboBox(master=self.frm_mod_tns_properties,
                                                   values=self.mvc_controller.oci_config_profiles_list())
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
        if self.tooltips_enabled():
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
                                    size=(30, 30))
        self.btn_mod_launch_directory = ctk.CTkButton(master=self.frm_mod_gui_session,
                                                      text='',
                                                      bg_color="transparent",
                                                      fg_color="transparent",
                                                      width=40,
                                                      height=20,
                                                      command=self.mvc_controller.ask_client_launch_directory,
                                                      image=folder_image
                                                      )
        self.btn_mod_launch_directory.grid(row=row, column=0, padx=(120, 0), pady=0, sticky='w')
        if self.tooltips_enabled():
            opm_app_theme_tooltip = ToolTip(self.btn_mod_launch_directory,
                                            f"Set the default cloud wallet location.",
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
        if self.tooltips_enabled():
            lbl_theme_tooltip = ToolTip(self.lbl_mod_connection_banner,
                                        f"Select a banner type, to be displayed when launching the client tool in "
                                        f"command line mode.",
                                        TOOLTIP_DELAY)

        # TODO: Hook up the next 3 widgets with the controller

        column += 1
        banner_values = self.mvc_controller.banner_options()
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
        if self.tooltips_enabled():
            lbl_theme_tooltip = ToolTip(self.lbl_mod_connection_text_colour,
                                        'Select a colour for the connection message.',
                                        TOOLTIP_DELAY)

        column += 1
        colour_values = self.mvc_controller.banner_colours()
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
        if self.tooltips_enabled():
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
                                                            command=self.mvc_controller.toggle_mod_tunnel_widgets)
        if self.tooltips_enabled():
            opm_app_theme_tooltip = ToolTip(self.swt_mod_ssh_tunnel_required_yn,
                                            f"Enable, if SSH is required for this connection.",
                                            TOOLTIP_DELAY)
        self.swt_mod_ssh_tunnel_required_yn.grid(row=row, column=column, padx=(10, 5), pady=default_pady,
                                                 sticky='w')
        column += 1

        self.lbl_mod_tunnel_templates = ctk.CTkLabel(master=self.frm_mod_ssh_settings,
                                                     text='Select Tunnel:', anchor='e')
        self.lbl_mod_tunnel_templates.grid(row=row, column=column, padx=default_padx, pady=default_pady, sticky='w')
        if self.tooltips_enabled():
            lbl_theme_tooltip = ToolTip(self.lbl_mod_tunnel_templates,
                                        f"Select the SSH tunnelling entry, required for this connection.",
                                        TOOLTIP_DELAY)
        column += 1
        ssh_templates = mod.preferences_scope_names(db_file_path=db_file, scope='ssh_templates')
        self.opm_mod_tunnel_code = ctk.CTkOptionMenu(master=self.frm_mod_ssh_settings,
                                                     values=ssh_templates,
                                                     command=self.mvc_controller.toggle_mod_ssh_port,
                                                     width=150)
        self.opm_mod_tunnel_code.grid(row=row, column=column, padx=(5, 5), pady=default_pady)

        column += 1
        self.lbl_mod_listener_port = ctk.CTkLabel(master=self.frm_mod_ssh_settings,
                                                  text='Listener Port:',
                                                  anchor='e')
        self.lbl_mod_listener_port.grid(row=row, column=column, padx=(5, 5), pady=default_pady, sticky='w')
        if self.tooltips_enabled():
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

    def toggle_password_display(self, event=None):
        if self.password_hidden:
            self.password_hidden = False
            self.ent_mod_ocid.configure(show="")
        else:
            self.password_hidden = True
            self.ent_mod_ocid.configure(show="*")

    def update_opm_connections(self, connection_identifiers_list: list):
        """The update_opm_connections function, updates the connections' widget, under instruction of the controller
        class, following the addition/deletion of connection entries."""
        self.opm_connections.configure(values=connection_identifiers_list)

    def show_vault_mod_widgets(self):
        self.lbl_mod_oci_profile.configure(state=tk.NORMAL)
        self.cmo_mod_oci_profile.configure(state=tk.NORMAL)
        self.tk_mod_wallet_required.set('Y')
        # self.swt_mod_wallet_required.grid_remove()

    def hide_vault_mod_widgets(self):
        self.lbl_mod_oci_profile.configure(state=tk.DISABLED)
        self.cmo_mod_oci_profile.configure(state=tk.DISABLED)
        self.ent_mod_ocid.configure(placeholder_text='Password')
        self.swt_mod_wallet_required.grid()

    def launch_in_gui_mode(self):
        self.title("DB Client Connection Manager")
        self.render_root_window_contents()


if __name__ == "__main__":
    pass
