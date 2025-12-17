#!/usr/bin/python3

# When a NID randomization has been detected, try to match to the closest function in the previous firmware
# Usage example: ./match-nids.py PSPLibDoc/kd/ata.xml 620.PBP/F0/kd/ata.prx 630.PBP/F0/kd/ata.prx

from collections import defaultdict
import Levenshtein
import psp_libdoc
import re
import subprocess
import sys

# Run prxtool on a .prx file
def run_prxtool(binary_path):
    return subprocess.check_output(["prxtool", "-w", binary_path], stderr=subprocess.DEVNULL).decode('ascii')

# Get the raw disassembly (without addresses) of the functions of a .prx file
def get_raw_functions(binary_path):
    data = run_prxtool(binary_path)
    funs = defaultdict(str)
    cur_fun = None
    names = []
    for line in data.split('\n'):
        if 'Subroutine' in line:
            m = re.match(r"; Subroutine ([^ ]*) .*", line)
            names = [m.groups()[0]]
            alias_pos = line.find("Aliases: ")
            if alias_pos != -1:
                alias_str = line[alias_pos + len("Aliases: "):]
                names += alias_str.split(", ")
        elif line.startswith('\t0x'):
            m = re.match(r"\t0x[0-9A-F]{8}: 0x([0-9A-F]{8})", line)
            data = m.groups()[0]
            for n in names:
                funs[n] += data
        elif '; Imported from' in line:
            break
    return funs

# Match the functions of two module (versions) by repeatedly finding the closest pairs
def match_module_pair(func_old, func_new, path1, path2):
    # Find the functions of both modules, ignoring unexported functions
    funs1 = {k: v for k, v in get_raw_functions(path1).items() if not (k.startswith('sub_') or k.startswith('loc_') or k.startswith('module_'))}
    funs1 = {k: funs1[k] for k in funs1.keys() if k in func_old}
    funs2 = {k: v for k, v in get_raw_functions(path2).items() if not (k.startswith('sub_') or k.startswith('loc_') or k.startswith('module_'))}
    funs2 = {k: funs2[k] for k in funs2.keys() if k in func_new}
    distances = defaultdict(dict)
    #print('computing distances...')
    for (f1, c1) in funs1.items():
        lib1 = f1[:-8]
        for (f2, c2) in funs2.items():
            lib2 = f2[:-8]
            if lib1 != lib2:
                continue
            distances[f1][f2] = Levenshtein.distance(c1, c2)

    #print('associating functions...')
    result = {}
    while len(funs1) > 0 and len(funs2) > 0:
        closest_pair = None
        min_dist = None
        for (f1, c1) in funs1.items():
            lib1 = f1[:-8]
            for (f2, c2) in funs2.items():
                lib2 = f2[:-8]
                # Only match functions belonging to the same library
                if lib1 != lib2:
                    continue
                cur_dist = distances[f1][f2]
                if min_dist is None or cur_dist < min_dist:
                    min_dist = cur_dist
                    closest_pair = (f1, f2)
        if closest_pair is None: # could happen if the two remaining functions are in different libraries
            break
        #print(closest_pair, min_dist)
        del funs1[closest_pair[0]]
        del funs2[closest_pair[1]]
        result[closest_pair[0]] = closest_pair[1]
    # Return a dictionary of (name of function in path1) -> (name of function in path2)
    return result

def list_matches(ver1, ver2, mod1, mod2):
    # nid_matches contains a (obfuscated NID) -> (unobfuscated NID) mapping
    func_old = []
    func_new = []
    for line in open('obfuscations.csv', 'r').read().split('\n')[:-1]:
        lib = line.split(',')[1]
        old = line.split(',')[2]
        new = line.split(',')[3]
        typ = line.split(',')[4]
        nid = line.split(',')[5]
        if old == ver1 and new == ver2:
            if typ == 'OLD':
                func_old.append(lib + '_' + nid)
            elif typ == 'NEW':
                func_new.append(lib + '_' + nid)
    nid_matches = match_module_pair(func_old, func_new, mod1, mod2)
    for nid in nid_matches:
        print(nid + ',' + nid_matches[nid])

if __name__ == '__main__':
    list_matches(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

