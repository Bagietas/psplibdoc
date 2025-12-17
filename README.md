# PSPLibDoc
An attempt to document symbols of PSP modules across all firmwares.\
Page with the current NID status for each library can be found [here](https://pspdev.github.io/psplibdoc/).
<br>
 
## Usage
### How to contribute
Just edit the CSV files in PSPLibDoc/ and submit a pull request.

You can update the CSV files using the psp_libdoc.py script (see below).

If you are motivated enough to rebuild the XML files (which is the common psplibdoc format used by various tools), run the `build_xml_from_csv.sh` script (it takes some time to run). Otherwise the XMLs will be updated later.

### Prerequisites
psp_libdoc.py requires python3 with lxml module.

### Most useful psp_libdoc operations
 - Loading source files
    - Load one or more PSP export files
        - psp_libdoc.py -e input_1.exp input_2.exp input_3.exp...

    - Load one or more PSPLibDoc XML files
        - psp_libdoc.py -l input_1.xml input_2.xml input_3.xml...

    - Load one or more NID CSV files (as are present in the PSPLibDoc/ dir in this repo)
        - psp_libdoc.py -i input_1.csv input_2.csv input_3.csv...

 - Update a PSPLibDoc XML file with known NIDs from all loaded sources
    - psp_libdoc.py *sources* -u psp_libdoc_to_update.xml

 - Update a CSV file (as is present in PSPLibDoc/ on this repo) with known NIDs from all loaded sources
    - psp_libdoc.py *sources* -U psp_libdoc_to_update.csv

### Other operations

 - Load one or more PPSSPP source files (HLEFunction arrays)
    - psp_libdoc.py -p input_1.cpp input_2.cpp input_3.cpp...

 - Combination of multiple different sources
    - psp_libdoc.py -l input_1.xml input_2.xml... -e input_1.exp input_2.exp... -p ...

 - Save a combined PSPLibDoc XML file from all loaded sources
    - psp_libdoc.py *sources* -c psp_libdoc.xml
    - scripts/save_combined.sh will create a combined PSPLibDoc file for all firmwares and modules
    - scripts/save_per_fw_version.sh will create a combined PSPLibDoc file for all firmware versions, each containing all modules

 - Save PRX modules as individual PSPLibDoc XML files from all loaded sources
    - psp_libdoc.py *sources* -s outputFolder

 - Export all unknown NIDs from all loaded sources
    - psp_libdoc.py *sources* -o unknown_nids.txt

 - Export all known function names from all loaded sources
    - psp_libdoc.py *sources* -k known_function_names.txt
<br>

### Obfuscated NIDs

In later firmware versions, most NIDs for kernel functions were "randomized" (most probably by adding an unknown string at the end of the names before being hashed), meaning for one function you can have different NIDs for 1.50, 3.30, 6.60 etc. and only the first one can be confirmed from the name. However, using heuristics, we can try to match the newer functions with the former non-obfuscated names.
- detect_obfuscations.py detects if and when NIDs were obfuscated for each module and generates obfuscations.csv. It uses the heuristic that if >20% of the former version disappeared and >20% of the newer version just appeared, then it means they must have been obfuscated.
- match-nids.py uses the assembly output (using prxtool) to find closer matches between functions before and after obfuscation (or re-obfuscation). It generates obfuscation_pairs.csv.

Note some minor edits have been made manually to obfuscations.csv and obfuscation_pairs.csv to fix some mistakes, and there might remain a lot (mostly newer NIDs matched with the incorrect functions).

<br>

### Misc tools
 - Check if NIDs are marked "matching" if and only if they actually match
   - ./verify-sources.py

 - Generate a page containing the statistics of known and unknown NIDs
   - ./build_stats_pages.py
<br>

## Firmware Notes
 - Firmware 1.00 is an accidentally leaked pre-release firmware by Sony (also known as 1.00 Bogus)
 - Firmware 1.03 is the actual PSP Japan release firmware (VSH only reports 1.00)
 - Firmwares in the ePSPVitaLibDoc folder refer to PS Vita firmware
 - The PS Vita ePSP emulator was based on different PSP firmwares throughout its lifecycle
    - Since PS Vita ePSP 0.931 -> PSP 6.20
    - Since PS Vita ePSP 0.990 -> PSP 6.36
    - Since PS Vita ePSP 1.03 -> PSP 6.60
    - Since PS Vita ePSP 3.36 -> PSP 6.61
<br>

## Credits
A big thanks goes to
 - All original PSPLibDoc contributers
 - All PPSSPP contributers for additional user library symbols
 - All uOFW contributors for updated 6.60 and 6.61 symbols
 - artart78, Draan, efonte, GrapheneCt, sajattack, SilverSpring, zecoxao, Spenon-Dev for additional symbol sources and NIDs
 - Spenon-Dev for the original repo [here](https://github.com/Spenon-dev/PSPLibDoc)
