set -e
echo '=== 1. Update apt ==='
sudo apt-get update -qq

echo '=== 2. Install prerequisites ==='
sudo apt-get install -y -qq git ca-certificates curl wget gnupg lsb-release jq openssl rsync >/dev/null
echo "git: $(git --version)"
echo "rsync: $(rsync --version | head -1)"

echo '=== 3. Configure /etc/resolv.conf with COFAR DNS ==='
sudo cp /etc/resolv.conf /etc/resolv.conf.bak
sudo bash -c 'cat > /etc/resolv.conf <<EOF
nameserver 172.16.10.50
nameserver 172.16.10.51
nameserver 8.8.8.8
nameserver 1.1.1.1
search cofar.com
EOF'
cat /etc/resolv.conf
echo '---'

echo '=== 4. Test DNS resolution to COFAR (puede fallar si estamos fuera de la VPN) ==='
echo "dc3-cofar.com -> $(getent hosts dc3-cofar.com 2>&1 | head -1)"
echo "google.com -> $(getent hosts google.com 2>&1 | head -1)"

echo '=== 5. Install Docker (official repo) ==='
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update -qq
sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin >/dev/null
echo "docker: $(docker --version)"
echo "compose: $(docker compose version)"

echo '=== 6. Add sistemas to docker group ==='
sudo usermod -aG docker sistemas

echo '=== 7. Enable + start docker ==='
sudo systemctl enable docker
sudo systemctl start docker
sudo systemctl is-active docker

echo '=== 8. Verify docker (usando sudo porque todavia no recargo grupo) ==='
sudo docker run --rm hello-world 2>&1 | head -8

echo '=== 9. Create /opt/sgd ==='
sudo mkdir -p /opt/sgd
sudo chown sistemas:sistemas /opt/sgd
ls -la /opt/

echo '=== 10. Create /opt/sgd/scripts and /opt/sgd/backups ==='
mkdir -p /opt/sgd/{backups,scripts,deploy}

echo '=== SETUP DOCKER COMPLETO ==='
