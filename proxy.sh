#!/bin/bash

echo "🔧 Mise à jour et suppression de TinyProxy s'il existe..."
sudo apt update
sudo apt purge tinyproxy -y
sudo rm -f /etc/tinyproxy/tinyproxy.conf

echo "📦 Installation de Squid Proxy..."
sudo apt install squid -y

echo "⚙️ Configuration du port 8080 et des règles d'accès..."
sudo sed -i 's/^http_port .*/http_port 8080/' /etc/squid/squid.conf

# Supprimer les règles de refus par défaut
sudo sed -i 's/^http_access deny all/#http_access deny all/' /etc/squid/squid.conf

# Ajouter règles pour autoriser toutes les IPs (si pas déjà présent)
sudo sed -i '1i acl all src 0.0.0.0/0\nhttp_access allow all' /etc/squid/squid.conf

echo "🔁 Redémarrage du service Squid..."
sudo systemctl restart squid

echo "✅ Proxy Squid installé et actif sur le port 8080 !"
echo "🌐 Teste avec : curl -x http://$(curl -s ifconfig.me):8080 http://example.com"
