# Installation Quickstart

- [Installation Quickstart](#installation-quickstart)
  - [Download the Automation Code](#download-the-automation-code)
  - [Setup Terraform Variables](#setup-terraform-variables)
  - [Start Deployment](#start-deployment)
  - [Clean up](#clean-up)


## Download the Automation Code

You'll need to use git to clone the deployment code when working off the master branch

```
$ git clone https://github.com/ocp-power-automation/infra.git
$ cd infra/infra-node
```

All further instructions assumes you are in the code directory eg. `infra/infra-node`

## Setup Terraform Variables

Update the [var.tfvars](./var.tfvars) based on your environment.
You can use environment variables for sensitive data that should not be saved to disk.

```
$ set +o history
$ export IBMCLOUD_API_KEY=xxxxxxxxxxxxxxx
$ export RHEL_SUBS_USERNAME=xxxxxxxxxxxxxxx
$ export RHEL_SUBS_PASSWORD=xxxxxxxxxxxxxxx
$ set -o history
```

These set of variables specify the VM capacity and count

Change the values as per your requirement.
The defaults (recommended config) should suffice for most of the common use-cases.
```
bastion     = {memory      = "16",   processors  = "1",    "count"   = 1}
```
These set of variables specify the RHEL boot image names. These images should have been already imported in your PowerVS service instance.
```
rhel_image_name     = "<rhel_or_centos_image-name>"
```
This variable specifies the name of the private network that is configured in your PowerVS service instance.
```
network_name        = "ocp-net"
```
This variables specifies the VM name.
Edit it as per your requirements.
```
vm_id_prefix           = "infra-node"
vm_id                  = ""
```
These set of variables specify the type of processor and physical system type to be used for the VMs.
Change the default values according to your requirement.
```
processor_type      = "shared"  #Can be shared or dedicated
system_type         = "s922"    #Can be either s922 or e980
```

These set of variables specify the username and the SSH key to be used for accessing the bastion node.
```
rhel_username               = "root"
public_key_file             = "data/id_rsa.pub"
private_key_file            = "data/id_rsa"
```
Please note that only OpenSSH formatted keys are supported. Refer to the following links for instructions on creating SSH key based on your platform.
- Windows 10 - https://phoenixnap.com/kb/generate-ssh-key-windows-10
- Mac OSX - https://www.techrepublic.com/article/how-to-generate-ssh-keys-on-macos-mojave/
- Linux - https://www.siteground.com/kb/generate_ssh_key_in_linux/

Create the SSH key-pair and keep it under the `data` directory

These set of variables specify the RHEL subscription details.
This is sensitive data, and if you don't want to save it on disk, use environment variables `RHEL_SUBS_USERNAME` and `RHEL_SUBS_PASSWORD` and pass them to `terraform apply` command as shown in the [Quickstart guide](./quickstart.md#setup-terraform-variables).
If you are using CentOS as the bastion image, then leave these variables as-is.

```
rhel_subscription_username  = "user@test.com"
rhel_subscription_password  = "mypassword"
```

This variable specifies the number of hardware threads (SMT) that's used for the bastion node.
Default setting should be fine for majority of the use-cases.

```
rhel_smt                    = 4
```

## Start Deployment

Run the following commands from within the directory.

```
$ terraform init
$ terraform apply -var-file var.tfvars
```
If using environment variables for sensitive data, then do the following, instead.
```
$ terraform init
$ terraform apply -var-file var.tfvars -var ibmcloud_api_key="$IBMCLOUD_API_KEY" -var rhel_subscription_username="$RHEL_SUBS_USERNAME" -var rhel_subscription_password="$RHEL_SUBS_PASSWORD"
```

Now wait for the installation to complete. It may take around 30 mins to complete provisioning.

On successful install cluster details will be printed as shown below.
```
bastion_private_ip = 192.168.200.57
bastion_public_ip = 128.168.101.66
bastion_ssh_command = ssh -i data/id_rsa root@128.168.101.66
```

These details can be retrieved anytime by running the following command from the root folder of the code
```
$ terraform output
```


## Clean up

To destroy after you are done using the cluster you can run command `terraform destroy -var-file var.tfvars` to make sure that all resources are properly cleaned up.
Do not manually clean up your environment unless both of the following are true:

1. You know what you are doing
2. Something went wrong with an automated deletion.
