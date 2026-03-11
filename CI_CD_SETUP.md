# CI/CD Setup Guide - Development to Production

## Overview
This guide sets up automatic CI/CD with:
- **Development**: Test builds on `dev` branch (stays in GitHub Actions cache)
- **Production**: Auto-deploy to VPS when merging to `main` branch

## Setup Steps

### 1. Generate SSH Key for Deployment

```bash
# On your local machine
ssh-keygen -t ed25519 -f ~/.ssh/vps-deploy-key -C "github-deploy"
cat ~/.ssh/vps-deploy-key  # Copy this for VPS_SSH_KEY secret
```

### 2. Add Public Key to VPS

```bash
# On your VPS
mkdir -p ~/.ssh
echo "PASTE_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 3. Configure GitHub Secrets

Go to **GitHub Repo** → **Settings** → **Secrets and variables** → **Actions**

Add these secrets:

| Secret Name | Value |
|------------|-------|
| `VPS_HOST` | Your VPS IP or domain (e.g., `1.2.3.4` or `bakaya.tech`) |
| `VPS_USER` | SSH user on VPS (e.g., `ubuntu`, `root`, `deploy`) |
| `VPS_SSH_KEY` | Private SSH key from step 1 (entire key including `-----BEGIN---`) |

### 4. Verify VPS SSH Access (Optional)

```bash
# From your CI machine
ssh -i ~/.ssh/vps-deploy-key ubuntu@YOUR_VPS_IP "echo 'SSH Works!'"
```

## Workflows

### Development Workflow (→ `dev` branch)

```
Your Code
    ↓
git push dev
    ↓
GitHub Actions: test-dev.yml
  - Builds Docker images
  - Runs tests
  - Does NOT push to Docker Hub
  - Does NOT deploy
    ↓
Check action results
```

**Use for**: Feature development, bug fixes, experimentation

### Production Workflow (→ `main` branch)

```
Code on dev branch
    ↓
Create Pull Request (dev → main)
    ↓
GitHub Actions: test-dev.yml runs
    ↓
Review & Merge PR
    ↓
git push main
    ↓
GitHub Actions: docker-hub.yml
  - Builds & pushes to Docker Hub (matthl2002/*)
    ↓
GitHub Actions: deploy-prod.yml
  - SSH into VPS
  - pulls latest code
  - Runs: docker compose -f docker-compose.yml -f deploy/vps/docker-compose.prod.yml up -d --build
  - Verifies health check
    ↓
🚀 Live on bakaya.tech
```

## File Structure

```
.github/workflows/
├── docker-hub.yml          # Build & push to Docker Hub (on branches)
├── deploy-prod.yml         # Deploy to VPS (main branch only)
└── test-dev.yml           # Test builds (dev & PRs)
```

## Key Points

- ✅ **dev branch**: Safe sandbox for testing
- ✅ **main branch**: Protected, auto-deploys to production
- ✅ **No manual deploy needed**: Push to main = live
- ✅ **Health checks**: Verifies deployment succeeded
- ✅ **Secrets**: All sensitive data in GitHub secrets, not in code

## Troubleshooting

### Deployment fails with "SSH: Permission denied"
- Check `VPS_SSH_KEY` secret has full private key (including `-----BEGIN-----`)
- Verify public key is in VPS `~/.ssh/authorized_keys`
- Test locally: `ssh -i key ubuntu@VPS_IP "exit"`

### Docker build fails on VPS
- SSH into VPS: `ssh ubuntu@VPS_IP`
- Check docker is running: `sudo systemctl status docker`
- Check disk space: `df -h`
- Check logs: `docker compose logs`

### Website not loading after deploy
- Wait 30-60 seconds for health checks to complete
- Check VPS: `sudo docker compose -f docker-compose.yml -f deploy/vps/docker-compose.prod.yml ps`
- Check Nginx: `sudo systemctl status nginx`
- Check logs: `sudo docker compose logs frontend backend`

## Manual Deployment (if needed)

```bash
# SSH into VPS
ssh ubuntu@bakaya.tech

# Manual deploy
cd /opt/emailfilter
git pull origin main
sudo docker compose -f docker-compose.yml -f deploy/vps/docker-compose.prod.yml up -d --build
```

## Environment Variables

Your `.env` file should exist on VPS at `/opt/emailfilter/.env` with:
- `JWT_SECRET=your_secret`
- `DB_HOST=mysql`
- `DB_USER=root`
- `DB_PASSWORD=your_password`
- `DB_NAME=detectish`
- `HF_TOKEN=your_huggingface_token`
- etc.

The CI/CD doesn't modify `.env`, so manage it separately on the VPS.
