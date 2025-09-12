# Sales Dashboard Azure Deployment Guide

## 🚀 Complete Step-by-Step Azure Deployment

### Phase 1: Azure Portal Setup ✅ COMPLETED

#### Step 1: Create Azure Account
1. Go to [portal.azure.com](https://portal.azure.com)
2. Sign in or create a free account
3. You get $200 credit for 30 days with free account

#### Step 2: Create Resource Group
1. Search "Resource groups" in Azure Portal
2. Click "Create"
3. **Settings**:
   - Name: `sales-dashboard-rg`
   - Region: `East US` (or closest to you)
4. Click "Review + Create" → "Create"

#### Step 3: Create App Service
1. Search "App Services" in Azure Portal
2. Click "Create" → "Web App"
3. **Basic Settings**:
   - **Subscription**: Your subscription
   - **Resource Group**: `sales-dashboard-rg`
   - **Name**: `kiran-sales-dashboard-2024` (must be globally unique - try variations)
   - **Publish**: Code
   - **Runtime stack**: Python 3.11
   - **Operating System**: Linux
   - **Region**: East US (or try West US 2 if quota issues)
   - **App Service Plan**: 
     - Click "Create new"
     - Plan name: `sales-dashboard-plan`
     - **Pricing Plan**: **F1 (Free)** - Select "Change size" → "Dev/Test" → "F1 Free"
4. Click "Review + Create" → "Create"

**Note**: If you get quota errors, try F1 Free tier or different regions like West US 2 or Central US.

### Phase 2: Configure Deployment Source

#### Step 4: Connect GitHub Repository
1. Go to your created App Service in Azure Portal
2. **Deployment** → **Deployment Center**
3. **Source**: GitHub
4. **GitHub Account**: Authorize and select your account
5. **Organization**: kiranfor2004
6. **Repository**: Sales-dashboard
7. **Branch**: main
8. Click "Save"

#### Step 5: Configure Application Settings
1. Go to **Configuration** → **Application settings**
2. Add these settings:
   - **Name**: `SCM_DO_BUILD_DURING_DEPLOYMENT`
   - **Value**: `true`
3. **General settings**:
   - **Stack**: Python
   - **Major version**: 3.11
   - **Minor version**: 3.11
   - **Startup Command**: `gunicorn --bind=0.0.0.0 --timeout 600 --chdir backend app_stable:app`
4. Click "Save"

### Phase 3: Deploy and Test

#### Step 6: Trigger Deployment
1. **Navigate to Deployment Center**:
   - In your App Service → Left sidebar → **"DEPLOYMENT"** → **"Deployment Center"**
   - You should see your GitHub repo connected: `kiranfor2004/Sales-dashboard`

2. **Trigger Deployment**:
   - Look for **"Sync"** button at the top → Click **"Sync"**
   - OR if you see **"Browse"** → Click to see deployment history → Click **"Redeploy"**
   - A new deployment should appear in the list

3. **Monitor Deployment Progress**:
   - Click on the **latest deployment** in the history list
   - Click **"View Logs"** or **"Logs"** tab
   - Watch for these key stages:
     ```
     ✅ Fetching changes from GitHub
     ✅ Installing Python dependencies (pip install)
     ✅ Building application
     ✅ Starting gunicorn server
     ✅ Deployment successful
     ```

4. **Wait for Completion**:
   - **Success**: Green checkmark ✅ and "Deployment successful" message
   - **Failure**: Red X ❌ - check logs for error details
   - **Duration**: Usually takes 3-5 minutes for first deployment

**Troubleshooting Deployment:**
- If deployment fails, check the error logs
- Common issues: Missing dependencies, incorrect startup command
- Try **"Sync"** again if it gets stuck

#### Step 7: Test Your Application
1. Go to **Overview** in your App Service
2. Click on your app URL (e.g., `https://kiran-sales-dashboard.azurewebsites.net`)
3. Test the API endpoints:
   - `https://your-app.azurewebsites.net/api/test`
   - `https://your-app.azurewebsites.net/api/overall_sales_performance`

### Phase 4: Frontend Configuration

#### Step 8: Update Frontend URLs
Your frontend files need to point to the Azure backend:

1. **Update operational.js**:
   ```javascript
   const API_BASE = 'https://your-app-name.azurewebsites.net/api';
   ```

2. **Update strategic.js**:
   ```javascript
   const API_BASE = 'https://your-app-name.azurewebsites.net/api';
   ```

#### Step 9: Host Frontend Files
**Option A: Azure Static Web Apps (Recommended)**
1. Create new "Static Web App" in Azure
2. Connect to same GitHub repo
3. Set build details:
   - App location: `/frontend`
   - Output location: `/frontend`

**Option B: Same App Service**
1. Create a static route in your Flask app
2. Serve frontend files from Flask

### Phase 5: Production Optimizations

#### Step 10: Scale and Monitor
1. **Scale up**: App Service Plan → Scale up for better performance
2. **Application Insights**: Enable for monitoring
3. **Custom Domain**: Add your domain if needed
4. **SSL Certificate**: Enable HTTPS (free with App Service)

## 🔧 Configuration Files Created

✅ **Files ready for deployment**:
- `requirements.txt` - Updated with latest versions
- `startup.txt` - Azure startup command
- `Procfile` - For alternative deployment methods
- `runtime.txt` - Python version specification
- `web.config` - IIS configuration for Windows
- `main.py` - Application entry point
- `.gitignore` - Ignore unnecessary files

## 🌐 Access Your Dashboard

Once deployed successfully:
- **API Base URL**: `https://your-app-name.azurewebsites.net`
- **Test Endpoint**: `https://your-app-name.azurewebsites.net/api/test`
- **Frontend**: Upload to Static Web App or serve from same domain

## 💡 Tips for Success

1. **Monitor Logs**: Use Application Insights for real-time monitoring
2. **Environment Variables**: Use Azure Configuration for sensitive data
3. **Database**: Consider Azure Database for PostgreSQL for production
4. **CDN**: Use Azure CDN for better performance globally
5. **Backup**: Enable automatic backups in App Service

## 🆘 Troubleshooting

**Common Issues:**

### **Quota Exceeded Error (VMs)**
- **Error**: "Quota exceeded for : 0 VMs allowed, 1 VMs requested"
- **Solution 1**: Use **F1 Free tier** instead of B1 Basic
- **Solution 2**: Try different regions (West US 2, Central US, West Europe)
- **Solution 3**: Request quota increase in Subscriptions → Usage + quotas

### **Other Issues:**
- **Deployment fails**: Check Python version and requirements.txt
- **App won't start**: Verify startup command in Configuration
- **500 errors**: Check Application Logs in Log stream
- **CORS errors**: Ensure Flask-CORS is properly configured
- **Name not available**: Try variations like `kiran-sales-dashboard-2024` or `sales-dashboard-kiran`

Your application is now ready for Azure deployment! 🚀
