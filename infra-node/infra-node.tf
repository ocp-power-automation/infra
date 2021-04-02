provider "ibm" {
    ibmcloud_api_key = var.ibmcloud_api_key
    region           = var.ibmcloud_region
    zone             = var.ibmcloud_zone
}

resource "random_id" "label" {
    count = var.vm_id == "" ? 1 : 0
    byte_length = "2" # Since we use the hex, the word lenght would double
    prefix = "${var.vm_id_prefix}-"
}

locals {
    # Generates vm_id as combination of vm_id_prefix + (random_id or user-defined vm_id)
    vm_id      = var.vm_id == "" ? random_id.label[0].hex : "${var.vm_id_prefix}-${var.vm_id}"
}

module "prepare" {
    source                          = "github.com/ocp-power-automation/ocp4-upi-powervs//modules/1_prepare"

    bastion                         = var.bastion
    service_instance_id             = var.service_instance_id
    cluster_id                      = local.vm_id
    cluster_domain                  = ""
    rhel_image_name                 = var.rhel_image_name
    processor_type                  = var.processor_type
    system_type                     = var.system_type
    network_name                    = var.network_name
    #Specify dns for public network. Trim spaces that may be present in splitted values.
    network_dns                     = var.dns_forwarders == "" ? [] : [for dns in split(";", var.dns_forwarders): trimspace(dns)]
    rhel_username                   = var.rhel_username
    private_key                     = local.private_key
    public_key                      = local.public_key
    ssh_agent                       = var.ssh_agent
    rhel_subscription_username      = var.rhel_subscription_username
    rhel_subscription_password      = var.rhel_subscription_password
    rhel_subscription_org           = ""
    rhel_subscription_activationkey = ""
    rhel_smt                        = var.rhel_smt
    storage_type                    = var.storage_type
    volume_size                     = var.volume_size
    volume_shareable                = var.volume_shareable
    setup_squid_proxy               = false
    proxy                           = {}
    ansible_repo_name               = "ansible-2.9-for-rhel-8-ppc64le-rpms"
    bastion_health_status           = var.bastion_health_status
}
