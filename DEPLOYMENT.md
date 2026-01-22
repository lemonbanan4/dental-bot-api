# 🚀 DEPLOYMENT CHECKLIST

**Goal:** Get widget.lemontechno.org working by deploying the fixed backend  
**Status:** All code ready, awaiting deployment

---

## ✅ Pre-Deployment Verification

### Code Quality
- ✅ All files compile without errors
- ✅ Backward compatibility endpoints implemented
- ✅ Demo clinic fallback data configured  
- ✅ Error handling with graceful fallbacks
- ✅ All changes committed to git

### Backend Ready
- ✅ `POST /chat` → Routes to modular chat handler
- ✅ `POST /heartbeat` → Old widget compat endpoint
- ✅ `POST /typing` → Old widget compat endpoint
- ✅ `POST /feedback` → Old widget compat endpoint
- ✅ `POST /leads` → Routes to modular leads handler
- ✅ `POST /admin/*` → Routes to modular admin handler
- ✅ `GET /health` → Health check endpoint
- ✅ `GET /docs` → Swagger UI for API testing

### Configuration Ready
- ✅ `.env` has all required variables
- ✅ `requirements.txt` has all dependencies
- ✅ `Dockerfile` ready for containerization
- ✅ `docker-compose.yml` ready for local testing

### Frontend Ready
- ✅ `static/widget.js` variable scope fixed
- ✅ `static/demo_embed.html` ready for testing
- ✅ Widget configuration properly validated

---

## 📋 Deployment Options

### Option A: Render (Current Platform)
**Your current deployment platform**

#### Steps:
1. Push code to GitHub
   ```bash
   cd /Users/lemon/ai-project/dental-bot-api
   git push origin feature/rate-limit-and-ci
   ```

2. Trigger Render deployment
   - Go to Render dashboard
   - Select your service
   - Click "Manual Deploy" → "Deploy latest commit"
   - Or: Merge PR to main branch (auto-deploys)

3. Wait for build/deploy (5-10 minutes)

4. Verify deployment
   ```bash
   # Test the health endpoint
   curl https://dental-bot-api.onrender.com/health
   # Should return: {"status":"ok","env":"prod","redis_connected":true/false}
   ```

### Option B: Railway (Cloud.railway.app)
**Alternative deployment**

#### Steps:
1. Install Railway CLI
   ```bash
   npm install -g @railway/cli
   ```

2. Connect to Railway project
   ```bash
   railway login
   railway link
   ```

3. Deploy
   ```bash
   railway up
   ```

4. View logs
   ```bash
   railway logs
   ```

### Option C: Docker (Local Testing Before Deploy)
**Test locally first**

#### Steps:
1. Build Docker image
   ```bash
   docker build -t dental-bot-api:latest .
   ```

2. Run container
   ```bash
   docker run -p 8000:8000 --env-file .env dental-bot-api:latest
   ```

3. Test endpoints
   ```bash
   curl http://localhost:8000/health
   curl -X POST http://localhost:8000/heartbeat \
     -H "Content-Type: application/json" \
     -d '{"clinic_id":"lemon-main","session_id":"test"}'
   ```

### Option D: Manual Linux Server
**If hosting on your own server**

#### Steps:
1. SSH into server
2. Clone repo
3. Install Python 3.9+
4. Create virtual environment
5. Install dependencies: `pip install -r requirements.txt`
6. Set environment variables
7. Run: `python -m uvicorn app.main:app --host 0.0.0.0 --port 10000`
8. Use systemd to manage service

---

## 🔐 Environment Variables to Configure

Before deploying, ensure these are set:

### Required for Chat
```env
OPENAI_API_KEY=sk-... (from OpenAI)
```

### Optional but Recommended
```env
SUPABASE_URL=https://xxxx.supabase.co (from Supabase)
SUPABASE_SERVICE_ROLE_KEY=... (from Supabase)
REDIS_URL=redis://... (from Redis provider)
```

### Configuration
```env
PUBLIC_API_BASE=https://dental-bot-api.onrender.com
ALLOWED_ORIGINS=widget.lemontechno.org,demo.yourdomain.com
APP_ENV=prod
```

### Email (Optional, for lead notifications)
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@yourdomain.com
```

---

## 🧪 Post-Deployment Testing

### 1. Check Backend Health
```bash
# Should return 200 OK
curl https://your-api.com/health

# Response should look like:
# {"status":"ok","env":"prod","redis_connected":true/false}
```

### 2. Test Backward Compat Endpoints
```bash
# Heartbeat (old widget expects this)
curl -X POST https://your-api.com/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"clinic_id":"lemon-main","session_id":"test"}'

# Should return: {"status":"ok","messages":[]}
```

### 3. Test Chat Endpoint
```bash
# Main chat endpoint
curl -X POST https://your-api.com/chat \
  -H "Content-Type: application/json" \
  -d '{
    "clinic_id":"lemon-main",
    "message":"hello",
    "session_id":"test-session"
  }'

# Should return: {"reply":"...","session_id":"..."}
```

### 4. Test with Actual Widget
- Open widget.lemontechno.org in browser
- Open browser console (F12)
- Type message
- Check for network errors
- Response should show AI reply

### 5. Check Server Logs
```bash
# For Render
# Go to Dashboard → Logs

# For Railway  
railway logs

# For custom server
tail -f /path/to/logs/app.log
```

---

## 🚨 Troubleshooting Post-Deploy

### "503 Service Unavailable"
- Server not started
- Check logs for startup errors
- Verify environment variables set

### "404 Not Found" on `/chat` or `/heartbeat`
- Routes not registered
- Check that `app/routes/` imports are in main.py
- Restart server

### "Clinic not found" errors
- Clinic doesn't exist in database
- Check that DEMO_CLINICS fallback is configured
- Verify clinic data in Supabase

### "Redis connection failed"
- Redis not available (OK - falls back to in-memory)
- Check REDIS_URL if you want Redis
- Rate limiting will use in-memory fallback

### Widget still shows errors
- Clear browser cache (Ctrl+Shift+Delete)
- Check browser console for errors (F12)
- Check server logs for errors
- Verify CORS settings

---

## 📊 Monitoring Checklist

After deployment, regularly check:

- [ ] `/health` endpoint returns `"status":"ok"`
- [ ] No 500 errors in logs
- [ ] Chat responses complete within 30 seconds
- [ ] Leads are being created and emailed
- [ ] Widget appears and responds to messages

---

## 🔄 Rollback Plan

If deployment fails:

### For Render
1. Go to Render dashboard
2. Find your service
3. Click "Deployment Settings"
4. Select previous working deployment
5. Click "Deploy"

### For Railway
```bash
railway rollback
```

### For Manual Server
```bash
# Stop service
systemctl stop dental-bot-api

# Revert code
cd /path/to/repo
git revert HEAD
git push

# Restart service
systemctl start dental-bot-api
```

---

## 📈 Next Steps After Deployment

1. **Monitor widget** - Ensure widget.lemontechno.org works
2. **Set up Supabase** - Create database tables for real data
3. **Configure email** - Set up SMTP for lead notifications
4. **Migrate clinics** - Add real clinic data to Supabase
5. **Update widget** - Eventually update widget.js to use new API

---

## ⚡ Quick Deploy (Render)

If using Render and code is on GitHub:

```bash
# 1. Make sure all changes are committed
git add -A
git commit -m "Fix: Deploy backward compatibility layer"
git push origin feature/rate-limit-and-ci

# 2. Go to Render dashboard and manually deploy
# OR merge to main branch for auto-deploy

# 3. Wait 5-10 minutes

# 4. Test
curl https://your-api.onrender.com/health
```

---

## ✨ Expected Outcome

After successful deployment:

- ✅ widget.lemontechno.org loads without errors
- ✅ Chat messages are sent and AI responds
- ✅ Clinic fallback works (lemon-main uses demo data)
- ✅ Heartbeat endpoint keeps session alive
- ✅ No 404 errors
- ✅ Backend logs show successful requests

**You're ready to deploy! 🚀**
