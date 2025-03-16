import os
import glob
import subprocess
import getpass
import cairosvg
import pathlib
from typing import Self
import abc
import shutil
class FormError(Exception): pass


class IDialogManager(abc.ABC):
    @abc.abstractmethod
    def get_file(self, filters: tuple[tuple[str, ...]], root_dir: str) -> str:
        """
        Spawns a dialog that prompts a file
        :returns: the absolute path of that file
        :param filters: filters file extensions. The first string of each tuple is the title of
         the category while the others ones are the filters.
         ex: (("Images", "*.png", "*.jpg", "*.jpeg"), ("All files", "*"))
        :param root_dir: Absolute path to the directory where the dialog will open
        """
    @abc.abstractmethod
    def showinfo(self, title: str, message: str) -> None:
        """
        Spawns a subwindow similar to tkinter.messagebox.showinfo
        :param title: title of the message
        :param  message: message of the window
        """
    def showwarning(self, title: str, message: str) -> None:
        """
        Spawns a subwindow similar to tkinter.messagebox.showwarning
        :param title: title of the message
        :param  message: message of the window
        """
    def showerror(self, title: str, message: str) -> None:
        """
        Spawns a subwindow similar to tkinter.messagebox.showerror
        :param title: title of the message
        :param  message: message of the window
        """


class CinnamonDialogManager(IDialogManager):
    __instance: Self | None = None
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance
    
    def get_file(self, filters: tuple[tuple[str, ...]] = (), root_dir: str = "~") -> str:
        args: list[str] = ["zenity", "--file-selection"]
        for pattern in filters:
            args.append(f"--file-filter={pattern[0] + ' | ' + ' '.join(pattern[1::])}")
        return subprocess.run(
            args,
            capture_output=True, 
            text=True
            ).stdout[:-1]
    
    def showinfo(self, title: str = "information", message: str = "showinfo") -> None:
        subprocess.run(["zenity", "--info", f"--text={message}"])

    def showwarning(self, title: str = "warning", message: str = "warning") -> None:
        subprocess.run(["zenity", "--warning", f"--text={message}"])

    def showerror(self, title: str = "error", message: str = "error message") -> None:
        subprocess.run(["zenity", "--error", f"--text={message}"])



class Model:
    def __init__(self):
        self._name: str = ""
        self._executable: str = ""
        self._icon: str = ""
        self._cateogry: str = ""
        icon_theme: str = subprocess.run("gsettings get org.cinnamon.desktop.interface icon-theme", shell=True, capture_output=True, text=True).stdout[1:-2]
        self._icon_dict: dict[str, str] = {}
        self._icon_cache: dict[str, list[tuple[str, str]]] = {"":[]}

        for path in glob.iglob("**/*.[ps][nv]g", recursive=True, root_dir=f"/usr/share/icons/{icon_theme}/apps"):
            if os.path.isfile(f"/usr/share/icons/{icon_theme}/apps/" + path):
                self._icon_dict[os.path.split(path)[1][:-4]] = f"/usr/share/icons/{icon_theme}/apps/" + path

        for path in glob.iglob("*.[ps][nv]g", root_dir=f"/home/{getpass.getuser()}/.icons"):
            if os.path.isfile(f"/home/{getpass.getuser()}/.icons/{path}"):
                self._icon_dict[os.path.split(path)[1][:-4]] = f"/home/{getpass.getuser()}/.icons/{path}"

        for path in glob.iglob("**/*.[ps][nv]g", recursive=True, root_dir="/usr/share/pixmaps"):
            if os.path.isfile("/usr/share/pixmaps/" + path):
                self._icon_dict[os.path.split(path)[1][:-4]] = f"/usr/share/pixmaps/{path}"



    def set_executable(self, file: str) -> bool:
        if os.path.isfile(file):
            if os.access(file, os.X_OK):
                self._executable = file
            elif file.endswith("jar"):
                self._executable = f"java -jar {file}"
            elif file.endswith("py"):
                self._executable = f"python {file}"
            else:
                print(f"ERROR: '{file}' is not a valid file")
            return True
        print(f"ERROR: '{file}' is not a file")
        return False

    def get_name(self) -> str:
        return self._name

    def set_name(self, name: str):
        self._name = name
        return True

    def start(self) -> bool:
        """
        Starts the process of installing the app.
        Raises FormError if the given data is invalid
        May raise a subprocess.CalledProcessError if the implementation uses subprocess
        returns True if the installation was successful otherwise returns False
        """
        if not self._name:
            raise FormError("the name is invalid")
        if not self._executable:
            raise FormError("the executable file is invalid")
        print(self._name, self._executable, self._icon)
        subprocess.run(
            f"""~/bin/makelauncher "{self._name}" "{self._executable}" "{self._icon}" "{self._cateogry}\"""", 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=True
            ).check_returncode()
        return True


    def search_icon(self, name: str) -> list[tuple[str, str]]:
        if name not in self._icon_cache:
            self._icon_cache[name] = [(k,v) for k,v in self._icon_dict.items() if k.startswith(name)]
        return self._icon_cache[name]
    
    def set_icon(self, value: str):
        if value in self._icon_dict:
            self._icon = value
            return True
        return False
    
    def add_icon(self, file: str) -> bool:
        if not file.endswith(("png", "svg")):
            return False
        
        shutil.copyfile(file, pathlib.Path(f"~/.icons/{os.path.split(file[1])}").expanduser())
        for path in glob.iglob("*.[ps][nv]g", root_dir=f"/home/{getpass.getuser()}/.icons"):
            if os.path.isfile(f"/home/{getpass.getuser()}/.icons/{path}"):
                self._icon_dict[os.path.split(path)[1][:-4]] = f"/home/{getpass.getuser()}/.icons/{path}"
        return True
        

    def get_png(self, absolute_path: str) -> str:
        if not absolute_path.endswith("svg"):
            return absolute_path
        
        if not os.path.isdir('/tmp/installer_script'):
            os.makedirs('/tmp/installer_script')

        new_path = "/tmp/installer_script/" + absolute_path.replace('/', '\\').removesuffix("svg") + "png"
        if not os.path.exists(new_path):
            cairosvg.svg2png(url=absolute_path, write_to=new_path)
        
        return new_path
    
    def get_categories(self) -> list[str]:
        return ["Accesories", "Education", "Games", "Graphics", "Internet", "Office", "Other", "Programming", "SoundVideo", "Administration", "Preferences"]
    
    def add_category(self, value: str) -> bool:
        if (value in self.get_categories()) and (value not in self._cateogry.split(';')):
            self._cateogry += value + ";"
            return True
        return False
    
    def get_category(self) -> str:
        return self._cateogry

if __name__ == "__main__":
    pass
