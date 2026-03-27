#!/bin/bash

DIR=$1
RUN=$2

realpath ${DIR}/*.bin* | sed 's/$/,/' > list_of_files_run_${RUN}.txt
