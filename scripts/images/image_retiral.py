#!/usr/bin/env python3

import subprocess
import sys
import argparse
import yaml

"""image_retiral.py -m <imageRetiralManifestFile> -r <targetRegion> -k <apiKey> -i <instanceId>
-m, --imageManifest                Default is image_retiral_manifest.yaml in the present directory
-k, --apiKey                       Apikey from the IBM Cloud IAM
-r, --targetRegion                 Target region
-i, --instanceid                   IBM COS resource instance ID
Requirements:
    - Install ibmcloud CLI - https://cloud.ibm.com/docs/cli?topic=cli-install-ibmcloud-cli
    - Install power-iaas plugin - https://cloud.ibm.com/docs/power-iaas-cli-plugin?topic=power-iaas-cli-plugin-power-iaas-cli-reference
    - Create API key from IBM cloud IAM
"""


def exec_cmd(cmd):
    cp = subprocess.run(cmd, universal_newlines=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return cp.stdout, cp.stderr, cp.returncode


def ibmcloud_plugin_install():
    return exec_cmd("ibmcloud plugin install cloud-object-storage")


def ibmcloud_login(apiKey):
    return exec_cmd(["ibmcloud", "login", "--apikey", apiKey, "--no-region", "-q"])


def set_cos_config(region, instance_id):
    exec_cmd("ibmcloud cos config auth IAM")
    exec_cmd(["ibmcloud", "cos", "config", "crn", "--crn", instance_id])
    exec_cmd(["ibmcloud", "cos", "config", "region", "--region", region])
    out, err, ret = exec_cmd("ibmcloud cos config list")
    if ret != 0:
        print("Failed to set cos config list", err)
        sys.exit(2)
    print("Cos configuration", out)


def retire_images(image_retiral_manifest):
    with open(image_retiral_manifest) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        source_bucket = data["sourceBucket"]
        destination_bucket = data["destinationBucket"]
        for image in data["objectList"]:
            out, err, ret = exec_cmd(["ibmcloud", "cos", "object-copy", "--bucket", destination_bucket,
                                      "--key", image, "--copy-source", source_bucket + "/" + image])
            if ret != 0:
                print("Image: " + image + " not copied", err)
                continue
            else:
                print(out)
                out, err, ret = exec_cmd(["ibmcloud", "cos", "object-delete", "--bucket", source_bucket,
                                          "--key", image, "--force"])
                if ret == 0:
                    print(out)
                else:
                    print("Image: " + image + " not deleted", err)


def main():
    parser = argparse.ArgumentParser(
        epilog="Note: Create a Service credential in the COS to get the apikey  and the resource_instance_id")
    parser.add_argument("-k", "--apikey",
                        help="IBM Cloud API Key",
                        required=True)
    parser.add_argument("-r", "--region",
                        help="Bucket's region(e.g: us-south)",
                        required=True)
    parser.add_argument("-i", "--instanceid",
                        help="IBM COS resource instance ID",
                        required=True)
    parser.add_argument("-m", "--image_retiral_manifest",
                        help="Default is image_retiral_manifest.yaml in the present directory",
                        required=True)
    args = parser.parse_args()
    out, err, ret = ibmcloud_login(args.apikey)
    if ret != 0:
        print("Failed to login to IBM cloud", out, err)
        sys.exit(2)
    out, err, ret = ibmcloud_plugin_install()
    if ret != 0:
        print("Failed to install cos plugin", out, err)
        sys.exit(2)
    set_cos_config(args.region, args.instanceid)
    retire_images(args.image_retiral_manifest)


if __name__ == '__main__':
    main()
