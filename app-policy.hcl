# -------------------------------------------------
# DATABASE — dynamic credentials only
# -------------------------------------------------
path "database/creds/synapse-app" {
  capabilities = ["read"]
}

# -------------------------------------------------
# KV v2 — LLM API key (read-only)
# -------------------------------------------------
path "kv/data/llm/google_genai" {
  capabilities = ["read"]
}

# -------------------------------------------------
# TRANSIT — JWT signing ONLY
# -------------------------------------------------
path "transit/sign/jwt_signer_es256" {
  capabilities = ["update"]
}
