#!/usr/bin/env bash
set -euo pipefail
REGION=${REGION:-us-east-1}
: "${MAPPING_UUID:?Set MAPPING_UUID}"
aws lambda update-event-source-mapping --uuid "$MAPPING_UUID" --no-enabled --region "$REGION" --query '{State:State}' --output json
: "${BUCKET:?Set BUCKET}"
aws lambda update-function-configuration --function-name lost-and-found-api --region "$REGION" --environment "Variables={ITEMS_TABLE=LostAndFoundItems,MATCHES_TABLE=LostAndFoundMatches,IMAGE_BUCKET=$BUCKET,ENABLE_DEMO_UPLOAD=false}" --query '{LastUpdateStatus:LastUpdateStatus}' --output json
aws lambda wait function-updated --function-name lost-and-found-api --region "$REGION"
echo 'Upload disabled; mapping disabling/disabled. Check mapping again.'
