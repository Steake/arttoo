# Netlify Deployment Guide

This guide will help you deploy the Arttoo application to Netlify.

## Prerequisites

1. A [Netlify account](https://www.netlify.com/)
2. Access to all required environment variables and API keys

## Deployment Steps

### 1. Connect Your Repository

1. Log in to your Netlify account
2. Click "Add new site" → "Import an existing project"
3. Choose your Git provider (GitHub, GitLab, or Bitbucket)
4. Select the `arttoo` repository

### 2. Configure Build Settings

The build settings are already configured in `netlify.toml`:

- **Build command:** `npm run build`
- **Publish directory:** `.next`
- **Node version:** 20

### 3. Configure Environment Variables

You need to set up the following environment variables in Netlify:

Go to **Site settings** → **Environment variables** and add:

#### Required Variables

- `NEXT_PUBLIC_APP_URL` - Your Netlify site URL (e.g., https://your-site.netlify.app)
- `DATABASE_URL` - PostgreSQL database connection string
- `AUTH_SECRET` - Secret key for authentication (generate with `openssl rand -base64 32`)

#### API Keys

- `NEXT_PUBLIC_UNSPLASH_ACCESS_KEY` - Unsplash API access key
- `UPLOADTHING_SECRET` - UploadThing secret key
- `UPLOADTHING_APP_ID` - UploadThing app ID
- `REPLICATE_API_TOKEN` - Replicate API token

#### Authentication Providers

##### GitHub OAuth
- `AUTH_GITHUB_ID` - GitHub OAuth client ID
- `AUTH_GITHUB_SECRET` - GitHub OAuth client secret

##### Google OAuth
- `AUTH_GOOGLE_ID` - Google OAuth client ID
- `AUTH_GOOGLE_SECRET` - Google OAuth client secret

#### Stripe Payment Integration
- `STRIPE_SECRET_KEY` - Stripe secret key
- `STRIPE_PRICE_ID` - Stripe price ID
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook secret

### 4. Database Setup

Make sure your database is set up and accessible:

```bash
# If running migrations locally first
npm run db:generate
npm run db:migrate
```

**Note:** You may need to run migrations manually or set up a separate deployment hook for database migrations.

### 5. Deploy

1. Click "Deploy site"
2. Netlify will build and deploy your application
3. Once deployed, your site will be available at the Netlify URL

### 6. Post-Deployment Configuration

After your site is deployed:

1. **Update OAuth Callbacks:**
   - Update your GitHub OAuth app callback URL to: `https://your-site.netlify.app/api/auth/callback/github`
   - Update your Google OAuth app callback URL to: `https://your-site.netlify.app/api/auth/callback/google`

2. **Update Stripe Webhooks:**
   - Add your Netlify URL to Stripe webhook endpoints: `https://your-site.netlify.app/api/webhooks/stripe`

3. **Update NEXT_PUBLIC_APP_URL:**
   - Set it to your actual Netlify domain in the environment variables

## Continuous Deployment

Once connected, Netlify will automatically deploy:
- Every push to your main branch
- Pull requests (as preview deployments)

## Troubleshooting

### Build Failures

If the build fails:
1. Check the build logs in Netlify dashboard
2. Verify all environment variables are set correctly
3. Ensure your local build works: `npm run build`

### Runtime Errors

1. Check the Netlify function logs
2. Verify database connectivity
3. Ensure all API keys are valid and have proper permissions

### Database Connection Issues

- Ensure your database allows connections from Netlify's IP addresses
- For Neon Database, ensure the connection string is correct
- Check that your database is not in sleep mode (for free tiers)

## Custom Domain

To add a custom domain:
1. Go to **Site settings** → **Domain management**
2. Click "Add custom domain"
3. Follow the instructions to configure DNS

## Additional Resources

- [Netlify Next.js Documentation](https://docs.netlify.com/integrations/frameworks/next-js/)
- [Next.js Deployment Documentation](https://nextjs.org/docs/deployment)
- [Netlify Environment Variables](https://docs.netlify.com/environment-variables/overview/)
