# FindBack — AWS CloudShell lab kit

All commands in the presentation are for AWS CloudShell (`us-east-1`), not local VS Code. Students use their own AWS Learner Lab session.

**Important prerequisite:** Place this `findback_labkit/` folder at the **root** of the public/accessible `lost-and-found-cloud` GitHub repo **before** distributing the slides. The repo must also contain the actual FindBack React `package.json`, `src/`, and any frontend API integration that reads `import.meta.env.VITE_API_BASE_URL`. These frontend files are not included in this kit.

**Run order:** `00_setup.sh`, `01_create_data.sh`, `02_create_s3.sh`, `03_create_lambdas.sh`, `04_create_api.sh`, `05_setup_matching.sh`; after SNS email confirmation, set Lambda `DRY_RUN=false`, enable the existing DynamoDB Streams mapping, create a LOST and FOUND demo pair, then build React in CloudShell, create Amplify with `07_create_amplify.sh`, set CORS with `08_set_cors.sh`, upload the `dist/` ZIP using `06_deploy_amplify_zip.py`, test using `09_smoke_test.sh` and optionally stop notifications using `10_stop_demo.sh`.

**Deployment limitation:** AWS Learner Lab policy/quota and IAM Lambda execution role permissions vary; syntax checks cannot guarantee live AWS success. If API frontend branch is not published or code expects a different API contract, fix before sharing. `LabRole` must be allowed by the class account to access DynamoDB, DynamoDB Streams, S3, SNS and CloudWatch Logs. Never commit secrets.
