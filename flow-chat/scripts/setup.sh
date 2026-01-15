#!/bin/bash
# CIPHER Setup Script
# Run this on a fresh server to set up the complete system

set -e

echo "========================================"
echo "CIPHER Setup Script"
echo "Cross-Domain Learning System"
echo "========================================"

# Configuration
CIPHER_DIR="/opt/cipher"
CIPHER_USER="cipher"
DB_NAME="ldb"
DB_USER="lframework"
PYTHON_VERSION="3.11"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root"
    exit 1
fi

# Detect OS
if [ -f /etc/debian_version ]; then
    OS="debian"
    PKG_MANAGER="apt-get"
elif [ -f /etc/redhat-release ]; then
    OS="rhel"
    PKG_MANAGER="dnf"
else
    log_error "Unsupported OS"
    exit 1
fi

log_info "Detected OS: $OS"

# Update system
log_info "Updating system packages..."
if [ "$OS" = "debian" ]; then
    apt-get update && apt-get upgrade -y
    apt-get install -y \
        python${PYTHON_VERSION} \
        python${PYTHON_VERSION}-venv \
        python3-pip \
        postgresql \
        postgresql-contrib \
        git \
        curl \
        htop \
        vim
else
    dnf update -y
    dnf install -y \
        python${PYTHON_VERSION} \
        python${PYTHON_VERSION}-pip \
        postgresql-server \
        postgresql-contrib \
        git \
        curl \
        htop \
        vim
fi

# Create cipher user if not exists
if ! id "$CIPHER_USER" &>/dev/null; then
    log_info "Creating cipher user..."
    useradd -r -m -d $CIPHER_DIR -s /bin/bash $CIPHER_USER
fi

# Setup PostgreSQL
log_info "Setting up PostgreSQL..."
if [ "$OS" = "debian" ]; then
    systemctl start postgresql
    systemctl enable postgresql
else
    postgresql-setup --initdb
    systemctl start postgresql
    systemctl enable postgresql
fi

# Create database and user (if not exists)
log_info "Creating database..."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD 'changeme';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# Run schema
log_info "Applying database schema..."
if [ -f "$CIPHER_DIR/sql/schema.sql" ]; then
    sudo -u postgres psql -d $DB_NAME -f "$CIPHER_DIR/sql/schema.sql"
fi

# Setup Python virtual environment
log_info "Setting up Python environment..."
cd $CIPHER_DIR
python${PYTHON_VERSION} -m venv venv
source venv/bin/activate

# Install dependencies
log_info "Installing Python dependencies..."
pip install --upgrade pip
pip install \
    asyncpg \
    aiohttp \
    asyncio \
    psycopg2-binary \
    python-dotenv

# Create directory structure
log_info "Creating directory structure..."
mkdir -p $CIPHER_DIR/{mind,tools,integrations,resources,logs,config,sql,scripts}

# Set permissions
log_info "Setting permissions..."
chown -R $CIPHER_USER:$CIPHER_USER $CIPHER_DIR
chmod -R 750 $CIPHER_DIR
chmod 700 $CIPHER_DIR/config  # Config contains credentials

# Create environment file
log_info "Creating environment file..."
cat > $CIPHER_DIR/.env << 'EOF'
# CIPHER Environment Configuration
# Edit these values for your setup

# Database
CIPHER_DB_HOST=localhost
CIPHER_DB_PORT=5432
CIPHER_DB_NAME=ldb
CIPHER_DB_USER=lframework
CIPHER_DB_PASSWORD=changeme

# Paths
CIPHER_BASE_PATH=/opt/cipher

# API Keys (optional but recommended)
CIPHER_EMAIL=cipher@yourdomain.com
PUBMED_API_KEY=
S2_API_KEY=

# Learning Configuration
CIPHER_MAX_PAPERS=100
CIPHER_BATCH_SIZE=50
EOF

chmod 600 $CIPHER_DIR/.env
chown $CIPHER_USER:$CIPHER_USER $CIPHER_DIR/.env

# Create systemd service
log_info "Creating systemd service..."
cat > /etc/systemd/system/cipher.service << EOF
[Unit]
Description=CIPHER Cross-Domain Learning System
After=network.target postgresql.service

[Service]
Type=simple
User=$CIPHER_USER
Group=$CIPHER_USER
WorkingDirectory=$CIPHER_DIR
Environment=PATH=$CIPHER_DIR/venv/bin:/usr/bin
EnvironmentFile=$CIPHER_DIR/.env
ExecStart=$CIPHER_DIR/venv/bin/python $CIPHER_DIR/run.py
Restart=on-failure
RestartSec=60

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$CIPHER_DIR
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Create timer for periodic learning
log_info "Creating systemd timer..."
cat > /etc/systemd/system/cipher-learn.timer << EOF
[Unit]
Description=Run CIPHER learning cycle periodically

[Timer]
OnBootSec=5min
OnUnitActiveSec=6h
RandomizedDelaySec=30min

[Install]
WantedBy=timers.target
EOF

cat > /etc/systemd/system/cipher-learn.service << EOF
[Unit]
Description=CIPHER Learning Cycle
After=network.target postgresql.service

[Service]
Type=oneshot
User=$CIPHER_USER
Group=$CIPHER_USER
WorkingDirectory=$CIPHER_DIR
Environment=PATH=$CIPHER_DIR/venv/bin:/usr/bin
EnvironmentFile=$CIPHER_DIR/.env
ExecStart=$CIPHER_DIR/venv/bin/python $CIPHER_DIR/run.py --max-papers 50

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$CIPHER_DIR
PrivateTmp=true
EOF

# Reload systemd
systemctl daemon-reload

# Enable services
log_info "Enabling services..."
systemctl enable cipher-learn.timer

log_info "========================================"
log_info "Setup complete!"
log_info "========================================"
log_info ""
log_info "Next steps:"
log_info "1. Edit $CIPHER_DIR/.env with your credentials"
log_info "2. Change the database password:"
log_info "   sudo -u postgres psql -c \"ALTER USER $DB_USER PASSWORD 'your_secure_password';\""
log_info "3. Start the learning timer:"
log_info "   systemctl start cipher-learn.timer"
log_info "4. Or run manually:"
log_info "   sudo -u $CIPHER_USER $CIPHER_DIR/venv/bin/python $CIPHER_DIR/run.py"
log_info ""
log_info "View logs:"
log_info "   tail -f $CIPHER_DIR/logs/cipher.log"
log_info "   journalctl -u cipher-learn -f"
