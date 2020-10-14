# Misc Image Handling Scripts for PowerVS

- [Misc Image Handling Scripts for PowerVS](#misc-image-handling-scripts-for-powervs)
  - [Prerequisites](#prerequisites)
  - [Setup Repository](#setup-repository)
  - [Convert QCOW2 image to OVA](#convert-qcow2-image-to-ova)
    - [Running](#running)
  - [Upload Image to IBM Cloud Object Storage (COS)](#upload-image-to-ibm-cloud-object-storage-cos)
    - [Running](#running-1)
  - [Import Boot Images in PowerVS](#import-boot-images-in-powervs)
    - [Running](#running-2)


## Prerequisites

- Install `python3` package
  - Install `jinja2` & `boto3` modules with `pip3`
  - Upgrade `PyYAML` module to v5.1 or newer; see https://stackoverflow.com/questions/55551191/module-yaml-has-no-attribute-fullloader
- Install `qemu-img` package
- Install PowerVS (`power-iaas`) CLI; see https://cloud.ibm.com/docs/power-iaas-cli-plugin?topic=power-iaas-cli-plugin-power-iaas-cli-reference
- Ensure a minimum of 170 GB free disk space in /tmp (varies based on the resultant image size)


## Setup Repository

```
$ git clone https://github.com/ocp-power-automation/infra.git
$ cd infra/scripts/images
```


## Convert QCOW2 image to OVA

This script will help you to convert a QCOW2 image to OVA. OVA is the only supported image
format in PowerVS.

The script needs to be run on a Linux system with CPU arch matching the image architecture.
For example converting ppc64le images will require a ppc64le Linux system

### Running

```
$ python3 convert_qcow2_ova.py -u <imageUrl> -s <imageSize> -n <imageName> -d <imageDist> -U <rhUser> -P <rhPassword> -O <osPassword>
```
where:
```
-u:  URL pointing to the QCOW2 or the absolute local file path
-s:  Size(in Gb) of the image you want to create. Use min 120 GB for OpenShift images
-n:  Name of the ova image file
-d:  Image distribution; coreos, rhel, centos
-U:  Redhat Subscription username(for RHEL)
-P:  Redhat Subscription password(for RHEL)
-O:  OS Password (for RHEL and CentOS)
```

After successful run of the script, the OVA image file will be available in the current directory

**Note**:
 - URL must be pointing to a plain Qcow2 or gzipped Qcow2 image.
 - Use a strong password. Example use the following command to generate a password `openssl rand -base64 12`

#### RHEL/CentOS

##### Prerequisite
- Need a valid RedHat subscription for the RHEL image

##### Image Location

| Distro        | Location     |
| ------------- |-------------|
| RHEL 8.x Update KVM Guest Image |https://access.redhat.com/downloads/content/279/ver=/rhel---8/8.2/ppc64le/product-software|
| CentOS 8.x   |https://cloud.centos.org/centos/8/ppc64le/images/CentOS-8-GenericCloud-8.2.2004-20200611.2.ppc64le.qcow2|

##### How to run:
```shell script
# Generates the RHEL ova image of size 120GB with name rhel-82u2-ppc64le from downloaded rhel cloud image located at /root/rhel-8.2-update-2-ppc64le-kvm.qcow2
$ python3 convert_qcow2_ova.py -u /root/rhel-8.2-update-2-ppc64le-kvm.qcow2 -s 120 -n rhel-82u2-ppc64le -d rhel -U <rhUser> -P <rhPassword> -O <osPassword>
```

##### Note:
- Although the RHEL image is named KVM Guest Image, it works for both KVM and PowerVM.
- This script supports only official RHEL Cloud image(standard partitioning with two partitions) as of now

#### RHCOS(RedHat CoreOS)
##### Image Location
| Openshift Release | Location     |
| ------------- |-------------|
| 4.5.x |https://mirror.openshift.com/pub/openshift-v4/ppc64le/dependencies/rhcos/4.5/4.5.4/rhcos-4.5.4-ppc64le-openstack.ppc64le.qcow2.gz|
| 4.6.x(pre-release) |https://mirror.openshift.com/pub/openshift-v4/ppc64le/dependencies/rhcos/pre-release/4.6.0-0.nightly-ppc64le-2020-09-18-070611/rhcos-4.6.0-0.nightly-ppc64le-2020-09-18-070611-openstack.ppc64le.qcow2.gz|

##### How to run:
```shell script
# Generates the RHCOS ova image of size 120GB with name rhcos-454-ppc64le from downloaded rhcos image located at /root/rhcos-4.5.4-ppc64le-openstack.ppc64le.qcow2.gz
$ python3 convert_qcow2_ova.py -u /root/rhcos-4.5.4-ppc64le-openstack.ppc64le.qcow2.gz -s 120 -n rhcos-454-ppc64le -d coreos -U <rhUser> -P <rhPassword> -O <osPassword>
```

## Upload Image to IBM Cloud Object Storage (COS)

This script will help you to upload files (eg. OVA image) to IBM COS.
You'll need to create IBM COS bucket and required access keys.
The following links should help

- Instructions to create IBM Cloud Object Storage service and storage bucket: please refer to the following [link](https://cloud.ibm.com/docs/cloud-object-storage?topic=cloud-object-storage-getting-started-cloud-object-storage) for details.
- Instructions to create the bucket access and secret keys: please refer to the following [link](https://cloud.ibm.com/docs/cloud-object-storage?topic=cloud-object-storage-uhc-hmac-credentials-main) for details.
- Instructions to generate IBM Cloud API key: please refer to the following [link](https://cloud.ibm.com/docs/account?topic=account-userapikey)

Note:
- PowerVS currently only supports import from `us-east` , `us-south` and `eu-de` COS regions. Ensure you create COS service and bucket in one of these regions.


### Running

```
python3 upload_image.py -b <cosBucketName> -r <cosRegion> -f <fileUpload> -o <targetObjectName> -a <bucketAccessKey> -s <bucketSecretKey>
```

where:
```
-b: IBM COS Bucket name (eg. ocp-images-bucket)
-r: IBM COS Region (eg. us-south)
-f: File to upload (eg. rhcos0820.ova.gz)
-o: Target object name (eg. rhcos0820.ova.gz)
-a: IBM COS Bucket Access key
-s: IBM COS Bucket Secret key
```

Note:
- Please ensure that the `Target object name` follows the pattern `filename-without-dots.ova.gz`.
There is a bug in PowerVS which fails to import objects with names like `rhel8.0408.ova.gz`, `rhel.ppc64le.ova.gz`.

## Import Boot Images in PowerVS

This script will help you to import an image from IBM COS to PowerVS service instance.

### Running

```
$ python3 create_boot_images.py -a <bucketAccessKey> -s <bucketSecretKey> -i <imageManifestFile> -k <apiKey>
```

where:
```
-a: IBM COS Bucket Access key
-s: IBM COS Bucket Secret key
-i: YAML file describing the details
-k: IBM Cloud API key
```

Example image manifest file
```
---
- source:
    region: us-south
    bucket: ocp-images-bucket
    object: rhel0820.ova.gz
  target:
    imageName: rhel-8.2
    powerVSInstances:
      - ocp-powervs-frankfurt
```

