variable "ibmcloud_api_key" {
    description = "Denotes the IBM Cloud API key to use"
}
variable "power_instance_id" {
    #ibmcloud resource service-instances --long field
    description = "Power Virtual Server instance ID associated with your IBM Cloud account (note that this is NOT the API key)"
}

variable "ibmcloud_region" {
    description = "Denotes which IBM Cloud region to connect to"
}

variable "ibmcloud_zone" {
    description = "Denotes which IBM Cloud zone to connect to - .i.e: eu-de-1 eu-de-2  us-south etc."
}

