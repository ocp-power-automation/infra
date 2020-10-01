# powervs-data-collector

This collects the information regarding the number of VMs, Processors, Memory used by a given PowerVS service instance.


## Execution


```
export API_KEY=<YOUR IBM CLOUD API KEY> 

./collect.sh

```

or

```
export API_KEY=<YOUR IBM CLOUD API KEY>

./runner.sh API_KEY POWERVS_ID IBMCLOUD_REGION IBMCLOUD_ZONE --pretty

API_KEY, your IBM Cloud API Key.
POWERVS_ID, from ibmcloud resource service-instances --long.
IBMCLOUD_REGION, which IBM Cloud region to connect to, like lon.
IBMCLOUD_ZONE, which IBM Cloud zone to connect to, for instance eu-de-1, lon06.
```
