# Used to scope the firewall's SSH rule to the developer's current IP only
# (same pattern as sask's infra/tofu/main.tf).
data "http" "developer_ip" {
  url = "https://api.ipify.org"
}

# Looked up, not created — a dedicated key generated for this project
# (confirmed 2026-10-01, after reconsidering an earlier choice to reuse
# the genuinemerit key), registered once via `doctl`, then just
# referenced here. See variables.tf's ssh_key_name for how this was
# traced to a specific local key/fingerprint.
data "digitalocean_ssh_key" "web_sites" {
  name = var.ssh_key_name
}

# No cloud-init — Ansible owns all droplet configuration from a clean image
# (same pattern as sask).
resource "digitalocean_droplet" "web_sites" {
  name     = var.droplet_name
  region   = var.region
  size     = var.droplet_size
  image    = var.droplet_image
  ssh_keys = [data.digitalocean_ssh_key.web_sites.id]
}

# Reserved IP survives destroy/recreate — the SSH alias targets this, not
# the droplet, so it doesn't change across a destroy/reprovision cycle.
# DNS is deliberately NOT wired up here yet (see README.md in this
# directory) - when a site is ready to go live, pointing its domain at
# this IP is a separate, deliberate action, not bundled into
# infrastructure scaffolding.
resource "digitalocean_reserved_ip" "web_sites" {
  region = var.region
}

resource "digitalocean_reserved_ip_assignment" "web_sites" {
  ip_address = digitalocean_reserved_ip.web_sites.ip_address
  droplet_id = digitalocean_droplet.web_sites.id
}

resource "digitalocean_firewall" "web_sites" {
  name        = "web-sites-firewall"
  droplet_ids = [digitalocean_droplet.web_sites.id]

  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["${chomp(data.http.developer_ip.response_body)}/32"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "icmp"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}
