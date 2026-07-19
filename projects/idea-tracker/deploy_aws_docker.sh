#!/usr/bin/env bash
# Deploy Idea Forge to AWS Free Tier EC2 with Docker Compose + Caddy + SSM.
# Dry-run by default. Pass --apply to execute.
#
# Usage:
#   ./deploy_aws_docker.sh
#   ./deploy_aws_docker.sh --apply
#   AWS_REGION=us-west-1 ./deploy_aws_docker.sh --apply
#
# Prerequisites: aws CLI authenticated; jq; docker optional (build happens on EC2).

set -euo pipefail

APPLY=0
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-west-1}}"
PUBLIC_HOST="${IDEA_FORGE_PUBLIC_HOST:-ideaforge.extremesarcasm.org}"
INSTANCE_TYPE="${IDEA_FORGE_INSTANCE_TYPE:-t3.micro}"
NAME_TAG="${IDEA_FORGE_NAME_TAG:-ideaforge}"
SG_NAME="${IDEA_FORGE_SG_NAME:-ideaforge-web}"
ROLE_NAME="${IDEA_FORGE_ROLE_NAME:-IdeaForgeSSMRole}"
PROFILE_NAME="${IDEA_FORGE_PROFILE_NAME:-IdeaForgeSSMProfile}"
BUCKET_PREFIX="${IDEA_FORGE_BUCKET_PREFIX:-ideaforge-deploy}"
REMOTE_DIR="/opt/idea-forge"
STATE_DIR="${IDEA_FORGE_STATE_DIR:-$HOME/.idea-forge-aws}"

for arg in "$@"; do
  case "$arg" in
    --apply|--force) APPLY=1 ;;
    -h|--help)
      sed -n '1,20p' "$0"
      exit 0
      ;;
  esac
done

log() { printf '[deploy-aws] %s\n' "$*"; }
die() { log "ERROR: $*"; exit 1; }

run() {
  if [[ "$APPLY" -eq 1 ]]; then
    log "+ $*"
    "$@"
  else
    log "DRY-RUN: $*"
  fi
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

need_cmd aws
need_cmd jq
need_cmd tar
need_cmd openssl

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$STATE_DIR"

log "region=$REGION public_host=$PUBLIC_HOST instance_type=$INSTANCE_TYPE apply=$APPLY"

if ! aws sts get-caller-identity --region "$REGION" >/dev/null 2>&1; then
  die "AWS credentials not configured. Run: aws login   (or configure access keys)"
fi

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
CALLER_ARN="$(aws sts get-caller-identity --query Arn --output text)"
log "account=$ACCOUNT_ID caller=$CALLER_ARN"

BUCKET="${BUCKET_PREFIX}-${ACCOUNT_ID}-${REGION}"
AMI_ID="$(aws ec2 describe-images \
  --region "$REGION" \
  --owners 099720109477 \
  --filters \
    "Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*" \
    "Name=state,Values=available" \
  --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
  --output text)"
[[ -n "$AMI_ID" && "$AMI_ID" != "None" ]] || die "could not resolve Ubuntu 24.04 AMI in $REGION"
log "ami=$AMI_ID bucket=$BUCKET"

VPC_ID="$(aws ec2 describe-vpcs --region "$REGION" --filters Name=isDefault,Values=true \
  --query 'Vpcs[0].VpcId' --output text)"
[[ -n "$VPC_ID" && "$VPC_ID" != "None" ]] || die "no default VPC in $REGION"
SUBNET_ID="$(aws ec2 describe-subnets --region "$REGION" \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=default-for-az,Values=true" \
  --query 'Subnets[0].SubnetId' --output text)"
[[ -n "$SUBNET_ID" && "$SUBNET_ID" != "None" ]] || \
  SUBNET_ID="$(aws ec2 describe-subnets --region "$REGION" \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query 'Subnets[0].SubnetId' --output text)"
log "vpc=$VPC_ID subnet=$SUBNET_ID"

# --- Security group (80/443 only) ---
SG_ID="$(aws ec2 describe-security-groups --region "$REGION" \
  --filters "Name=group-name,Values=$SG_NAME" "Name=vpc-id,Values=$VPC_ID" \
  --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || true)"
if [[ -z "$SG_ID" || "$SG_ID" == "None" ]]; then
  if [[ "$APPLY" -eq 1 ]]; then
    SG_ID="$(aws ec2 create-security-group --region "$REGION" \
      --group-name "$SG_NAME" \
      --description "Idea Forge HTTPS only (no SSH)" \
      --vpc-id "$VPC_ID" \
      --query GroupId --output text)"
    aws ec2 create-tags --region "$REGION" --resources "$SG_ID" \
      --tags "Key=Name,Value=$SG_NAME" "Key=Project,Value=ideaforge"
    aws ec2 authorize-security-group-ingress --region "$REGION" --group-id "$SG_ID" \
      --ip-permissions \
      'IpProtocol=tcp,FromPort=80,ToPort=80,IpRanges=[{CidrIp=0.0.0.0/0,Description=HTTP}]' \
      'IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges=[{CidrIp=0.0.0.0/0,Description=HTTPS}]' \
      'IpProtocol=tcp,FromPort=80,ToPort=80,Ipv6Ranges=[{CidrIpv6=::/0,Description=HTTP}]' \
      'IpProtocol=tcp,FromPort=443,ToPort=443,Ipv6Ranges=[{CidrIpv6=::/0,Description=HTTPS}]' \
      >/dev/null || true
    log "created security group $SG_ID"
  else
    log "DRY-RUN: would create security group $SG_NAME in $VPC_ID (80/443 only)"
    SG_ID="sg-DRYRUN"
  fi
else
  log "using existing security group $SG_ID"
fi

# --- IAM instance role for SSM ---
ensure_iam() {
  if aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
    log "IAM role exists: $ROLE_NAME"
  else
    if [[ "$APPLY" -eq 1 ]]; then
      aws iam create-role --role-name "$ROLE_NAME" \
        --assume-role-policy-document '{
          "Version":"2012-10-17",
          "Statement":[{
            "Effect":"Allow",
            "Principal":{"Service":"ec2.amazonaws.com"},
            "Action":"sts:AssumeRole"
          }]
        }' >/dev/null
      aws iam attach-role-policy --role-name "$ROLE_NAME" \
        --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
      # Allow instance to pull deploy tarball from our bucket
      aws iam put-role-policy --role-name "$ROLE_NAME" --policy-name IdeaForgeS3Deploy \
        --policy-document "{
          \"Version\":\"2012-10-17\",
          \"Statement\":[{
            \"Effect\":\"Allow\",
            \"Action\":[\"s3:GetObject\",\"s3:ListBucket\"],
            \"Resource\":[
              \"arn:aws:s3:::${BUCKET}\",
              \"arn:aws:s3:::${BUCKET}/*\"
            ]
          }]
        }"
      log "created IAM role $ROLE_NAME"
    else
      log "DRY-RUN: would create IAM role $ROLE_NAME + SSM + S3 read"
    fi
  fi

  if aws iam get-instance-profile --instance-profile-name "$PROFILE_NAME" >/dev/null 2>&1; then
    log "instance profile exists: $PROFILE_NAME"
  else
    if [[ "$APPLY" -eq 1 ]]; then
      aws iam create-instance-profile --instance-profile-name "$PROFILE_NAME" >/dev/null
      aws iam add-role-to-instance-profile \
        --instance-profile-name "$PROFILE_NAME" \
        --role-name "$ROLE_NAME"
      log "created instance profile $PROFILE_NAME (waiting for propagation)"
      sleep 10
    else
      log "DRY-RUN: would create instance profile $PROFILE_NAME"
    fi
  fi

  # Ensure SSM policy attached even if role pre-existed
  if [[ "$APPLY" -eq 1 ]]; then
    aws iam attach-role-policy --role-name "$ROLE_NAME" \
      --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore 2>/dev/null || true
    aws iam put-role-policy --role-name "$ROLE_NAME" --policy-name IdeaForgeS3Deploy \
      --policy-document "{
        \"Version\":\"2012-10-17\",
        \"Statement\":[{
          \"Effect\":\"Allow\",
          \"Action\":[\"s3:GetObject\",\"s3:ListBucket\"],
          \"Resource\":[
            \"arn:aws:s3:::${BUCKET}\",
            \"arn:aws:s3:::${BUCKET}/*\"
          ]
        }]
      }" 2>/dev/null || true
  fi
}
ensure_iam

# --- Secrets ---
ENV_FILE="$STATE_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  SECRET="$(openssl rand -hex 32)"
  ADMIN_PW="$(openssl rand -base64 18 | tr -d '/+=' | head -c 24)"
  if [[ "$APPLY" -eq 1 ]]; then
    cat >"$ENV_FILE" <<EOF
SEEDBANK_PUBLIC_HOST=$PUBLIC_HOST
SEEDBANK_SECRET=$SECRET
SEEDBANK_ADMIN_PASSWORD=$ADMIN_PW
EOF
    chmod 600 "$ENV_FILE"
    log "wrote secrets to $ENV_FILE (admin password also printed once below)"
    log "ADMIN_PASSWORD=$ADMIN_PW"
  else
    log "DRY-RUN: would generate SEEDBANK_SECRET and SEEDBANK_ADMIN_PASSWORD into $ENV_FILE"
  fi
else
  log "reusing existing secrets file $ENV_FILE"
  ADMIN_PW="$(grep '^SEEDBANK_ADMIN_PASSWORD=' "$ENV_FILE" | cut -d= -f2- || true)"
fi

# --- Package + S3 ---
STAGE="$(mktemp -d)"
cleanup() { rm -rf "$STAGE"; }
trap cleanup EXIT

# App payload for Docker build context (exclude local data/secrets)
mkdir -p "$STAGE/app"
tar -C "$SCRIPT_DIR" \
  --exclude='data' \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.env' \
  --exclude='venv' \
  --exclude='.venv' \
  --exclude='*.pem' \
  -cf - . | tar -C "$STAGE/app" -xf -

if [[ "$APPLY" -eq 1 ]]; then
  cp "$ENV_FILE" "$STAGE/app/.env"
  chmod 600 "$STAGE/app/.env"
else
  printf 'SEEDBANK_PUBLIC_HOST=%s\nSEEDBANK_SECRET=dry-run\nSEEDBANK_ADMIN_PASSWORD=dry-run\n' \
    "$PUBLIC_HOST" >"$STAGE/app/.env"
fi

# PII/secrets scan before any AWS upload (allow .env app secrets; still block emails/keys)
SCAN_PII="${SCRIPT_DIR}/../../bash/scan_pii.sh"
if [[ -x "$SCAN_PII" ]]; then
  log "scanning bundle for PII/secrets ..."
  if ! "$SCAN_PII" --allow-env "$STAGE/app"; then
    die "PII/secrets scan failed — fix findings before uploading to AWS"
  fi
else
  log "WARNING: scan_pii.sh not found at $SCAN_PII — skipping pre-upload scan"
fi

TAR="$STATE_DIR/ideaforge-bundle.tgz"
tar -C "$STAGE" -czf "$TAR" app
log "bundle=$(du -h "$TAR" | awk '{print $1}') -> $TAR"

if [[ "$APPLY" -eq 1 ]]; then
  if ! aws s3api head-bucket --bucket "$BUCKET" --region "$REGION" 2>/dev/null; then
    if [[ "$REGION" == "us-east-1" ]]; then
      aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"
    else
      aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
        --create-bucket-configuration "LocationConstraint=$REGION"
    fi
    aws s3api put-public-access-block --bucket "$BUCKET" \
      --public-access-block-configuration \
      BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
    aws s3api put-bucket-encryption --bucket "$BUCKET" \
      --server-side-encryption-configuration \
      '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
    log "created private bucket s3://$BUCKET"
  fi
  aws s3 cp "$TAR" "s3://$BUCKET/ideaforge-bundle.tgz" --region "$REGION"
  log "uploaded s3://$BUCKET/ideaforge-bundle.tgz"
else
  log "DRY-RUN: would ensure s3://$BUCKET and upload bundle"
fi

# --- User data ---
USER_DATA="$STAGE/userdata.sh"
cat >"$USER_DATA" <<'USERDATA'
#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y ca-certificates curl gnupg unzip jq
# Docker
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable --now docker
# amazon-ssm-agent ships preinstalled as a snap on the official Ubuntu AMIs
# (no apt package exists); just make sure the snap service is running.
snap start amazon-ssm-agent 2>/dev/null || systemctl enable --now snap.amazon-ssm-agent.amazon-ssm-agent.service 2>/dev/null || true
# AWS CLI v2 (needed on-instance to pull the deploy bundle from S3)
if ! command -v aws >/dev/null; then
  curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
  unzip -q /tmp/awscliv2.zip -d /tmp
  /tmp/aws/install
  rm -rf /tmp/awscliv2.zip /tmp/aws
fi
# Swap for docker builds on t3.micro
if [[ ! -f /swapfile ]]; then
  fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi
apt-get install -y unattended-upgrades
dpkg-reconfigure -f noninteractive unattended-upgrades || true
mkdir -p /opt/idea-forge
touch /var/lib/cloud/instance/ideaforge-userdata-done
USERDATA

# --- Find or launch instance ---
INSTANCE_ID="$(aws ec2 describe-instances --region "$REGION" \
  --filters \
    "Name=tag:Name,Values=$NAME_TAG" \
    "Name=instance-state-name,Values=pending,running,stopping,stopped" \
  --query 'Reservations[0].Instances[0].InstanceId' --output text 2>/dev/null || true)"

if [[ -z "$INSTANCE_ID" || "$INSTANCE_ID" == "None" ]]; then
  if [[ "$APPLY" -eq 1 ]]; then
    log "launching $INSTANCE_TYPE ..."
    INSTANCE_ID="$(aws ec2 run-instances --region "$REGION" \
      --image-id "$AMI_ID" \
      --instance-type "$INSTANCE_TYPE" \
      --subnet-id "$SUBNET_ID" \
      --security-group-ids "$SG_ID" \
      --iam-instance-profile "Name=$PROFILE_NAME" \
      --metadata-options "HttpTokens=required,HttpPutResponseHopLimit=2,HttpEndpoint=enabled" \
      --block-device-mappings "[{
        \"DeviceName\":\"/dev/sda1\",
        \"Ebs\":{\"VolumeSize\":20,\"VolumeType\":\"gp3\",\"Encrypted\":true,\"DeleteOnTermination\":true}
      }]" \
      --user-data "file://$USER_DATA" \
      --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$NAME_TAG},{Key=Project,Value=ideaforge}]" \
      --query 'Instances[0].InstanceId' --output text)"
    log "launched $INSTANCE_ID"
    aws ec2 wait instance-running --region "$REGION" --instance-ids "$INSTANCE_ID"
  else
    log "DRY-RUN: would launch $INSTANCE_TYPE ami=$AMI_ID sg=$SG_ID profile=$PROFILE_NAME IMDSv2 encrypted gp3"
    INSTANCE_ID="i-DRYRUN"
  fi
else
  log "reusing instance $INSTANCE_ID"
  STATE="$(aws ec2 describe-instances --region "$REGION" --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].State.Name' --output text)"
  if [[ "$STATE" == "stopped" && "$APPLY" -eq 1 ]]; then
    aws ec2 start-instances --region "$REGION" --instance-ids "$INSTANCE_ID" >/dev/null
    aws ec2 wait instance-running --region "$REGION" --instance-ids "$INSTANCE_ID"
  fi
fi

# --- Elastic IP ---
ALLOC_ID=""
PUBLIC_IP=""
if [[ "$APPLY" -eq 1 && "$INSTANCE_ID" != "i-DRYRUN" ]]; then
  ASSOC="$(aws ec2 describe-addresses --region "$REGION" \
    --filters "Name=instance-id,Values=$INSTANCE_ID" \
    --query 'Addresses[0].AllocationId' --output text 2>/dev/null || true)"
  if [[ -n "$ASSOC" && "$ASSOC" != "None" ]]; then
    ALLOC_ID="$ASSOC"
    PUBLIC_IP="$(aws ec2 describe-addresses --region "$REGION" --allocation-ids "$ALLOC_ID" \
      --query 'Addresses[0].PublicIp' --output text)"
    log "EIP already associated: $PUBLIC_IP ($ALLOC_ID)"
  else
    # Prefer an existing unused EIP tagged for ideaforge
    ALLOC_ID="$(aws ec2 describe-addresses --region "$REGION" \
      --filters "Name=tag:Name,Values=$NAME_TAG" \
      --query 'Addresses[?AssociationId==null] | [0].AllocationId' --output text 2>/dev/null || true)"
    if [[ -z "$ALLOC_ID" || "$ALLOC_ID" == "None" ]]; then
      ALLOC_ID="$(aws ec2 allocate-address --region "$REGION" --domain vpc \
        --query AllocationId --output text)"
      aws ec2 create-tags --region "$REGION" --resources "$ALLOC_ID" \
        --tags "Key=Name,Value=$NAME_TAG" "Key=Project,Value=ideaforge"
    fi
    aws ec2 associate-address --region "$REGION" \
      --instance-id "$INSTANCE_ID" --allocation-id "$ALLOC_ID" >/dev/null
    PUBLIC_IP="$(aws ec2 describe-addresses --region "$REGION" --allocation-ids "$ALLOC_ID" \
      --query 'Addresses[0].PublicIp' --output text)"
    log "associated EIP $PUBLIC_IP -> $INSTANCE_ID"
  fi
  printf '%s\n' "$INSTANCE_ID" >"$STATE_DIR/instance_id"
  printf '%s\n' "$PUBLIC_IP" >"$STATE_DIR/public_ip"
  printf '%s\n' "$ALLOC_ID" >"$STATE_DIR/allocation_id"
else
  log "DRY-RUN: would allocate/associate Elastic IP"
fi

wait_ssm() {
  local id="$1" tries=0
  log "waiting for SSM agent on $id ..."
  while (( tries < 60 )); do
    local ping
    ping="$(aws ssm describe-instance-information --region "$REGION" \
      --filters "Key=InstanceIds,Values=$id" \
      --query 'InstanceInformationList[0].PingStatus' --output text 2>/dev/null || true)"
    if [[ "$ping" == "Online" ]]; then
      log "SSM Online"
      return 0
    fi
    tries=$((tries + 1))
    sleep 10
  done
  die "SSM agent not Online after ~10 minutes for $id"
}

run_ssm() {
  local id="$1"
  local script="$2"
  local cmd_id params b64
  b64="$(printf '%s' "$script" | base64 -w0)"
  # AWS-RunShellScript executes commands with /bin/sh (dash on Ubuntu), which
  # lacks `pipefail`; wrap everything in an explicit bash -c invocation.
  params="$(jq -n --arg b "$b64" '{commands:["bash -c \"echo \($b) | base64 -d | bash\""]}')"
  cmd_id="$(aws ssm send-command --region "$REGION" \
    --instance-ids "$id" \
    --document-name "AWS-RunShellScript" \
    --comment "Idea Forge deploy" \
    --parameters "$params" \
    --timeout-seconds 3600 \
    --query 'Command.CommandId' --output text)"
  log "ssm command $cmd_id"
  local status="Pending"
  for _ in $(seq 1 120); do
    status="$(aws ssm get-command-invocation --region "$REGION" \
      --command-id "$cmd_id" --instance-id "$id" \
      --query 'Status' --output text 2>/dev/null || echo Pending)"
    case "$status" in
      Success) break ;;
      Failed|Cancelled|TimedOut)
        aws ssm get-command-invocation --region "$REGION" \
          --command-id "$cmd_id" --instance-id "$id" \
          --query '{Status:Status,Stdout:StandardOutputContent,Stderr:StandardErrorContent}' \
          --output json >&2 || true
        die "SSM command failed: $status"
        ;;
    esac
    sleep 10
  done
  [[ "$status" == "Success" ]] || die "SSM command did not succeed ($status)"
  aws ssm get-command-invocation --region "$REGION" \
    --command-id "$cmd_id" --instance-id "$id" \
    --query 'StandardOutputContent' --output text
}

if [[ "$APPLY" -eq 1 && "$INSTANCE_ID" != "i-DRYRUN" ]]; then
  # Wait for userdata docker install
  log "waiting ~90s for userdata bootstrap ..."
  sleep 90
  wait_ssm "$INSTANCE_ID"

  DEPLOY_SCRIPT=$(cat <<EOF
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
# Ensure docker present (userdata race)
if ! command -v docker >/dev/null; then
  echo "docker missing; userdata may still be running"
  exit 1
fi
mkdir -p $REMOTE_DIR
cd /tmp
aws s3 cp s3://$BUCKET/ideaforge-bundle.tgz ./ideaforge-bundle.tgz --region $REGION
rm -rf $REMOTE_DIR/app
tar -xzf ideaforge-bundle.tgz -C $REMOTE_DIR
chmod 600 $REMOTE_DIR/app/.env
cd $REMOTE_DIR/app
docker compose pull || true
docker compose build
docker compose up -d
docker compose ps
sleep 2
# app is intentionally not published to the host; check it via Caddy's
# internal network instead of the host loopback.
docker compose exec -T caddy wget -q -O /dev/null http://app:5050/ \
  && echo "app_healthcheck=ok" || echo "app_healthcheck=FAILED"
echo DEPLOY_OK
EOF
)
  # Retry a few times if docker not ready
  ok=0
  for attempt in 1 2 3 4 5; do
    log "deploy attempt $attempt"
    if out="$(run_ssm "$INSTANCE_ID" "$DEPLOY_SCRIPT")"; then
      printf '%s\n' "$out"
      if printf '%s\n' "$out" | grep -q DEPLOY_OK; then
        ok=1
        break
      fi
    fi
    sleep 30
  done
  [[ "$ok" -eq 1 ]] || die "deploy via SSM failed"

  log "=== DONE ==="
  log "instance=$INSTANCE_ID"
  log "public_ip=$PUBLIC_IP"
  log "url=https://$PUBLIC_HOST  (point DNS A record to $PUBLIC_IP)"
  log "admin password is in $ENV_FILE"
  if [[ -n "${ADMIN_PW:-}" ]]; then
    log "SEEDBANK_ADMIN_PASSWORD=$ADMIN_PW"
  fi
  log "SSM shell: aws ssm start-session --target $INSTANCE_ID --region $REGION"
else
  log "Dry-run only. Re-run with --apply to create/update AWS resources and deploy."
  log "After apply: point $PUBLIC_HOST A record at the printed Elastic IP."
fi
