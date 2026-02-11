# Set-up guide

Here is an explanation of how you can set up this project to run locally.

---

## Initial Set-up

The dockerfile and docker compose files are provided to run a complete setup from scratch.

- Before running docker ensure you set up proper credentials for a database in docker compose file and store them safely. They are crucial to properly set-up vault.
- Build the docker container using "docker compose up --build" command after Database credentials are set
- Run migrations using alembic to properly set up the database once at start. Note: These migrations must be executed inside the docker container.


- Note: the database URL will follow this format: postgresql+asyncpg://username:password@db:5432/dbname
---

## Vault Set-up

The Vault **MUST** have 3 things for the project to run properly;

1. In vault "Secret Engine" DataBase must be Set-Up using the database URL and then synapse-app role must be created with the appropriate creation and revocation statements.
2. Now we must set up our Gemini Api key, this will live inside Secret Engine > KV v2 > llm > with the key "google_genai"
3. Finally we must set up transit with jwt_signer_es256 which is an asymmetric algorithm used for JWT tokens. Upon creation it will give a public key; paste the public key inside jwt_public_key.pem (app/security/jwt_public_key.pem)
4. AppRole & Policy (The Bridge)
Once the engines are configured, we need to create a "Bridge" that allows the application to talk to them.

    - Enable AppRole: Run vault auth enable approle.
    - Create a Policy: Create a .hcl policy (Look at app-policy.hcl for the policy this app uses) that grants read access to the paths you created above (Database, KV, and Transit).
    - Register the Role: Create the role in Vault (e.g., synapse-app) and attach that policy to it.
    - Retrieve Credentials: Run the Vault commands to generate your VAULT_ROLE_ID and VAULT_SECRET_ID and place them inside the env file.
---

## Frontend Setup

Prerequisites:
    - Node.js (v18 or higher)
    - npm

Installation steps:
1. Navigate to Client "cd client"

2. install dependencies inside the client directory using "npm install
3. Configure environment variables:
    - Create a .env file in the frontend root and add this variable:
    - VITE_API_URL=http://localhost:8000/api/v1
4. Start the development server using "npm run dev"



### And with that, the set-up for this project is complete.