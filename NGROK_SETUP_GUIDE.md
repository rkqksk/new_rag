# ngrok Tunnel Setup Guide

**Date**: 2025-11-19
**Status**: Authentication Failed - Token Invalid
**Error**: ERR_NGROK_107

---

## ❌ Current Problem

Your ngrok authtoken is **invalid**:
```
35ghNrR54uU7ilR3TTaO5Fu8t1Z_3tWQ9Q8BQ1o6J66suBcwy (INVALID)
```

**Why this happens**:
- ❌ Token was reset
- ❌ Removed from team account
- ❌ Token was explicitly revoked

---

## ✅ Solution: Get New Token and Reconfigure

### **Step 1: Get Your New Authtoken**

1. Open: **https://dashboard.ngrok.com/get-started/your-authtoken**
2. Sign in with your ngrok account
3. Copy your authtoken (looks like: `2abc...xyz`)

### **Step 2: Configure ngrok (Choose One Method)**

#### **Method A: Automated Setup (Recommended)**

```bash
# Run the setup script
./setup-ngrok.sh

# When prompted, paste your new authtoken
```

#### **Method B: Manual Setup**

```bash
# Replace YOUR_TOKEN with your actual authtoken
ngrok config add-authtoken YOUR_TOKEN_HERE

# Example:
# ngrok config add-authtoken 2abcdefghijklmnopqrstuvwxyz1234567890
```

### **Step 3: Verify Configuration**

```bash
# Check config file was created
cat ~/.config/ngrok/ngrok.yml

# Expected output:
# version: "2"
# authtoken: YOUR_TOKEN
```

### **Step 4: Test Your Tunnel**

```bash
# Test with your API server
ngrok http 8001

# Or with frontend
ngrok http 3000

# Or with custom domain
ngrok http --domain=your-custom-domain.ngrok.app 8001
```

---

## 🚀 Quick Commands

### **Start Tunnel for API**
```bash
ngrok http 8001 --log=stdout
```

### **Start Tunnel for Frontend**
```bash
ngrok http 3000 --log=stdout
```

### **Start Multiple Tunnels**
```bash
# Terminal 1: API
ngrok http 8001 --log=stdout

# Terminal 2: Frontend (requires paid plan)
ngrok http 3000 --log=stdout
```

---

## 📍 Configuration Locations

**ngrok v3** (current):
- Config: `~/.config/ngrok/ngrok.yml`
- Log: `~/.config/ngrok/ngrok.log`

**ngrok v2** (legacy):
- Config: `~/.ngrok2/ngrok.yml`

---

## 🔍 Troubleshooting

### **Error: "authentication failed"**
```bash
# Solution: Get new token and reconfigure
ngrok config add-authtoken YOUR_NEW_TOKEN
```

### **Error: "tunnel not found"**
```bash
# Solution: Make sure server is running first
cd apps/api
uvicorn main:app --port 8001 &

# Then start ngrok
ngrok http 8001
```

### **Error: "address already in use"**
```bash
# Find and kill existing ngrok process
ps aux | grep ngrok
kill -9 <PID>

# Or use killall
killall ngrok
```

### **Error: "account limit exceeded"**
```bash
# Free plan limits:
# - 1 tunnel at a time
# - 40 connections/minute
# - Random subdomain

# Solution: Upgrade to paid plan or use 1 tunnel at a time
```

---

## 💡 Common Use Cases

### **1. Expose Local API to Internet**
```bash
# Start API server
cd apps/api
uvicorn main:app --port 8001 &

# Start ngrok tunnel
ngrok http 8001

# Your API is now available at:
# https://abc123.ngrok.app
```

### **2. Share Frontend with Team**
```bash
# Start frontend
cd apps/web
pnpm dev &

# Start ngrok tunnel
ngrok http 3000

# Share the URL: https://xyz789.ngrok.app
```

### **3. Test Webhooks (Stripe, GitHub, etc.)**
```bash
# Start API with webhook handler
uvicorn main:app --port 8001 &

# Start ngrok
ngrok http 8001

# Use ngrok URL as webhook endpoint:
# https://abc123.ngrok.app/api/v1/webhooks/stripe
```

### **4. Custom Domain (Paid Plan)**
```bash
ngrok http --domain=myapp.ngrok.app 8001
```

---

## 📊 ngrok Dashboard

**Access**: https://dashboard.ngrok.com

**What you can do**:
- View active tunnels
- See request logs
- Manage authtokens
- Configure domains (paid)
- View usage statistics

---

## 🆓 Free Plan vs Paid Plan

| Feature | Free | Paid |
|---------|------|------|
| Tunnels | 1 at a time | Multiple |
| Connections | 40/min | Unlimited |
| Domain | Random | Custom |
| TLS | Yes | Yes |
| HTTP/TCP | Yes | Yes |
| Reserved domains | No | Yes |
| IP Whitelisting | No | Yes |

---

## 🔐 Security Best Practices

1. **Never commit authtoken to git**
   ```bash
   # Add to .gitignore
   echo "ngrok.log" >> .gitignore
   echo ".ngrok2/" >> .gitignore
   echo ".config/ngrok/" >> .gitignore
   ```

2. **Use environment variables for tokens**
   ```bash
   export NGROK_AUTHTOKEN="your_token"
   ngrok config add-authtoken $NGROK_AUTHTOKEN
   ```

3. **Rotate tokens regularly**
   - Go to dashboard
   - Reset authtoken
   - Update configuration

4. **Use IP whitelisting (paid plan)**
   ```yaml
   # ngrok.yml
   tunnels:
     api:
       proto: http
       addr: 8001
       ip_restriction:
         allow_cidrs:
           - 1.2.3.4/32
   ```

---

## 📝 Example ngrok.yml Configuration

```yaml
version: "2"
authtoken: YOUR_AUTHTOKEN_HERE

tunnels:
  api:
    proto: http
    addr: 8001
    inspect: true

  web:
    proto: http
    addr: 3000
    inspect: true

  websocket:
    proto: http
    addr: 8001
    inspect: true
    host_header: rewrite
```

**Usage**:
```bash
# Start single tunnel
ngrok start api

# Start multiple tunnels (paid plan)
ngrok start api web

# Start all tunnels
ngrok start --all
```

---

## ✅ Verification Checklist

After setup, verify:

- [ ] ngrok is installed: `ngrok version`
- [ ] Config file exists: `cat ~/.config/ngrok/ngrok.yml`
- [ ] Authtoken is valid (no errors when starting)
- [ ] Can start tunnel: `ngrok http 8001`
- [ ] Can access API through tunnel URL
- [ ] Dashboard shows active tunnel

---

## 🆘 Need Help?

**ngrok Documentation**: https://ngrok.com/docs
**Error Reference**: https://ngrok.com/docs/errors/
**Dashboard**: https://dashboard.ngrok.com
**Support**: https://ngrok.com/support

---

## 🔗 Integration with v10 Project

### **Add to docker-compose.yml** (optional)
```yaml
services:
  ngrok:
    image: ngrok/ngrok:latest
    command: http api:8001
    environment:
      - NGROK_AUTHTOKEN=${NGROK_AUTHTOKEN}
    depends_on:
      - api
    ports:
      - "4040:4040"  # ngrok web interface
```

### **Add to .env**
```bash
# ngrok Configuration
NGROK_AUTHTOKEN=your_authtoken_here
NGROK_DOMAIN=your-custom-domain.ngrok.app  # Optional, paid plan only
```

### **Add to scripts/**
```bash
# scripts/start-tunnel.sh
#!/bin/bash
cd "$(dirname "$0")/.."
ngrok http 8001 --log=stdout
```

---

**Last Updated**: 2025-11-19
**ngrok Version**: 3.33.0
**Status**: Ready for configuration
