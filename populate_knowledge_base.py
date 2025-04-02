import os
import sys
import json
from datetime import datetime
from app import app, db
from models import KnowledgeBaseEntry

def populate_knowledge_base():
    """Populate the knowledge base with initial entries from sample data"""
    print("Populating knowledge base with initial entries...")
    
    # Check if knowledge base already has entries
    existing_entries = KnowledgeBaseEntry.query.count()
    if existing_entries > 0:
        print(f"Knowledge base already contains {existing_entries} entries. Skipping.")
        return
    
    # Sample knowledge base entries based on the provided ticket samples
    entries = [
        {
            "title": "Fixing Sync Issues Between Devices",
            "content": """# How to Fix Sync Issues Between Devices

When data isn't syncing between your devices, follow these steps:

1. Ensure all devices are logged into the same account
2. Check internet connectivity on all devices
3. Go to Settings > Sync > Force Full Sync and wait 10 minutes
4. If the issue persists, check for corrupted sync tokens in your logs
5. For persistent issues, contact support with your sync logs attached

**Note:** Our latest update (v5.3+) includes a patch that prevents sync token corruption issues.
            """,
            "category": "software",
            "tags": json.dumps(["sync", "data", "troubleshooting", "mobile"]),
            "source_ticket_id": "TECH_004"
        },
        {
            "title": "Device Compatibility Information",
            "content": """# Device Compatibility Information

Our smart home application has the following compatibility requirements:

## Supported Device Models
- HT-2020 and newer: All app versions
- HT-2019: App versions up to 5.0
- HT-2018 and older: App versions up to 4.8

If you're using an older device model with a newer app version, you have two options:
1. Roll back your app to a compatible version
2. Upgrade your device to a newer model

Contact customer support for available upgrade discounts if your device is no longer supported.
            """,
            "category": "hardware",
            "tags": json.dumps(["compatibility", "smart home", "hardware", "devices"]),
            "source_ticket_id": "TECH_003"
        },
        {
            "title": "Resolving Network Connectivity Issues",
            "content": """# Resolving Network Connectivity Issues

If your app displays "No Internet Connection" despite having Wi-Fi access:

## Quick Fixes
1. Check app permissions: Go to Settings > Apps > [App Name] > Permissions and ensure "Local Network" is enabled
2. Clear app cache: Navigate to Settings > Storage > Clear Cache
3. Force stop and restart the app
4. Check if your network has restrictions for certain applications

## After App Updates
Recent updates may reset app permissions. Always check permissions after updating.

## VPN Interference
If you're using a VPN, try disconnecting it temporarily as it might interfere with the app's network detection.
            """,
            "category": "network",
            "tags": json.dumps(["network", "connectivity", "internet", "troubleshooting", "wifi"]),
            "source_ticket_id": "TECH_002"
        },
        {
            "title": "Payment Gateway Integration Guide",
            "content": """# Payment Gateway Integration Guide

## SSL Certificate Requirements
- All integrations must use TLS 1.3 or higher
- Certificates must be valid and not self-signed
- Minimum key length: 2048 bits

## Common Integration Errors
- **Invalid SSL Certificate**: Ensure your server supports TLS 1.3
- **Authentication Failed**: Check API keys and ensure they have the correct permissions
- **Invalid Request Format**: Verify JSON format matches our API documentation

## Testing Integration
Before going live, use our sandbox environment for testing:
```
api-sandbox.example.com
```

For detailed integration instructions, refer to our developer documentation.
            """,
            "category": "account",
            "tags": json.dumps(["payment", "gateway", "integration", "API", "SSL", "TLS"]),
            "source_ticket_id": "TECH_005"
        },
        {
            "title": "Troubleshooting Software Installation Failures",
            "content": """# Troubleshooting Software Installation Failures

## Common Installation Issues
If installation fails at specific percentages:

### 75% Failure
This typically indicates interference from security software:
1. Temporarily disable antivirus and firewall
2. Retry installation
3. Re-enable security software after installation completes

### Installation Hangs at 30%
1. Ensure you have admin privileges
2. Check for sufficient disk space
3. Close all other applications

### "Unknown Error" Messages
1. Download the offline installer from our website
2. Run in compatibility mode if using a newer OS
3. Install using the command line with logs: `setup.exe /log:install.txt`

Always restart your computer after failed installation attempts before trying again.
            """,
            "category": "software",
            "tags": json.dumps(["installation", "software", "troubleshooting", "error", "antivirus"]),
            "source_ticket_id": "TECH_001"
        }
    ]
    
    # Add admin user ID (assuming first admin is ID 1)
    admin_id = 1
    
    for entry_data in entries:
        entry = KnowledgeBaseEntry(
            title=entry_data["title"],
            content=entry_data["content"],
            category=entry_data["category"],
            tags=entry_data["tags"],
            source_ticket_id=entry_data.get("source_ticket_id"),
            created_by=admin_id,
            views_count=0,
            helpful_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(entry)
    
    try:
        db.session.commit()
        print(f"Successfully added {len(entries)} knowledge base entries")
    except Exception as e:
        db.session.rollback()
        print(f"Error populating knowledge base: {str(e)}")

if __name__ == "__main__":
    with app.app_context():
        populate_knowledge_base()