FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Install system dependencies and basic penetration testing tools
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    git \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    # Core networking tools
    nmap \
    netcat-traditional \
    telnet \
    openssh-client \
    dnsutils \
    whois \
    # Web application testing tools
    nikto \
    sqlmap \
    gobuster \
    dirb \
    whatweb \
    # Password and hash tools
    hydra \
    john \
    hashcat \
    # SMB tools
    smbclient \
    # Network analysis tools
    wireshark-common \
    tshark \
    tcpdump \
    # Python tools that require system packages
    python3-dev \
    python3-setuptools \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install additional tools manually that aren't in standard repos
RUN apt-get update && apt-get install -y unzip && \
    # Install enum4linux-ng (modern version)
    git clone https://github.com/cddmp/enum4linux-ng.git /opt/enum4linux-ng && \
    chmod +x /opt/enum4linux-ng/enum4linux-ng.py && \
    ln -s /opt/enum4linux-ng/enum4linux-ng.py /usr/local/bin/enum4linux && \
    # Install wfuzz
    pip3 install wfuzz && \
    # Install masscan from source
    git clone https://github.com/robertdavidgraham/masscan /opt/masscan && \
    cd /opt/masscan && make && make install && \
    rm -rf /var/lib/apt/lists/*

# Install additional security tools via snap
RUN apt-get update && apt-get install -y snapd
# Note: In production, you might want to install these tools differently

# Create app directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Install additional Python-based security tools
RUN pip3 install --no-cache-dir \
    impacket \
    bloodhound \
    crackmapexec \
    responder \
    dnspython \
    requests \
    beautifulsoup4 \
    paramiko \
    scapy

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/reports

# Create non-root user for security
RUN useradd -m -u 1000 pentester && \
    chown -R pentester:pentester /app && \
    # Allow pentester to use network tools that require privileges
    chmod u+s /usr/bin/nmap && \
    chmod u+s /usr/bin/masscan

# Switch to non-root user
USER pentester

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command with proper logging
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
