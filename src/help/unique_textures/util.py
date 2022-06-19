import logging
import os
import re
import json
import logging
from logging import log
from pprint import pprint
from src.help.fighter_names.util import c2f, n2cs, c2n

single_slot = re.compile(r"c0[0-7]")
multiple_slots = re.compile(r"c0[0-7]-c0[0-7]")
reference = re.compile(r"^(?P<l1>\S+.+)\n(?P<info>(?:^\t.+\n?)+)", flags=re.MULTILINE)
replacement = re.compile(r"^(?P<l2>(?:\t| {4}).+)\n(?P<data>(?:^(?:\t| {4}){2,3}.+\n?)+)", flags=re.MULTILINE)
all_slots = ["c00", "c01", "c02", "c03", "c04", "c05", "c06", "c07"]
even_slots = ["c00", "c02", "c04", "c06"]
odd_slots = ["c01", "c03", "c05", "c07"]


def parse():
    with open("src/help/unique_textures/reference.txt", "r", encoding="utf8") as f:
        text = f.read()
        all_references = reference.findall(text)
    reference_dict = {}
    for ref in all_references:
        fighter = sorted([f for f in n2cs if ref[0].startswith(f)], key=lambda x: len(x))[-1]
        if fighter not in reference_dict:
            reference_dict[fighter] = {}
        replacements = replacement.findall(ref[1])
        original_slots = get_slots(ref[0])
        reference_dict[fighter][",".join(original_slots)] = {}
        for repl in replacements:
            replace_slots = get_slots(repl[0], original_slots)
            reference_dict[fighter][",".join(original_slots)][",".join(replace_slots)] = repl[1]
    return reference_dict


def get_slots(line, rest=[]):
    line_l = line.lower()
    if "any other" in line_l:
        slots = [s for s in all_slots if s not in rest]
    elif "even" in line_l:
        slots = even_slots
    elif "odd" in line_l:
        slots = odd_slots
    else:
        slots = single_slot.findall(line)
        multi_slots = multiple_slots.findall(line)
        for ms in multi_slots:
            s1, s2 = ms.split("-")
            between = [f"c0{i}" for i in range(int(s1[1:]), int(s2[1:]))]
            slots += between
    return sorted(list(set(slots)))


reference_dict = parse()


def get_replacement(fighter_code, orig_slot, over_slot):
    fighter_name = c2n[fighter_code]
    if fighter_name not in reference_dict:
        return None
    for orig_slots in reference_dict[fighter_name]:
        if orig_slot in orig_slots:
            for over_slots in reference_dict[fighter_name][orig_slots]:
                if over_slot in over_slots:
                    replacement_code = reference_dict[fighter_name][orig_slots][over_slots]
                    path_parts = replacement_code.split('":')[0].split("/")
                    if path_parts[-2] != fighter_code:
                        continue
                    replacement_slot = path_parts[-1]
                    replacement_code = replacement_code.replace(replacement_slot, over_slot)
                    replacement_code = json.loads("{" + replacement_code + "}")
                    return replacement_code
    return None


def make_config(out_path, combinations, custom_config_path=""):
    # combinations = {'ike': [('c01', 'c04'), ('c01', 'c04')], 'wario': [('c01', 'c04'), ('c01', 'c04')]}
    config_dict = {}
    out_file = os.path.join(out_path, "config.json")
    if os.path.exists(out_file):
        with open(out_file, "r", encoding="utf8") as f:
            config_dict = json.load(f)["new-dir-files"]
    for code, replacements in combinations.items():
        for repl in replacements:
            repl_dict = get_replacement(code, repl[0], repl[1])
            if repl_dict:
                config_dict.update(repl_dict)
            if custom_config_path:
                custom_config = read_config_part(custom_config_path, code, repl[0], repl[1])
                if custom_config:
                    for slot_path, file_list in custom_config.items():
                        if slot_path in config_dict:
                            config_dict[slot_path] += [f for f in file_list if f not in config_dict[slot_path]]
                        else:
                            config_dict[slot_path] = file_list

    if config_dict:
        with open(out_file, "w", encoding="utf8") as f:
            json.dump({"new-dir-files": config_dict}, f, indent=4)


def read_config_part(in_path, fighter_code, orig_slot, over_slot):
    config_path = os.path.join(in_path, "config.json")
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf8") as f:
        config = json.load(f)
    config_key = f"fighter/{fighter_code}/{orig_slot}"
    if "new_dir_files" in config:
        config["new-dir-files"] = config["new_dir_files"]
        del(config["new_dir_files"])
    if "new-dir-files" not in config:
        log(logging.WARN, f"config.json found for {in_path}/{fighter_code} but no new-dir-files found in {config}")
        return {}
    if config_key not in config["new-dir-files"]:
        return {}
    slot_config = config["new-dir-files"][config_key]
    new_config = {f"fighter/{fighter_code}/{over_slot}": [s.replace(f"/{orig_slot}/", f"/{over_slot}/") for s in slot_config]}
    return new_config


if __name__ == "__main__":
    make_config("", {'ike': [('c01', 'c04'), ('c01', 'c04')], 'wario': [('c01', 'c04'), ('c01', 'c04')]})
