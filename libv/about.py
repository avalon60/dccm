"""Class container for the About application class."""

import customtkinter as ctk
import libm.dccm_m as mod
from PIL import Image
import lib.cbtk_kit as cbtk

__title__ = mod.__title__
__author__ = mod.__author__
__version__ = mod.__version__

images_location = mod.images_location
app_themes_dir = mod.themes_location
class About(ctk.CTkToplevel):
    def __init__(self, controller, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.controller = controller
        self.enable_tooltips = False

        widget_corner_radius = 5
        ABOUT_WIDTH = 400
        ABOUT_HEIGHT = 284
        position_geometry = controller.retrieve_geometry(window_name='about')
        self.title('CTk Theme Builder')
        self.geometry(position_geometry)
        self.geometry(f'{ABOUT_WIDTH}x{ABOUT_HEIGHT}')

        # Make preferences dialog modal
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)

        frm_about_main = ctk.CTkFrame(master=self, corner_radius=widget_corner_radius, border_width=0)
        frm_about_main.grid(column=0, row=0, sticky='nsew')
        frm_about_main.columnconfigure(1, weight=1)
        frm_about_main.rowconfigure(0, weight=1)
        frm_about_main.rowconfigure(1, weight=0)

        frm_widgets = ctk.CTkFrame(master=frm_about_main, corner_radius=widget_corner_radius, border_width=0)
        frm_widgets.grid(column=0, row=0, padx=10, pady=10, sticky='nsew')

        frm_about_logo = ctk.CTkFrame(master=frm_about_main, corner_radius=widget_corner_radius,
                                      fg_color="transparent", border_width=0)
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
                                      border_width=0,
                                      bg_color="transparent",
                                      fg_color="transparent",
                                      image=dccm_icon
                                      )
        btn_dccm_icon.grid(row=1, column=0, sticky='ew')

        lbl_version = ctk.CTkLabel(master=frm_widgets, text=f'Version: {__version__}')
        lbl_version.grid(row=2, column=0, sticky='ew')

        lbl_ctk_version = ctk.CTkLabel(master=frm_widgets, text=f'CustomTkinter: {ctk.__version__}')
        lbl_ctk_version.grid(row=3, column=0, sticky='ew')

        lbl_author = ctk.CTkLabel(master=frm_widgets, text=f'Author: {__author__}')
        lbl_author.grid(row=4, column=0, padx=(10, 10), sticky='ew')

        lbl_logo = ctk.CTkLabel(master=frm_widgets, text=f'Logo: Jan Bajec')
        lbl_logo.grid(row=5, column=0, padx=(10, 10), sticky='ew')

        logo_image = ctk.CTkImage(light_image=Image.open(images_location / 'bear-logo-colour.jpg'),
                                  dark_image=Image.open(images_location / 'bear-logo-colour.jpg'),
                                  size=(210, 210))

        # Hide the button hover, by using the frame fg_color, for hover_color
        button_hover_color = cbtk.get_color_from_name(widget_type='CTkFrame', widget_property='fg_color')
        btn_logo = ctk.CTkButton(master=frm_about_logo, text='', height=50, width=50,
                                 corner_radius=widget_corner_radius,
                                 bg_color="transparent",
                                 fg_color="transparent",
                                 hover_color=button_hover_color,
                                 border_color=None,
                                 border_width=0,
                                 image=logo_image)
        btn_logo.grid(row=0, column=1, sticky='ew')

        frm_buttons = ctk.CTkFrame(master=frm_about_main, corner_radius=widget_corner_radius, border_width=0)
        frm_buttons.grid(column=0, row=1, padx=(5, 5), pady=(0, 0), sticky='ew', columnspan=2)

        btn_ok = ctk.CTkButton(master=frm_buttons, text='OK', width=ABOUT_WIDTH - 20,
                               corner_radius=widget_corner_radius,
                               command=self.close_dialog)
        btn_ok.grid(row=0, column=0, padx=(5, 5), pady=10)

        self.grab_set()

    def close_dialog(self):
        geometry = self.geometry()
        self.controller.save_geometry(window_name='about', geometry=geometry)
        self.destroy()

