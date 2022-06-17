from kivy.app import App
from kivy.graphics import Rectangle, Color
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.settings import Settings
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.uix.recycleview import RecycleView
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.lang import Builder
from kivy.config import ConfigParser, Config

from src.Mod import ModFolder
from src.finder import search_subdirectories
from src.help.fighter_names.util import c2f
from src.utils import tabbed_join

config = ConfigParser()
config.add_section("custom")
config.set("custom", "mod_dirs0", "")
config.set("custom", "mod_dirs1", "")
config.set("custom", "mod_dirs2", "")
config.set("custom", "mod_dirs3", "")
config.set("custom", "mod_dirs4", "")
config.write()


# Designate Our .kv design file
Builder.load_file('gui/layout.kv')


class SettingsTab(Settings):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.add_json_panel('Mod Folders', config, 'gui/config.json')



class ModButton(Button):
    def __init__(self, info_zone, mod, **kwargs):
        super().__init__(**kwargs)
        self.info_zone = info_zone
        self.mod: ModFolder = mod

    def load_info(self):
        self.info_zone.title.text = self.mod.name
        self.info_zone.chars.text = ", ".join(self.mod.get_all_fighters())
        self.info_zone.link.text = self.mod.metadata["url"]
        self.info_zone.image.source = self.mod.get_img()
        txt = ""
        for mod in self.mod.mods:
            print(mod.info)
            fighters = mod.fighter.codes
            for c in fighters:
                txt += f"\n{c2f[c]} - {mod.name}\n"
                if c in mod.info:
                    for s in mod.info[c]:
                        txt += f"      {s}\n"
                        for typ in mod.info[c][s]:
                            txt += f"            {typ}\n"
                            txt += f"{tabbed_join(mod.info[c][s][typ], 3)}\n"
        skins: ScrollView = self.info_zone.skins
        skins.clear_widgets()
        lbl = Label(text=txt, size_hint_y=None, size_hint_x=1, halign="left", padding=(50, 50))
        lbl.texture_update()
        lbl.size = lbl.texture_size
        lbl.text_size = (skins.width, lbl.texture_size[1])
        skins.add_widget(lbl)






class Main(TabbedPanel):

    mod_list: GridLayout = ObjectProperty(None)
    info_box: BoxLayout = ObjectProperty(None)
    mod_folders = []

    def add_mod(self):
        self.mod_list.add_widget(ModButton(self.info_box))

    def load_mods(self):
        self.mod_list.clear_widgets()
        for path in [config.get("custom", f"mod_dirs{i}") for i in range(5)]:
            if path:
                self.mod_folders += search_subdirectories(path)
        for mod in self.mod_folders:
            self.mod_list.add_widget(ModButton(text=mod.name, info_zone=self.info_box, mod=mod))





class MainApp(App):
    def build(self):
        m = Main()
        return m



def main():
    MainApp().run()



if __name__ == '__main__':
    main()
