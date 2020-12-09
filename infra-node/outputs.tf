################################################################
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Licensed Materials - Property of IBM
#
# ©Copyright IBM Corp. 2020
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################

output "bastion_private_vip" {
    value = module.prepare.bastion_vip == "" ? null : module.prepare.bastion_vip
}

output "bastion_private_ip" {
    value = join(", ", module.prepare.bastion_ip)
}

output "bastion_public_ip" {
    value = join(", ", module.prepare.bastion_public_ip)
}

output "bastion_ssh_command" {
    value = join(", ", formatlist("ssh -i ${var.private_key_file} ${var.rhel_username}@%s", module.prepare.bastion_public_ip))
}
