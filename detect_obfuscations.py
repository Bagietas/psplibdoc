#! /usr/bin/env python3

import psp_libdoc
import glob
import os
import sys
from collections import defaultdict, Counter

def get_nids_ver(nids, ver):
    output = []
    for nid in nids:
        if ver in nid["versions"]:
            output.append(nid)
    return output

def handle_library(module, lib, nids, versions):
    vers = list(sorted(set([v for nid in nids for v in nid["versions"]])))
    # Indicates the NIDs had at least one round of randomization in previous (or current) firmware version
    prev_nonobf = {}
    prev_ok = {}
    for (v1, v2) in zip(vers, vers[1:]):
        # For each consecutive firmware versions v1 and v2, see their respective NIDs
        v1_nids = set([x["nid"] for x in get_nids_ver(nids, v1)])
        v2_nids = set([x["nid"] for x in get_nids_ver(nids, v2)])
        # Check the NIDs which appeared and the ones which disappeared
        new_nids = v2_nids - v1_nids
        disappear_nids = v1_nids - v2_nids
        # Heuristic to find randomization rounds: if more than 20% of the NIDs of the new version are new, and more than 20% of the NIDs of the previous version disappeared
        # This works in almost all cases, except it never detects if a library got randomized NIDs from the beginning
        new_ratio = len(new_nids) / len(v2_nids)
        dis_ratio = len(disappear_nids) / len(v1_nids)
        is_obfuscated = False
        if new_ratio > 0.2 and dis_ratio > 0.2:
            is_obfuscated = True
            # If we find a new NID whose name is known, then it means there cannot have been a randomization here (note this check triggers rarely), except for 5.55 which misses functions from 5.51
            for n in new_nids:
                name = None
                for nid in get_nids_ver(nids, v2):
                    if nid["nid"] == n:
                        name = nid["name"]
                if psp_libdoc.compute_nid(name) == n and v1 != '5.55': # some exceptions exist for 5.55 (which misses functions from 5.51)
                    is_obfuscated = False
        if is_obfuscated:
            for i in new_nids:
                print(','.join([module, lib, v1, v2, "NEW", i]))
            for i in disappear_nids:
                print(','.join([module, lib, v1, v2, "OLD", i]))

def main():
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
            nid_bylib[e.prx][e.libraryName].append({"nid": e.nid, "name": e.name, "versions": cur_ver})

    versions = list(sorted(versions))

    for prx in sorted(nid_bylib):
        for lib in sorted(nid_bylib[prx]):
            handle_library(prx, lib, nid_bylib[prx][lib], versions)

if __name__ == '__main__':
    main()

