################################################################
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Licensed Materials - Property of IBM
#
# ©Copyright IBM Corp. 2020
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################

################################################################
# Configure the IBM Cloud provider
################################################################
variable "ibmcloud_api_key" {
    description = "IBM Cloud API key associated with user's identity"
    default = "<key>"
}

variable "service_instance_id" {
    description = "The cloud instance ID of your account"
    default = ""
}

variable "ibmcloud_region" {
    description = "The IBM Cloud region where you want to create the resources"
    default = ""
}

variable "ibmcloud_zone" {
    description = "The zone of an IBM Cloud region where you want to create Power System resources"
    default = ""
}

################################################################
# Configure the Instance details
################################################################

variable "bastion" {
    # only one node is supported
    default = {
        count       = 1
        memory      = "16"
        processors  = "1"
    }
    validation {
        condition       = lookup(var.bastion, "count", 1) >= 1 && lookup(var.bastion, "count", 1) <= 2
        error_message   = "The bastion.count value must be either 1 or 2."
    }
}


variable "rhel_image_name" {
    description = "Name of the RHEL image that you want to use for the bastion node"
    default = "rhel-8.2"
}

variable "processor_type" {
    description = "The type of processor mode (shared/dedicated)"
    default = "shared"
}

variable "system_type" {
    description = "The type of system (s922/e980)"
    default = "s922"
}

variable "network_name" {
    description = "The name of the network to be used for deploy operations"
    default = "my_network_name"
}

variable "rhel_username" {
    default = "root"
}

variable "public_key_file" {
    description = "Path to public key file"
    # if empty, will default to ${path.cwd}/data/id_rsa.pub
    default     = "data/id_rsa.pub"
}

variable "private_key_file" {
    description = "Path to private key file"
    # if empty, will default to ${path.cwd}/data/id_rsa
    default     = "data/id_rsa"
}

variable "private_key" {
    description = "content of private ssh key"
    # if empty string will read contents of file at var.private_key_file
    default = ""
}

variable "public_key" {
    description = "Public key"
    # if empty string will read contents of file at var.public_key_file
    default     = ""
}

variable "rhel_subscription_username" {
    default = ""
}

variable "rhel_subscription_password" {
    default = ""
}

variable "rhel_smt" {
    description = "SMT value to set on the bastion node. Eg: on,off,2,4,8"
    default = 4
}

################################################################
### Instrumentation
################################################################
variable "ssh_agent" {
    description = "Enable or disable SSH Agent. Can correct some connectivity issues. Default: false"
    default     = false
}

variable "pull_secret_file" {
    default   = "data/pull-secret.txt"
}

variable "dns_forwarders" {
    default   = "8.8.8.8; 8.8.4.4"
}

locals {
    private_key_file    = var.private_key_file == "" ? "${path.cwd}/data/id_rsa" : var.private_key_file
    public_key_file     = var.public_key_file == "" ? "${path.cwd}/data/id_rsa.pub" : var.public_key_file
    private_key         = var.private_key == "" ? file(coalesce(local.private_key_file, "/dev/null")) : var.private_key
    public_key          = var.public_key == "" ? file(coalesce(local.public_key_file, "/dev/null")) : var.public_key
}

# Must consist of lower case alphanumeric characters, '-' or '.', and must start and end with an alphanumeric character
# Should not be more than 14 characters
variable "vm_id_prefix" {
    default   = "infra-node"
}
# Must consist of lower case alphanumeric characters, '-' or '.', and must start and end with an alphanumeric character
# Length cannot exceed 14 characters when combined with cluster_id_prefix
variable "vm_id" {
    default   = ""
}
