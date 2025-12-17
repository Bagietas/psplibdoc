#! /bin/bash

PRX_FOLDERS=("kd" "vsh/module")

PRX_FILES=()
for PRX_FOLDER in ${PRX_FOLDERS[@]}
do
    PRX_PATH="./generated-xml/ByModule/${PRX_FOLDER}/"
    if [ -d "${PRX_PATH}" ]; then
        mapfile -t -O "${#PRX_FILES[@]}" PRX_FILES < <(ls -1 "${PRX_PATH}"*.xml)
    fi
done

COMBINED_LIBDOC_FILE="PSPLibDoc.xml"
echo "Saving combined PSP-Libdoc file ${COMBINED_LIBDOC_FILE}"
./psp_libdoc.py -l ${PRX_FILES[@]} -c "./generated-xml/${COMBINED_LIBDOC_FILE}"

