#! /bin/bash

PRX_FOLDERS=("kd" "vsh/module")

PRX_FILES=()
for PRX_FOLDER in ${PRX_FOLDERS[@]}; do
    PRX_PATH="./PSPLibDoc/${PRX_FOLDER}"
    if [ -d "${PRX_PATH}" ]; then
        for CSV_FILE in "${PRX_PATH}"/*.csv; do
            XML_FILE="./generated-xml/ByModule/$PRX_FOLDER/$(basename ${CSV_FILE/.csv}.xml)"
            ./psp_libdoc.py -i "$CSV_FILE" -u "$XML_FILE"
        done
    fi
done

./scripts/save_combined.sh
./scripts/save_per_fw_version.sh

