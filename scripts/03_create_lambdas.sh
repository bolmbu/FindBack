#!/usr/bin/env bash
set -euo pipefail
export AWS_PAGER=''
REGION=${REGION:-us-east-1}
: "${BUCKET:?Set BUCKET first}"
: "${ROLE_ARN:?Set ROLE_ARN to an instructor-approved execution role ARN}"
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
(cd "$ROOT/backend" && zip -q -j /tmp/findback-api.zip lambda_function.py)
(cd "$ROOT/backend" && zip -q -j /tmp/findback-matching.zip matching.py matching_lambda.py)
aws lambda create-function --function-name lost-and-found-api --runtime python3.13 \
 --handler lambda_function.lambda_handler --role "$ROLE_ARN" \
 --zip-file fileb:///tmp/findback-api.zip --timeout 15 --memory-size 256 --region "$REGION" >/dev/null
aws lambda wait function-active-v2 --function-name lost-and-found-api --region "$REGION"
aws lambda update-function-configuration --function-name lost-and-found-api --environment \
 "Variables={ITEMS_TABLE=LostAndFoundItems,MATCHES_TABLE=LostAndFoundMatches,IMAGE_BUCKET=$BUCKET,ENABLE_DEMO_UPLOAD=false}" --region "$REGION" >/dev/null
aws lambda wait function-updated --function-name lost-and-found-api --region "$REGION"
aws lambda create-function --function-name lost-and-found-matching --runtime python3.13 \
 --handler matching_lambda.handler --role "$ROLE_ARN" --zip-file fileb:///tmp/findback-matching.zip \
 --timeout 30 --memory-size 128 --region "$REGION" >/dev/null
aws lambda wait function-active-v2 --function-name lost-and-found-matching --region "$REGION"
aws lambda update-function-configuration --function-name lost-and-found-matching --environment \
 "Variables={ITEMS_TABLE=LostAndFoundItems,MATCHES_TABLE=LostAndFoundMatches,DRY_RUN=true}" --region "$REGION" >/dev/null
aws lambda wait function-updated --function-name lost-and-found-matching --region "$REGION"
echo 'CREATED: API and Matching Lambdas (DRY_RUN=true)'
