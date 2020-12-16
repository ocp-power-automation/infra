#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import platform
import sys


def upload_object_aspera(cos, bucket, file_name, object_name):
    from ibm_s3transfer.aspera.manager import AsperaTransferManager

    # Create Transfer manager
    with AsperaTransferManager(cos) as transfer_manager:
        # Perform upload
        future = transfer_manager.upload(file_name, bucket,
                                         object_name)

        # Wait for upload to complete
        future.result()


def main():
    parser = argparse.ArgumentParser(
        epilog="Note: Create a Service credential in the COS to get the apikey and the resource_instance_id")
    parser.add_argument("-b", "--bucket",
                        help="Bucket name",
                        required=True)
    parser.add_argument("-r", "--region",
                        help="Bucket's region(e.g: us-south)",
                        required=True)
    parser.add_argument("-f", "--file",
                        help="Input file to be uploaded",
                        required=True)
    parser.add_argument("-o", "--object",
                        help="Target object name to be created in the bucket",
                        required=True)
    parser.add_argument("-a", "--accesskey",
                        help="Storage Bucket's Access Key ID(not required if --aspera set")
    parser.add_argument("-s", "--secret",
                        help="Storage Bucket's Secret Access Key(not required if --aspera set)")
    parser.add_argument("--aspera",
                        help="Use aspera client to upload an image(available only in x86 linux environment)",
                        action="store_true",
                        default=False)
    parser.add_argument("-k", "--apikey",
                        help="IBM Cloud API Key(required if --aspera set)")
    parser.add_argument("-i", "--instanceid",
                        help="IBM COS resource instance ID(required if --aspera set)")

    args = parser.parse_args()
    if args.aspera:
        print("Aspera option is set..")
        if platform.machine() != "x86_64" or platform.system() != "Linux":
            print("--aspera option is supported only on distro: Linux, architecture: x86_64")
            sys.exit(2)
        import ibm_boto3
        from ibm_botocore.client import Config
        cos = ibm_boto3.client(
            service_name='s3',
            ibm_api_key_id=args.apikey,
            ibm_service_instance_id=args.instanceid,
            ibm_auth_endpoint='https://iam.cloud.ibm.com/identity/token',
            config=Config(signature_version='oauth'),
            endpoint_url='https://s3.' + args.region
                         + '.cloud-object-storage.appdomain.cloud/',
        )
        upload_object_aspera(cos, args.bucket, args.file, args.object)
    else:
        print("Aspera option is not set, continuing with normal boto3 client..")
        import boto3
        s3 = boto3.client('s3',
                          endpoint_url='https://s3.' + args.region + '.cloud-object-storage.appdomain.cloud/',
                          region_name=args.region,
                          aws_access_key_id=args.accesskey,
                          aws_secret_access_key=args.secret)
        with open(args.file, "rb") as f:
            s3.upload_fileobj(f, args.bucket, args.object)


if __name__ == '__main__':
    print("*******************************************************************************")
    print("This scripts is deprecated in favor of pvsadm. Try pvsadm today, it's great!")
    print("For more information: https://github.com/ppc64le-cloud/pvsadm")
    print("*******************************************************************************")
    main()
