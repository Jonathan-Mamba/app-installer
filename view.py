import customtkinter as ctk
from typing import Callable, Self
from model import Model, FormError, CinnamonDialogManager
from PIL import Image
import subprocess
import os









class Colors:
    blue: str = "#1F6AA5"
    gray0: str = "gray5"
    gray1: str = "gray10"
    gray2: str = "gray15"
    gray3: str = "gray25"
    gray4: str = "gray35"
    gray5: str = "gray50"
    white: str = "white"






class EntryButtonFrame(ctk.CTkFrame):
    def __init__(self, master, width = 160, height = 20, corner_radius = None, border_width = 2, bg_color = "transparent", fg_color = "gray25", border_color = "gray50", background_corner_colors = None,
                  entry_placeholder: str = "", button_text: str = "", button_callback: Callable[..., None] = None,  **kwargs):
        
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color, border_color, background_corner_colors, None, **kwargs)
        
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)

        self.entry = ctk.CTkEntry(self, width=2/3*width-4, height=height-4,
                                  fg_color=Colors.gray3, 
                                  border_color=Colors.gray3, 
                                  placeholder_text=entry_placeholder,
                                  placeholder_text_color=Colors.gray5,
                                  text_color="white"
                                  )
        self.button = ctk.CTkButton(self, width=1/3*width-4, height=height-4, 
                                    text=button_text, 
                                    fg_color=Colors.gray2, 
                                    text_color=Colors.white, 
                                    border_color=Colors.gray3,
                                    hover_color=Colors.gray0,
                                    command=button_callback,
                                    corner_radius=0
                                    )
        self.entry.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=(2, 2))
        self.button.pack(side="right", padx=(0, 3), pady=(1, 0))
        
        
        on_focus = lambda x: self.configure(True, border_color=Colors.blue)
        on_leave = lambda x: self.configure(True, border_color=Colors.gray5)
        self.bind("<Enter>", on_focus)
        self.bind("<Leave>", on_leave)
        self.entry.bind("<Enter>", on_focus)
        self.entry.bind("<Leave>", on_leave)
        self.button.bind("<Enter>", on_focus)
        self.button.bind("<Leave>", on_leave)






class SearchResult(ctk.CTkFrame):
    image_cache: dict[str, Image.Image] = {}
    def __init__(self, master, width = 200, height = 200, corner_radius = None, border_width = None, bg_color = "transparent", fg_color = None, border_color = None, background_corner_colors = None, overwrite_preferred_drawing_method = None,
                    image_path: str = "", result_name: str = "", image_size: tuple[int, int] = (20, 20), hover_color: str | tuple[str, str] = None, callback: Callable[[str], None] = None, **kwargs):
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color, border_color, background_corner_colors, overwrite_preferred_drawing_method, **kwargs)


        image = SearchResult.image_cache.get(image_path, Image.open(image_path))
        self.name = result_name
        self.image = ctk.CTkImage(light_image=image, dark_image=image, size=image_size)
        self.image_label = ctk.CTkLabel(self, image=self.image, fg_color=fg_color, text="", height=height-4, corner_radius=corner_radius)
        self.label = ctk.CTkLabel(self, fg_color=fg_color, text_color="white", text=result_name, height=height-4, corner_radius=corner_radius)
        
        self.image_label.grid(row=0, padx=(8, 0), pady=(2, 3))
        self.label.grid(row=0, column=1, padx=(0, 8), pady=(2, 3))
        
        def on_focus(*_):
            self.label.configure(False, fg_color=hover_color)
            self.image_label.configure(False, fg_color=hover_color)
            self.configure(True, border_color=Colors.blue, fg_color=hover_color)
        def on_leave(*_):
            self.label.configure(False, fg_color=fg_color)
            self.image_label.configure(False, fg_color=fg_color)
            self.configure(True, border_color=Colors.gray5, fg_color=fg_color)
        self.bind("<Enter>", on_focus)
        self.bind("<Leave>", on_leave)
        self.bind("<Button-1>", lambda x: callback(result_name))
        self.label.bind("<Enter>", on_focus)
        self.label.bind("<Leave>", on_leave)
        self.label.bind("<Button-1>", lambda x: callback(result_name))
        self.image_label.bind("<Enter>", on_focus)
        self.image_label.bind("<Leave>", on_leave)
        self.image_label.bind("<Button-1>", lambda x: callback(result_name))

class IconTopLevel(ctk.CTkToplevel):    
    def __init__(self, model: Model, *args, fg_color = Colors.gray2, callback: Callable[[str], None] = lambda x:x, **kwargs):
        super().__init__(*args, fg_color=fg_color, **kwargs)

        self.geometry("250x320")
        self.resizable(True, False)
        self.model = model
        self.wm_title("Icon Browser")
        self.columnconfigure(0, weight=1)
        self.callback: Callable[[str], None] = lambda x: (callback(x), self.destroy())[0]

        self.search_bar = EntryButtonFrame(self, width=180, height=20, border_color=Colors.gray5, entry_placeholder="discord", button_text="Add", button_callback=lambda *_:self.add_icon())
        self.result_frame = ctk.CTkScrollableFrame(self,
                                                     width=180,
                                                     border_width=2,
                                                     fg_color=Colors.gray3,
                                                     border_color=Colors.gray5,
                                                     label_fg_color=Colors.gray1,
                                                     label_text="0 results ",
                                                     label_text_color="white",
                                                     label_font=ctk.CTkFont(size=15, slant='italic')
                                                     )
        self.search_bar.entry.bind("<KeyRelease>", self.reconstruct_frame)
        self.search_bar.grid(pady=10)
        self.result_frame.grid(row=1, padx=25, sticky="nswe", pady=(0, 10))

    def add_icon(self):
        file = CinnamonDialogManager().get_file(filters=(("Image (*.png, *.svg)", "*.png", "*.svg"),))
        self.model.add_icon(file)
        self.reconstruct_frame()

    def reconstruct_frame(self, event=None): 
        search_result = self.model.search_icon(self.search_bar.entry.get())
        self.result_frame.configure(label_text=f"{len(search_result)} results ")
        
        for widget in self.result_frame.children.values():
            widget.pack_forget()
        self.result_frame.children.clear()

        for name, path in search_result:
            SearchResult(self.result_frame,
                        width=160,
                        height=20,
                        corner_radius=10,
                        border_width=2,
                        fg_color=Colors.gray2,
                        border_color=Colors.gray5,
                        hover_color=Colors.gray1,
                        image_path=self.model.get_png(path),
                        result_name=name,
                        image_size=(32, 32),
                        callback=self.callback
                        ).pack(pady=(5, 0), anchor="w", expand=True)
        





class App(ctk.CTk):
    def __init__(self, model: Model):
        super().__init__(fg_color="gray15")
        self.title("App installer")
        self.geometry("300x300")
        self.resizable(False, False)
        self.model = model

        self.grid_columnconfigure(0, weight=1)
        # variables
        self.category_var = ctk.StringVar(value="Categories:")

        # labels
        self.title_label = ctk.CTkLabel(self, text="App installer", fg_color="gray20", corner_radius=10, text_color="white", height=22, font=("Arial", 20))
        self.error_label = ctk.CTkLabel(self, text="", text_color="#f01a1a", font=ctk.CTkFont(slant='italic'))

        # forms
        self.name_entry = ctk.CTkEntry(self, 
                                    width=220, 
                                    height=30,
                                    placeholder_text="discord",
                                    placeholder_text_color=Colors.gray5,
                                    fg_color=Colors.gray3,
                                    border_color=Colors.gray5,
                                    text_color="white"
                                    )
        self.executable_frame = EntryButtonFrame(self, 
                                                width=220, 
                                                height=20, 
                                                border_color=Colors.gray5, 
                                                border_width=2, 
                                                button_text="Browse...", 
                                                entry_placeholder="$HOME/discord.exe", 
                                                button_callback=self.exe_button_callback
                                                )
        self.icon_frame = EntryButtonFrame(self, 
                                          width=220, 
                                          height=20, 
                                          border_color=Colors.gray5, 
                                          border_width=2, 
                                          button_text="Browse...", 
                                          entry_placeholder="discord_icon.png", 
                                          corner_radius=5, 
                                          button_callback=lambda: IconTopLevel(self.model, self, callback=self.icon_browser_callback)
                                          )
        self.category_frame = ctk.CTkFrame(self, border_color=Colors.gray5, border_width=2, fg_color=Colors.gray3, corner_radius=5)
        self.category_widget = ctk.CTkOptionMenu(self.category_frame,
                                               width=214,
                                               height=22,
                                               fg_color=Colors.gray3,
                                               values=self.model.get_categories(),
                                               variable=self.category_var,
                                               corner_radius=5,
                                               button_color=Colors.gray2,
                                               button_hover_color=Colors.gray0,
                                               command=self.category_callback,
                                               dropdown_fg_color=Colors.gray3,
                                               dropdown_text_color="white",
                                               dropdown_hover_color=Colors.gray2
                                               )


        #button
        self.start_button = ctk.CTkButton(self, text="Install", text_color="white", corner_radius=10, height=20, command=self.install)

        # grid
        self.title_label.grid(row=0, pady=20, padx=7, sticky="we")
        self.name_entry.grid(row=1, pady=(5, 10))
        self.executable_frame.grid(row=2, pady=(0, 10))
        self.icon_frame.grid(row=3, pady=(0, 10))
        self.category_widget.grid(padx=3, pady=3)
        self.category_frame.grid(row=4, pady=(0, 25))
        self.start_button.grid(row=5, sticky="we", padx=25)
        self.error_label.grid(row=6)

        self.__bind()

    def __bind(self):
        self.name_entry.bind("<Enter>", lambda x: self.name_entry.configure(True, border_color=Colors.blue))
        self.name_entry.bind("<Leave>", lambda x: self.name_entry.configure(True, border_color=Colors.gray5))
        self.name_entry.bind("<KeyRelease>", lambda x: self.model.set_name(self.name_entry.get()))
        self.category_frame.bind("<Enter>", lambda x: self.category_frame.configure(True, border_color=Colors.blue))
        self.category_frame.bind("<Leave>", lambda x: self.category_frame.configure(True, border_color=Colors.gray5))
        self.category_widget.bind("<Enter>", lambda x: self.category_frame.configure(True, border_color=Colors.blue))
        self.category_widget.bind("<Leave>", lambda x: self.category_frame.configure(True, border_color=Colors.gray5))

    def category_callback(self, category: str):
        self.model.add_category(category)
        self.category_var.set(self.model.get_category())
    
    def exe_button_callback(self):
        file = CinnamonDialogManager().get_file(filters=(
            ("Executables (*.exe, *.sh, *.zsh, *.jar, *.py)", '*.exe', '*.sh', '*.zsh', '*.jar', '*.py'),
            ("All files", '*')
        ))
        if self.model.set_executable(file):
            self.executable_frame.entry.delete(0, 'end')
            self.executable_frame.entry.insert(0, file)

    def icon_browser_callback(self, icon_name: str):
        if self.model.set_icon(icon_name):
            self.icon_frame.entry.delete(0, 'end')
            self.icon_frame.entry.insert(0, icon_name)

    def install(self):
        success: bool = False
        try:
            success = self.model.start()
        except FormError as e:
            self.error_label.configure(text=e, text_color="#f01a1a")
        except subprocess.CalledProcessError as e:
            self.error_label.configure(text=f"Installation error ({e.returncode}): {e.stderr} ", text_color="#f01a1a")
        else:
            if success:
                self.error_label.configure(text=f"{self.model.get_name()} was installed sucessfully!", text_color="green")

