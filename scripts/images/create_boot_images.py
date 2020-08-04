#!/usr/bin/env python3

import yaml
import subprocess
import json
import sys
import getopt

help_message = """create_boot_images.py -a <accessKey> -s <secretKey> -i <imageManifestFile> -k <apiKey>

-a, --accessKey                    IBM Cloud COS Service credential's accesskey
-s, --secretKey                    IBM Cloud COS Service credential's secretkey
-i, --imageManifest                default is image-manifest.yaml in the present directory
-k, --apiKey                       apikey from the IBM Cloud IAM

Requirements:
    - Install ibmcloud CLI - https://cloud.ibm.com/docs/cli?topic=cli-install-ibmcloud-cli
    - Install power-iaas plugin - https://cloud.ibm.com/docs/power-iaas-cli-plugin?topic=power-iaas-cli-plugin-power-iaas-cli-reference
    - Create a Service credential in the COS to get the accessKey and the secretKey
"""


def exec_cmd(cmd):
    cp = subprocess.run(cmd, universal_newlines=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return cp.stdout, cp.stderr, cp.returncode


def ibmcloud_login(apiKey):
    return exec_cmd(["ibmcloud", "login", "--apikey", apiKey, "--no-region", "-q"])


def get_boot_images():
    images = []
    out, err, ret = exec_cmd(["ibmcloud", "pi", "images", "--json"])
    if ret != 0:
        raise Exception("Failed to get the images")
    jsonout = json.loads(out)
    for image in jsonout["Payload"]["images"]:
        images.append(image["name"])
    return images


def create_boot_image(accessKey, secretKey, imageManifest):
    with open(imageManifest) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        for image in data:
            out, err, ret = exec_cmd(
                ["ibmcloud", "pi", "service-list", "--json"])
            if ret != 0:
                print("Failed to get the service-list, exiting!")
                sys.exit(2)
            y = json.loads(out)
            for instance in image["target"]["powerVSInstances"]:
                for resource in y:
                    if resource["Name"] == instance:
                        print("\nImporting...")
                        print("Source: ", image["source"])
                        print("PowerVS resource: ", resource["Name"])
                        print("Boot Image Name: ",
                              image["target"]["imageName"])
                        out, err, ret = exec_cmd(
                            ["ibmcloud", "pi", "service-target", resource["CRN"]])
                        if ret != 0:
                            print("Failed to set the service-target for ",
                                  instance, " skipping to next powerVS resource!")
                            continue
                        if image["target"]["imageName"] in get_boot_images():
                            print("Warning: This PowerVS instance already has an image name with ",
                                  image["target"]["imageName"], " hence skipping the image-import")
                            continue
                        out, err, ret = exec_cmd(["ibmcloud", "pi", "image-import", image["target"]["imageName"], "--image-path", "s3.private."+image["source"]["region"] +
                                                  ".cloud-object-storage.appdomain.cloud/"+image["source"]["bucket"]+"/"+image["source"]["object"], "--access-key", accessKey, "--secret-key", secretKey])
                        if ret != 0:
                            print("Failed to image-import", err)
                            continue


def main(argv):
    accessKey = ''
    secretKey = ''
    imageManifest = 'image-manifest.yml'
    apiKey = ''
    try:
        (opts, args) = getopt.getopt(argv, 'ha:s:i:k:', [
            'accessKey=',
            'secretKey=',
            'imageManifest=',
            'apiKey='
        ])
    except getopt.GetoptError:
        print(help_message)
        sys.exit(2)
    for (opt, arg) in opts:
        if opt == '-h':
            print(help_message)
            sys.exit()
        elif opt in ('-a', '--accessKey'):
            accessKey = arg
        elif opt in ('-s', '--secretKey'):
            secretKey = arg
        elif opt in ('-i', '--imageManifest'):
            imageManifest = arg
        elif opt in ('-k', '--apiKey'):
            apiKey = arg
    out, err, ret = ibmcloud_login(apiKey)
    if ret != 0:
        print("Failed to login to IBM cloud", out, err)
        sys.exit(2)
    create_boot_image(accessKey, secretKey, imageManifest)


if __name__ == '__main__':
    main(sys.argv[1:])
