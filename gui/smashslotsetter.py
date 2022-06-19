import json
import os.path
import webbrowser
import logging
from logging import log as py_log
import sys
from datetime import datetime
import traceback

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.settings import Settings
from kivy.properties import ObjectProperty
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.lang import Builder
from kivy.config import ConfigParser

from src.Mod import ModFolder, Mod
from src.finder import search_subdirectories
from src.globals import SLOTS
from src.help.fighter_names.util import c2f, n2cs
from src.help.unique_textures.util import make_config
from src.utils import tabbed_join, make_dir

logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] %(message)s")
rootLogger = logging.getLogger()
make_dir("logs")
fileHandler = logging.FileHandler(f"logs/{datetime.now().strftime('%Y%m%d%H%M%S')}.log")
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)
rootLogger.addHandler(logging.StreamHandler(sys.stdout))


def log(msg, loglevel=logging.INFO, *args, **kwargs):
    py_log(loglevel, msg, *args, **kwargs)


config = ConfigParser()
config.add_section("custom")
config.set("custom", "out_dir", "")
config.set("custom", "mod_dirs0", "")
config.set("custom", "mod_dirs1", "")
config.set("custom", "mod_dirs2", "")
config.set("custom", "mod_dirs3", "")
config.set("custom", "mod_dirs4", "")
config.write()

Builder.load_file('gui/layout.kv')


class SettingsTab(Settings):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.add_json_panel('Folders', config, 'gui/config.json')


class SlotsTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, orientation="vertical")
        self.char_picker = GridLayout(rows=1, size_hint_x=None)
        for fighter_name in sorted(list(n2cs)):
            fighter_label = CharButton(text=fighter_name)
            fighter_label.texture_update()
            fighter_label.width = fighter_label.texture_size[0]
            self.char_picker.add_widget(fighter_label)
        self.char_picker.width = sum([c.width for c in self.char_picker.children])
        self.char_scroller = ScrollView(do_scroll_x=True, size_hint_y=.1)
        self.char_scroller.add_widget(self.char_picker)
        self.add_widget(self.char_scroller)
        self.content = SlotPanel(fighter="")
        CharButton.content = self.content
        self.add_widget(self.content)


class SlotPanel(BoxLayout):
    def __init__(self, fighter, **kwargs):
        super().__init__(**kwargs, spacing=10, padding=10, orientation="vertical")
        self.replace(fighter)

    def replace(self, fighter):
        log(f"loading panel for fighter {fighter}")
        self.safe_config()
        self.clear_widgets()
        self.fighter = fighter
        self.codes = n2cs[self.fighter] if self.fighter else []
        self.make_slot_header()
        for slot in SLOTS:
            self.make_slot_panel(slot)
        self.loaded_mod_ids = {c: [] for c in self.codes}
        self.load_mod_list()
        self.load_config()

    def make_slot_header(self):
        box = BoxLayout(orientation="horizontal")
        box.add_widget(Label(text="", size_hint_x=0.1))
        for code in self.codes:
            box.add_widget(Label(text=c2f[code], font_size='20sp'))
        self.add_widget(box)

    def make_slot_panel(self, slot):
        box = BoxLayout(orientation="horizontal", spacing=15)
        box.add_widget(Label(text=slot, size_hint_x=0.1, font_size='20sp'))
        for code in self.codes:
            code_box = BoxLayout(orientation="horizontal")
            dd = ModDropDown(code=code, panel=self)
            code_box.ids["mod"] = dd
            code_box.add_widget(dd)
            code_box.add_widget(RefButton(dd))
            sdd = SlotDropDown(dd)
            code_box.add_widget(sdd)
            code_box.ids["slot"] = sdd
            box.ids[code] = code_box
            box.add_widget(code_box)
        self.ids[slot] = box
        self.add_widget(box)

    def load_mod_list(self):
        for code in self.codes:
            mod_ids: list[int] = sorted(Root.root.get_mods_from_code(code))
            if mod_ids == self.loaded_mod_ids[code]:
                continue
            self.loaded_mod_ids[code] = mod_ids

    def safe_config(self):
        log("attempting to save current config")
        if hasattr(self, "codes"):
            for slot in SLOTS:
                for code in self.codes:
                    mod_id = self.ids[slot].ids[code].ids["mod"].selected_mod_id
                    to_slot = self.ids[slot].ids[code].ids["slot"].text
                    if mod_id and to_slot:
                        Root.root.fill_config(self.fighter, slot, code, to_slot, mod_id)

    def load_config(self):
        log("attempting to load a saved config")
        for slot in SLOTS:
            for code in self.codes:
                config = Root.root.configs[self.fighter][slot][code]
                if config:
                    mod_id = config[1]
                    if mod_id in self.loaded_mod_ids[code]:
                        self.ids[slot].ids[code].ids["mod"].set_mod(Root.root.get_mod_name(config[1]), config[1])
                        self.ids[slot].ids[code].ids["slot"].text = config[0]
                    else:
                        Root.root.configs[self.fighter][slot][code] = None
                        self.ids[slot].ids[code].ids["mod"].set_mod("Select the Mod", None)
                        self.ids[slot].ids[code].ids["slot"].text = "Slot"
                else:
                    self.ids[slot].ids[code].ids["mod"].set_mod("Select the Mod", None)
                    self.ids[slot].ids[code].ids["slot"].text = "Slot"


class CharButton(Button):
    content: SlotPanel = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs, size_hint_y=1, size_hint_x=None, height=30, padding=(10, 10))

    def on_release(self):
        self.content.replace(self.text)

class RefButton(Button):
    def __init__(self, dropdown, **kwargs):
        super().__init__(**kwargs)
        self.dropdown: ModDropDown = dropdown

    def on_release(self):
        super().on_release()
        if self.dropdown.selected_mod_id:
            mod = Root.root.get_folder_from_mod(self.dropdown.selected_mod_id)
            if mod and "url" in mod.metadata:
                webbrowser.open(mod.metadata["url"])


class ModDropDown(Button):
    dropdown = None

    def __init__(self, code, panel, **kwargs):
        super().__init__(**kwargs, text="Select the Mod", padding_x=5)
        self.panel = panel
        self.dropdown = DropDown()
        self.fighter_code = code
        self.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=lambda instance, x: setattr(self, 'text', x))
        self.selected_mod_id = None

    def on_release(self):
        super().on_release()
        mod_id_list = self.panel.loaded_mod_ids[self.fighter_code]
        current_mods = sorted([b.mod_id for b in self.dropdown.children if type(b) == ModDDButton])
        if mod_id_list == current_mods:
            return
        self.dropdown.clear_widgets()
        for mod_id in mod_id_list:
            btn = ModDDButton(mod_id=mod_id)
            btn.bind(on_release=lambda b: (self.set_mod(b.text, b.mod_id)))
            self.dropdown.add_widget(btn)
        for button in self.dropdown.children:
            if type(button) == ModDDButton:
                button.texture_update()
                button.width = button.texture_size[0]
                button.x = self.x
        self.parent.ids["slot"].text = "Slot"

    def set_mod(self, mod_name, mod_id):
        self.dropdown.select(mod_name)
        self.selected_mod_id = mod_id


class SlotDropDown(Button):

    def __init__(self, dd, **kwargs):
        super().__init__(**kwargs, padding_x=5, text="Slot", size_hint_x=None, width=40)
        self.mod_dropdown: ModDropDown = dd
        self.dropdown = DropDown()
        self.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=lambda instance, x: setattr(self, 'text', x))
        self.slots = []
        self.fill_slots()

    def fill_slots(self):
        new_slots = self.get_slots()
        if self.slots == new_slots:
            return
        self.dropdown.clear_widgets()
        for slot in new_slots:
            btn = Button(text=slot, size_hint_y=None, size_hint_x=1, height=30, padding=(5, 5))
            btn.bind(on_release=lambda b: (self.dropdown.select(b.text)))
            self.dropdown.add_widget(btn)
        self.slots = new_slots

    def get_slots(self):
        mod_id = self.mod_dropdown.selected_mod_id
        if mod_id:
            mod = Root.root.get_mod(mod_id)
            return list(mod.get_slots()[self.mod_dropdown.fighter_code].keys())
        else:
            return []

    def on_release(self):
        super().on_release()
        self.fill_slots()


class ModDDButton(Button):
    def __init__(self, mod_id, **kwargs):
        super().__init__(text=Root.root.get_mod_name(mod_id), **kwargs)
        self.mod_id = mod_id


class ModButton(Button):
    def __init__(self, info_zone, folder_id, **kwargs):
        super().__init__(**kwargs)
        self.info_zone = info_zone
        self.folder_id = folder_id

    def load_info(self):
        folder = Root.root.get_folder(self.folder_id)
        log(f"loading info for {folder.name}")
        self.info_zone.title.text = folder.name
        self.info_zone.chars.text = ", ".join(folder.fighters)
        self.info_zone.link.text = f"[ref={folder.metadata['url']}]{folder.metadata['url']}[/ref]"
        self.info_zone.image.source = folder.get_img()
        txt = ""
        for mod in folder.mods:
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

    def get_mod(self):
        return Root.root.get_folder(self.mod_id)


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


class SmashSlotSetter(TabbedPanel):

    mod_list: GridLayout = ObjectProperty(None)
    info_box: BoxLayout = ObjectProperty(None)
    dropdown: Button = ObjectProperty(None)
    fighter_select: BoxLayout = ObjectProperty(None)
    slots_tab: SlotsTab = ObjectProperty(None)
    mod_folders: dict[int, ModFolder] = {}
    mods: dict[int, tuple[int, int]] = {}
    folder2mods: dict[int, list[int]] = {}
    configs: dict[str, dict[str, dict[str, tuple[str, int]]]] = {f: {s: {c: None for c in n2cs[f]} for s in SLOTS} for f in n2cs.keys()}
    config_edited = False

    def load_mods(self):
        log("loading mods")
        self.mod_list.clear_widgets()
        for path in [config.get("custom", f"mod_dirs{i}") for i in range(5)]:
            if path:
                log(f"mod folder: {os.path.basename(path)}")
                for mf in search_subdirectories(path):
                    folder_id = len(self.mod_folders)
                    self.mod_folders[folder_id] = mf
                    self.folder2mods[folder_id] = []
                    for i in range(len(mf.mods)):
                        mod_id = len(self.mods)
                        self.mods[mod_id] = (folder_id, i)
                        self.folder2mods[folder_id].append(mod_id)
        log("loaded mod folders:\n\t" + "\n\t".join([f"{i:>5}: {m.name}" for i, m in self.mod_folders.items()]))
        log("loaded mods:\n\t" + "\n\t".join([f"{i:>5}: {self.get_mod(i).full_name}" for i in self.mods.keys()]))
        for folder_id, folder in self.mod_folders.items():
            self.mod_list.add_widget(ModButton(text=folder.name, info_zone=self.info_box, folder_id=folder_id))
        configs = self.config_from_file()
        if configs and not self.config_edited:
            self.configs = configs

    def get_folders_from_code(self, code):
        mods = []
        for i, folder in self.mod_folders.items():
            if code in folder.codes:
                mods.append(i)
        return mods

    def get_mods_from_code(self, code):
        mods = []
        for mod_id in self.mods.keys():
            if code in self.get_mod(mod_id).codes:
                mods.append(mod_id)
        return mods

    def search(self, string):
        if string == "Search...":
            string = ""
        fighter = self.dropdown.text
        for m in self.mod_list.children:
            if type(m) != ModButton:
                continue
            if string.lower() in m.text.lower() and \
                    (fighter in ["All", "Choose your Fighter"] or
                     any(f in self.get_folder(m.folder_id).codes for f in n2cs[fighter])):
                m.opacity = 1
                m.disable = False
                m.height = m.texture_size[1]
            else:
                m.opacity = 0
                m.disable = True
                m.height = 0

    def get_folder(self, folder_id) -> ModFolder:
        return self.mod_folders[folder_id]

    def get_folder_from_mod(self, mod_id) -> ModFolder:
        folder_id, mod_index = self.mods[mod_id]
        return self.mod_folders[folder_id]

    def get_mod(self, mod_id) -> Mod:
        folder_id, mod_index = self.mods[mod_id]
        return self.mod_folders[folder_id].mods[mod_index]

    def get_mod_ids(self, folder_id) -> list[int]:
        return self.folder2mods[folder_id]

    def get_mod_name(self, mod_id) -> str:
        return self.get_mod(mod_id).full_name

    def fill_config(self, fighter, slot, code, mod_slot, mod_id):
        log(f"saving {mod_slot}, {mod_id} to {fighter}/{slot}/{code}")
        self.config_edited = True
        self.configs[fighter][slot][code] = (mod_slot, mod_id)

    def config_to_file(self, path):
        with open(os.path.join(path, "modpack_config.json"), "w", encoding="utf8") as f:
            json.dump(self.configs, f, indent=2)

    def config_from_file(self):
        if os.path.exists("modpack_config.json"):
            with open("modpack_config.json", "r", encoding="utf8") as f:
                return json.load(f)
        return None

    def reset_config_single(self, fighter):
        for s in SLOTS:
            for c in self.configs[fighter][s]:
                self.configs[fighter][s][c] = None
        self.slots_tab.content.load_config()

    def reset_config(self):
        self.configs = {f: {s: {c: None for c in n2cs[f]} for s in SLOTS} for f in n2cs.keys()}
        self.slots_tab.content.load_config()

    def make_modpack_single(self, fighter):
        log(f"Creating Mod Pack for {fighter}")
        # mod.transfer("Neuer Ordner", {"purin": [("c00", "c01"), ("c04", "c02"), ("c06", "c03")]})
        out_folder = config.get("custom", f"out_dir")
        if out_folder:
            out_folder = os.path.join(out_folder, "ModPack")
            make_dir(out_folder)
        else:
            return
        self.config_to_file(out_folder)
        for slot in SLOTS:
            for code in n2cs[fighter]:
                if self.configs[fighter][slot][code] != None:
                    mod_slot, mod_id = self.configs[fighter][slot][code]
                    slot_changes = {code: [(mod_slot, slot)]}
                    mod = self.get_mod(mod_id)
                    try:
                        mod.transfer(out_folder, slot_changes)
                        make_config(os.path.join(out_folder, mod.name), slot_changes, mod.path)
                    except Exception as e:
                        log(f"Something went wrong during packing of {fighter}/{slot}/{code}: {mod.full_name}", loglevel=logging.ERROR)
                        log(e, loglevel=logging.ERROR)
                        log(traceback.format_exc(), loglevel=logging.ERROR)
                        continue
        log("done")

    def make_full_modpack(self):
        log(f"Creating Full Mod Pack")
        # mod.transfer("Neuer Ordner", {"purin": [("c00", "c01"), ("c04", "c02"), ("c06", "c03")]})
        out_folder = config.get("custom", "out_dir")
        if out_folder:
            out_folder = os.path.join(out_folder, "ModPack")
            make_dir(out_folder)
        else:
            return
        self.config_to_file(out_folder)
        for fighter in n2cs.keys():
            for slot in SLOTS:
                for code in n2cs[fighter]:
                    if self.configs[fighter][slot][code] != None:
                        mod_slot, mod_id = self.configs[fighter][slot][code]
                        slot_changes = {code: [(mod_slot, slot)]}
                        mod = self.get_mod(mod_id)
                        try:
                            mod.transfer(out_folder, slot_changes)
                            make_config(os.path.join(out_folder, mod.name), slot_changes, mod.path)
                        except Exception as e:
                            log(f"Something went wrong during packing of {fighter}/{slot}/{code}: {mod.full_name}", loglevel=logging.ERROR)
                            log(e, loglevel=logging.ERROR)
                            log(traceback.format_exc(), loglevel=logging.ERROR)
                            continue
        log("done")


class Root:
    root: SmashSlotSetter = None


class MainApp(App):
    def build(self):
        self.title = "SmashSlotSetter"
        m = SmashSlotSetter()
        Root.root = m
        return m


def main():
    MainApp().run()


if __name__ == '__main__':
    main()
