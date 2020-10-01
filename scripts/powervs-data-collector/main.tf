terraform {
  required_version = ">= 0.13.3"
  required_providers {
    ibm = {
      source  = "ibm-cloud/ibm"
      version = "1.12.0"
    }
  }
}

data "ibm_pi_cloud_instance" "pi_cloud_instances"{
	pi_cloud_instance_id = var.power_instance_id
}

output "powervs_id"{
    value = "${data.ibm_pi_cloud_instance.pi_cloud_instances.id}"
}

output "region"{
    value = "${data.ibm_pi_cloud_instance.pi_cloud_instances.region}"
}

output "capabilities"{
    value="${data.ibm_pi_cloud_instance.pi_cloud_instances.capabilities}"
}

output "pvm_instances"{
    value="${data.ibm_pi_cloud_instance.pi_cloud_instances.*.pvm_instances}"
}

output "instance_count"{
    value ="${data.ibm_pi_cloud_instance.pi_cloud_instances.total_instances}"
}

output "instance_memory"{
    value ="${data.ibm_pi_cloud_instance.pi_cloud_instances.total_memory_consumed}"
}

output "instance_processors"{
    value ="${data.ibm_pi_cloud_instance.pi_cloud_instances.total_processors_consumed}"
}

output "instance_ssd"{
    value ="${data.ibm_pi_cloud_instance.pi_cloud_instances.total_ssd_storage_consumed}"
}

output "instance_standard"{
    value ="${data.ibm_pi_cloud_instance.pi_cloud_instances.total_standard_storage_consumed}"
}

