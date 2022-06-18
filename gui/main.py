from kivy.app import App
from kivy.graphics import Rectangle, Color
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
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
from src.help.fighter_names.util import c2f, n2cs
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
        self.info_zone.chars.text = ", ".join(self.mod.fighters)
        self.info_zone.link.text = f"[ref={self.mod.metadata['url']}]{self.mod.metadata['url']}[/ref]"
        self.info_zone.image.source = self.mod.get_img()
        txt = ""
        for mod in self.mod.mods:
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


class FighterDropDown(Button):
    max_width = 0
    dropdown = None
    main = ObjectProperty(None)
    search = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = "Choose your Fighter"
        self.padding_x = 10
        self.size_hint_x = None
        self.dropdown = DropDown()
        btn = Button(text="All", size_hint_y=None, size_hint_x=1, height=30, padding=(10, 10))
        btn.bind(on_release=lambda b: (self.dropdown.select(b.text), self.main.search(self.search.text)))
        self.dropdown.add_widget(btn)
        for char_name in sorted(list(n2cs.keys())):
            btn = Button(text=char_name, size_hint_y=None, size_hint_x=1, height=30, padding=(10, 10))
            btn.bind(on_release=lambda b: (self.dropdown.select(b.text), self.main.search(self.search.text)))
            self.dropdown.add_widget(btn)
        for btn in self.dropdown.children[0].children + [self]:
            btn.texture_update()
            self.max_width = max(btn.texture_size[0], self.max_width)
        self.width = self.max_width
        self.texture_update()
        self.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=lambda instance, x: setattr(self, 'text', x))


class Main(TabbedPanel):

    mod_list: GridLayout = ObjectProperty(None)
    info_box: BoxLayout = ObjectProperty(None)
    dropdown: Button = ObjectProperty(None)
    mod_folders = []

    def load_mods(self):
        self.mod_list.clear_widgets()
        for path in [config.get("custom", f"mod_dirs{i}") for i in range(5)]:
            if path:
                self.mod_folders += search_subdirectories(path)
        for mod in self.mod_folders:
            self.mod_list.add_widget(ModButton(text=mod.name, info_zone=self.info_box, mod=mod))

    def search(self, string):
        if string == "Search...":
            string = ""
        fighter = self.dropdown.text
        for m in self.mod_list.children:
            if type(m) != ModButton:
                continue
            if string.lower() in m.text.lower() and (fighter == "All" or any(f in m.mod.codes for f in n2cs[fighter])):
                m.opacity = 1
                m.disable = False
                m.height = m.texture_size[1]
            else:
                m.opacity = 0
                m.disable = True
                m.height = 0





class MainApp(App):
    def build(self):
        m = Main()
        return m



def main():
    MainApp().run()



if __name__ == '__main__':
    main()
