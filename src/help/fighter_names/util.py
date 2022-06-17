import re

char_re = re.compile(r"(?P<nr>\d+)(?P<append>[A-Z]?)\.(?P<name>.+?)- {(?P<code>[a-z]*)}")


def parse():
    with open("src/help/fighter_names/fighter code names.txt", "r", encoding="utf8") as f:
        text = f.read()
        all_fighters = char_re.findall(text)

    # dictionaries 1 and 2: fighter to code and code to fighter
    d1 = {f[2]: f[3] for f in all_fighters if f[3]}
    d2 = {f[3]: f[2] for f in all_fighters if f[3]}

    # dictionaries 3 and 4: fighter to all associated code names and code names to the combined fighter name
    dtemp = {}
    for f in all_fighters:
        if f[1] and f[1] in "BPM":
            dtemp[f[0]]["codes"].append(f[3])
            if f[1] == "M":
                dtemp[f[0]]["name"] += " & " + f[2]
        elif f[1] and f[1] == "E":
            dtemp[f[0]+"E"] = {}
            dtemp[f[0]+"E"]["codes"] = [f[3]] if f[3] else []
            dtemp[f[0]+"E"]["name"] = f[2]
        else:
            dtemp[f[0]] = {}
            dtemp[f[0]]["codes"] = [f[3]] if f[3] else []
            dtemp[f[0]]["name"] = f[2]
    d3 = {f["name"]: f["codes"] for f in dtemp.values()}
    d4 = {f["codes"][i]: f["name"] for f in dtemp.values() for i in range(len(f["codes"]))}
    return d1, d2, d3, d4


f2c, c2f, n2cs, c2n = parse()


if __name__ == "__main__":
    print(parse())
