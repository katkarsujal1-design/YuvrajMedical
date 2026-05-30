#!/bin/bash

cd /home/admin/YuvrajMedical

echo "Pulling latest code..."
git pull origin main

echo "Restarting Gunicorn..."
sudo systemctl restart gunicorn

echo "Deployment completed!"
