output "reserved_ip" {
  description = "The stable IP that survives destroy/recreate; the SSH alias targets this. Not yet wired to any DNS record - see README.md."
  value       = digitalocean_reserved_ip.web_sites.ip_address
}

output "droplet_id" {
  description = "The current droplet's ID (changes every destroy/recreate, unlike the reserved IP)."
  value       = digitalocean_droplet.web_sites.id
}

output "droplet_size" {
  value = digitalocean_droplet.web_sites.size
}

output "droplet_region" {
  value = digitalocean_droplet.web_sites.region
}

output "next_steps" {
  description = "Reminder of what still needs to happen after `tofu apply`."
  value       = <<-EOT
    Droplet created. Next:
      1. ssh -o User=root ${var.droplet_name}   # only account that exists so far
      2. Run tools/ops/deploy.sh to bootstrap the `${var.ssh_admin_user}` admin
         account, harden the platform, and install/configure nginx.
         After that, the plain alias (`ssh ${var.droplet_name}`) connects as
         ${var.ssh_admin_user}.
      3. DNS is deliberately not wired up yet — this droplet has no domain
         pointed at it. Going live with a site is a separate, later,
         deliberately-reviewed step (see planning/roadmap.md Phase 3).
  EOT
}
