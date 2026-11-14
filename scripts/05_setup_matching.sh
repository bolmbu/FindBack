#!/usr/bin/env bash
set -euo pipefail
export AWS_PAGER=''
REGION=${REGION:-us-east-1}
: "${ALERT_EMAIL:?Set ALERT_EMAIL to your own mailbox}"
TOPIC_ARN=$(aws sns create-topic --name findback-match-alerts --region "$REGION" --query TopicArn --output text)
aws sns subscribe --topic-arn "$TOPIC_ARN" --protocol email --notification-endpoint "$ALERT_EMAIL" --region "$REGION"
echo "CONFIRM SUBSCRIPTION IN YOUR EMAIL, THEN RUN THE NEXT COMMANDS"
printf 'SNS_TOPIC_ARN=%s\n' "$TOPIC_ARN"
aws dynamodb update-table --table-name LostAndFoundItems --stream-specification \
 StreamEnabled=true,StreamViewType=NEW_IMAGE --region "$REGION" >/dev/null
STREAM_ARN=$(aws dynamodb describe-table --table-name LostAndFoundItems --region "$REGION" --query Table.LatestStreamArn --output text)
aws lambda update-function-configuration --function-name lost-and-found-matching --environment \
 "Variables={ITEMS_TABLE=LostAndFoundItems,MATCHES_TABLE=LostAndFoundMatches,SNS_TOPIC_ARN=$TOPIC_ARN,DRY_RUN=true}" --region "$REGION" >/dev/null
aws lambda wait function-updated --function-name lost-and-found-matching --region "$REGION"
aws lambda create-event-source-mapping --function-name lost-and-found-matching --event-source-arn "$STREAM_ARN" \
 --starting-position LATEST --batch-size 1 --no-enabled --region "$REGION" \
 --query '{UUID:UUID,State:State}' --output json
printf 'STREAM_ARN=%s\n' "$STREAM_ARN"
