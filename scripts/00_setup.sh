#!/usr/bin/env bash
set -euo pipefail
export AWS_PAGER=""
export REGION=us-east-1
export ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
export GROUP_TAG="lab$(date +%s)"
export BUCKET="findback-images-${ACCOUNT}-${GROUP_TAG}"
export ROLE_ARN="arn:aws:iam::${ACCOUNT}:role/LabRole"
mkdir -p "$HOME/findback-lab"
{
  printf 'export REGION=%q\n' "$REGION"
  printf 'export ACCOUNT=%q\n' "$ACCOUNT"
  printf 'export GROUP_TAG=%q\n' "$GROUP_TAG"
  printf 'export BUCKET=%q\n' "$BUCKET"
  printf 'export ROLE_ARN=%q\n' "$ROLE_ARN"
} > "$HOME/findback-lab/lab.env"
printf 'READY: region=%s\n' "$REGION"
