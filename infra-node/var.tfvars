### IBM Cloud details

ibmcloud_api_key            = "<key>"
ibmcloud_region             = "<region>"
ibmcloud_zone               = "<zone>"
service_instance_id         = "<cloud_instance_ID>"

### VM Details
vm_id_prefix = "infra-node"
vm_id        = ""

### This is default minimalistic config. For PowerVS processors are equal to entitled physical count
### So N processors == N physical core entitlements == ceil[N] vCPUs.
### Example 0.5 processors == 0.5 physical core entitlements == ceil[0.5] = 1 vCPU == 8 logical OS CPUs (SMT=8)
### Example 1.5 processors == 1.5 physical core entitlements == ceil[1.5] = 2 vCPU == 16 logical OS CPUs (SMT=8)
### Example 2 processors == 2 physical core entitlements == ceil[2] = 2 vCPU == 16 logical OS CPUs (SMT=8)
bastion                     = {memory      = "16",   processors  = "1",    "count"   = 1}

rhel_image_name             = "rhel-83-11242020"
processor_type              = "shared"
system_type                 = "s922"
network_name                = "ocp-net"

rhel_username               = "root"
public_key_file             = "data/id_rsa.pub"
private_key_file            = "data/id_rsa"
rhel_subscription_username  = "<subscription-id>"          #Leave this as-is if using CentOS as bastion image
rhel_subscription_password  = "<subscription-password>"    #Leave this as-is if using CentOS as bastion image
rhel_smt                    = 4
