# Guide to use automation script for conversion of qcow2 image to ova
This needs to be run on a Linux system with CPU arch matching the image architecture.
For example converting ppc64le images will require a ppc64le Linux system

## Requirements
- Install python (version 3 and above)
- Install qemu-img package 
- Ensure a minimum of 120 GB free disk space in /tmp
 
## Setup Repository
Clone this git repository on the client machine:
```
$ git clone https://github.com/ocp-power-automation/infra.git
$ cd infra/scripts/images
```

## Run script to convert qcow2 image to ova
```
python3 convert_qcow2_ova.py -u <imageUrl> -s <imageSize> -n <imageName> -d <imageDist> -U <rhUser> -P <rhPassword> -O <osPassword>
```
### where:
* `-u` *--imageUrl:*                 URL pointing to the qcow2.gz or the absolute local file path
* `-s` *--imageSize:*                Size(in Gb) of the image you want to create
* `-n` *--imageName:*                Name of the ova image file
* `-d` *--imageDist:*                Image distribution; coreos, rhel, centos
* `-U` *--rhUser:*                   Redhat Subscription username(for RHEL)
* `-P` *--rhPassword:*               Redhat Subscription password(for RHEL)
* `-O` *--osPassword:*               OS Password (for RHEL and CentOS)

After successful run of the automation script, the ova.gz file will be available in the current directory

## Note:
 - qemu-img binary should be available
 - URL must be pointing to an gziped qcow2 image
 - Machine should be having enough disk space to create intermediate images as well
 - For working with RHEL image, you should have redhat subscription
 - For RHEL image conversion, the triggering node should be ppc64le(chroot)
 - This script supports only official RHEL Cloud image(standard partitioning with two partitions) as of now
 - You can download the the RHEL cloud image(Red Hat Enterprise Linux 8.2 Update KVM Guest Image) from support 
   site(https://access.redhat.com/downloads/content/279/ver=/rhel---8/8.2/ppc64le/product-software)
 - You can get the CentOS image from https://cloud.centos.org/centos/8/ppc64le/images/CentOS-8-GenericCloud-8.2.2004-20200611.2.ppc64le.qcow2
