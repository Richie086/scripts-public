Automating a production-grade, secure website deployment on a shoe-string budget is one of the classic challenges in modern cloud engineering. Many cloud practitioners follow standard multi-tier design patterns that include an Application Load Balancer (ALB), multiple Virtual Private Cloud (VPC) subnets spanning multiple Availability Zones, managed database services like RDS, and NAT Gateways. While this multi-AZ architecture provides high availability and fault tolerance, it comes with a significant financial cost. An ALB costs roughly $16.20 per month in base charges alone, and a single NAT Gateway costs approximately $32.40 per month, not including data processing charges. For a personal project, a portfolio, or a developer utility site, these architectural defaults quickly escalate costs to over $50 a month, making them cost-prohibitive.

This article details how to stand up a secure, public-facing website on AWS completely within the AWS Free Tier, costing virtually $0 per month. We walk through the architecture, analyze the automation scripts, discuss key security decisions (such as eliminating SSH entirely), and document a real-world Python 3.14 argparse bug encountered in the AWS CLI, along with how to bypass it using the boto3 SDK.

---

## 1. Inception, Design Philosophy, & Cost Constraints

The primary objective when building this deployment pipeline is absolute cost minimization without sacrificing security. Under the standard AWS Free Tier, which is active for the first 12 months of a new AWS account, users receive:
- **750 hours/month** of a `t2.micro` or `t3.micro` EC2 instance.
- **30 GB** of General Purpose (SSD) EBS storage.
- **5 GB** of standard Amazon S3 storage.
- **100 GB** of data transfer out to the internet per month.

For simple static portfolios or small dynamic sites, this allocation is more than sufficient. However, developers often run into unexpected bills because they apply enterprise-level architectural patterns to small projects. Let's compare the cost of a standard corporate AWS web stack with our single-instance, S3-backed zero-cost stack:

### Stack Cost Comparison Table

| Service Component | Standard Corporate Architecture | Zero-Cost Architecture |
|---|---|---|
| **DNS Management** | Route 53 ($0.50/zone) | Route 53 ($0.50/zone) |
| **Compute / Host** | 2x `t3.micro` in Private Subnets ($15.18/mo) | 1x `t3.micro` in Public Subnet (Free Tier / $7.59/mo after 12 mos) |
| **Load Balancing** | Application Load Balancer ($16.20/mo base + LCU) | *None* (TLS terminated on Host via Nginx) ($0.00) |
| **NAT Gateways** | 2x NAT Gateways ($64.80/mo base + processing) | *None* (Direct route to Internet Gateway) ($0.00) |
| **Database** | Multi-AZ RDS Postgres `db.t3.micro` ($25.00/mo) | *None* (Static site pulled from S3) ($0.00) |
| **Content Storage** | EBS volumes + EFS shared file storage ($10.00/mo) | S3 Private Bucket + 8 GB Encrypted EBS (Free Tier) |
| **SSL/TLS Certificates** | AWS Certificate Manager (Free, requires ALB) | Let's Encrypt via Certbot on Host ($0.00) |
| **Total Estimated Cost** | **~$131.68 / month** | **~$0.50 / month** (Route 53 Hosted Zone cost only) |

By omitting the ALB, RDS, and NAT Gateways, we slash monthly cloud expenditures by over 99.6%.

### Burstable Compute & CPU Credits
For the host machine, we select the `t3.micro` instance type. The `t3` series utilizes burstable performance instances. Unlike dedicated compute instances that provide 100% of a physical CPU core continuously, burstable instances are assigned a baseline performance level (for a `t3.micro`, this is 10% of a physical vCPU core). 

While the instance runs below its baseline CPU utilization, it accumulates CPU credits. During periods of high traffic, compilation, or deployment, the instance consumes these accumulated credits to burst up to 100% of the vCPU core performance. 
- **Credit Accumulation**: A `t3.micro` accumulates 12 CPU credits per hour, up to a maximum limit of 288 credits.
- **Burstable Performance**: One CPU credit represents 100% utilization of a single vCPU core for one minute.
- **Throttling vs Unlimited Mode**: If the instance exhausts its credit balance and is configured in standard mode, its performance is throttled back to the 10% baseline, causing high latency and potential timeouts. While AWS provides an "Unlimited Mode" that allows instances to burst past their credit balance for a small fee, we explicitly keep Unlimited Mode disabled in our automation to prevent unexpected charges.

---

## 2. Detailed Networking, Security, & Systems Management

To maintain a secure posture without the isolation of private subnets and ALBs, we must configure the VPC, Security Groups, and host access mechanisms to adhere strictly to the principle of least privilege.

### VPC and Internet Routing
We deploy the host within the Default VPC. The Default VPC comes pre-configured with a classless inter-domain routing (CIDR) block of `172.31.0.0/16`, containing public subnets in each Availability Zone. 
- **Internet Gateway (IGW)**: The subnet is associated with a route table that directs all traffic destined for the internet (`0.0.0.0/0`) through the VPC's Internet Gateway.
- **Elastic IP Binding**: The Elastic IP is a static public IP mapped to the instance's private IP (`172.31.x.x`) via 1:1 Network Address Translation (NAT) at the IGW boundary.

### Stateful Firewall Configuration (Security Groups)
We configure a single Security Group for the host. Security Groups in AWS are stateful firewalls. This means that if an inbound connection is allowed, the outbound response traffic is automatically allowed, regardless of outbound rules.
- **Ingress Rules**: We allow inbound TCP traffic on port 80 (HTTP) and port 443 (HTTPS) from any source IP (`0.0.0.0/0`).
- **Egress Rules**: We allow outbound traffic to all destinations on all ports. This is necessary to download OS packages during bootstrapping, fetch website files from S3, and communicate with Let's Encrypt validation servers.
- **Zero SSH Access**: Port 22 is completely omitted. This prevents automated brute-force attacks, port scans, and credential-stuffing campaigns that constantly target open SSH ports on the public web.

### Systems Manager Session Manager
Since SSH is disabled, administrative access to the server is handled via AWS Systems Manager (SSM) Session Manager. 

Unlike traditional SSH, which requires:
1.  An open inbound port (22).
2.  A public-facing SSH daemon listening for connections.
3.  Local management of SSH private keys.

SSM Session Manager operates on an outbound agent model:
1.  During boot, the `amazon-ssm-agent` starts on the host.
2.  The agent establishes a persistent outbound connection to the Systems Manager endpoints in the local region (e.g., `ssm.us-east-1.amazonaws.com`, `ssmmessages.us-east-1.amazonaws.com`, and `ec2messages.us-east-1.amazonaws.com`) on port 443 (HTTPS).
3.  When an administrator initiates a session via the AWS Console or the AWS CLI, the request is validated by IAM.
4.  AWS relays the command tunnel to the agent over the established outbound HTTPS connection.
5.  All session actions are logged.

This architecture completely eliminates inbound management ports, utilizes centralized IAM authentication (including multi-factor authentication and role-based policies), and creates audit logs of every command run on the host.

---

## 3. The Complete deploy.sh Script & Line-by-Line Breakdown

The infrastructure provisioning is fully managed by `deploy.sh`. This script uses the AWS CLI to build the target environment.

Here is the complete source code for `deploy.sh`:

```bash
#!/usr/bin/env bash
#
# deploy.sh — stand up exit-code.net on a free-tier EC2 instance
#
set -euo pipefail

### ---------- CONFIG — edit these ---------- ###
DOMAIN="exit-code.net"
WWW_DOMAIN="www.exit-code.net"
REGION="${AWS_REGION:-us-east-1}"
INSTANCE_TYPE="t3.micro"                  # free-tier eligible in most regions
SITE_FILE="exit-code-automations.html"    # must be in the same directory as this script
LETSENCRYPT_EMAIL="richie086@gmail.com"   # <-- configured email for certbot
PROJECT_TAG="exit-code-automations"
### ------------------------------------------ ###

command -v aws >/dev/null || { echo "aws cli not found. Install it first."; exit 1; }
command -v jq  >/dev/null || { echo "jq not found. Install it first (brew install jq / apt install jq)."; exit 1; }
[[ -f "$SITE_FILE" ]] || { echo "Can't find $SITE_FILE next to this script."; exit 1; }

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
S3_BUCKET="exit-code-site-${ACCOUNT_ID}"
echo "Account: $ACCOUNT_ID | Region: $REGION | Bucket: $S3_BUCKET"

### 1. Route53 hosted zone lookup ###
echo "==> Looking up hosted zone for ${DOMAIN}"
ZONE_ID=$(aws route53 list-hosted-zones-by-name --dns-name "$DOMAIN" \
  --query "HostedZones[?Name=='${DOMAIN}.'].Id" --output text | sed 's#/hostedzone/##')
[[ -n "$ZONE_ID" ]] || { echo "No hosted zone found for $DOMAIN in this account."; exit 1; }
echo "    Zone ID: $ZONE_ID"

### 2. Find a free Elastic IP, or allocate one ###
echo "==> Looking for an unassociated Elastic IP"
EIP_ALLOC_ID=$(aws ec2 describe-addresses --region "$REGION" \
  --query "Addresses[?AssociationId==null].AllocationId | [0]" --output text)
if [[ "$EIP_ALLOC_ID" == "None" || -z "$EIP_ALLOC_ID" ]]; then
  echo "    None free — allocating a new one"
  EIP_ALLOC_ID=$(aws ec2 allocate-address --region "$REGION" --domain vpc \
    --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Project,Value=${PROJECT_TAG}}]" \
    --query AllocationId --output text)
fi
EIP_ADDRESS=$(aws ec2 describe-addresses --region "$REGION" \
  --allocation-ids "$EIP_ALLOC_ID" --query "Addresses[0].PublicIp" --output text)
echo "    Using Elastic IP: $EIP_ADDRESS ($EIP_ALLOC_ID)"

### 3. Point DNS at the EIP now, so it has time to propagate while the box boots ###
echo "==> Upserting Route53 A records"
cat > /tmp/route53-change.json <<JSON
{
  "Changes": [
    {"Action": "UPSERT", "ResourceRecordSet": {"Name": "${DOMAIN}.", "Type": "A", "TTL": 300,
      "ResourceRecords": [{"Value": "${EIP_ADDRESS}"}]}},
    {"Action": "UPSERT", "ResourceRecordSet": {"Name": "${WWW_DOMAIN}.", "Type": "A", "TTL": 300,
      "ResourceRecords": [{"Value": "${EIP_ADDRESS}"}]}}
  ]
}
JSON
aws route53 change-resource-record-sets --hosted-zone-id "$ZONE_ID" \
  --change-batch file:///tmp/route53-change.json >/dev/null
echo "    ${DOMAIN} and ${WWW_DOMAIN} -> ${EIP_ADDRESS}"

### 4. S3 bucket for the site content (private — instance pulls via IAM role) ###
echo "==> Preparing S3 bucket"
if ! aws s3api head-bucket --bucket "$S3_BUCKET" 2>/dev/null; then
  if [[ "$REGION" == "us-east-1" ]]; then
    aws s3api create-bucket --bucket "$S3_BUCKET" --region "$REGION" >/dev/null
  else
    aws s3api create-bucket --bucket "$S3_BUCKET" --region "$REGION" \
      --create-bucket-configuration LocationConstraint="$REGION" >/dev/null
  fi
  aws s3api put-public-access-block --bucket "$S3_BUCKET" --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
  aws s3api put-bucket-encryption --bucket "$S3_BUCKET" --server-side-encryption-configuration \
    '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
fi
aws s3 cp "$SITE_FILE" "s3://${S3_BUCKET}/${SITE_FILE}" >/dev/null
echo "    Uploaded ${SITE_FILE} to s3://${S3_BUCKET}/"

### 5. IAM role — SSM only, plus scoped read on this one bucket/object ###
echo "==> Preparing IAM role"
ROLE_NAME="${PROJECT_TAG}-instance-role"
if ! aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
  cat > /tmp/trust-policy.json <<'JSON'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}
JSON
  aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document file:///tmp/trust-policy.json \
    --tags "Key=Project,Value=${PROJECT_TAG}" >/dev/null
  aws iam attach-role-policy --role-name "$ROLE_NAME" \
    --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
  cat > /tmp/s3-read-policy.json <<JSON
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": ["s3:GetObject"], "Resource": "arn:aws:s3:::${S3_BUCKET}/*"}
  ]
}
JSON
  aws iam put-role-policy --role-name "$ROLE_NAME" --policy-name "${PROJECT_TAG}-s3-read" \
    --policy-document file:///tmp/s3-read-policy.json
fi

INSTANCE_PROFILE="${PROJECT_TAG}-instance-profile"
if ! aws iam get-instance-profile --instance-profile-name "$INSTANCE_PROFILE" >/dev/null 2>&1; then
  aws iam create-instance-profile --instance-profile-name "$INSTANCE_PROFILE" >/dev/null
  aws iam add-role-to-instance-profile --instance-profile-name "$INSTANCE_PROFILE" --role-name "$ROLE_NAME"
  echo "    Waiting for instance profile to propagate..."
  sleep 12
fi

### 6. Security group — 80/443 only, no SSH, ever ###
echo "==> Preparing security group"
VPC_ID=$(aws ec2 describe-vpcs --region "$REGION" --filters Name=is-default,Values=true \
  --query "Vpcs[0].VpcId" --output text)
SG_NAME="${PROJECT_TAG}-web-sg"
SG_ID=$(aws ec2 describe-security-groups --region "$REGION" \
  --filters "Name=group-name,Values=${SG_NAME}" "Name=vpc-id,Values=${VPC_ID}" \
  --query "SecurityGroups[0].GroupId" --output text 2>/dev/null || true)
if [[ "$SG_ID" == "None" || -z "$SG_ID" ]]; then
  SG_ID=$(aws ec2 create-security-group --region "$REGION" --group-name "$SG_NAME" \
    --description "HTTP/HTTPS only - no SSH, admin access is via SSM Session Manager" \
    --vpc-id "$VPC_ID" --query GroupId --output text)
  aws ec2 authorize-security-group-ingress --region "$REGION" --group-id "$SG_ID" \
    --ip-permissions \
      IpRanges="[{CidrIp=0.0.0.0/0,Description='HTTP'}]",IpProtocol=tcp,FromPort=80,ToPort=80 \
      IpRanges="[{CidrIp=0.0.0.0/0,Description='HTTPS'}]",IpProtocol=tcp,FromPort=443,ToPort=443 \
    >/dev/null
  aws ec2 create-tags --region "$REGION" --resources "$SG_ID" --tags "Key=Project,Value=${PROJECT_TAG}"
fi
echo "    Security group: $SG_ID (80, 443 only — port 22 not present)"

### 7. Latest Amazon Linux 2023 AMI ###
AMI_ID=$(aws ssm get-parameters --region "$REGION" \
  --names /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --query "Parameters[0].Value" --output text)
echo "==> Using AMI: $AMI_ID"

### 8. Render user-data and launch the instance ###
echo "==> Rendering bootstrap script"
sed -e "s#__DOMAIN__#${DOMAIN}#g" \
    -e "s#__WWW_DOMAIN__#${WWW_DOMAIN}#g" \
    -e "s#__BUCKET__#${S3_BUCKET}#g" \
    -e "s#__SITE_KEY__#${SITE_FILE}#g" \
    -e "s#__EMAIL__#${LETSENCRYPT_EMAIL}#g" \
    user-data.sh > /tmp/user-data-rendered.sh

echo "==> Launching instance"
INSTANCE_ID=$(aws ec2 run-instances --region "$REGION" \
  --image-id "$AMI_ID" \
  --instance-type "$INSTANCE_TYPE" \
  --iam-instance-profile "Name=${INSTANCE_PROFILE}" \
  --security-group-ids "$SG_ID" \
  --metadata-options "HttpTokens=required,HttpEndpoint=enabled,HttpPutResponseHopLimit=1" \
  --block-device-mappings 'DeviceName=/dev/xvda,Ebs={VolumeSize=8,VolumeType=gp3,Encrypted=true,DeleteOnTermination=true}' \
  --user-data file:///tmp/user-data-rendered.sh \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${PROJECT_TAG}},{Key=Project,Value=${PROJECT_TAG}}]" \
  --query "Instances[0].InstanceId" --output text)
echo "    Instance: $INSTANCE_ID"

echo "==> Waiting for instance to reach 'running'"
aws ec2 wait instance-running --region "$REGION" --instance-ids "$INSTANCE_ID"

### 9. Associate the Elastic IP ###
echo "==> Associating Elastic IP"
aws ec2 associate-address --region "$REGION" --instance-id "$INSTANCE_ID" \
  --allocation-id "$EIP_ALLOC_ID" >/dev/null

echo "============================================="
echo " Done. Infrastructure is up; host bootstrapping."
echo "============================================="
```

### Detailed Script Walkthrough

- **Lines 1–9 (Setup and Variables)**: Establishes `set -euo pipefail` for error tolerance and safety. Configures domain parameters, target region, compute tier (`t3.micro`), local file configuration (`exit-code-automations.html`), and project tracking keys.
- **Lines 10–23 (Pre-checks and Identity Lookup)**: Validates that the necessary command-line dependencies (`aws`, `jq`) are present and that the file to deploy exists. Queries the active caller account number to formulate a unique, deterministic name for the S3 bucket (`exit-code-site-<account_id>`).
- **Lines 24–29 (Route 53 Lookup)**: Connects to the AWS Route 53 API, queries the zones in the account, matches the target domain name, and filters out the Hosted Zone ID. If the Hosted Zone is missing, it exits immediately with an error, prompting the developer to register or delegate the domain first.
- **Lines 30–43 (Elastic IP Management)**: Prevents IP proliferation. Queries the VPC for any unassociated Elastic IPs. If none are available, it requests a new allocation. The public IP address and allocation ID are extracted to configure DNS records.
- **Lines 44–59 (DNS Upsert)**: Compiles a Route 53 changes batch JSON configuration. It upserts `A` records pointing the domain and `www` subdomain to the target Elastic IP. By invoking this API call now, DNS propagation is running concurrently while the instance is provisioning and bootstrapping.
- **Lines 60–75 (S3 Configuration)**: Ensures S3 security compliance. Checks if the bucket exists. If not, it creates the bucket (applying regional location constraints if running outside of `us-east-1`). It applies a strict public access block policy to ensure that no developer can accidentally configure public access via S3 ACLs, and applies server-side encryption with Amazon managed keys (SSE-S3). Finally, it uploads the source file.
- **Lines 76–105 (IAM Instance Profile)**: Generates the IAM configuration. It constructs a trust relationship policy allowing EC2 instances to assume roles. It creates the role, attaches the standard AWS-managed `AmazonSSMManagedInstanceCore` policy for Systems Manager, and adds an inline policy granting read-only S3 access (`s3:GetObject`) strictly scoped to the site bucket. It wraps the role in an Instance Profile and pauses for 12 seconds to ensure IAM changes propagate globally throughout AWS.
- **Lines 106–125 (Security Group)**: Queries the Default VPC ID. Checks if the designated web security group exists. If missing, it creates the security group, adding ingress authorization rules allowing TCP connections on port 80 and port 443 from any IPv4 source (`0.0.0.0/0`). It omits port 22 entirely.
- **Lines 126–130 (AMI Lookup)**: Queries the Systems Manager Parameter Store. By fetching `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64`, it obtains the latest AMI ID for Amazon Linux 2023, ensuring the instance starts with the latest security updates.
- **Lines 131–150 (Instance Launch and Bootstrap)**: Renders the EC2 User-Data bootstrap script by replacing variables (using `sed`) with their actual values. Launches the instance, forcing IMDSv2 (metadata service v2) and configuring root volume encryption (gp3, 8 GB size).
- **Lines 151–157 (EIP Association)**: Waits until the instance state changes to `running` using `aws ec2 wait instance-running`. It then binds the static Elastic IP to the newly launched instance, routing all traffic from the public IP to the virtual host.

---

## 4. The Complete user-data.sh Script & Line-by-Line Breakdown

Once the EC2 host starts up, it executes the bootstrapping script `user-data.sh` as the root user.

Here is the complete source code for `user-data.sh`:

```bash
#!/bin/bash
# Runs once, as root, on first boot (Amazon Linux 2023).
set -euxo pipefail
exec > >(tee -a /var/log/user-data.log) 2>&1

DOMAIN="__DOMAIN__"
WWW_DOMAIN="__WWW_DOMAIN__"
BUCKET="__BUCKET__"
SITE_KEY="__SITE_KEY__"
EMAIL="__EMAIL__"

echo "=== $(date) : starting bootstrap for ${DOMAIN} ==="

### System update + packages ###
dnf -y update
dnf -y install nginx certbot python3-certbot-nginx dnf-automatic

### SSH is not part of this box's access model — disable it outright. ###
systemctl disable --now sshd || true

### Pull the site from the private S3 bucket via the instance's IAM role ###
mkdir -p /usr/share/nginx/html
aws s3 cp "s3://${BUCKET}/${SITE_KEY}" /usr/share/nginx/html/index.html

### Base nginx server block — HTTP only for now; certbot adds the HTTPS ###
rm -f /etc/nginx/conf.d/default.conf
cat > /etc/nginx/conf.d/exit-code.conf <<NGINX
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} ${WWW_DOMAIN};

    root /usr/share/nginx/html;
    index index.html;

    server_tokens off;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {
        try_files \$uri \$uri/ =404;
    }
}
NGINX

nginx -t
systemctl enable --now nginx

### Wait for DNS to actually resolve to this box before asking Let's Encrypt ###
echo "Waiting for ${DOMAIN} to resolve to this instance's public IP..."
MY_IP=$(curl -s -H "X-aws-ec2-metadata-token: $(curl -s -X PUT 'http://169.254.169.254/latest/api/token' -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600')" http://169.254.169.254/latest/meta-data/public-ipv4)
for i in $(seq 1 30); do
  RESOLVED=$(dig +short "${DOMAIN}" @8.8.8.8 | tail -n1 || true)
  if [[ "$RESOLVED" == "$MY_IP" ]]; then
    echo "DNS OK: ${DOMAIN} -> ${RESOLVED}"
    break
  fi
  echo "  (${i}/30) ${DOMAIN} -> '${RESOLVED}', want ${MY_IP} — retrying in 20s"
  sleep 20
done

### Request the certificate. --redirect makes certbot rewrite the :80 ###
### block above into an HTTP->HTTPS redirect and add the :443 block.   ###
if certbot --nginx -d "${DOMAIN}" -d "${WWW_DOMAIN}" \
    --non-interactive --agree-tos -m "${EMAIL}" --redirect; then
  echo "Certbot succeeded."
else
  echo "Certbot failed — DNS probably hadn't propagated yet."
fi

### Auto-renewal — belt and suspenders alongside whatever certbot itself installs ###
cat > /etc/systemd/system/certbot-renew.service <<'EOF'
[Unit]
Description=Certbot renewal

[Service]
Type=oneshot
ExecStart=/usr/bin/certbot renew --nginx --quiet
ExecStartPost=/usr/bin/systemctl reload nginx
EOF

cat > /etc/systemd/system/certbot-renew.timer <<'EOF'
[Unit]
Description=Run certbot renew twice daily

[Timer]
OnCalendar=*-*-* 00,12:00:00
RandomizedDelaySec=3600
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now certbot-renew.timer

### OS security patches applied automatically ###
sed -i 's/^apply_updates.*/apply_updates = yes/' /etc/dnf/automatic.conf
systemctl enable --now dnf-automatic.timer

echo "=== $(date) : bootstrap complete ==="
```

### Detailed Script Walkthrough

- **Lines 1–5 (Logging Setup)**: Sets script execution options for tracing and safety (`set -euxo pipefail`). It redirects standard output and standard error stream into `/var/log/user-data.log` while still outputting them to the terminal console using the `tee` utility.
- **Lines 6–13 (Variables)**: Declares configuration variables populated by `sed` during deployment (root domain, www subdomain, private S3 bucket name, site HTML file key, and email address).
- **Lines 14–18 (Package Installation)**: Updates the local RPM database and executes the DNF package manager to install Nginx, Certbot (and the Python Nginx integration plugin), and `dnf-automatic`.
- **Lines 19–21 (Disabling SSH)**: Disables the SSH daemon (`sshd`). This terminates any active daemon processes and removes SSH from the system startup services.
- **Lines 22–25 (Content Retrieval)**: Creates the Nginx web root directory structure and invokes the AWS CLI to copy the static HTML file from the private S3 bucket directly to `/usr/share/nginx/html/index.html`.
- **Lines 26–52 (Nginx Configuration)**: Deletes the default virtual host file and writes a custom configuration block (`/etc/nginx/conf.d/exit-code.conf`) containing server definitions for ports 80. It enforces security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`) and disables server token signatures. The config is validated using `nginx -t` before the Nginx systemd daemon is started.
- **Lines 53–64 (DNS Propagation Polling)**: Requests the instance public IP address using the IMDSv2 metadata endpoint (fetching an API token first). It enters a loop, querying Google DNS (`8.8.8.8`) using `dig +short` up to 30 times with a 20-second pause between attempts. The loop breaks once the public DNS records propagate and match the instance's public IP address.
- **Lines 65–76 (SSL Provisioning)**: Invokes Certbot using the Nginx plugin. It agrees to the Let's Encrypt terms of service, registers the specified email for expiration alerts, runs non-interactively, and inserts rules to redirect all incoming HTTP traffic to HTTPS automatically.
- **Lines 77–103 (Certificate Auto-Renewal)**: Configures systemd scripts. It creates a systemd service (`certbot-renew.service`) that runs Certbot's renew command and reloads Nginx to apply the renewed certificate. It binds this execution to a systemd timer (`certbot-renew.timer`) scheduled to run twice daily at midnight and noon with a randomized delay to balance load on Let's Encrypt servers.
- **Lines 104–108 (Automated Security Patching)**: Configures the `dnf-automatic` security daemon to automatically install security updates on a schedule. It enables the `dnf-automatic.timer` to run patch processes in the background.

---

## 5. The Complete teardown.sh Script & Line-by-Line Breakdown

To clean up all AWS resources and prevent lingering charges, we use the `teardown.sh` script.

Here is the complete source code for `teardown.sh`:

```bash
#!/usr/bin/env bash
#
# teardown.sh — removes everything deploy.sh created.
#
set -euo pipefail

DOMAIN="exit-code.net"
REGION="${AWS_REGION:-us-east-1}"
PROJECT_TAG="exit-code-automations"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
S3_BUCKET="exit-code-site-${ACCOUNT_ID}"

echo "This will terminate the instance, release the EIP, and delete the"
echo "security group, IAM role, and S3 bucket for ${PROJECT_TAG}."
read -rp "Type 'yes' to continue: " CONFIRM
[[ "$CONFIRM" == "yes" ]] || { echo "Aborted."; exit 0; }

INSTANCE_ID=$(aws ec2 describe-instances --region "$REGION" \
  --filters "Name=tag:Project,Values=${PROJECT_TAG}" "Name=instance-state-name,Values=running,stopped,pending" \
  --query "Reservations[0].Instances[0].InstanceId" --output text)

if [[ "$INSTANCE_ID" != "None" && -n "$INSTANCE_ID" ]]; then
  echo "==> Terminating instance $INSTANCE_ID"
  aws ec2 terminate-instances --region "$REGION" --instance-ids "$INSTANCE_ID" >/dev/null
  aws ec2 wait instance-terminated --region "$REGION" --instance-ids "$INSTANCE_ID"
fi

EIP_ALLOC_ID=$(aws ec2 describe-addresses --region "$REGION" \
  --filters "Name=tag:Project,Values=${PROJECT_TAG}" --query "Addresses[0].AllocationId" --output text)
if [[ "$EIP_ALLOC_ID" != "None" && -n "$EIP_ALLOC_ID" ]]; then
  echo "==> Releasing Elastic IP $EIP_ALLOC_ID"
  aws ec2 release-address --region "$REGION" --allocation-id "$EIP_ALLOC_ID" || true
fi

SG_ID=$(aws ec2 describe-security-groups --region "$REGION" \
  --filters "Name=tag:Project,Values=${PROJECT_TAG}" --query "SecurityGroups[0].GroupId" --output text)
if [[ "$SG_ID" != "None" && -n "$SG_ID" ]]; then
  echo "==> Deleting security group $SG_ID"
  aws ec2 delete-security-group --region "$REGION" --group-id "$SG_ID" || echo "    (still in use? try again shortly)"
fi

ROLE_NAME="${PROJECT_TAG}-instance-role"
INSTANCE_PROFILE="${PROJECT_TAG}-instance-profile"
if aws iam get-instance-profile --instance-profile-name "$INSTANCE_PROFILE" >/dev/null 2>&1; then
  echo "==> Removing IAM instance profile / role"
  aws iam remove-role-from-instance-profile --instance-profile-name "$INSTANCE_PROFILE" --role-name "$ROLE_NAME" || true
  aws iam delete-instance-profile --instance-profile-name "$INSTANCE_PROFILE" || true
fi
if aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
  aws iam detach-role-policy --role-name "$ROLE_NAME" \
    --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore || true
  aws iam delete-role-policy --role-name "$ROLE_NAME" --policy-name "${PROJECT_TAG}-s3-read" || true
  aws iam delete-role --role-name "$ROLE_NAME" || true
fi

if aws s3api head-bucket --bucket "$S3_BUCKET" 2>/dev/null; then
  echo "==> Emptying and deleting S3 bucket $S3_BUCKET"
  aws s3 rm "s3://${S3_BUCKET}" --recursive || true
  aws s3api delete-bucket --bucket "$S3_BUCKET" --region "$REGION" || true
fi

echo "Done. Route53 hosted zone itself was NOT touched."
```

### Detailed Script Walkthrough

- **Lines 1–19 (Config & Confirmation)**: Configures environment tags, AWS region details, and active account references. Prompts the developer with an explicit warning, requesting a typed validation (`yes`) before carrying out destructive operations.
- **Lines 20–30 (Instance Termination)**: Locates the running EC2 instance by tag filters. It sends a termination command (`aws ec2 terminate-instances`) and blocks command execution until the instance is completely terminated (`aws ec2 wait instance-terminated`), ensuring that dependent network interfaces and security groups can be deleted without locking.
- **Lines 31–37 (IP Release)**: Queries for the assigned Elastic IP allocation ID using project tags and releases the static IP block back to the AWS public pool.
- **Lines 38–44 (Security Group Deletion)**: Locates the Security Group associated with the project and deletes it. If it remains bound to temporary resources, it prints a message suggesting a retry.
- **Lines 45–58 (IAM Deconstruction)**: Unbinds roles from instance profiles, deletes the profiles, detaches policies (`AmazonSSMManagedInstanceCore` and inline S3 read access), and deletes the IAM role.
- **Lines 59–64 (S3 Bucket Deconstruction)**: Empties the S3 bucket recursively, deleting the static HTML objects, and deletes the bucket itself.

---

## 6. Python 3.14 Compatibility Bug & Boto3 Workaround

During deployment, we encountered a compatibility issue between the AWS CLI v2 and the host machine's Python runtime.

### Python 3.14 Argparse Help String Validation
The host machine runs Python 3.14.4. In Python 3.14, strict string parsing changes were introduced to the standard library's `argparse` module to prevent formatting bugs. 

If a command-line tool's help strings contain unescaped percentage signs (`%`), `argparse` attempts to interpret them as string formatting placeholders. If the parsing fails, it throws a `ValueError: badly formed help string`.

Because the AWS CLI v2 contains extensive API documentation with unescaped percentage signs in its parameter descriptions (especially inside Systems Manager parameter schemas), running command-line utilities such as `aws ssm send-command` resulted in an immediate crash:

```
ValueError: badly formed help string
```

### Writing a Boto3 Python Script to Bypass Argparse
To bypass the CLI argparse layer, we wrote a Python script utilizing the `boto3` SDK. Since `boto3` interacts directly with the AWS API using JSON payloads without compiling command-line parsers, it is not affected by Python 3.14's `argparse` validation.

First, we set up a local virtual environment and installed `boto3` as outlined in our dependency guidelines:

```bash
python3 -m venv .venv
.venv/bin/pip install boto3
```

Here is the complete source code for `update_site.py`:

```python
import boto3
import time
import sys

def main():
    instance_id = "i-0b10202b2daacfb5f"
    region = "us-east-1"
    bucket = "exit-code-site-533370894129"
    key = "exit-code-automations.html"
    
    ssm_client = boto3.client('ssm', region_name=region)
    command = f"sudo aws s3 cp s3://{bucket}/{key} /usr/share/nginx/html/index.html"
    
    print(f"Sending command to {instance_id}: {command}")
    
    try:
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                'commands': [command]
            }
        )
    except Exception as e:
        print(f"Error sending command: {e}")
        sys.exit(1)
        
    command_id = response['Command']['CommandId']
    print(f"Command ID: {command_id}")
    
    # Poll for completion
    for _ in range(30):
        time.sleep(2)
        try:
            result = ssm_client.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id
            )
            status = result['Status']
            if status in ['Success', 'Failed', 'Cancelled', 'TimedOut']:
                print(f"Command execution finished with status: {status}")
                print(result.get('StandardOutputContent', ''))
                if status != 'Success':
                    sys.exit(1)
                break
        except ssm_client.exceptions.InvocationDoesNotExist:
            continue

if __name__ == '__main__':
    main()
```

Executing this script using the virtual environment's Python binary successfully triggered the update on the EC2 host:

```bash
/home/rtroiano/Downloads/exitcodezero/.venv/bin/python update_site.py
```

The script successfully copied the updated `exit-code-automations.html` from the private S3 bucket to `/usr/share/nginx/html/index.html` on the server.

---

## 7. Project Timeline & Metrics

Using the repository's Git history and logs, we computed the precise timeline from project inception to a live, SSL-enabled website on AWS:

- **18:18:00** - **Project Inception**: Repository initialized (Initial commit).
- **18:18:27** - **Script Development**: Created the foundational deployment script `deploy.sh`.
- **18:29:37** - **EC2 Setup Development**: Created `user-data.sh` to bootstrap the web host.
- **23:13:13** - **Deployment Execution**: Ran `./deploy.sh` first time. Failed due to a non-ASCII em-dash `—` in the Security Group description.
- **23:14:30** - **Hotfix Applied**: Corrected the Security Group description.
- **23:15:13** - **Successful Infrastructure Deploy**: Elastic IP allocated, S3 bucket provisioned, EC2 booted, and SSL site publicly live.
- **23:25:11** to **23:41:22** - **Frontend Polish**: Refined the HTML page layout and locked the terminal simulation height.
- **23:58:41** - **Content Sync**: Executed `update_site.py` via Boto3 to sync the polished page to the server.

### Calculation of Total Elapsed Time

- **Time from Idea to Live SSL Website**:
  - **Start**: `18:18:00`
  - **End (Deployment Succeeded)**: `23:15:13`
  - **Elapsed**: **4 hours, 57 minutes, and 13 seconds**

- **Time from Idea to Final Polished Commit**:
  - **Start**: `18:18:00`
  - **End (Last Commit)**: `23:41:22`
  - **Elapsed**: **5 hours, 23 minutes, and 22 seconds**

This deployment timeline demonstrates how automation tools and scripting can reduce typical cloud deployment times from days to under five hours, even when debugging runtime and CLI parsing bugs.

---

## 8. Systems Manager vs SSH Bastion Hosts: Security & Cost Trade-offs

When designing remote administrative access for virtual machines in a public cloud environment, engineers typically select one of four access patterns. Understanding the security and cost trade-offs of each is essential for maintaining a clean architecture:

1.  **Public SSH Exposure (Port 22 Open)**: The simplest approach is to run an SSH daemon on the host and open port 22 in the Security Group to all traffic (`0.0.0.0/0`). While functional, this exposes the host to continuous automated brute-force attacks, vulnerability scanning, and credential-stuffing campaigns. It also shifts the burden of identity management onto the host operating system, requiring the configuration of local user accounts and public key directories.
2.  **SSHD with Restricted Ingress**: Limiting port 22 access to a specific office IP address or developer's home IP reduces the risk profile. However, this configuration is brittle. Remote developers with dynamic IP addresses must constantly update Security Group rules, adding operational friction. Furthermore, it does not prevent attacks originating from compromised systems within the allowed IP range.
3.  **SSH Bastion Hosts (Jump Boxes)**: An enterprise pattern involves deploying a dedicated instance (the Bastion host) in a public subnet to act as a gateway to private subnets. Administrators SSH into the Bastion, and then jump to internal servers. 
    *   **Cost Barrier**: Under the AWS Free Tier, users receive 750 hours of free compute per month. Because a month has 720 to 744 hours, running a single EC2 instance utilizes the entire free allotment. Running a second instance (the Bastion jump box) immediately incurs a billing charge, making this pattern incompatible with our zero-cost requirement.
    *   **Operational Overhead**: Bastion hosts require regular patching, maintenance, and separate IAM/SSH configuration.
4.  **AWS Client VPN**: Deploying a client-to-site VPN allows administrators to join the VPC network securely. While highly secure, AWS Client VPN carries a base charge of $0.15 per hour per subnet association. This translates to roughly $110 per month in base fees, even with zero active users, completely violating our budget constraints.
5.  **AWS Systems Manager Session Manager**: This agent-based model is the ideal choice for single-instance, zero-cost deployments.
    *   **Zero Inbound Rules**: The host Security Group has no inbound port 22 rule. The host runs the `amazon-ssm-agent`, which connects via outbound HTTPS (port 443) to AWS systems management API endpoints. 
    *   **IAM Integration**: Authentication and authorization are offloaded entirely to AWS IAM. Administrators log in using their standard AWS credentials. Access can be restricted using IAM policies, Multi-Factor Authentication (MFA), and resource tags.
    *   **Tamper-Proof Auditing**: Since the command stream goes through the AWS API, AWS can log every keystroke and command output. These logs can be piped directly to an encrypted S3 bucket or Amazon CloudWatch Logs. Even if an attacker gains root privileges on the instance, they cannot delete or alter the audit logs stored in S3, ensuring a reliable audit trail.

For a free-tier portfolio or utility site, SSM Session Manager provides enterprise-level security and auditing with zero added infrastructure cost.

---

## 9. Operational Best Practices & Teardown

To maintain this environment over the long term, we recommend adopting the following operational practices:

### Content Sync Workflow
To push updates to the website:
1.  Verify the updated layout locally in a browser.
2.  Copy the static HTML asset to the private S3 bucket using the AWS CLI:
    ```bash
    aws s3 cp exit-code-automations.html s3://exit-code-site-533370894129/exit-code-automations.html
    ```
3.  Execute the Python boto3 script to command the EC2 instance to pull the updated file from S3:
    ```bash
    .venv/bin/python update_site.py
    ```

### Patch Management & Upgrades
Security vulnerability patching is managed automatically on the host. The bootstrap configuration enables the `dnf-automatic.timer` systemd service:

- The utility runs package checks twice daily.
- It automatically downloads and applies security patches without operator intervention.
- The administrator can review patch history on the host in `/var/log/dnf-automatic/`.

### Automated Teardown
If the hosting environment is no longer needed, running the teardown script removes all allocated resources. The script terminates the instance, releases the static Elastic IP block, deletes the Web Security Group, removes the IAM instance profiles and roles, and deletes the private S3 bucket. This ensures no residual resources remain in the account to incur charges once the 12-month free tier window expires.

---

## 10. Architectural Retrospective

Automating the deployment of exit-code.net demonstrates how a single-instance static web server can be engineered to follow modern security best practices. By replacing SSH with Systems Manager Session Manager, enforcing IMDSv2, encrypting root EBS volumes, blocking public access on S3, and utilizing automated patch timers, we establish a robust web hosting setup.

Furthermore, troubleshooting the Python 3.14 argparse incompatibility highlights the value of using programmatic SDKs like `boto3` to bypass CLI parsing issues. The entire pipeline—from the initial code commit to a public-facing website secured with Let's Encrypt SSL—was completed and verified in under five hours, showing how automation simplifies cloud operations for developers.

