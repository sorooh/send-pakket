# 🚀 Send-Pakket Platform - One-Click Deployment

[![Deploy to Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/YOUR_USERNAME/sendpakket-platform)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/YOUR_USERNAME/sendpakket-platform)
[![Deploy to Fly.io](https://fly.io/button.svg)](https://fly.io/launch/github/YOUR_USERNAME/sendpakket-platform)

**Send-Pakket: European Shipping Platform** - Competing with Sendcloud through superior architecture and global scalability.

## ⚡ One-Click Deployment

### Step 1: Upload to GitHub First! 📤

**Before using the deployment buttons, you need to upload this project to GitHub:**

```bash
# Run the upload script
./push_to_github.bat
```

Or manually:
1. Create a new repository on GitHub (public or private)
2. Copy the repository URL
3. Run these commands:
```bash
git remote add origin YOUR_REPOSITORY_URL
git push -u origin master
```

### Step 2: Replace YOUR_USERNAME in Deployment Buttons

After uploading to GitHub:
1. Open this README.md file
2. Replace `YOUR_USERNAME` with your actual GitHub username
3. Commit and push the changes

### Step 3: Deploy Instantly! 🚀

### Option 1: Railway (Recommended - Easiest) 🚂
1. Click the **"Deploy to Railway"** button above
2. Connect your GitHub account
3. Select this repository
4. Railway will automatically deploy your app!

### Option 2: Render 🌀
1. Click the **"Deploy to Render"** button above
2. Connect your GitHub account
3. Render will use `render.yaml` for automatic setup

### Option 3: Fly.io ✈️
1. Click the **"Deploy to Fly.io"** button above
2. Fly.io will use `fly.toml` for deployment

### Option 4: Heroku 🟣
1. Create Heroku app
2. Connect this GitHub repository
3. Enable automatic deploys from main branch

## 📋 What You Get

- ✅ **Complete Django REST API** with 77 passing tests
- ✅ **Multi-tenant architecture** for global scalability
- ✅ **Stripe payment integration** with webhooks
- ✅ **PostgreSQL database** with Redis caching
- ✅ **Celery background tasks** with monitoring
- ✅ **Production-ready security** (HTTPS, CSRF, etc.)
- ✅ **Automatic health checks** and monitoring
- ✅ **API documentation** at `/api/docs/`

## 🔧 Quick Setup (Manual)

```bash
# Clone and setup
git clone https://github.com/YOUR_USERNAME/sendpakket-platform.git
cd sendpakket-platform

# Environment setup
cp .env.example .env.prod
# Edit .env.prod with your production values

# Deploy
./deploy.bat
```

## 🌐 API Endpoints

Once deployed, your API will be available at:
- **Base URL**: `https://your-app-url.com`
- **API Docs**: `https://your-app-url.com/api/docs/`
- **Admin Panel**: `https://your-app-url.com/admin/`
- **Health Check**: `https://your-app-url.com/health/`

## 📊 Architecture

```
🌐 Nginx (SSL, Security)
    ↓
🖥️ Django + Gunicorn (4 workers)
    ↓
📊 PostgreSQL + Redis + Celery
```

## 🔒 Security Features

- HTTPS enforcement with SSL certificates
- Rate limiting and DDoS protection
- CSRF protection and secure cookies
- Input validation and sanitization
- Multi-tenant data isolation
- JWT authentication with refresh tokens

## 🚀 Performance

- Horizontal scaling ready
- Redis caching optimized
- Database connection pooling
- Static files optimization
- Background task processing

## 📞 Support

- **Documentation**: Check `DEPLOYMENT_CHECKLIST.md`
- **Issues**: Open GitHub issues
- **Deployment Help**: Check platform-specific docs

---
**Built for Excellence - Ready to Compete Globally** 🌍✨

## 🏗️ Architecture

- **Backend**: Django 4.2.7 + DRF
- **Database**: PostgreSQL (production) / SQLite (development)
- **Cache**: Redis
- **Authentication**: JWT
- **Payments**: Stripe
- **Background Tasks**: Celery + Redis
- **Multi-tenancy**: Company-based isolation

## 🚀 Quick Start (Development)

```bash
# Clone repository
git clone <repository-url>
cd send-pakket-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

## 🐳 Production Deployment

### Quick Production Setup

1. **Configure Environment:**
   ```bash
   cp .env.example .env.prod
   # Edit .env.prod with your production values
   ```

2. **Deploy with Docker:**
   ```bash
   # For production with optimized settings
   docker-compose -f docker-compose.prod.yml up -d --build

   # Or use the deployment script
   ./deploy.bat
   ```

3. **SSL Certificate Setup:**
   ```bash
   # Using Let's Encrypt
   sudo certbot --nginx -d yourdomain.com
   ```

### Production Scripts

- `deploy.bat` - Complete deployment automation
- `backup.bat` - Database backup script
- `monitor.bat` - Production monitoring and maintenance
- `manage_prod.py` - Django management with production settings

### Production Architecture

- **Web Server:** Nginx + Gunicorn
- **Database:** PostgreSQL
- **Cache/Broker:** Redis
- **Background Tasks:** Celery + Redis
- **Monitoring:** Health checks, logging, Sentry integration

### Security Features

- HTTPS enforcement
- Security headers
- CSRF protection
- Rate limiting
- Input validation
- Secure session management

## ⚙️ Environment Variables

### Required for Production

```env
# Django Settings
DEBUG=False
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (PostgreSQL recommended)
DATABASE_URL=postgresql://user:password@db:5432/sendpakket

# Redis
REDIS_URL=redis://redis:6379/0

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## 🔧 Services Configuration

### Web Server (Nginx)

The platform includes Nginx configuration for:
- Static file serving
- SSL termination
- Gunicorn proxying
- Security headers

### Background Tasks (Celery)

```bash
# Start Celery worker
celery -A sendpakket worker -l info

# Start Celery beat (scheduled tasks)
celery -A sendpakket beat -l info
```

## 📊 Monitoring & Logging

- **Logs**: Stored in `logs/` directory
- **Monitoring**: Django Debug Toolbar (development)
- **Error Tracking**: Sentry integration ready
- **Metrics**: Platform core metrics available via API

## 🔒 Security Features

- JWT authentication with refresh tokens
- Company-based multi-tenancy
- CORS protection
- CSRF protection
- Secure headers via Nginx
- Input validation and sanitization

## 📈 API Documentation

Access API documentation at `/api/docs/` when running the server.

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run manage.py test
coverage report
```

## 🚀 Scaling

The platform is designed for horizontal scaling:
- Stateless Django application
- Redis for caching and sessions
- PostgreSQL with connection pooling
- Celery for background task distribution

## 📞 Support

For deployment issues or questions, check:
1. Django deployment documentation
2. Docker Compose logs: `docker-compose logs`
3. Application logs: `logs/django.log`

## 📋 Checklist Before Going Live

- [ ] Environment variables configured
- [ ] Database migrated
- [ ] Static files collected
- [ ] SSL certificate installed
- [ ] Domain DNS configured
- [ ] Email service tested
- [ ] Stripe webhooks configured
- [ ] Redis connectivity verified
- [ ] All tests passing
- [ ] Backup strategy in place