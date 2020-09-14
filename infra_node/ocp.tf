provider "ibm" {
    ibmcloud_api_key = var.ibmcloud_api_key
    region           = var.ibmcloud_region
    zone             = var.ibmcloud_zone
}

module "prepare" {
    source                          = "./modules/1_prepare"

    bastion                         = var.bastion
    service_instance_id             = var.service_instance_id
    cluster_id                      = var.cluster_id
    rhel_image_name                 = var.rhel_image_name
    processor_type                  = var.processor_type
    system_type                     = var.system_type
    network_name                    = var.network_name
    rhel_username                   = var.rhel_username
    public_key                      = local.public_key
}
