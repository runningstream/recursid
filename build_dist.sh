DIST_BASE="distribution"
DIST_FOLDER="${DIST_BASE}/Recursid"
BIN_FOLDER="${DIST_FOLDER}/bin"
CONFIG_SRC_FOLDER="configs"
MODULE_DEST="${DIST_FOLDER}"
CONFIG_DEST_FOLDER="${MODULE_DEST}/recursid/etc/recursid"
SYSTEMD_FOLDER="${MODULE_DEST}/recursid/etc/systemd/system"
DIST_SPT="distribution_support"

mkdir -p "${DIST_FOLDER}"
mkdir -p "${BIN_FOLDER}"
mkdir -p "${SYSTEMD_FOLDER}"
mkdir -p "${CONFIG_DEST_FOLDER}"

cp "${DIST_SPT}/recursid.service" "${SYSTEMD_FOLDER}"
cp ${CONFIG_SRC_FOLDER}/* "${CONFIG_DEST_FOLDER}"
cp recursid_multithread.py "${BIN_FOLDER}"
cp recursid_multiprocess.py "${BIN_FOLDER}"
cp -r recursid "${MODULE_DEST}"

cp "${DIST_SPT}/setup.py" "${DIST_FOLDER}"
cp "${DIST_SPT}/MANIFEST.in" "${DIST_FOLDER}"
cp "LICENSE.md" "${DIST_FOLDER}"
cp README.md "${DIST_FOLDER}"
cp version "${DIST_FOLDER}"


PRE_DIR="$(pwd)"
cd "${DIST_FOLDER}"
python3 setup.py sdist bdist_wheel || exit 1
cd "${PRE_DIR}"

cp -r "${DIST_FOLDER}/dist" ./
rm -rf "${DIST_BASE}"
