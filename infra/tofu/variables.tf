variable "region" {
  description = "DigitalOcean region for the droplet and reserved IP. fra1 - confirmed 2026-09-30 (closer to David; also where sask-droplet already lives, though that wasn't the deciding factor)."
  type        = string
  default     = "fra1"
}

variable "droplet_size" {
  description = "DigitalOcean droplet size slug. Matches the legacy gmerit-nyc2 droplet exactly (confirmed via `doctl compute droplet get gmerit-nyc2` 2026-10-01, not guessed from RAM/disk numbers alone)."
  type        = string
  default     = "s-1vcpu-2gb-70gb-intel"
}

variable "droplet_image" {
  description = "DigitalOcean base image slug. Ubuntu 26.04 LTS - the confirmed target (original project goal: latest fully-supported Ubuntu LTS)."
  type        = string
  default     = "ubuntu-26-04-x64"
}

variable "droplet_name" {
  description = "DigitalOcean-visible droplet name; also the SSH alias tools/ops/provision.sh writes."
  type        = string
  default     = "web-sites-droplet"
}

variable "ssh_key_name" {
  description = "Name of the SSH key already registered in the DigitalOcean account (looked up, not created). Confirmed 2026-10-01: a dedicated key for this project, not the shared genuinemerit key (earlier choice, revised). Traced to local ~/.ssh/ws_ed25519, DO key ID 59722532, fingerprint MD5:fa:11:67:04:a7:71:5b:20:64:20:06:fd:89:4f:7c:8d."
  type        = string
  default     = "ubuvm_ws"
}

variable "ssh_private_key_name" {
  description = "Filename, under ~/.ssh/, of the private key matching ssh_key_name."
  type        = string
  default     = "ws_ed25519"
}

variable "ssh_admin_user" {
  description = "Non-root SSH/admin login account Ansible bootstraps on first connection."
  type        = string
  default     = "dave"
}

variable "ssh_config_path" {
  description = "Path to the generated SSH config snippet for the droplet alias."
  type        = string
  default     = "~/.ssh/config.d/ubuvm_ws"
}
