#!/bin/bash

echo "🚀 DEPLOYING FIXED BACKEND TO RENDER"
echo "======================================"
echo ""

# Step 1: Verify we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "❌ ERROR: Not in dental-bot-api directory"
    exit 1
fi

# Step 2: Check git status
echo "📋 Git Status:"
git status

echo ""
echo "✅ Code is ready to deploy!"
echo ""
echo "🌐 DEPLOYMENT INSTRUCTIONS:"
echo "============================"
echo ""
echo "Option 1: AUTOMATIC (Recommended)"
echo "---------------------------------"
echo "1. Go to: https://dashboard.render.com"
echo "2. Select your 'dental-bot-api' service"
echo "3. Click 'Manual Deploy' → 'Deploy latest commit'"
echo "4. Wait 5-10 minutes for build to complete"
echo ""
echo "Option 2: MANUAL GIT PUSH"
echo "------------------------"
echo "If you have auto-deploy enabled on 'main' branch:"
echo "  git push origin feature/rate-limit-and-ci:main"
echo ""
echo "Option 3: CHECK DEPLOYMENT STATUS"
echo "---------------------------------"
echo "After deploying, verify with:"
echo "  curl https://dental-bot-api.onrender.com/health"
echo ""
echo "Expected output (NEW format):"
echo '  {"status":"ok","env":"prod","redis_connected":true/false}'
echo ""
echo "Test /heartbeat endpoint (should return 200 OK now):"
echo "  curl -X POST https://dental-bot-api.onrender.com/heartbeat \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"clinic_id\":\"lemon-main\",\"session_id\":\"test\"}'"
echo ""
echo "Once deployed, widget.lemontechno.org will work! ✨"
echo ""
