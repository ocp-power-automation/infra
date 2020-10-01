#!/bin/bash

: '
Copyright (C) 2020 IBM Corporation
Licensed under the Apache License, Version 2.0 (the “License”);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an “AS IS” BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
    Rafael Sene <rpsene@br.ibm.com> - Initial implementation.
'
# Trap ctrl-c and call ctrl_c()
trap ctrl_c INT

function ctrl_c() {
        echo "Bye!"
}

# Variables
TODAY=$(date +'%m%d%Y')
API_KEY="$1"
POWERVS_ID="$2"
IBMCLOUD_REGION="$3"
IBMCLOUD_ZONE="$4"
PVSNAME="$5"
TERRAFORM_LOG="$6"
CSV_FILE="$7"

if [ $# -eq 0 ]
  then
    echo "Please, set the correct parameters to run this script."
    exit
fi

# Check if key vars are empty:
if [ -z "$API_KEY" ]; then
    echo "Please set API_KEY."
    exit
fi
if [ -z "$POWERVS_ID" ]; then
    echo "Please set POWERVS_ID."
    exit
fi
if [ -z "$IBMCLOUD_REGION" ]; then
    echo "Please set IBMCLOUD_REGION."
    exit
fi
if [ -z "$IBMCLOUD_ZONE" ]; then
    echo "Please set IBMCLOUD_ZONE."
    exit
fi

echo "> collecting data from $PVSNAME ($IBMCLOUD_REGION)..."
> $TERRAFORM_LOG

# Run Terraform
terraform apply -auto-approve -var ibmcloud_api_key=$API_KEY -var power_instance_id=$POWERVS_ID -var ibmcloud_region=$IBMCLOUD_REGION -var ibmcloud_zone=$IBMCLOUD_ZONE > /dev/null 2>&1

# Convert output to JSON
terraform output -json >> $TERRAFORM_LOG

# Parse the JSON
ID=$(cat $TERRAFORM_LOG | jq -r '.powervs_id.value')
REGION=$(cat $TERRAFORM_LOG | jq -r '.region.value')
NINSTANCES=$(cat $TERRAFORM_LOG | jq -r  '.instance_count.value')
PROCESSORS=$(cat $TERRAFORM_LOG | jq -r '.instance_processors.value')
MEMORY=$(cat $TERRAFORM_LOG | jq -r '.instance_memory.value')
TIER1=$(cat $TERRAFORM_LOG | jq -r '.instance_ssd.value')
TIER3=$(cat $TERRAFORM_LOG | jq -r '.instance_standard.value')
INSTANCES=$(cat $TERRAFORM_LOG | jq -rc '.pvm_instances.value')

# Print the values
echo "$ID,$PVSNAME,$REGION,$NINSTANCES,$PROCESSORS,$MEMORY,$TIER1,$TIER3" >> $CSV_FILE

if [[ "$*" == *--pretty* ]]; then
    # Pretty-print values
    echo "*********************************************"
    echo "PowerVS Name: $PVSNAME"
    echo "PowerVS ID: $ID"
    echo "Region: $REGION"
    echo "Number of instances: $NINSTANCES"
    echo "Number of processors: $PROCESSORS"
    echo "Amount of memory: $MEMORY"
    echo "Amount of Tier1 storage: $TIER1"
    echo "Amount of Tier3 storage: $TIER3"
    if [[ $NINSTANCES -gt 0  &&  "$NINSTANCES" != "null" ]]; then
        echo -e "Instances:\n"
        for row in $(echo "${INSTANCES}" | jq -r '.[] | @base64'); do
            INAME=$(echo "${row}" | base64 --decode | jq -r '.[].name')
            printf '%s\n' $INAME
        done
    fi
    echo "*********************************************"
fi

# Destroy the resources
terraform destroy -auto-approve -var ibmcloud_api_key=$API_KEY -var power_instance_id=$POWERVS_ID -var ibmcloud_region=$IBMCLOUD_REGION -var ibmcloud_zone=$IBMCLOUD_ZONE > /dev/null 2>&1
