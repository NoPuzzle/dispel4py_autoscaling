#!/bin/bash

function run_experiment() {
    local val=$1
    LOGFILE="output_int_${val}.log"

    # Empty the log file first
    > $LOGFILE

    # Use the provided patterns for the four types of experiments
    declare -a patterns=("dyn_multi" "dyn_auto_multi" "dyn_redis" "dyn_auto_redis")

    for pattern in "${patterns[@]}"; do
        # Iterate over the number of processors for each pattern
        for n in 4 8 12 16; do
            echo "${pattern} : running with $n processors" >> $LOGFILE
            python -m dispel4py.new.processor $pattern int_ext_graph.py -d '{"read" : [ {"input" : "cp_coordinates_'$val'.txt"} ]}' -n $n >> $LOGFILE 2>&1
            echo "---------------------------------" >> $LOGFILE
        done
    done

    echo "Experiments for $val completed!" >> $LOGFILE
}

# Call the function for each desired value
# for i in 100 200 300; do
for i in 100; do
    run_experiment $i
done