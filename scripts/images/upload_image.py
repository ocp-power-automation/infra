#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ibm_boto3
import sys
import getopt
from ibm_botocore.client import Config
from ibm_s3transfer.aspera.manager import AsperaTransferManager
from ibm_s3transfer.aspera.manager import AsperaConfig

cos = ''
help_message="""upload_image.py -k <apikey> -i <resource_instance_id> -r <region> -b <bucketname> -f <file_to_be_uploaded> -o <objectname_to_be_created_for_a_file>

Note: Create a Service credential in the COS to get the apikey and the resource_instance_id"""

def upload_object(bucket_name, upload_filename, object_name):

    # Create Transfer manager

    with AsperaTransferManager(cos) as transfer_manager:

        # Perform upload

        future = transfer_manager.upload(upload_filename, bucket_name,
                object_name)

        # Wait for upload to complete

        future.result()


def main(argv):
    global cos
    apikey = ''
    instanceid = ''
    region = ''
    bucketname = ''
    infile = ''
    objectname = ''
    try:
        (opts, args) = getopt.getopt(argv, 'hk:i:r:b:f:o:', [
            'apikey=',
            'instanceid=',
            'region=',
            'bucketname=',
            'infile=',
            'objectname=',
            ])
    except getopt.GetoptError:
        print(help_message)
        sys.exit(2)
    for (opt, arg) in opts:
        if opt == '-h':
            print(help_message)
            sys.exit()
        elif opt in ('-k', '--apikey'):
            apikey = arg
        elif opt in ('-i', '--instanceid'):
            instanceid = arg
        elif opt in ('-r', '--region'):
            region = arg
        elif opt in ('-b', '--bucketname'):
            bucketname = arg
        elif opt in ('-f', '--infile'):
            infile = arg
        elif opt in ('-o', '--objectname'):
            objectname = arg
    cos = ibm_boto3.client(
        service_name='s3',
        ibm_api_key_id=apikey,
        ibm_service_instance_id=instanceid,
        ibm_auth_endpoint='https://iam.cloud.ibm.com/identity/token',
        config=Config(signature_version='oauth'),
        endpoint_url='https://s3.' + region
            + '.cloud-object-storage.appdomain.cloud/',
        )

    # Configure 2 sessions for transfer

    ms_transfer_config = AsperaConfig(multi_session=2,
            multi_session_threshold_mb=100)

    # Create the Aspera Transfer Manager

    transfer_manager = AsperaTransferManager(client=cos,
            transfer_config=ms_transfer_config)
    upload_object(bucketname, infile, objectname)


if __name__ == '__main__':
    main(sys.argv[1:])
