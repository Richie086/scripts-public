# How to Update Rust Desk Pro Self Hosted - Docker

Keeping your self-hosted RustDesk Pro instance up to date is crucial for security and enjoying the latest features. If you are running RustDesk using Docker, the update process can be completed in just a few steps depending on your deployment method.

## Update via Docker Compose

If you are using a `docker-compose.yml` file, follow these steps:

### Step 1: Navigate to Your Directory

First, navigate to the directory where your `docker-compose.yml` file is located:

```bash
cd /path/to/your/rustdesk-folder
```

### Step 2: Stop the Running Services

Take down the currently running services:

```bash
sudo docker compose down
```

### Step 3: Pull the Latest Image Versions

Pull the latest images from the Docker registry:

```bash
sudo docker compose pull
```

### Step 4: Restart the Containers

Start the services back up in detached mode:

```bash
sudo docker compose up -d
```

---

## Update via Raw Docker Commands

If you deployed using raw `docker run` commands instead of a Compose file, you must manually stop, remove, and recreate the container to pull the newest tag:

### Step 1: Stop the Active Containers

```bash
docker stop rustdesk-hbbs rustdesk-hbbr
```

### Step 2: Remove the Old Container Instances

```bash
docker rm rustdesk-hbbs rustdesk-hbbr
```

### Step 3: Pull the Updated Pro Image

```bash
docker pull rustdesk/rustdesk-server-pro:latest
```

After pulling the latest image, you will need to run your original `docker run` commands to recreate the `rustdesk-hbbs` and `rustdesk-hbbr` containers with your specific settings and mapped volumes.
