#!/bin/bash

function test_one {
    TEMP_OUT="/tmp/recursid_test_temp_out"
    EXPECTED_OUT="log_loop_expected_out"
    TEMP_NC_OUT="/tmp/recursid_test_temp_nc_out"
    EXPECTED_NC_OUT="log_loop_expected_nc_out"
    EXPECTED_NC_OUT_FILT="log_loop_expected_nc_out_filt"

    LOG_LOOP_CFG="log_loop_config.json"
    LOG_LOOP_CFG_PORT=15539

    SED_TIMESTAMP_FILTER='s/"@timestamp": "[^"]*"//'

    cat "${EXPECTED_NC_OUT}" | sed "${SED_TIMESTAMP_FILTER}" > "${EXPECTED_NC_OUT_FILT}"

    nc -l "${LOG_LOOP_CFG_PORT}" | sed "${SED_TIMESTAMP_FILTER}" > "${TEMP_NC_OUT}" &
    NC_PROC="$!"
    
    "../recursid_multi${1}.py" "${LOG_LOOP_CFG}" 2> "${TEMP_OUT}"


    diff "${TEMP_OUT}" "${EXPECTED_OUT}"
    diff "${TEMP_NC_OUT}" "${EXPECTED_NC_OUT_FILT}"

    kill "${NC_PROC}" &> /dev/null
    rm "${EXPECTED_NC_OUT_FILT}" "${TEMP_OUT}" "${TEMP_NC_OUT}" &> /dev/null
}

function run_test {
    TEST_OUT=`test_one $1`
    if [ "$TEST_OUT" != "" ]; then
        echo "$1 Test Fail: "
        echo $TEST_OUT
        return 1
    else
        echo "$1 Test Success"
        return 0
    fi
}

echo "Beginning Integrated Testing"
run_test thread; RET1=$?
run_test process; RET2=$?
echo "Integrated Testing Complete"
if [[ "$RET1" == "0" ]] && [[ "$RET2" == "0" ]]; then
    exit 0
fi

exit 1
