#!/bin/bash

set -e
set -o pipefail

echo "process started"
echo "Start: vfb-pipeline-dumps"
echo "VFBTIME:"
date

## get remote configs
echo "Sourcing remote config"
source ${CONF_DIR}/config.env

export ROBOT_JAVA_ARGS=${ROBOT_ARGS}
export OUTDIR=/out
export RAW_DUMPS_DIR=$OUTDIR/raw
export FINAL_DUMPS_DIR=$OUTDIR/dumps
export SPARQL_DIR=$CONF_DIR/sparql
export SCRIPTS_DIR=$WORKSPACE/scripts
export VFB_CONFIG=${VFB_CONFIG}
export SPARQL_ENDPOINT=${SPARQL_ENDPOINT}
export DUMPS_SOLR=${DUMPS_SOLR}
export DUMPS_PDB=${DUMPS_PDB}
export DUMPS_OWLERY=${DUMPS_OWLERY}


echo "** Creating temporary directories.. **"
cd ${WORKSPACE}
mkdir -p $FINAL_DUMPS_DIR $RAW_DUMPS_DIR
find $FINAL_DUMPS_DIR -type f -delete
find $RAW_DUMPS_DIR -type f -delete

echo "VFBTIME:"
date

echo '** Executing pipeline.. **'

make all

echo "End: vfb-pipeline-dumps"
echo "VFBTIME:"
date
echo "process complete"
