#!/usr/bin/env bash
set -euo pipefail
export AWS_PAGER=""
REGION=${REGION:-us-east-1}
: "${BUCKET:?Set BUCKET}"
: "${API_ID:?Set API_ID}"
: "${APP_ID:?Set APP_ID}"
ORIGIN="https://main.${APP_ID}.amplifyapp.com"
cat >/tmp/findback-cors-api.json <<JSON
{"AllowOrigins":["http://localhost:5173","${ORIGIN}"],"AllowMethods":["GET","POST","OPTIONS"],"AllowHeaders":["content-type"],"AllowCredentials":false}
JSON
aws apigatewayv2 update-api --api-id "$API_ID" --region "$REGION" --cors-configuration file:///tmp/findback-cors-api.json >/dev/null
cat >/tmp/findback-cors-s3.json <<JSON
{"CORSRules":[{"AllowedHeaders":["*"],"AllowedMethods":["GET","POST"],"AllowedOrigins":["http://localhost:5173","${ORIGIN}"],"MaxAgeSeconds":3000}]}
JSON
aws s3api put-bucket-cors --bucket "$BUCKET" --region "$REGION" --cors-configuration file:///tmp/findback-cors-s3.json
printf 'CORS now includes %s\n' "$ORIGIN"
