import re

QUASAR_APIData = "APIData.json"
QUASAR_ContentData = "ContentData.json"
QUASAR_Gamebanana = "Gamebanana.json"
QUASAR_LibraryData = "LibraryData.json"
QUASAR_METADATA_FILES = [QUASAR_APIData, QUASAR_ContentData, QUASAR_Gamebanana, QUASAR_LibraryData]

MOD_SUBFOLDERS = ["fighter", "ui", "effect", "sound", "stream;"]
UMM_SUBFOLDERS = ["UI", "c00", "c01", "c02", "c03", "c04", "c05", "c06", "c07"]

SLOTS = ["c00", "c01", "c02", "c03", "c04", "c05", "c06", "c07"]
slot_re = re.compile(r"c0[0-7]")
ui_slot_re = re.compile(r"0[0-7]\.bntx")
