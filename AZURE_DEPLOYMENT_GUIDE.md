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

**5a. Navigate to Configuration:**
1. **In your App Service page**, look at the **left sidebar menu**
2. **Scroll down** to find the **"SETTINGS"** section
3. **Click on "Configuration"** (it has a ⚙️ gear icon)
4. **You'll see tabs**: Application settings, General settings, Path mappings

**5b. Add Application Settings:**
1. **Make sure** you're on the **"Application settings"** tab (default)
2. **Click "+ New application setting"** button at the top
3. **Add Setting #1**:
   - **Name**: `SCM_DO_BUILD_DURING_DEPLOYMENT`
   - **Value**: `true`
   - **Click "OK"**

4. **Click "+ New application setting"** again
5. **Add Setting #2**:
   - **Name**: `WEBSITES_ENABLE_APP_SERVICE_STORAGE`
   - **Value**: `false`
   - **Click "OK"**

6. **Click "+ New application setting"** again
7. **Add Setting #3**:
   - **Name**: `PYTHONPATH`
   - **Value**: `/home/site/wwwroot`
   - **Click "OK"**

**5c. Configure General Settings:**
1. **Click on "General settings" tab** (next to Application settings)
2. **Configure these settings**:
   - **Stack**: Python
   - **Major version**: 3.11
   - **Minor version**: 3.11 (or leave auto)
   - **Startup Command**: `python main.py`
3. **Click "Save"** at the top of the page
4. **Wait for confirmation** that settings have been saved

**Navigation Help:**
- **If you can't find Configuration**: Use the search box within your App Service page and type "Configuration"
- **Visual reference**: Look for the ⚙️ gear icon next to Configuration in the menu
- **Breadcrumb check**: Make sure you see your app name in the top breadcrumb trail

**Left Menu Structure:**
```
📋 Overview
📊 Activity log
🔧 Access control (IAM)

📁 DEPLOYMENT
   📄 Deployment Center
   🔄 Deployment slots

⚙️ SETTINGS                    ← Look for this section
   🔧 Configuration            ← Click HERE!
   🔐 Authentication
   🔒 TLS/SSL settings
   🌐 Custom domains
   📱 Scale up
   📊 Scale out
```

**What you should see after adding settings:**
```
Application Settings:
- SCM_DO_BUILD_DURING_DEPLOYMENT = true
- WEBSITES_ENABLE_APP_SERVICE_STORAGE = false  
- PYTHONPATH = /home/site/wwwroot
```

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

**7a. Find Your App Name and URL:**

**How to Find Your App Name:**
1. **Method 1 - From Azure Portal:**
   - Go to [portal.azure.com](https://portal.azure.com)
   - Search "App Services" in the top search bar
   - Your app should be listed as: **`kiran-sales-dashboard-2024`**
   - Click on it to open the app service page

2. **Method 2 - From Overview Page:**
   - In your App Service, click **"Overview"** in the left sidebar
   - Look for **"URL"** on the right side of the Overview page
   - Your URL will show: `https://kiran-sales-dashboard-2024.azurewebsites.net`
   - The app name is: `kiran-sales-dashboard-2024` (everything before `.azurewebsites.net`)

**Your Complete App Information:**
- **App Name**: `kiran-sales-dashboard-2024`
- **Base URL**: `https://kiran-sales-dashboard-2024.azurewebsites.net`
- **API Base**: `https://kiran-sales-dashboard-2024.azurewebsites.net/api`

**7b. Check Deployment Status First:**
1. **Go to your App Service** → **"Deployment Center"**
2. **Look at deployment history**:
   - ✅ **Green checkmark**: Deployment successful
   - 🔄 **Blue circle**: Deployment in progress (wait for completion)
   - ❌ **Red X**: Deployment failed (check logs)
3. **If deployment is still running**: Wait 5-10 minutes and refresh
4. **If deployment failed**: Click on the failed deployment → View logs for error details

**7c. Test Basic App Access:**
1. **Only test after deployment shows successful** (green checkmark)
2. **Click on your app URL** or paste it in a new browser tab
3. **What you should see**:
   - ✅ **Success**: A webpage loads (even if it shows an error, the app is running)
   - ❌ **Failure**: "This site can't be reached" or "Application Error"

**If you see "This site can't be reached":**
- Deployment is likely still in progress or failed
- Go back to Deployment Center and check status
- Wait for deployment to complete before testing URLs

**7d. Test API Endpoints (Only After Successful Deployment):**
**⚠️ IMPORTANT: Only test these URLs AFTER your deployment shows a green checkmark in Deployment Center**

**Your Specific API URLs:**
Based on your app name `kiran-sales-dashboard-2024`, here are your exact API endpoints:

1. **Test Basic API**:
   - **URL**: `https://kiran-sales-dashboard-2024.azurewebsites.net/api/test`
   - **Expected**: JSON response with "message": "API is working"
   - **How to test**: Copy and paste this exact URL in your browser

2. **Test Sales Performance API**:
   - **URL**: `https://kiran-sales-dashboard-2024.azurewebsites.net/api/overall_sales_performance`
   - **Expected**: JSON data with revenue streams and amounts
   - **How to test**: Copy and paste this exact URL in your browser

3. **Test Other APIs** (optional):
   - **Monthly transfers**: `https://kiran-sales-dashboard-2024.azurewebsites.net/api/monthly_transfers_shipments`
   - **Sales trends**: `https://kiran-sales-dashboard-2024.azurewebsites.net/api/sales_trends_analysis`
   - **Top items**: `https://kiran-sales-dashboard-2024.azurewebsites.net/api/top_items_retail_transfers`

**Quick Copy-Paste Test URLs:**
```
https://kiran-sales-dashboard-2024.azurewebsites.net
https://kiran-sales-dashboard-2024.azurewebsites.net/api/test
https://kiran-sales-dashboard-2024.azurewebsites.net/api/overall_sales_performance
```

**7e. What Success Looks Like:**
```json
// For /api/test
{
  "message": "API is working",
  "status": "success"
}

// For /api/overall_sales_performance
{
  "revenue_streams": ["Retail Sales", "Retail Transfers", "Warehouse Sales"],
  "total_amounts": [123456, 78910, 45678]
}
```

**7f. Immediate Troubleshooting - "This site can't be reached":**

**Step 1: Check Deployment Status**
1. Go to your App Service → **Deployment Center**
2. Look at the **latest deployment** in the history
3. **Status Check**:
   - 🔄 **"Running" or "Building"**: Deployment still in progress - **WAIT**
   - ❌ **"Failed"**: Click on it → View logs → Look for error messages
   - ✅ **"Success"**: Proceed to next step

**Step 2: If Deployment is Successful but Site Still Not Working**
1. Go to **Overview** page of your App Service
2. Look for **"Status"**: Should show "Running"
3. If Status shows "Stopped": Click **"Start"** button

**Step 3: Check Application Logs**
1. Go to **Monitoring** → **Log stream**
2. Look for error messages when the app starts
3. Common errors:
   - `ModuleNotFoundError`: Missing package in requirements.txt
   - `FileNotFoundError`: Data file not found
   - `Port binding error`: Incorrect startup command

**Step 4: Verify Configuration**
1. Go to **Configuration** → **General settings**
2. Verify **Startup Command**: Should be `python main.py`
3. Check **Application settings** are all present:
   - `SCM_DO_BUILD_DURING_DEPLOYMENT = true`
   - `WEBSITES_ENABLE_APP_SERVICE_STORAGE = false`
   - `PYTHONPATH = /home/site/wwwroot`

**7g. Troubleshooting Failed Tests:**

**If app won't load:**
- Check **Log stream** in Azure Portal (Monitoring → Log stream)
- Verify **Startup Command** is `python main.py`
- Check if **requirements.txt** was installed correctly

**If APIs return errors:**
- Look at **Application Logs** for Python errors
- Verify **data file** was uploaded correctly
- Check **environment variables** are set

**If you get 404 errors:**
- Make sure you're using the correct URL format
- Check that your app is fully deployed (no deployment in progress)

**Quick Test Commands** (copy and paste these exact URLs in your browser):
```
Main App: https://kiran-sales-dashboard-2024.azurewebsites.net
Test API: https://kiran-sales-dashboard-2024.azurewebsites.net/api/test
Sales API: https://kiran-sales-dashboard-2024.azurewebsites.net/api/overall_sales_performance
```

**Expected Timeline:**
- **App startup**: 1-2 minutes after deployment
- **First request**: May take 30 seconds (cold start)
- **Subsequent requests**: Should be fast (2-3 seconds)

### Phase 4: Frontend Configuration

#### Step 8: Update Frontend URLs
Your frontend files need to point to the Azure backend:

1. **Update operational.js**:
   ```javascript
   const API_BASE = 'https://kiran-sales-dashboard-2024.azurewebsites.net/api';
   ```

2. **Update strategic.js**:
   ```javascript
   const API_BASE = 'https://kiran-sales-dashboard-2024.azurewebsites.net/api';
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
- **App Name**: `kiran-sales-dashboard-2024`
- **API Base URL**: `https://kiran-sales-dashboard-2024.azurewebsites.net`
- **Test Endpoint**: `https://kiran-sales-dashboard-2024.azurewebsites.net/api/test`
- **Frontend**: Upload to Static Web App or serve from same domain

## 💡 Tips for Success

1. **Monitor Logs**: Use Application Insights for real-time monitoring
2. **Environment Variables**: Use Azure Configuration for sensitive data
3. **Database**: Consider Azure Database for PostgreSQL for production
4. **CDN**: Use Azure CDN for better performance globally
5. **Backup**: Enable automatic backups in App Service

## 🆘 Troubleshooting

**Common Issues:**

### **Application Testing Issues**
- **App won't load**: Check Log stream (Monitoring → Log stream) for startup errors
- **404 errors on APIs**: Verify app is fully deployed and startup command is correct
- **500 internal errors**: Check Application logs for Python exceptions
- **Slow responses**: First request after deployment takes 30-60 seconds (cold start)
- **Data errors**: Verify "Sales data - Filtered" file exists in repository

### **Configuration Navigation Issues**
- **Can't find Configuration**: Search "Configuration" in your App Service page search box
- **Wrong location**: Make sure you're in your App Service (not Resource Group)
- **Missing tabs**: Refresh the page if Application settings tab doesn't appear
- **Settings not saving**: Wait for the "Saved successfully" notification before proceeding

### **Deployment Issues**
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
