#!/bin/bash
# Complete Credential Migration to admincostplus User
# Run this script with: sudo bash COMPLETE-CREDENTIAL-MIGRATION.sh

set -e

echo "🔐 Complete credential migration to admincostplus user..."
echo ""

# Ensure admincostplus home directory exists
if [ ! -d "/home/admincostplus" ]; then
    echo "⚠️  Creating /home/admincostplus directory..."
    mkdir -p /home/admincostplus
    chown admincostplus:admincostplus /home/admincostplus
    chmod 755 /home/admincostplus
    echo "✅ Home directory created"
fi

# Copy ALL .env files from jeremy's projects
echo ""
echo "📦 Copying ALL .env files from jeremy's projects..."
env_copied=0
find /home/jeremy -name ".env*" -type f 2>/dev/null | while read file; do
    relative_path="${file#/home/jeremy/}"
    target_dir="/home/admincostplus/$(dirname "$relative_path")"
    mkdir -p "$target_dir"
    cp "$file" "$target_dir/"
    ((env_copied++))
    echo "  ✓ Copied: $relative_path"
done
echo "✅ .env files copied"
echo ""

# Copy GPG keys
echo "📦 Copying GPG keys..."
if [ -d "/home/jeremy/.gnupg" ]; then
    cp -r /home/jeremy/.gnupg /home/admincostplus/
    chmod 700 /home/admincostplus/.gnupg
    chmod 600 /home/admincostplus/.gnupg/* 2>/dev/null || true
    echo "✅ GPG keys copied"
else
    echo "⚠️  No GPG keys found"
fi

# Copy SSH keys
echo ""
echo "🔑 Copying SSH keys..."
if [ -d "/home/jeremy/.ssh" ]; then
    cp -r /home/jeremy/.ssh /home/admincostplus/
    chmod 700 /home/admincostplus/.ssh
    chmod 600 /home/admincostplus/.ssh/id_* 2>/dev/null || true
    chmod 644 /home/admincostplus/.ssh/*.pub 2>/dev/null || true
    chmod 600 /home/admincostplus/.ssh/config 2>/dev/null || true
    chmod 600 /home/admincostplus/.ssh/known_hosts 2>/dev/null || true
    echo "✅ SSH keys copied"
else
    echo "⚠️  No SSH keys found"
fi

# Copy GCP credentials
echo ""
echo "☁️  Copying GCP credentials..."
if [ -d "/home/jeremy/.config/gcloud" ]; then
    mkdir -p /home/admincostplus/.config
    cp -r /home/jeremy/.config/gcloud /home/admincostplus/.config/
    echo "✅ GCP credentials copied"
else
    echo "⚠️  No GCP credentials found"
fi

# Copy password store (pass)
echo ""
echo "🔒 Copying password store..."
if [ -d "/home/jeremy/.password-store" ]; then
    cp -r /home/jeremy/.password-store /home/admincostplus/
    chmod 700 /home/admincostplus/.password-store
    echo "✅ Password store copied"
else
    echo "⚠️  No password store found"
fi

# Copy GitHub CLI config
echo ""
echo "🐙 Copying GitHub CLI config..."
if [ -d "/home/jeremy/.config/gh" ]; then
    mkdir -p /home/admincostplus/.config
    cp -r /home/jeremy/.config/gh /home/admincostplus/.config/
    echo "✅ GitHub CLI config copied"
else
    echo "⚠️  No GitHub CLI config found"
fi

# Set ownership for everything
echo ""
echo "👤 Setting ownership..."
chown -R admincostplus:admincostplus /home/admincostplus
echo "✅ Ownership set"

echo ""
echo "📊 Verification Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Count .env files
env_count=$(find /home/admincostplus -name ".env*" -type f 2>/dev/null | wc -l)
echo "✅ .env files: $env_count"

# Check GPG
if [ -d "/home/admincostplus/.gnupg" ]; then
    gpg_count=$(ls -1 /home/admincostplus/.gnupg 2>/dev/null | wc -l)
    echo "✅ GPG files: $gpg_count"
fi

# Check SSH
if [ -d "/home/admincostplus/.ssh" ]; then
    ssh_count=$(ls -1 /home/admincostplus/.ssh 2>/dev/null | wc -l)
    echo "✅ SSH files: $ssh_count"
fi

# Check GCP
if [ -d "/home/admincostplus/.config/gcloud" ]; then
    echo "✅ GCP credentials: present"
fi

# Check password store
if [ -d "/home/admincostplus/.password-store" ]; then
    pass_count=$(find /home/admincostplus/.password-store -name "*.gpg" 2>/dev/null | wc -l)
    echo "✅ Password entries: $pass_count"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉 Credential migration complete!"
echo ""
echo "Next steps:"
echo "1. Test login: sudo su - admincostplus"
echo "2. Verify GCP: gcloud auth list"
echo "3. Verify SSH: ssh-add -l"
echo "4. Verify pass: pass ls"
