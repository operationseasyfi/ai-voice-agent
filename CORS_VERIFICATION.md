# CORS Fix Verification Guide

This document provides commands to verify that the CORS fix is working correctly in production.

## Changes Made

1. **Global Exception Handlers**: Added exception handlers for all error types (HTTPException, RequestValidationError, and generic Exception) that ensure CORS headers are present on error responses.

2. **Response Middleware**: Added HTTP middleware that guarantees CORS headers and debug version header on ALL responses, including error responses.

3. **Debug Header**: Added `X-Debug-Version: 2025-01-28-cors-fix` header to all responses to verify the deployed code is running.

4. **OPTIONS Preflight Handler**: Explicit handling of OPTIONS requests in middleware.

## Verification Commands

### 1. Check for Debug Header (Verify Deployment)

After deploying, verify the new code is running by checking for the debug header:

```bash
curl -i -H "Origin: https://ai-voice-agent-frontend-l6bu.onrender.com" \
  "https://ai-voice-agent-30yv.onrender.com/api/phone-numbers/"
```

**Expected Result**: You should see `x-debug-version: 2025-01-28-cors-fix` in the response headers.

**If you don't see this header**: The deployed container is not running the updated code. Check:
- Docker build completed successfully
- Deployment completed
- Container is using the correct entrypoint (start.py)

### 2. Verify CORS Headers on Success Response

```bash
curl -i -H "Origin: https://ai-voice-agent-frontend-l6bu.onrender.com" \
  "https://ai-voice-agent-30yv.onrender.com/health"
```

**Expected Headers**:
```
access-control-allow-origin: https://ai-voice-agent-frontend-l6bu.onrender.com
access-control-allow-credentials: true
access-control-allow-methods: GET,POST,PUT,DELETE,OPTIONS,PATCH
access-control-allow-headers: Content-Type,Authorization
x-debug-version: 2025-01-28-cors-fix
```

### 3. Verify CORS Headers on Error Response (500)

This is the critical test - ensure CORS headers are present even when the backend returns a 500 error:

```bash
curl -i -H "Origin: https://ai-voice-agent-frontend-l6bu.onrender.com" \
  "https://ai-voice-agent-30yv.onrender.com/api/phone-numbers/"
```

**Expected Result**: 
- If the endpoint requires authentication and you're not authenticated, you should get a 401/403 with CORS headers
- If there's a database error, you should get a 500 with CORS headers
- **The key is**: You should ALWAYS see `access-control-allow-origin` header, even on error responses

**Before the fix**: You would see a 500 response but NO `access-control-allow-origin` header, causing the browser to block it.

**After the fix**: You should see a 500 response WITH `access-control-allow-origin` header, allowing the browser to show the actual error message.

### 4. Verify OPTIONS Preflight Request

```bash
curl -i -X OPTIONS \
  -H "Origin: https://ai-voice-agent-frontend-l6bu.onrender.com" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" \
  "https://ai-voice-agent-30yv.onrender.com/api/phone-numbers/"
```

**Expected Result**: 
- Status code: 204
- All CORS headers present
- `x-debug-version` header present

### 5. Test from Browser Console

After deployment, open your browser's developer console on the frontend and run:

```javascript
fetch('https://ai-voice-agent-30yv.onrender.com/api/phone-numbers/', {
  method: 'GET',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
  }
})
.then(response => {
  console.log('Status:', response.status);
  console.log('Headers:', [...response.headers.entries()]);
  return response.json();
})
.then(data => console.log('Data:', data))
.catch(error => console.error('Error:', error));
```

**Expected Result**: 
- No CORS error in console
- Response status and data are visible
- If there's a 500 error, you can see the error message instead of "Failed to fetch"

## Troubleshooting

### If CORS headers are still missing:

1. **Check deployment**: Verify `X-Debug-Version` header appears. If not, the new code isn't deployed.

2. **Check middleware order**: The custom middleware should run after CORSMiddleware. In FastAPI, middleware runs in reverse order of addition, so we add CORSMiddleware first, then our custom middleware.

3. **Check exception handlers**: Verify exception handlers are registered before routes are included.

4. **Check logs**: Look for any errors in the application logs that might indicate middleware isn't running.

### If you see the debug header but still get CORS errors:

1. **Check origin matching**: Verify the frontend origin exactly matches what's in `FRONTEND_ORIGIN` constant.

2. **Check browser cache**: Clear browser cache or use incognito mode.

3. **Check network tab**: In browser DevTools Network tab, verify the response actually contains CORS headers (sometimes the error message is misleading).

## Next Steps After CORS is Fixed

Once CORS headers are confirmed to be present on all responses:

1. **Debug the actual 500 errors**: Now that CORS is fixed, you can see the real error messages from the backend.

2. **Check backend logs**: Look at Render service logs to see stack traces for 500 errors.

3. **Common issues to check**:
   - Database connection issues
   - Missing environment variables
   - Authentication/authorization problems
   - Missing database migrations

## Summary

The fix ensures that:
- ✅ CORS headers are ALWAYS present, even on error responses
- ✅ Debug header verifies the deployed code is running
- ✅ OPTIONS preflight requests are handled correctly
- ✅ All exception types are caught and return CORS-enabled responses

This allows the browser to show actual error messages instead of blocking responses with "Failed to fetch" errors.

