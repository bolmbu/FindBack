#!/usr/bin/env bash
set -euo pipefail
export AWS_PAGER=''
REGION=${REGION:-us-east-1}
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
LAMBDA_ARN="arn:aws:lambda:${REGION}:${ACCOUNT}:function:lost-and-found-api"
API_ID=$(aws apigatewayv2 create-api --name findback-http-api --protocol-type HTTP --region "$REGION" --query ApiId --output text)
aws apigatewayv2 create-stage --api-id "$API_ID" --stage-name '$default' --auto-deploy --region "$REGION" >/dev/null
INTEGRATION=$(aws apigatewayv2 create-integration --api-id "$API_ID" --integration-type AWS_PROXY \
 --integration-uri "$LAMBDA_ARN" --payload-format-version 2.0 --region "$REGION" --query IntegrationId --output text)
for ROUTE in 'GET /items' 'POST /items' 'POST /upload-url' 'GET /matches'; do
 aws apigatewayv2 create-route --api-id "$API_ID" --route-key "$ROUTE" \
   --target "integrations/$INTEGRATION" --region "$REGION" >/dev/null
done
aws lambda add-permission --function-name lost-and-found-api --statement-id "AllowFindBack${API_ID}" \
 --action lambda:InvokeFunction --principal apigateway.amazonaws.com \
 --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT}:${API_ID}/*/*/*" --region "$REGION" >/dev/null
aws apigatewayv2 update-api --api-id "$API_ID" --cors-configuration \
 '{"AllowOrigins":["http://localhost:5173"],"AllowMethods":["GET","POST","OPTIONS"],"AllowHeaders":["content-type"]}' --region "$REGION" >/dev/null
printf 'export API_ID=%s\nexport API_URL=https://%s.execute-api.%s.amazonaws.com\n' "$API_ID" "$API_ID" "$REGION"
