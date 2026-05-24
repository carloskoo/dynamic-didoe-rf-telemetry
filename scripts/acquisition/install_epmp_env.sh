#!/usr/bin/env bash
set -e

sudo apt update
sudo apt install -y openssh-client sshpass gawk coreutils util-linux procps

mkdir -p /home/carlos/epmp_logs

echo "Entorno base instalado."
echo "Ahora crea /home/carlos/epmp_logs/.ap_pass con la contraseña del admin."
