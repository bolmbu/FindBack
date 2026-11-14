#!/usr/bin/env bash
set -euo pipefail
export AWS_PAGER=""
REGION=${REGION:-us-east-1}
: "${GROUP_TAG:?Set GROUP_TAG first}"
APP_NAME="findback-lab-${GROUP_TAG}"
APP_ID=$(aws amplify create-app --name "$APP_NAME" --platform WEB --region "$REGION" --query 'app.appId' --output text)
aws amplify create-branch --app-id "$APP_ID" --branch-name main --region "$REGION" >/dev/null
printf 'export APP_ID=%s\nexport AMPLIFY_ORIGIN=https://main.%s.amplifyapp.com\n' "$APP_ID" "$APP_ID"
