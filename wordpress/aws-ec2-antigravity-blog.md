# Create an Amazon AWS EC2 Linux Instance to run Google Antigravity (Because Your Laptop Can't Handle It)

Welcome to the future of AI-first development! Google Antigravity (AGY) is a powerful platform that supercharges your coding workflows. Sure, you *could* try running it locally on that machine Microsoft insists on updating right when you're in the middle of a thought, but hosting Antigravity on an Amazon Web Services (AWS) EC2 instance provides 24/7 availability. Because unlike your attention span while doom-scrolling Facebook, the cloud never sleeps. 

In this guide, we'll walk you through provisioning an AWS EC2 Linux instance step-by-step and installing Google Antigravity. It's almost easy enough that an executive could do it. Almost.

---

## Prerequisites & Best Practices

Before we get started, here is what you need to know and set up:

- **AWS Account:** You will need an Amazon AWS account. Yes, Jeff Bezos wants more of your money, but we'll try to keep it free today.
- **IAM User Setup (Crucial Security Step):** **Do not use your root login** to perform any of these tasks! Using your root account for daily tasks is a terrible idea. Always create a new IAM user with the *least amount of privileges* needed. Ensure this user does not have permission to interact with any other Amazon AWS services.
- **Free Tier Instance:** I would recommend going with a free tier EC2 Linux instance to start with so you can experiment at no cost.
- **Elastic IP:** You will need to get an Elastic IP from AWS. This is a static IPv4 address that Amazon owns, ensuring your instance's IP doesn't dynamically change whenever it reboots—which happens less frequently than a Windows crash, but still.
- **Domain Name & DNS (Optional but Recommended):** Owning a domain name is not required, but highly recommended so you can have a named endpoint on the internet. A domain name is also strictly required if you plan on using SSL for secure HTTPS connections.

---

## Step 1: Allocating an Elastic IP

Before launching our instance, let's reserve a static public IP address.
1. In the AWS Management Console, navigate to the **EC2 Dashboard**.
2. Under **Network & Security** on the left menu, click **Elastic IPs**.
3. Click the orange **Allocate Elastic IP address** button at the top right and confirm the allocation. 

We will associate this IP with our EC2 instance shortly.

### Registering a Domain and Setting up DNS with Route 53 (Optional)
If you choose to use a custom domain name, AWS makes this easy via Route 53:
1. **Register a Domain:** Open the **Route 53** console in AWS. Navigate to **Registered domains** and click **Register Domain**. Search for your desired name and follow the checkout process.
2. **Setup an A Record:** Once you have your domain and your newly allocated Elastic IP, go to **Hosted zones** in Route 53. Click on your domain name, then click **Create record**. Set the *Record type* to **A - Routes traffic to an IPv4 address and some AWS resources**, and paste your Elastic IP into the *Value* box. 

---

## Step 2: Launching a Free Tier EC2 Linux Instance

Amazon will often try to push Amazon Linux 2 on you by default, which is a RedHat/Fedora-based Linux distro. Personally, I like **Ubuntu Server 26.04** because I prefer not to retrain my brain. However, if you are comfortable with RedHat, that is entirely up to you. Whatever keeps you away from Windows Server, right?

You can launch your instance using either the visual AWS Management Console (GUI) or AWS CloudShell.

### Method A: Via the AWS Management Console (GUI)
1. **Launch Instance:** From the EC2 Dashboard, click the orange **Launch Instance** button.
2. **Name:** Give your instance a recognizable name. `Antigravity-Node` is fine, though `Skynet-Alpha` is definitely funnier.
3. **AMI (OS):** Select **Ubuntu** from the Quick Start list and ensure you choose **Ubuntu Server 26.04 LTS**. Verify that the "Free tier eligible" tag is visible, unless you want to personally fund Blue Origin's next rocket launch.
4. **Instance Type:** Select a Free Tier eligible instance type (usually `t2.micro` or `t3.micro`).
5. **Key Pair:** Click **Create new key pair** if you don't already have one. Name it, choose RSA, and download the `.pem` file to your computer. **Keep this file safe!** 
6. **Network Settings & Security Group:** It is a major security risk to leave SSH open to the entire internet. You aren't Mark Zuckerberg leaving user data exposed for the world to see, so click **Edit** in the Network Settings section to create a new security group.
   - Change the **Source type** for the SSH rule to **Custom** (or **My IP**).
   - If using Custom, input your exact public IPv4 address followed by `/32`. For example, if your external IP address is `44.55.66.77`, your CIDR is `44.55.66.77/32`. 
   - **Why /32?** The `32` represents the number of bits turned on in the subnet mask for a given IP address. When all 32 subnet mask bits are 1's, it means this *specific host only*. 
7. **Storage:** Leave the default (usually 8 GB) or increase it up to 30 GB.
8. **Launch:** Click **Launch Instance** at the bottom right.
9. **Associate your IP:** Go back to the **Elastic IPs** page, select the IP you allocated earlier, click **Actions > Associate Elastic IP address**, and select your newly running instance from the dropdown.

### Method B: Via AWS CloudShell
If you prefer deploying infrastructure via the command line (because GUIs are for people who don't like reading documentation):

1. Open **CloudShell** by clicking the terminal icon `>_` in the top navigation bar of the AWS console.
2. Find the latest Ubuntu 26.04 AMI ID for your region. 
3. Launch a free tier instance:
   ```bash
   aws ec2 run-instances \
     --image-id ami-0abcdef1234567890 \
     --count 1 \
     --instance-type t2.micro \
     --key-name your-existing-keypair-name \
     --security-group-ids sg-YOUR_SG_ID \
     --subnet-id subnet-YOUR_SUBNET_ID
   ```
4. Allocate a new Elastic IP and associate it with the Instance ID returned from the previous command:
   ```bash
   aws ec2 allocate-address --domain vpc
   aws ec2 associate-address --instance-id i-YOUR_INSTANCE_ID --allocation-id eipalloc-YOUR_ALLOCATION_ID
   ```

---

## Step 3: Connecting to Your Instance

Now that your server is running with a static IP, it's time to connect to it. You have two primary options: the highly secure AWS Systems Manager or the traditional SSH approach.

### Option A: Connect Securely via AWS Systems Manager Session Manager (Recommended)
If you want to completely avoid exposing SSH (port 22) to the internet, you can use AWS Systems Manager Session Manager. This is a cloud-based terminal only accessible when you are logged into the AWS console. It supports copy/paste and is by far the most secure method of accessing AWS EC2 instances. Plus, you don't even have to open inbound ports!

1. **Attach an IAM Role to your EC2 Instance:** For Session Manager to work, your instance needs permission to communicate with the Systems Manager service. Go to the EC2 Dashboard, right-click your instance, and choose **Security > Modify IAM role**. 
2. Attach an IAM role that includes the `AmazonSSMManagedInstanceCore` policy.
3. **Connect via Console:** Once the role is attached, wait a moment for the instance agent to register. Then, select your instance in the EC2 Dashboard and click the **Connect** button at the top of the screen.
4. Select the **Session Manager** tab and click **Connect**. You will instantly be dropped into a secure, browser-based terminal!

### Option B: Connect via SSH (Traditional)
If you prefer using your local terminal, complete with hacker green-on-black text:

1. Open your local terminal (or PowerShell on Windows).
2. Navigate to the folder where you saved your `.pem` key file.
3. If you are on Mac or Linux, restrict the file permissions first:
   ```bash
   chmod 400 agy-key.pem
   ```
4. Connect using SSH and your Elastic IP (or domain name, if you set up Route 53):
   ```bash
   ssh -i "agy-key.pem" ubuntu@<Your-Elastic-IP-or-Domain>
   ```
5. Type `yes` when prompted. You are now inside your cloud environment!

---

## Step 4: Installing Google Antigravity

Google may have killed Google Reader, Google Wave, Google Plus, and Inbox, but thankfully Antigravity is here to stay (fingers crossed). Ensure your Ubuntu server is up to date and has the necessary dependencies:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install git curl unzip build-essential -y
```

With the environment prepped, run the official install script to download and configure the Antigravity CLI (`agy`):

```bash
curl -fsSL https://antigravity.google/install.sh | bash
```
*(Note: Always check the [official Antigravity documentation](https://antigravity.google/docs) for the most up-to-date commands).*

Verify the installation:
```bash
agy --version
```

To launch the Antigravity Text User Interface directly in your terminal, simply type:
```bash
agy
```

## Conclusion

Congratulations! You've successfully provisioned a secure AWS EC2 instance without handing over all your hard-earned cash to Jeff Bezos. You locked down your network tighter than Microsoft locking down Windows 11 hardware requirements, and installed Google Antigravity. By leveraging a free tier cloud server, you can effortlessly experiment with robust AI coding tools from anywhere in the world. 

Happy coding!
