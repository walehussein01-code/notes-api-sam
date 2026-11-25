# Notes API (Serverless, AWS SAM)

A serverless REST API for creating, listing, and deleting notes, protected by Amazon Cognito authentication.

## Architecture

```
Client
  |  HTTPS + JWT (Authorization: Bearer <token>)
  v
API Gateway (HTTP API) --- JWT authorizer ---> Cognito User Pool
  |
  v
AWS Lambda (Python 3.12)
  |
  v
DynamoDB
```

## Services used

- **API Gateway (HTTP API):** routes requests and validates JWTs. I chose an HTTP API over a REST API for lower cost and latency.
- **Cognito User Pool:** handles sign-up and login, and issues tokens.
- **Lambda (Python 3.12):** the application logic.
- **DynamoDB:** note storage.
- **AWS SAM / CloudFormation:** infrastructure as code.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/notes` | Create a note. Body: `{"text": "..."}` |
| GET | `/notes` | List notes |
| DELETE | `/notes/{noteId}` | Delete a note |

All routes require an `Authorization: Bearer <token>` header.

## Deploy

Prerequisites: AWS CLI configured, AWS SAM CLI, Python 3.12.

```bash
sam build
sam deploy --guided
```

## Try it

```bash
# 1. Create a user
aws cognito-idp sign-up --client-id <CLIENT_ID> --username you@example.com --password '<PASSWORD>'
aws cognito-idp admin-confirm-sign-up --user-pool-id <POOL_ID> --username you@example.com

# 2. Get a token
TOKEN=$(aws cognito-idp initiate-auth --auth-flow USER_PASSWORD_AUTH \
  --client-id <CLIENT_ID> \
  --auth-parameters USERNAME=you@example.com,PASSWORD='<PASSWORD>' \
  --query "AuthenticationResult.IdToken" --output text)

# 3. Call the API
curl -X POST <API_URL>/notes -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"text":"hello"}'
curl <API_URL>/notes -H "Authorization: Bearer $TOKEN"
curl -X DELETE <API_URL>/notes/<NOTE_ID> -H "Authorization: Bearer $TOKEN"
```

## Security

- Every route requires a valid Cognito JWT. Requests without one get `401 Unauthorized`.
- Lambda uses a least-privilege IAM role scoped to the notes table.
- No credentials are stored in the repo.

## Cost and cleanup

Everything runs on pay-per-use services and fits in the free tier for light use. To remove all resources:

```bash
sam delete --stack-name sam-app
```

## Lessons learned

- HTTP APIs deployed by SAM use the `$default` stage, so there is no `/Prod/` in the URL (REST APIs do have it).
- An implicit HTTP API is referenced as `ServerlessHttpApi` in the template, not `ServerlessRestApi`.
- A `401 Unauthorized` response means the route exists but the token is missing or invalid, while `404 Not Found` means the route doesn't exist.

## Roadmap

- GitHub Actions CI/CD pipeline
- Per-user note isolation using the Cognito `sub` claim
- Unit tests and structured logging
