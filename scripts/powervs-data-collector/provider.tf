provider "ibm" {
    version          = ">= 1.8.0"
    ibmcloud_api_key = var.ibmcloud_api_key
    region           = var.ibmcloud_region
    zone             = var.ibmcloud_zone
}

