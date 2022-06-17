import os
from pprint import pprint
from os import path, listdir, walk
from shutil import copytree, copy2

from src.globals import MOD_SUBFOLDERS, UMM_SUBFOLDERS, slot_re, ui_slot_re
from src.help.fighter_names.util import c2f, c2n
from src.help.unique_textures.util import make_config
from src.utils import find_in_dict, find_file_in_dict, make_dir


class ModFolder:
    def __init__(self, f_path):
        self.path = f_path
        self.name = path.basename(f_path)
        self.mods = self.get_submods()
        self.valid = len(self.mods) > 0

    def get_submods(self):
        mods = []
        found_mods = []
        for root, dirs, files in walk(self.path):
            if any([root.startswith(m) for m in found_mods]):
                continue
            root_folder = path.basename(root)
            if any([d in dirs for d in MOD_SUBFOLDERS]):
                found_mods.append(root)
                mods.append(Mod(root))
            elif any([d in dirs for d in UMM_SUBFOLDERS]):
                found_mods.append(root)
                mods.append(Mod(root, umm=True))
        return mods


class Mod:
    def __init__(self, f_path, umm=False):
        self.umm = umm
        self.path = f_path
        self.name = path.basename(f_path)
        self.dir = self.get_dir()
        self.fighter, self.ui, self.effect, self.sound, self.stream = self.parse_folders()
        self.has_config = path.exists(path.join(self.path, "config.json"))

    def get_dir(self):
        def get_dir_rec(p):
            new_dir = {}
            for f in os.listdir(p):
                joined = path.join(p, f)
                if path.isdir(joined):
                    new_dir[f] = get_dir_rec(joined)
                else:
                    new_dir[f] = ""
            return new_dir
        return get_dir_rec(self.path)

    def parse_folders(self):
        fighter = FighterData(path.join(self.path, "fighter"), self.dir["fighter"]) if "fighter" in self.dir else None
        sound = SoundData(path.join(self.path, "sound"), self.dir["sound"], fighter.codes) if fighter and ("sound" in self.dir) else None
        ui = UIData(path.join(self.path, "ui"), self.dir["ui"], fighter.codes) if fighter and ("ui" in self.dir) else None
        return fighter, ui, None, sound, None

    def transfer(self, out_path, slot_changes):
        out_folder = path.join(out_path, self.name)
        make_dir(out_folder)
        for fighter_code, changes in slot_changes.items():
            for change in changes:
                if self.fighter:
                    self.fighter.copy(fighter_code, change[0], change[1], path.join(out_folder, "fighter"))
                if self.ui:
                    self.ui.copy(fighter_code, change[0], change[1], path.join(out_folder, "ui"))
                if self.sound:
                    self.sound.copy(fighter_code, change[0], change[1], path.join(out_folder, "sound"))
        make_config(out_folder, slot_changes, self.path if self.has_config else "")


class FighterData:
    def __init__(self, f_path, directory):
        self.path = f_path
        self.dir = directory
        self.codes = [c for c in self.dir.keys() if c in c2f]
        self.common = "common" in self.dir
        self.chars = [c2f[f] for f in self.codes]
        self.fighters = list(dict.fromkeys([c2n[f] for f in self.codes]).values())
        self.slots = self.get_slots()
        # pprint(self.slots)
        # exit(0)

    def get_slots(self):
        chars = {}
        for c in self.codes:
            found_slots = find_in_dict(self.dir[c], slot_re)
            char_slots = {}
            for s in found_slots:
                slot = s[-1]
                if slot not in char_slots:
                    char_slots[slot] = {"fighter": []}
                char_slots[slot]["fighter"].append(s)
            chars[c] = char_slots
        return chars

    def copy(self, fighter, slot, desired_slot, desired_path):
        for folder in self.slots[fighter][slot]["fighter"]:
            path_to_copy = path.join(self.path, fighter, *folder)
            path_to_paste = path.join(desired_path, fighter, *folder[:-1], desired_slot)
            copytree(path_to_copy, path_to_paste)


class SoundData:
    def __init__(self, f_path, directory, codes):
        self.path = f_path
        self.dir = directory
        self.codes = [c for c in codes if find_file_in_dict(self.dir, c)]
        self.common = "common" in self.dir
        self.chars = [c2f[f] for f in self.codes]
        self.fighters = list(dict.fromkeys([c2n[f] for f in self.codes]).values())
        self.slots = self.get_slots()
        # pprint(self.slots)
        # exit(0)

    def get_slots(self):
        chars = {}
        for c in self.codes:
            found_files = find_file_in_dict(self.dir, c)
            char_slots = {}
            for s in found_files:
                m = slot_re.search(s[-1])
                if m:
                    slot = m.group(0)
                    if slot not in char_slots:
                        char_slots[slot] = {"sound": []}
                    char_slots[slot]["sound"].append(s)
            chars[c] = char_slots
        return chars

    def copy(self, fighter, slot, desired_slot, desired_path):
        for folder in self.slots[fighter][slot]["sound"]:
            path_to_copy = path.join(self.path, *folder)
            new_file_name = folder[-1].replace(slot, desired_slot)
            path_to_paste = path.join(desired_path, *folder[:-1], new_file_name)
            make_dir(path.dirname(path_to_paste))
            copy2(path_to_copy, path_to_paste)


class UIData:
    def __init__(self, f_path, directory, codes):
        self.path = f_path
        self.dir = directory
        self.codes = [c for c in codes if find_file_in_dict(self.dir, c)]
        self.common = "common" in self.dir
        self.chars = [c2f[f] for f in self.codes]
        self.fighters = list(dict.fromkeys([c2n[f] for f in self.codes]).values())
        self.slots = self.get_slots()
        # pprint(self.slots)
        # exit(0)

    def get_slots(self):
        chars = {}
        for c in self.codes:
            found_files = find_file_in_dict(self.dir, c)
            char_slots = {}
            for s in found_files:
                if "chara_5" in s or "chara_7" in s:
                    continue
                m = ui_slot_re.search(s[-1])
                if m:
                    slot = "c" + m.group(0).split(".")[0]
                    if slot not in char_slots:
                        char_slots[slot] = {"ui": []}
                    char_slots[slot]["ui"].append(s)
            chars[c] = char_slots
        return chars

    def copy(self, fighter, slot, desired_slot, desired_path):
        for folder in self.slots[fighter][slot]["ui"]:
            path_to_copy = path.join(self.path, *folder)
            new_file_name = folder[-1].replace(slot[1:]+".bntx", desired_slot[1:]+".bntx")
            path_to_paste = path.join(desired_path, *folder[:-1], new_file_name)
            make_dir(path.dirname(path_to_paste))
            copy2(path_to_copy, path_to_paste)
