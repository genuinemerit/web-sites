# Targets var.ssh_admin_user, not root: that account doesn't exist on a
# freshly created droplet until Ansible's bootstrap play creates it (the
# only account a no-cloud-init droplet starts with is root, and the base
# role disables root login once bootstrap is done, matching
# legacy/security-review.md's recommendation).
#
# StrictHostKeyChecking accept-new: a destroy/recreate cycle keeps the same
# reserved IP but gets a fresh droplet with a different host key every
# time. tools/ops/destroy.sh purges the stale known_hosts entry on
# teardown, so the next provision's first connection is always genuinely
# "new" rather than "changed" (which plain accept-new would still refuse).
resource "local_file" "ssh_config" {
  filename        = pathexpand(var.ssh_config_path)
  file_permission = "0600"
  content         = <<-EOT
    Host ${var.droplet_name}
        HostName ${digitalocean_reserved_ip.web_sites.ip_address}
        User ${var.ssh_admin_user}
        IdentityFile ~/.ssh/${var.ssh_private_key_name}
        IdentitiesOnly yes
        StrictHostKeyChecking accept-new
  EOT
}
