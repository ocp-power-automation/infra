#/bin/bash

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

DEPENDENCIES=(terraform ibmcloud jq awk)

for i in "${DEPENDENCIES[@]}"
do
	if ! command -v $i &> /dev/null; then
    		echo "$i could not be found, exiting!"
    		exit
	else
		echo "$i found!"
	fi
done

# Define the variables used during the execution
TODAY=$(date +'%m%d%Y')
TMP_FILE_NAME="powervs_instances_$TODAY"
POWERVSINSTANCES_LOG="/tmp/$TMP_FILE_NAME.log"
TERRAFORM_LOG="/tmp/$TMP_FILE_NAME.json"
CSV_FILE="/tmp/$TMP_FILE_NAME.csv"
TOTAL_LON=0
TOTAL_DE=0
TOTAL_TOR=0
TOTAL_SYD=0
> $TERRAFORM_LOG
> $POWERVSINSTANCES_LOG
> $CSV_FILE

# IBM Cloud Login
echo "Connecting to IBM Cloud..."
ibmcloud login --no-region --apikey $API_KEY > /dev/null 2>&1

# Terraform Init
echo "Starting Terraform..."
terraform init > /dev/null 2>&1

# Collect the all the services in a given IBM Cloud account
echo "Collecting PowerVS raw data from IBM Cloud..."
ibmcloud resource service-instances --long --output json | jq '.[] | "\(.guid),\(.name),\(.region_id),\(.id)"' | tr -d "\"" >> $POWERVSINSTANCES_LOG

while read line; do
	SID=$(echo "$line" | awk '{split($0,a,","); print a[1]}')
	SNAME=$(echo "$line" | awk '{split($0,a,","); print a[2]}')
	SLOC=$(echo "$line" | awk '{split($0,a,","); print a[3]}')
	STYPE=$(echo "$line" | awk '{split($0,a,","); print a[4]}' | awk '{split($0,a,":"); print a[5]}')

	#TODO: add US
	if [[ $SLOC == *"lon"* ]]; then
    		SREG="lon"
		((TOTAL_LON=TOTAL_LON+1))
	elif [[ $SLOC == *"de"* ]]; then
    		SREG="eu-de"
		((TOTAL_DE=TOTAL_DE+1))
	elif [[ $SLOC == *"tor"* ]]; then
		SREG="tor"
		((TOTAL_TOR=TOTAL_TOR+1))
	elif [[ $SLOC == *"syd"* ]]; then
        	SREG="syd"
		((TOTAL_SYD=TOTAL_SYD+1))
	else
   		SREG="none"
	fi

	if [[ $STYPE == "power-iaas" ]]; then
		#echo $API_KEY $SID $SREG $SLOC "$SNAME" "$TERRAFORM_LOG" "$CSV_FILE"
		./runner.sh $API_KEY $SID $SREG $SLOC "$SNAME" "$TERRAFORM_LOG" "$CSV_FILE" "$*"
    fi
done < $POWERVSINSTANCES_LOG

# Processing the data collected
echo "Processing the raw data..."
mv $CSV_FILE ./
cat ./"$TMP_FILE_NAME.csv" | grep -v '^null' >> ./"$TMP_FILE_NAME-tmp.csv"
mv ./"$TMP_FILE_NAME-tmp.csv" ./"$TMP_FILE_NAME.csv"

TOTAL_INSTANCES=$(awk -F"," '{x+=$4}END{print x}' ./$TMP_FILE_NAME.csv)
TOTAL_PROCESSORS=$(awk -F"," '{x+=$5}END{print x}' ./$TMP_FILE_NAME.csv)
TOTAL_MEMORY=$(awk -F"," '{x+=$6}END{print x}' ./$TMP_FILE_NAME.csv)
TOTAL_TIER1=$(awk -F"," '{x+=$7}END{print x}' ./$TMP_FILE_NAME.csv)
TOTAL_TIER2=$(awk -F"," '{x+=$8}END{print x}' ./$TMP_FILE_NAME.csv)

# Sort the CSV file by the amount of memory and remove lines starting with null (which means regions not yet explored)
sort -t "," --key 6 --numeric-sort ./$TMP_FILE_NAME.csv | grep -v '^null' >> $TMP_FILE_NAME-sorted.csv

# Sets the header for the csv file
echo "PowerVS ID,PowerVS Name,PowerVS Region,Number of Instances,Allocated Processors,Allocated Memory,TIER1 Usage,TIER3 Usage\n$(cat $TMP_FILE_NAME-sorted.csv)" > $TMP_FILE_NAME-sorted.csv

# Add the total at the end of the sorted .csv
echo "******,******,******,******,******,******,******,******" >> $TMP_FILE_NAME-sorted.csv
echo "Total Instances: $TOTAL_INSTANCES,Total Processors: $TOTAL_PROCESSORS,Total Memory: $TOTAL_MEMORY,Total TIER1: $TOTAL_TIER1,Total TIER2: $TOTAL_TIER2,******,******,******" >> $TMP_FILE_NAME-sorted.csv
echo "Total PowerVS in London: $TOTAL_LON, Total PowerVS in Deutschland: $TOTAL_DE, Total  PowerVS in Toronto: $TOTAL_TOR, Total PowerVS in Sydney: $TOTAL_SYD,******,******,******,******" >> $TMP_FILE_NAME-sorted.csv

echo "Done!"
ls | grep ".csv"

# Cleanup
rm -rf ./.terraform
rm -f ./terraform.tfstate
rm -f ./terraform.tfstate.backup
rm -f $POWERVSINSTANCES_LOG
rm -f $TERRAFORM_LOG
