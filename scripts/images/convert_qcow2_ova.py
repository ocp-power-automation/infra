#!/usr/bin/env python3

import subprocess
import sys
import getopt
import gzip
import os
import tarfile
import urllib.request
import tempfile
import shutil
import stat
from urllib.parse import urlparse
from pathlib import Path
from jinja2 import Template



help_message = """convert_qcow2_ova.py -u <imageUrl> -s <imageSize> -n <imageName> -d <imageDist> -U <rhUser> -P <rhPassword> -O <osPassword>

-u, --imageUrl                 URL pointing to the qcow2.gz or the absolute local file path
-s, --imageSize                Size of the image you want to create
-n, --imageName                Name of the ova image file
-d, --imageDist                Image distribution; coreos, rhel, centos
-U, --rhUser                   Redhat Subscription username(for RHEL)
-P, --rhPassword               Redhat Subscription password(for RHEL)
-O, --osPassword               OS username (for RHEL and CentOS)

Note:
    - qemu-img binary should be available
    - URL must be pointing to an gziped qcow2 image
    - Machine should be having enough disk space to create intermediate images as well
    - For working with RHEL image, you should have redhat subscription
    - For RHEL image conversion, the triggering node should be ppc64le(chroot)
    - This script supports only official RHEL Cloud image(standard partitioning with two partitions) as of now
    - You can download the the RHEL cloud image(Red Hat Enterprise Linux 8.2 Update KVM Guest Image) 
        from support site(https://access.redhat.com/downloads/content/279/ver=/rhel---8/8.2/ppc64le/product-software)
    - You can get the CentOS image from https://cloud.centos.org/centos/8/ppc64le/images/CentOS-8-GenericCloud-8.2.2004-20200611.2.ppc64le.qcow2
"""

template_meta = """os-type = rhel
architecture = ppc64le
vol1-file = {{ imagename }}
vol1-type = boot"""

template_ovf = """<?xml version="1.0" encoding="UTF-8"?>
<ovf:Envelope xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1" xmlns:rasd="http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ovf:References>
    <ovf:File href="{{ volumename }}" id="file1" size="{{ volumesize }}"/>
  </ovf:References>
  <ovf:DiskSection>
    <ovf:Info>Disk Section</ovf:Info>
    <ovf:Disk capacity="{{ volumesize }}" capacityAllocationUnits="byte" diskId="disk1" fileRef="file1"/>
  </ovf:DiskSection>
  <ovf:VirtualSystemCollection>
    <ovf:VirtualSystem ovf:id="vs0">
      <ovf:Name>{{ imagename }}</ovf:Name>
      <ovf:Info></ovf:Info>
      <ovf:ProductSection>
        <ovf:Info/>
        <ovf:Product/>
      </ovf:ProductSection>
      <ovf:OperatingSystemSection ovf:id="79">
        <ovf:Info/>
        <ovf:Description>RHEL</ovf:Description>
        <ns0:architecture xmlns:ns0="ibmpvc">ppc64le</ns0:architecture>
      </ovf:OperatingSystemSection>
      <ovf:VirtualHardwareSection>
        <ovf:Info>Storage resources</ovf:Info>
        <ovf:Item>
          <rasd:Description>Temporary clone for export</rasd:Description>
          <rasd:ElementName>{{ volumename }}</rasd:ElementName>
          <rasd:HostResource>ovf:/disk/disk1</rasd:HostResource>
          <rasd:InstanceID>1</rasd:InstanceID>
          <rasd:ResourceType>17</rasd:ResourceType>
          <ns1:boot xmlns:ns1="ibmpvc">True</ns1:boot>
        </ovf:Item>
      </ovf:VirtualHardwareSection>
    </ovf:VirtualSystem>
    <ovf:Info/>
    <ovf:Name>{{ imagename }}</ovf:Name>
  </ovf:VirtualSystemCollection>
</ovf:Envelope>
"""

template_rhel_bash = """#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail
set -o xtrace
if [ "{{ distribution }}" == "rhel" ];then
    subscription-manager register --force --auto-attach --username={{ rh_sub_username }} --password={{ rh_sub_password }}
fi
yum update -y
yum install http://public.dhe.ibm.com/systems/virtualization/powervc/rhel8_cloud_init/cloud-init-19.1-8.ibm.el8.noarch.rpm -y
ln -s /usr/lib/systemd/system/cloud-init-local.service /etc/systemd/system/multi-user.target.wants/cloud-init-local.service
ln -s /usr/lib/systemd/system/cloud-init.service /etc/systemd/system/multi-user.target.wants/cloud-init.service
ln -s /usr/lib/systemd/system/cloud-config.service /etc/systemd/system/multi-user.target.wants/cloud-config.service
ln -s /usr/lib/systemd/system/cloud-final.service /etc/systemd/system/multi-user.target.wants/cloud-final.service

rm -rf /etc/systemd/system/multi-user.target.wants/firewalld.service

rpm -vih --nodeps http://public.dhe.ibm.com/software/server/POWER/Linux/yum/download/ibm-power-repo-latest.noarch.rpm
sed -i 's/^more \/opt\/ibm\/lop\/notice/#more \/opt\/ibm\/lop\/notice/g' /opt/ibm/lop/configure
echo 'y' | /opt/ibm/lop/configure
yum install  powerpc-utils librtas DynamicRM  devices.chrp.base.ServiceRM rsct.opt.storagerm rsct.core rsct.basic rsct.core src -y
sed -i 's/GRUB_CMDLINE_LINUX=.*$/GRUB_CMDLINE_LINUX="console=tty0 console=hvc0,115200n8  biosdevname=0  crashkernel=auto"/g' /etc/default/grub
grub2-mkconfig -o /boot/grub2/grub.cfg
rm -rf /etc/sysconfig/network-scripts/ifcfg-eth0
echo {{ root_password }} | passwd root --stdin
if [ "{{ distribution }}" == "rhel" ];then
    subscription-manager unregister
    subscription-manager clean
fi
touch /.autorelabel"""

template_cloud_config = """# The top level settings are used as module
# and system configuration.

# A set of users which may be applied and/or used by various modules
# when a 'default' entry is found it will reference the 'default_user'
# from the distro configuration specified below
users:
   - default

# If this is set, 'root' will not be able to ssh in and they
# will get a message to login instead as the default $user
disable_root: false

mount_default_fields: [~, ~, 'auto', 'defaults,nofail', '0', '2']
resize_rootfs_tmp: /dev
ssh_pwauth:   0

# This will cause the set+update hostname module to not operate (if true)
preserve_hostname: false

# Example datasource config
# datasource:
#    Ec2:
#      metadata_urls: [ 'blah.com' ]
#      timeout: 5 # (defaults to 50 seconds)
#      max_wait: 10 # (defaults to 120 seconds)

datasource_list: [ ConfigDrive, None ]
datasource:
  ConfigDrive:
    dsmode: local

# The modules that run in the 'init' stage
cloud_init_modules:
 - migrator
 - seed_random
 - bootcmd
 - write-files
 - growpart
 - resizefs
 - disk_setup
 - mounts
 - set_hostname
 - update_hostname
 - update_etc_hosts
 - ca-certs
 - rsyslog
 - users-groups
 - ssh

# The modules that run in the 'config' stage
cloud_config_modules:
 - reset_rmc
 - ssh-import-id
 - locale
 - set-passwords
 - spacewalk
 - yum-add-repo
 - ntp
 - timezone
 - disable-ec2-metadata
 - runcmd

# The modules that run in the 'final' stage
cloud_final_modules:
 - package-update-upgrade-install
 - puppet
 - chef
 - mcollective
 - salt-minion
 - rightscale_userdata
 - scripts-vendor
 - scripts-per-once
 - scripts-per-boot
 - scripts-per-instance
 - scripts-user
 - ssh-authkey-fingerprints
 - keys-to-console
 - phone-home
 - final-message
 - power-state-change

# System and/or distro specific settings
# (not accessible to handlers/transforms)
system_info:
   # This will affect which distro class gets used
   distro: rhel
   # Default user name + that default users groups (if added/used)
   default_user:
     name: rhel
     lock_passwd: True
     gecos: rhel Cloud User
     groups: [wheel, adm, systemd-journal]
     sudo: ["ALL=(ALL) NOPASSWD:ALL"]
     shell: /bin/bash
   # Other config here will be given to the distro class and/or path classes
   paths:
      cloud_dir: /var/lib/cloud/
      templates_dir: /etc/cloud/templates/
   ssh_svcname: sshd"""


def exec_cmd(cmd):
    execute = subprocess.run([cmd], shell=True, universal_newlines=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return execute.stdout, execute.stderr, execute.returncode

def gzip_gunzip(sfile, dfile, block_size=65536):
    with gzip.open(sfile, 'rb') as s_file, open(dfile, 'wb') as d_file:
        while True:
            block = s_file.read(block_size)
            if not block:
                break
            else:
                d_file.write(block)

def gzip_gzip(sfile, dfile, block_size=65536):
    with gzip.open(dfile, 'wb') as d_file, open(sfile, 'rb') as s_file:
        while True:
            block = s_file.read(block_size)
            if not block:
                break
            else:
                d_file.write(block)

def get_image_name(image_url):
    a = urlparse(image_url)
    return (os.path.basename(a.path))

def get_image(image_url, image_file):
    with urllib.request.urlopen(image_url) as response, open(image_file, 'wb') as out_file:
        data = response.read() # a `bytes` object
        out_file.write(data)

def remove_extn(file_path):
    return os.path.splitext(file_path)[0]

def get_file_size(image_file):
    return Path(image_file).stat().st_size

def create_tar(image_file_source, image_file_path):
    with tarfile.open( image_file_path, "w" ) as tar:
        os.chdir(image_file_source)
        for name in os.listdir('.'):
            tar.add(name)

def prepare_rhel(extracted_raw_file_path, tmpdir, rhUser, rhPassword, osPassword, imageDist):
    mount_dir = tmpdir + '/' + 'tempMount'
    rhel_bash_file = mount_dir  + '/' + 'rhel_bash.sh'
    rhel_cloud_config_file = mount_dir  + '/etc/cloud/' + 'cloud.cfg'
    real_root = os.open("/", os.O_RDONLY)
    os.mkdir(mount_dir) # Temporary mount directory
    print("Getting a free loop device ...")
    cmd = 'losetup --nooverlap  --partscan  -f ' + extracted_raw_file_path
    out, err, ret = exec_cmd(cmd)
    if ret != 0:
        print('ERROR: Failed to get a free loop device:', err)
        sys.exit(2)
    cmd = 'losetup -l --output NAME,BACK-FILE | grep ' + extracted_raw_file_path + '| awk \'{print $1}\' '
    out, err, ret = exec_cmd(cmd)
    if ret != 0:
        print('ERROR: Getting loop device name failed:', err)
        sys.exit(2)

    loop_device = out.rstrip()

    print("probing partition table ...")
    cmd = 'partprobe ' + loop_device
    out, err, ret = exec_cmd(cmd)
    if ret != 0:
        print('ERROR: Getting loop device name failed:', err)
        sys.exit(2)

    try:
        print("mounting the loop device ...")
        cmd = 'mount ' + loop_device + 'p2' + ' ' + mount_dir
        out, err, ret = exec_cmd(cmd)
        if ret != 0:
            print('ERROR: Failed mounting the device:', err)
            sys.exit(2)
        for sdir in ('/proc', '/dev', '/sys', '/var/run/', '/etc/machine-id'):
            cmd = 'mount -o bind ' + sdir + ' ' + mount_dir + sdir
            out, err, ret = exec_cmd(cmd)
            if ret != 0:
                print('ERROR: Failed mounting the device:', err)
                sys.exit(2)

        rhel_bash_template = Template(template_rhel_bash)
        rhel_bash = rhel_bash_template.render(rh_sub_username=rhUser, rh_sub_password=rhPassword, root_password=osPassword, distribution=imageDist )
        with open(rhel_bash_file, "w") as stream:
            stream.write(rhel_bash)
        st = os.stat(rhel_bash_file)
        os.chmod(rhel_bash_file, st.st_mode | stat.S_IEXEC)

        rhel_cloud_config_template = Template(template_cloud_config)
        rhel_cloud_config = rhel_cloud_config_template.render()
        with open(rhel_cloud_config_file, "w") as stream:
            stream.write(rhel_cloud_config)

        os.chroot(mount_dir)
        os.chdir('/')

        print("Running script ...")
        cmd = './rhel_bash.sh'
        out, err, ret = exec_cmd(cmd)
        print("shell script :", out)
        if ret != 0:
            print('ERROR: failed to run the script:', err)
            sys.exit(2)

    finally:
        os.fchdir(real_root)
        os.chroot('.')
        os.close(real_root)
        print("Unmounting all")
        for sdir in ('/proc', '/dev', '/sys', '/var/run/', '/etc/machine-id'):
            cmd = 'umount ' + mount_dir + sdir
            out, err, ret = exec_cmd(cmd)
            if ret != 0:
                print('ERROR: Failed to unmount the device:', err)

        cmd = 'umount ' + mount_dir
        out, err, ret = exec_cmd(cmd)
        if ret != 0:
            print('ERROR: Failed to unmount device:', err)

        print("Freeing up loop device")
        cmd = 'losetup -d ' + loop_device
        out, err, ret = exec_cmd(cmd)
        if ret != 0:
            print('ERROR: Failed to release the device:', err)



def convert_qcow2_ova(imageUrl, imageSize, imageName, imageDist, rhUser, rhPassword, osPassword):
    current_dir = os.getcwd()
    tmpdir = tempfile.mkdtemp() # Temporary work directory
    image_file_name = get_image_name(imageUrl) # Get image file name from url
    image_file_path = tmpdir + '/' + image_file_name 
    extracted_qcow2_file_path = tmpdir + '/' + remove_extn(image_file_name)
    converted_images_dir = tmpdir + '/' + "image"
    extracted_raw_file_path =  converted_images_dir + '/' + remove_extn(remove_extn(image_file_name))
    meta_data_file = converted_images_dir + '/' + imageName + '.meta'
    ovf_data_file = converted_images_dir + '/' + imageName + '.ovf'
    ova_image_file = tmpdir + '/' + imageName + '.ova'
    ova_gz_image_file = tmpdir + '/' + imageName + '.ova.gz' 

    try:
        os.mkdir(converted_images_dir) # Target directory to keep volume, meta and ovf files
        if imageUrl.startswith('http://') or imageUrl.startswith('https://'):
            print("Download image.......")
            get_image(imageUrl, image_file_path )
        else:
            shutil.copyfile(imageUrl, image_file_path)
        if image_file_path.endswith(".gz"):
            print("Extracting gz image...")
            gzip_gunzip(image_file_path, extracted_qcow2_file_path, 65536)
        else:
            extracted_qcow2_file_path = image_file_path

        print("Converting to raw ....")
        cmd =  'qemu-img convert -f qcow2 -O raw ' + extracted_qcow2_file_path  + '  ' + extracted_raw_file_path
        out, err, ret = exec_cmd(cmd)
        if ret != 0:
            print('ERROR: problem converting file (do you have qemu-img installed?)')
            sys.exit(2)
        if imageDist == 'rhel' or  imageDist == 'centos':
            print("Preparing rhel image...")
            prepare_rhel(extracted_raw_file_path, tmpdir, rhUser, rhPassword, osPassword, imageDist)

        print("Resizing image ....")
        cmd = 'qemu-img resize ' + extracted_raw_file_path + ' ' + imageSize + 'G'
        out, err, ret = exec_cmd(cmd)
        if ret != 0:
            print('ERROR: Resizing failed')
            sys.exit(2)

        print("Getting new image size...")
        volumesize = get_file_size(extracted_raw_file_path)

        print("Preparing meta data file...")
        meta_data_template = Template(template_meta)
        meta_data = meta_data_template.render(imagename=imageName)
        with open(meta_data_file, "w") as stream:
            stream.write(meta_data)

        print("Preparing ovf data file...")
        ovf_data_template = Template(template_ovf)
        ovf_data = ovf_data_template.render(imagename=imageName, volumesize=volumesize, volumename=remove_extn(remove_extn(image_file_name)))
        with open(ovf_data_file, "w") as stream:
            stream.write(ovf_data)

        print("Creating ova image...")
        create_tar(converted_images_dir, ova_image_file)

        print("Compressing ova file...")
        gzip_gzip(ova_image_file, ova_gz_image_file)


        shutil.move(ova_gz_image_file, current_dir)
    finally:
        shutil.rmtree(tmpdir)

    
def main(argv):
    ImageUrl = ''
    imageSize = ''
    imageName = ''
    try:
        (opts, args) = getopt.getopt(argv, 'hu:s:n:d:U:P:O:', [
            'imageUrl=',
            'imageSize=',
            'imageName=',
            'imageDist',
            'rhUser',
            'rhPassword',
            'osPassword'
        ])
    except getopt.GetoptError:
        print(help_message)
        sys.exit(2)
    for (opt, arg) in opts:
        if opt == '-h':
            print(help_message)
            sys.exit()
        elif opt in ('-u', '--ImageUrl'):
            ImageUrl = arg
        elif opt in ('-s', '--imageSize'):
            imageSize = arg
        elif opt in ('-n', '--imageName'):
            imageName = arg
        elif opt in ('-d', '--imageDist'):
            imageDist = arg
        elif opt in ('-U', '--rhUser'):
            rhUser = arg
        elif opt in ('-P', '--rhPassword'):
            rhPassword = arg
        elif opt in ('-O', '--osPassword'):
            osPassword = arg
    if imageDist == 'rhel' and ( rhUser is None or rhPassword is None or osPassword is None ):
        print("Please set rhUser,rhPassword, and osPassword")
        sys.exit(2)
    if imageDist == 'coreos' and ( ImageUrl is None or imageSize is None or imageName is None ):
        print("Please set ImageUrl, imageSize, and imageName")
        sys.exit(2)
    if imageDist == 'centos' and ( ImageUrl is None or imageSize is None or imageName is None or osPassword is None ):
        print("Please set ImageUrl, imageSize, osPassword and imageName")
        sys.exit(2)
    
    convert_qcow2_ova(ImageUrl, imageSize, imageName, imageDist, rhUser, rhPassword, osPassword)


if __name__ == '__main__':
    main(sys.argv[1:])
