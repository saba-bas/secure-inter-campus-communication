# One image for all six nodes (Ubuntu 24.04). Build ONCE while online.
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      openssl nginx strongswan strongswan-swanctl charon-systemd \
      libcharon-extra-plugins libstrongswan-extra-plugins \
      tcpdump tshark nmap curl dnsutils iproute2 iptables iputils-ping \
      python3 python3-cryptography python3-pytest \
      git ca-certificates procps xxd bsdextrautils \
    && rm -rf /var/lib/apt/lists/*
# testssl.sh 3.2 (branch)
RUN git clone --depth 1 --branch 3.2 https://github.com/testssl/testssl.sh.git /opt/testssl \
    && ln -s /opt/testssl/testssl.sh /usr/local/bin/testssl.sh
WORKDIR /work
