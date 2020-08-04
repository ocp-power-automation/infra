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
from urllib.parse import urlparse
from pathlib import Path
from jinja2 import Template



help_message = """convert_qcow2_ova.py -u <imageUrl> -s <imageSize> -n <imageName>

-u, --imageUrl                 URL pointing to the qcow2.gz rhcos image
-s, --imageSize                Size of the image you want to create
-n, --imageName                Name of the ova image file

Note:
    - qemu-img binary should be available
    - URL must be pointing to an gziped qcow2 image
    - Machine should be having enough disk space to create intermediate images as well
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

def exec_cmd(cmd):
    execute = subprocess.Popen([cmd],shell=True,stdout=subprocess.PIPE)
    return execute.communicate()[0]

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

def convert_qcow2_ova(imageUrl, imageSize, imageName):
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

    os.mkdir(converted_images_dir) # Target directory to keep volume, meta and ovf files

    print("Download image.......")
    get_image(imageUrl, image_file_path )

    print("Extracting gz image...")
    gzip_gunzip(image_file_path, extracted_qcow2_file_path, 65536)

    print("Converting to raw ....")
    cmd =  'qemu-img convert -f qcow2 -O raw ' + extracted_qcow2_file_path  + '  ' + extracted_raw_file_path
    try:
        response = exec_cmd(cmd)
    except:
        print('ERROR: problem converting file (do you have qemu-img installed?)')

    print("Resizing image ....")
    cmd = 'qemu-img resize ' + extracted_raw_file_path + ' ' + imageSize + 'G'
    try:
        response = exec_cmd(cmd)
    except:
        print('ERROR: Resizing failed')
    
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
    shutil.rmtree(tmpdir)

    
def main(argv):
    ImageUrl = ''
    imageSize = ''
    imageName = ''
    try:
        (opts, args) = getopt.getopt(argv, 'hu:s:n:', [
            'imageUrl=',
            'imageSize=',
            'imageName='
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
    convert_qcow2_ova(ImageUrl, imageSize, imageName)


if __name__ == '__main__':
    main(sys.argv[1:])
