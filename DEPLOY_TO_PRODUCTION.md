# M1 Limousine - Production Deployment Guide

## Issue
Logo and static files visible locally but not on remote production server (62.169.19.39:8081)

## Root Cause
Static files need to be collected and served properly in production. Django's development server serves static files automatically, but production requires explicit collection to the `STATIC_ROOT` directory.

## Static Files Configuration
- **STATIC_URL**: `/static/`
- **STATIC_ROOT**: `staticfiles/` (where collected files go)
- **STATICFILES_DIRS**: `static/` (source directory)

## Logo Files Present
- `static/images/logo-white.png` ✓
- `static/images/logo-dark.png` ✓
- `static/images/favicon.ico` ✓

## Deployment Steps

### 1. Collect Static Files (Run Locally First)
```powershell
# Collect all static files into staticfiles/ directory
python manage.py collectstatic --noinput

# This will copy files from static/ to staticfiles/
# Output should show: X static files copied to 'staticfiles'
```

### 2. Push Changes to Production Server
```powershell
# Option A: Using Git (Recommended)
git add .
git commit -m "Fix: Add static files and logo for production"
git push origin main

# Then on the server, pull the changes:
# ssh user@62.169.19.39
# cd /path/to/m1limo
# git pull origin main
```

```powershell
# Option B: Using SCP/RSYNC to Transfer Files
# Replace 'user' with your actual username

# Transfer the entire staticfiles directory
scp -r staticfiles user@62.169.19.39:/path/to/m1limo/

# Or transfer just the static source files and collect on server
scp -r static user@62.169.19.39:/path/to/m1limo/
```

### 3. On Production Server - Collect Static Files
```bash
# SSH into the server
ssh user@62.169.19.39

# Navigate to project directory
cd /path/to/m1limo

# Activate virtual environment (if using one)
source venv/bin/activate  # or: . venv/bin/activate

# Collect static files on the server
python manage.py collectstatic --noinput

# Verify files were collected
ls -la staticfiles/images/
# Should see: logo-white.png, logo-dark.png, favicon.ico
```

### 4. Configure Web Server to Serve Static Files

#### For Nginx (Recommended)
Add this to your nginx configuration:

```nginx
server {
    listen 8081;
    server_name 62.169.19.39 m1limo.com;

    # Serve static files directly
    location /static/ {
        alias /path/to/m1limo/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Serve media files
    location /media/ {
        alias /path/to/m1limo/media/;
    }

    # Proxy to Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Then reload nginx:
```bash
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

#### For Apache
Add to your Apache configuration:

```apache
Alias /static/ /path/to/m1limo/staticfiles/
<Directory /path/to/m1limo/staticfiles>
    Require all granted
</Directory>

Alias /media/ /path/to/m1limo/media/
<Directory /path/to/m1limo/media>
    Require all granted
</Directory>
```

Then restart Apache:
```bash
sudo systemctl restart apache2
```

#### For Gunicorn + Whitenoise (Alternative - No Web Server Config Needed)
If you want Django to serve static files in production:

1. Install whitenoise:
```bash
pip install whitenoise
```

2. Update settings.py:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this line
    'django.contrib.sessions.middleware.SessionMiddleware',
    # ... rest of middleware
]

# Add at the end of settings.py
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

3. Restart Django application:
```bash
sudo systemctl restart gunicorn  # or your Django service name
```

### 5. Restart Django Application
```bash
# If using systemd service
sudo systemctl restart m1limo  # or your service name

# If using supervisor
sudo supervisorctl restart m1limo

# If running manually with gunicorn
pkill gunicorn
gunicorn --bind 0.0.0.0:8000 wsgi:application
```

### 6. Verify Deployment
Open browser and check:
- http://62.169.19.39:8081/ - Logo should appear
- http://62.169.19.39:8081/static/images/logo-white.png - Direct image access
- Check browser console (F12) for any 404 errors on static files

## Quick Deployment Commands (Summary)

```powershell
# LOCAL MACHINE
python manage.py collectstatic --noinput
git add .
git commit -m "Deploy: Collect static files for production"
git push origin main

# PRODUCTION SERVER
ssh user@62.169.19.39
cd /path/to/m1limo
git pull origin main
source venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart m1limo
sudo systemctl reload nginx
```

## Troubleshooting

### Logo Still Not Showing
1. **Check file permissions**:
```bash
ls -la staticfiles/images/
chmod 644 staticfiles/images/*.png
```

2. **Check browser console** (F12 → Console tab):
- Look for 404 errors on `/static/images/logo-white.png`
- Check what URL is being requested

3. **Verify STATIC_ROOT path**:
```bash
python manage.py findstatic images/logo-white.png
# Should output: Found 'images/logo-white.png' here: /path/to/staticfiles/images/logo-white.png
```

4. **Check web server logs**:
```bash
# Nginx
sudo tail -f /var/log/nginx/error.log

# Apache
sudo tail -f /var/log/apache2/error.log
```

5. **Test with DEBUG=True temporarily**:
- Set `DEBUG = True` in settings.py on production
- Django will serve static files automatically
- If logo appears, it's a web server configuration issue
- **Remember to set DEBUG=False again!**

## Production Settings Checklist

Ensure these settings are correct in production:

```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['62.169.19.39', 'm1limo.com', 'localhost']

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

CSRF_TRUSTED_ORIGINS = ['http://62.169.19.39:8081']
BASE_URL = 'http://62.169.19.39:8081'
```

## Next Steps After Deployment
1. ✓ Verify logo appears on homepage
2. ✓ Test all pages for broken images/CSS
3. ✓ Check browser console for 404 errors
4. ✓ Test mobile navigation
5. ✓ Create a test reservation to verify full flow

## Need Help?
If issues persist:
1. Share the output of `python manage.py collectstatic --noinput`
2. Share nginx/apache error logs
3. Share browser console errors (F12)
4. Verify the actual deployment method you're using (Git, FTP, etc.)
