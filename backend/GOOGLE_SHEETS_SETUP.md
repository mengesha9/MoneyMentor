# Google Sheets Integration Setup (Simplified)

This guide shows how to set up Google Sheets integration using only environment variables instead of JSON credential files.

## Required Environment Variables

You only need these **3 environment variables**:

```bash
GOOGLE_SHEET_ID=your_spreadsheet_id_here
GOOGLE_CLIENT_EMAIL=your_service_account_email@project-id.iam.gserviceaccount.com
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYour_Private_Key_Here\n-----END PRIVATE KEY-----"
```

## Setup Steps

### 1. Create Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Sheets API and Google Drive API
4. Go to "IAM & Admin" > "Service Accounts"
5. Create a new service account
6. Download the JSON key file

### 2. Extract Credentials from JSON

From your downloaded JSON file, extract these values:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----",
  "client_email": "service-account@project-id.iam.gserviceaccount.com",
  "client_id": "client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/service-account@project-id.iam.gserviceaccount.com"
}
```

### 3. Set Environment Variables

Add to your `.env` file:

```bash
# Google Sheets Configuration
GOOGLE_SHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
GOOGLE_CLIENT_EMAIL=your-service-account@your-project-id.iam.gserviceaccount.com
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----"
```

### 4. Create Google Sheets

1. Create a new Google Sheets document
2. Copy the spreadsheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
   ```
   The ID is: `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`

### 5. Share Spreadsheet

Share the spreadsheet with your service account email (read/write access).

## Testing the Setup

Run the debug script to test your configuration:

```bash
python debug_google_sheets.py
```

## Advantages of This Approach

✅ **No credential files needed** - Everything in environment variables  
✅ **Easier deployment** - No file management in containers  
✅ **Better security** - Credentials not stored as files  
✅ **Simpler setup** - Just 3 environment variables  
✅ **Cloud-friendly** - Works well with cloud platforms  

## Troubleshooting

### Common Issues

1. **Private Key Format**: Make sure the private key includes the full PEM format with newlines
2. **Service Account Permissions**: Ensure the service account has access to the spreadsheet
3. **API Enablement**: Make sure Google Sheets API is enabled in your Google Cloud project

### Debug Commands

```bash
# Test connection
python debug_google_sheets.py

# Check environment variables
echo $GOOGLE_SHEET_ID
echo $GOOGLE_CLIENT_EMAIL
echo $GOOGLE_PRIVATE_KEY | head -c 50
```

## Migration from JSON File

If you were previously using `GOOGLE_APPLICATION_CREDENTIALS`:

1. Extract `client_email` and `private_key` from your JSON file
2. Set the new environment variables
3. Remove the `GOOGLE_APPLICATION_CREDENTIALS` variable
4. Test with `python debug_google_sheets.py`

## Security Notes

- Keep your private key secure and never commit it to version control
- Use environment variables in production, not hardcoded values
- Rotate service account keys regularly
- Use least privilege principle for service account permissions
