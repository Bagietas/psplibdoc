#! /usr/bin/env python3

# Generate a HTML report from all the PSP export files, specifying known names for all libraries, and determining which NIDs have been randomized

import psp_libdoc
import glob
import os
import sys
from collections import defaultdict, Counter

OUTPUT_HTML = "./github-pages"

# List of colors & descriptions for each "category" of NID
HTML_STATUS = [
    # for both obfuscated and non-obfuscated
    ("known", "green", "matching the name hash"),
    # for non-obfuscated
    ("unknown", "orange", "unknown"),
    ("wrong", "red", "not matching the name hash"),
    # for obfuscated
    ("obf_ok", "yellow", "obfuscated but matching a previously known name"),
    ("obf_unk", "orange", "unknown but non-obfuscated in a previous version"),
    ("obf_new", "grey", "present only as obfuscated")
]

def find_html_status(status):
    for (s, color, desc) in HTML_STATUS:
        if s == status:
            return (color, desc)

# Header for the main HTML page
def html_header(versions):
    header = """<!DOCTYPE html>
<html>
<title>PSP NID Status</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
<style>
.w3-table .w3-container {
    padding: 0em 0px;
}
.w3-col {
    height:24px;
}
</style>
<body>
<div class="w3-container" style="height:100vh; width:100vw; overflow: scroll;">
<h1>PSP NID Status</h1>
<p>
This page contains the status of all the NIDs from the PSP official firmwares. <br />
To get more details about a library, click its name to see its list of NIDs. <br />
On later firmwares, some kernel NIDs were randomized. A star indicates (most of) the library's NIDs were (re-)randomized at that firmware version. Note that the algorithm used to identify the randomizations is imperfect and, in particular, won't detect libraries whose NIDs have been randomized from the beginning. <br />
Progress counts are given for both non-randomized and randomized NIDs (if present). Note that for randomized NIDs, all specified names are considered correct even though they cannot be verified. <br />
Hover a color to get the numbers and the definition of its status. <br />
</p>"""
    header += """<table class="w3-table"><tr><th>Module name</th><th>Library name</th><th>Progress</th>"""
    for ver in versions:
        header += f"<th>{ver}</th>"
    header += "</tr>"
    return header

# Footer for the main HTML page
def html_footer():
    return """</table></div></body></html>"""

# Output a row of the large table of the main page, for a given module & library, with the statistics given by "make_stats"
def html_library(module, lib, stats_byver, versions):
    # Specify the module and library name
    output = f"""<tr><td>{module}</td><td><a href="modules/{module}_{lib}.html">{lib}</a></td>"""
    # Make statistics over all versions to give an overall % of resolution for the library
    status_bynid = {}
    for ver in stats_byver:
        for status in stats_byver[ver]:
            if status == "total" or status == "is_obf":
                continue
            for cur_nid in stats_byver[ver][status]:
                status_bynid[cur_nid["nid"]] = status
    cnt = Counter(status_bynid.values())
    both_stats = []
    nonobf_ok = cnt["known"]
    nonobf_total = nonobf_ok + cnt["wrong"] + cnt["unknown_nonobf"] + cnt["unknown"]
    obf_ok = cnt["nok_from_previous"] + cnt["nok_dubious"]
    obf_total = obf_ok + cnt["unknown_obf"]
    if nonobf_total != 0:
        both_stats.append("%.1f%% (%d/%d)" % (nonobf_ok / nonobf_total * 100, nonobf_ok, nonobf_total))
    if obf_total != 0:
        both_stats.append("%.1f%% (%d/%d)" % (obf_ok / obf_total * 100, obf_ok, obf_total))
    agg_stats = " / ".join(both_stats)
    output += f"""<td style="white-space: nowrap;">{agg_stats}</td>"""

    # Make a column for each firmware version
    for ver in versions:
        # Show an empty cell if the library didn't exist in that firmware version
        if ver not in stats_byver:
            output += "<td></td>"
            continue
        output += "<td>"
        cur_stats = stats_byver[ver]
        # Add a star if the NIDs of that library were (re-)randomized in that firmware version
        if stats_byver[ver]["is_obf"]:
            obf_str = '<div style="position: absolute; width: 100%; height: 100%; text-align: center;">*</div>'
        else:
            obf_str = ''

        # Make progress bars with tooltips and colors given in HTML_STATUS
        for (status, color, desc) in HTML_STATUS:
            if status not in cur_stats:
                continue
            count = len(cur_stats[status])
            if count == 0:
                continue
            total = cur_stats['total']
            percent = int(count / total * 100)

            output += f"""<div style="position: relative;"><div class="w3-col w3-container w3-{color} w3-tooltip" style="width:{percent}%">
<span style="position:absolute;left:0;bottom:18px" class="w3-text w3-tag">{count}/{total} NIDs are {desc}</span>
</div>"""
        output += f"{obf_str}</div></td>"
    return output

# Output a HTML page for a single library
def html_single_library(module, lib, stats_bynid, versions):
    output = f"""<!DOCTYPE html>
<html>
<title>PSP NID Status for {lib} in {module}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
<body>
<div class="w3-container" style="height:100vh; width:100vw; overflow: scroll;">
<h1>{module}: {lib}</h1>
<p>
This page contains the status of all the NIDs from the {lib} library inside the {module} module.<br />
Hover a cell to know the meaning of the color. <br />
"..." means the given name is the same as the one on its left. <br />
</p>
"""
    # Output the header row (containing all the firmware versions)
    output += """<table class="w3-table"><tr><th>NID</th>"""
    for v in versions:
        output += f"<th>{v}</th>"
    output += '</tr>'
    # Sort NIDs by the first firmware version they appear in, then by the names associated to them
    sorted_nids = []
    sources = {}
    for v in versions:
        ver_nids = []
        for nid in stats_bynid:
            if v in stats_bynid[nid]:
                (_, name, source) = stats_bynid[nid][v]
                sources[name] = source
                ver_nids.append((name, nid))
        for (_, nid) in sorted(ver_nids):
            if nid not in sorted_nids:
                sorted_nids.append(nid)
    # For each NID, show the associated name, status & a tooltip explaining its status
    for nid in sorted_nids:
        output += f"<tr><td>{nid}</td>"
        last_name = None
        for v in versions:
            if v not in stats_bynid[nid]:
                output += "<td></td>"
            else:
                (status, name, source) = stats_bynid[nid][v]
                show_name = name
                source_str = ''
                if name == last_name:
                    show_name = '...'
                elif source != '' and source != 'matching':
                    source_str = ' (source: ' + source + ')'
                last_name = name
                (color, desc) = find_html_status(status)
                output += f"""<td class="w3-{color}"><div class="w3-tooltip">{show_name}{source_str}<span style="position:absolute;left:0;bottom:18px" class="w3-text w3-tag">NID is {desc}</span></div></td>"""
        output += "</tr>"
    output += "</table></div></body></html>"
    return output

# Build the statistics for a given library at a given version.
def make_stats(module, lib, version, cur_nids, nid_names, obfuscation_pairs):
    unk_nids = []
    nok_nids = []
    ok_nids = []
    obf_ok_nids = []
    obf_unk_nids = []
    obf_new_nids = []
    is_obf = False
    # Sort NIDs by category: unknown (name ends with the NID), ok (NID matches the hash) and nok (NID doesn't match the hash)
    for cur_nid in cur_nids:
        fullname = lib + '_' + cur_nid
        # TODO: handle guesses
        if fullname in nid_names:
            if nid_names[fullname][1] == 'matching':
                ok_nids.append({"nid": cur_nid, "name": nid_names[fullname][0], "source": nid_names[fullname][1]})
            else:
                unk_nids.append({"nid": cur_nid, "name": nid_names[fullname][0], "source": nid_names[fullname][1]})
        else:
            is_obf = True
            oldername = fullname
            cycle_detect = [oldername]
            while oldername in obfuscation_pairs:
                oldername = obfuscation_pairs[oldername]
                if oldername in nid_names: # used to avoid some cycles (NIDs which reappeared as non-obfuscated)
                    break
                if oldername in cycle_detect:
                    print("cycle detected with", fullname)
                    exit(1)
            oldest_nid = oldername.split('_')[-1]
            if oldername in nid_names:
                if nid_names[oldername][1] == 'matching':
                    obf_ok_nids.append({"nid": oldest_nid, "name": fullname, "source": "obf_matching"})
                else:
                    obf_unk_nids.append({"nid": oldest_nid, "name": fullname, "source": "obf_unknown"})
            else:
                obf_new_nids.append({"nid": oldest_nid, "name": fullname, "source": "obf_new"})

    stats = {"known": ok_nids, "unknown": unk_nids, "wrong": nok_nids, "obf_ok": obf_ok_nids, "obf_unk": obf_unk_nids, "obf_new": obf_new_nids}

    stats['total'] = len(cur_nids)
    stats['is_obf'] = is_obf

    return stats

def get_nids_ver(nids, ver):
    output = []
    for nid in nids:
        if ver in nid["versions"]:
            output.append(nid["nid"])
    return output

# Make statistics for all the versions of a library, write the single HTML page, and return the row for the main page
def handle_library(module, lib, nids, versions, nid_names, obf_pairs):
    vers = list(sorted(set([v for nid in nids for v in nid["versions"]])))
    prev_nonobf = {}
    prev_ok = {}
    stats_byver = {vers[0]: make_stats(module, lib, vers[0], get_nids_ver(nids, vers[0]), nid_names, obf_pairs)}
    for (v1, v2) in zip(vers, vers[1:]):
        # For each consecutive firmware versions v1 and v2, see their respective NIDs
        stats_byver[v2] = make_stats(module, lib, v2, get_nids_ver(nids, v2), nid_names, obf_pairs)

    # Get the results by NID for the individual pages
    stats_bynid = defaultdict(dict)
    for v in vers:
        for status in stats_byver[v]:
            if status == "total" or status == "is_obf":
                continue
            for cur_nid in stats_byver[v][status]:
                stats_bynid[cur_nid["nid"]][v] = (status, cur_nid["name"], cur_nid["source"])
    with open(OUTPUT_HTML + '/modules/' + module + '_' + lib + '.html', 'w') as fd:
        fd.write(html_single_library(module, lib, stats_bynid, vers))

    return html_library(module, lib, stats_byver, versions)

def main():
    # Create the folders for the HTML output
    os.makedirs(OUTPUT_HTML, exist_ok=True)
    os.makedirs(OUTPUT_HTML + "/modules", exist_ok=True)

    # Parse all the NID export files
    filelist = glob.glob('generated-xml/ByModule/kd/*.xml') + glob.glob('generated-xml/ByModule/vsh/module/*.xml')

    nid_bylib = defaultdict(lambda: defaultdict(list))
    versions = set()

    for file in filelist:
        entries = psp_libdoc.loadPSPLibdoc(file)
        for e in entries:
            cur_ver = [v for v in e.versions if not v.startswith('vita')]
            for v in cur_ver:
                versions.add(v)
            if len(cur_ver) == 0:
                continue
            nid_bylib[e.prx][e.libraryName].append({"nid": e.nid, "versions": cur_ver})

    obfuscations = []
    for line in open('obfuscations.csv', 'r').read().split('\n')[:-1]:
        obfuscations.append(line.split(','))

    obfuscation_pairs = {}
    for line in open('obfuscation_pairs.csv', 'r').read().split('\n')[:-1]:
        obfuscation_pairs[line.split(',')[1]] = line.split(',')[0]

    nid_names = {}
    for csv in glob.glob('PSPLibDoc/kd/*.csv') + glob.glob('PSPLibDoc/vsh/module/*.csv'):
        for line in open(csv, 'r').read().split('\n')[:-1]:
            lib = line.split(',')[0]
            nid = line.split(',')[2]
            name = line.split(',')[3]
            source = line.split(',')[4]

            nid_names[lib + '_' + nid] = (name, source)

    versions = list(sorted(versions))

    # Output the main and single HTML pages
    html_output = html_header(versions)
    for prx in sorted(nid_bylib):
        for lib in sorted(nid_bylib[prx]):
            html_output += handle_library(prx, lib, nid_bylib[prx][lib], versions, nid_names, obfuscation_pairs)
    html_output += html_footer()
    with open(OUTPUT_HTML + "/index.html", 'w') as fd:
        fd.write(html_output)

if __name__ == '__main__':
    main()

