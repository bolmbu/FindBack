#!/usr/bin/env bash
set -euo pipefail
export AWS_PAGER=''
REGION=${REGION:-us-east-1}
: "${BUCKET:?Set a globally unique BUCKET name first}"
aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"
aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
cat >/tmp/findback-cors.json <<EOF
{"CORSRules":[{"AllowedHeaders":["*"],"AllowedMethods":["GET","POST"],"AllowedOrigins":["http://localhost:5173"],"MaxAgeSeconds":3000}]}
EOF
aws s3api put-bucket-cors --bucket "$BUCKET" --cors-configuration file:///tmp/findback-cors.json
printf 'CREATED PRIVATE BUCKET: %s\n' "$BUCKET"
