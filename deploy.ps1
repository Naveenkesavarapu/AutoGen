# Deployment script for AutoGen application
param (
    [switch]$Force
)

# Function to prompt for input with validation
function Get-UserInput {
    param (
        [string]$prompt,
        [string]$default = "",
        [switch]$isPassword
    )
    
    do {
        if ($isPassword) {
            $input = Read-Host -Prompt "$prompt" -AsSecureString
            $input = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($input))
        } else {
            $input = Read-Host -Prompt "$prompt [$default]"
            if ([string]::IsNullOrWhiteSpace($input)) {
                $input = $default
            }
        }
        
        if ([string]::IsNullOrWhiteSpace($input)) {
            Write-Host "Value cannot be empty. Please try again." -ForegroundColor Red
            $isValid = $false
        } else {
            $isValid = $true
        }
    } while (-not $isValid)
    
    return $input
}

# Clear the screen and show welcome message
Clear-Host
Write-Host "AutoGen Deployment Script" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

# Collect deployment information
$config = @{
    # Server Information
    RemoteHost = Get-UserInput -prompt "Enter remote server IP/hostname" -default "localhost"
    RemoteUser = Get-UserInput -prompt "Enter remote server username" -default "$env:USERNAME"
    RemotePassword = Get-UserInput -prompt "Enter remote server password" -isPassword
    SshKeyPath = Get-UserInput -prompt "Enter SSH key path (leave empty for password auth)" -default ""
    
    # Application Configuration
    AppPort = Get-UserInput -prompt "Enter application port" -default "5000"
    AppEnv = Get-UserInput -prompt "Enter environment (production/staging)" -default "production"
    
    # Domain Configuration (if using SSL)
    UseSsl = (Get-UserInput -prompt "Configure SSL? (yes/no)" -default "no") -eq "yes"
    DomainName = ""
}

# If SSL is requested, get domain information
if ($config.UseSsl) {
    $config.DomainName = Get-UserInput -prompt "Enter domain name (e.g., example.com)" -default ""
}

# Display configuration summary
Write-Host "`nDeployment Configuration Summary:" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host "Remote Server: $($config.RemoteHost)"
Write-Host "Username: $($config.RemoteUser)"
Write-Host "Application Port: $($config.AppPort)"
Write-Host "Environment: $($config.AppEnv)"
Write-Host "SSL Enabled: $($config.UseSsl)"
if ($config.UseSsl) {
    Write-Host "Domain Name: $($config.DomainName)"
}

# Confirm deployment
$confirm = Get-UserInput -prompt "`nProceed with deployment? (yes/no)" -default "no"
if ($confirm -ne "yes") {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
    exit
}

# Create temporary deployment directory
$deployDir = ".\deploy_temp"
New-Item -ItemType Directory -Force -Path $deployDir | Out-Null

# Generate environment file
$envContent = @"
PORT=$($config.AppPort)
DEBUG=False
ENV=$($config.AppEnv)
API_VERSION=v1
API_PREFIX=/api
LOG_LEVEL=INFO
"@

$envContent | Out-File -FilePath "$deployDir\.env" -Encoding UTF8 -Force

# Generate deployment script
$deployScript = @"
#!/bin/bash
set -e

echo "Starting AutoGen deployment..."

# Update system and install dependencies
sudo apt-get update
sudo apt-get install -y python3.8 python3.8-venv python3.8-dev build-essential nginx git curl

# Create application user and directories
sudo groupadd -f autogen
sudo useradd -r -g autogen -d /opt/AutoGen -s /bin/false autogen || true
sudo mkdir -p /opt/AutoGen /var/log/autogen /opt/AutoGen/logs
sudo chown -R autogen:autogen /opt/AutoGen /var/log/autogen

# Copy application files
sudo cp -r ./* /opt/AutoGen/
sudo chown -R autogen:autogen /opt/AutoGen

# Setup Python environment
cd /opt/AutoGen
sudo -u autogen python3.8 -m venv venv
sudo -u autogen ./venv/bin/pip install --upgrade pip
sudo -u autogen ./venv/bin/pip install -r requirements.txt

# Copy configuration files
sudo cp config/mcp-server.service /etc/systemd/system/
sudo cp config/mcp-server.nginx.conf /etc/nginx/sites-available/mcp-server
sudo ln -sf /etc/nginx/sites-available/mcp-server /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Start services
sudo systemctl daemon-reload
sudo systemctl enable mcp-server
sudo systemctl start mcp-server
sudo nginx -t && sudo systemctl restart nginx

echo "Deployment completed successfully!"
"@

if ($config.UseSsl) {
    $deployScript += @"

# Setup SSL
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d $($config.DomainName) --non-interactive --agree-tos --email admin@$($config.DomainName)
"@
}

$deployScript | Out-File -FilePath "$deployDir\deploy.sh" -Encoding UTF8 -Force

# Copy necessary files to deployment directory
Copy-Item -Path ".\*" -Destination $deployDir -Recurse -Force

# Create archive for deployment
$archivePath = "$deployDir\autogen-deploy.zip"
Compress-Archive -Path "$deployDir\*" -DestinationPath $archivePath -Force

# Setup deployment command
$deployCmd = if ($config.SshKeyPath) {
    "scp -i `"$($config.SshKeyPath)`" `"$archivePath`" $($config.RemoteUser)@$($config.RemoteHost):/tmp/autogen-deploy.zip"
} else {
    "scp `"$archivePath`" $($config.RemoteUser)@$($config.RemoteHost):/tmp/autogen-deploy.zip"
}

# Deploy to remote server
try {
    Write-Host "`nDeploying to remote server..." -ForegroundColor Cyan
    
    # Copy files
    Invoke-Expression $deployCmd
    
    # Execute deployment script
    $sshCmd = if ($config.SshKeyPath) {
        "ssh -i `"$($config.SshKeyPath)`" $($config.RemoteUser)@$($config.RemoteHost)"
    } else {
        "ssh $($config.RemoteUser)@$($config.RemoteHost)"
    }
    
    $remoteCommands = @"
cd /tmp
unzip -o autogen-deploy.zip
cd autogen-deploy
chmod +x deploy.sh
./deploy.sh
"@
    
    $remoteCommands | & $sshCmd
    
    Write-Host "`nDeployment completed successfully!" -ForegroundColor Green
    Write-Host "You can access the application at: http://$($config.RemoteHost)"
    if ($config.UseSsl) {
        Write-Host "or https://$($config.DomainName)"
    }
    
} catch {
    Write-Host "Error during deployment: $_" -ForegroundColor Red
} finally {
    # Cleanup
    Remove-Item -Path $deployDir -Recurse -Force
} 