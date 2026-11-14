#!/usr/bin/env bash
set -euo pipefail
export AWS_PAGER=''
REGION=${REGION:-us-east-1}
for spec in 'LostAndFoundItems:itemId' 'LostAndFoundMatches:matchId'; do
  TABLE=${spec%%:*}; KEY=${spec##*:}
  if aws dynamodb describe-table --table-name "$TABLE" --region "$REGION" >/dev/null 2>&1; then
    echo "Exists: $TABLE"
  else
    aws dynamodb create-table --table-name "$TABLE" --attribute-definitions AttributeName="$KEY",AttributeType=S \
      --key-schema AttributeName="$KEY",KeyType=HASH --billing-mode PAY_PER_REQUEST --region "$REGION" >/dev/null
  fi
  aws dynamodb wait table-exists --table-name "$TABLE" --region "$REGION"
  echo "READY: $TABLE"
done
