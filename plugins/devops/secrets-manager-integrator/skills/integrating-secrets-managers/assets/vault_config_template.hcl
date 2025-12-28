# Vault Configuration File Template

# This file provides a basic template for configuring Vault.
# Modify the values below to suit your specific environment.
# Refer to the Vault documentation for detailed explanations of each parameter:
# https://www.vaultproject.io/docs/configuration

storage "raft" {
  path    = "/opt/vault/data" # Adjust this path to your desired storage location.
  node_id = "vault-node-1"  # Unique identifier for this Vault node.

  # Raft configuration options (optional, but recommended for production):
  #  - retry_join: Attempts to join the cluster on startup if initial join fails.
  #  - snapshot_threshold: Number of logs before a snapshot is taken.
  #  - snapshot_interval: Interval between snapshots.
  #  - leader_transfer_interval: Interval after which a leader will attempt to transfer leadership.
  #
  # Example:
  # retry_join {
  #   leader_api_addr = "http://vault-node-2:8200" # Address of another Vault node in the cluster.
  # }
  # snapshot_threshold   = 8192
  # snapshot_interval    = "2m"
  # leader_transfer_interval = "5s"
}


listener "tcp" {
  address     = "0.0.0.0:8200" # Change to your desired listening address.
  tls_disable = true        # Disable TLS for development/testing purposes ONLY.
                             # ENABLE TLS FOR PRODUCTION. See TLS configuration below.
  # tls_cert_file = "/opt/vault/tls/vault.crt" # Path to the TLS certificate.
  # tls_key_file  = "/opt/vault/tls/vault.key" # Path to the TLS key.
}

# Optional: Configure TLS for secure communication.
# listener "tcp" {
#   address     = "0.0.0.0:8200" # Change to your desired listening address.
#   tls_cert_file = "/opt/vault/tls/vault.crt" # Path to the TLS certificate.
#   tls_key_file  = "/opt/vault/tls/vault.key" # Path to the TLS key.
# }


telemetry {
  # Enable metrics gathering (optional).  Consider enabling for production environments.
  #  - StatsD:  A popular open-source metrics aggregator.
  #  - Prometheus:  A popular open-source monitoring solution.
  #
  # Example (StatsD):
  # statsd_address = "127.0.0.1:9125"
  # Example (Prometheus):
  # prometheus_retention_time = "1h"
  disable_hostname = true # Prevent hostname from being included in metrics.
}


ui = true # Enable the Vault UI.  Disable if you are managing Vault programmatically only.

# Example of an audit log.  Enable for production environments.
# audit "file" {
#   path = "/opt/vault/audit.log" # Adjust this path to your desired audit log location.
#   file_hmac_algorithm = "sha256"
#   hmac_accessor = true
# }