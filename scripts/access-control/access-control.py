#!/usr/bin/env python3

import yaml
import subprocess
import sys
import getopt
import json

help_message = """access-control.py -k <apiKey> -f <access-bindings-file>

-k, --apiKey                       apikey from the IBM Cloud IAM
-b, --access-bindings              access binding file which contains the users and the access controls(groups)
-h, --help                         print help
"""

existing_users = []


def get_existing_users(pull=False):
    global existing_users
    if pull:
        out, err, ret = exec_cmd(["ibmcloud", "account", "users", "--output", "JSON"])
        if ret != 0:
            raise Exception("Failed to get the users list from IBM cloud", out, err)
        users = json.loads(out)
        for user in users:
            existing_users.append(user["userId"])
    return existing_users


def exec_cmd(cmd):
    cp = subprocess.run(cmd, universal_newlines=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return cp.stdout, cp.stderr, cp.returncode

def ibmcloud_login(apiKey):
    return exec_cmd(["ibmcloud", "login", "--apikey", apiKey, "--no-region", "-q"])

def sync(access_bindings_file):
    invitation_failed_users = []
    access_group_failed_users = []
    get_existing_users(pull=True)
    with open(access_bindings_file) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        for group in data["groups"]:
            print("group: ", group["name"])
            print("users: ", group["users"])
            for user in group["users"]:
                print("Inviting user ", user)
                if user not in existing_users:
                    out, err, ret = invite_user(user)
                    if ret != 0:
                        invitation_failed_users.append(user)
                        print("Failed to invite an user", out, err)
                        continue
                else:
                    print("user: ", user, "already in the existing users list, hence skipped to invite")
                print("Adding user ", user, " to the group: ", group["name"])
                out, err, ret = add_to_access_group(user, group["name"])
                if ret != 0:
                    access_group_failed_users.append(user)
                    print("Failed to add user", user, " to", group["name"])
    if len(invitation_failed_users) != 0 or len(access_group_failed_users) != 0:
        raise Exception("Failed to sync! invitation_failed_users: ", invitation_failed_users,
                        " and access_group_failed_users: ", access_group_failed_users)

def invite_user(user):
    return exec_cmd(["ibmcloud", "account", "user-invite", user])

def add_to_access_group(user, group):
    return exec_cmd(["ibmcloud", "iam", "access-group-user-add", group, user])

def main(argv):
    apiKey = ''
    access_bindings = "access-bindings.yaml"
    try:
        (opts, args) = getopt.getopt(argv, 'hk:b:', [
            'access-bindings='
            'apiKey='
        ])
    except getopt.GetoptError:
        print(help_message)
        sys.exit(2)
    for (opt, arg) in opts:
        if opt in ('-h', '--help'):
            print(help_message)
            sys.exit()
        elif opt in ('-k', '--apiKey'):
            apiKey = arg
        elif opt in ('-b', '--access-bindings'):
            access_bindings = arg

    out, err, ret = ibmcloud_login(apiKey)
    if ret != 0:
        print("Failed to login to IBM cloud", out, err)
        sys.exit(2)
    try:
        sync(access_bindings)
    except Exception as syncerr:
        print(syncerr)
        sys.exit(2)

if __name__ == '__main__':
    main(sys.argv[1:])
