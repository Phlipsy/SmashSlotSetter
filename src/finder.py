import os
import json
from tqdm import tqdm

from src.Mod import Mod, ModFolder
from src.globals import QUASAR_METADATA_FILES
from src.help.fighter_names.util import c2f


def search_subdirectories(path):
    found_mods = []
    for folder in tqdm(os.listdir(path)):
        mod_folder = ModFolder(os.path.join(path, folder))
        if mod_folder.valid:
            found_mods.append(mod_folder)
        else:
            print(f"Invalid Folder: {mod_folder.path}")
    return found_mods


def print_mods(path):
    mod_folders = search_subdirectories(path)
    with open("found_mods.txt", "w", encoding="utf8") as f:
        for mf in mod_folders:
            f.write(f"{mf.name}\n")
            for m in mf.mods:
                f.write(f"\t({'umm' if m.umm else 'arc'}) {m.name}\n")
                if m.fighter:
                    for cha, slots in m.fighter.slots.items():
                        f.write(f"\t\t{c2f[cha]} Slots: {slots.keys()}\n")



if __name__ == "__main__":
    # print_mods("C:/Users/Philipp/Desktop/SmashMods/Library/Mods")
    mod = search_subdirectories("C:/Users/Philipp/Desktop/SmashMods/Library/Mods")[0].mods[0]
    mod.transfer("Neuer Ordner", {"purin": [("c00", "c01"), ("c04", "c02"), ("c06", "c03")]})

