# YuvrajMedical - Complete Setup Guide

This file explains what is required to run the YuvrajMedical project on another PC.

Project architecture:
- Frontend: HTML, CSS, JavaScript, Bootstrap/Jinja templates
- Backend: Python Flask
- Database: MySQL
- Reverse Proxy: Nginx
- Containerization: Docker + Docker Compose
- Optional public tunnel: Cloudflare Tunnel / cloudflared

IMPORTANT:
If the project is started using Docker Compose, Python, Flask, MySQL and Nginx normally do NOT need to be installed separately on the host PC because Docker runs them inside containers.

============================================================
1. REQUIRED SOFTWARE
============================================================

Minimum required:

1. Git
   Used to clone the project from GitHub.

2. Docker
   Used to run the application and services.

3. Docker Compose
   Modern Docker installations normally include Docker Compose as:
       docker compose

Recommended:
- VS Code
- Web browser such as Chrome / Firefox / Edge

Optional:
- MySQL Workbench, only if you want a graphical database client.
- Python, only if you want to run/debug Flask outside Docker.

============================================================
2. WINDOWS INSTALLATION
============================================================

Install:

1. Git for Windows
   https://git-scm.com/download/win

2. Docker Desktop
   https://www.docker.com/products/docker-desktop/

Docker Desktop includes Docker Compose.

After installation, restart the PC if requested.

Open Command Prompt or PowerShell and verify:

    git --version
    docker --version
    docker compose version

All three commands should return version information.

============================================================
3. LINUX INSTALLATION
============================================================

For Ubuntu/Debian:

    sudo apt update
    sudo apt install -y git curl

Install Docker using Docker's official installation method:
    https://docs.docker.com/engine/install/

After Docker installation, verify:

    git --version
    docker --version
    docker compose version

To use Docker without sudo, optionally run:

    sudo usermod -aG docker $USER

Then log out and log in again.

============================================================
4. GET THE PROJECT
============================================================

METHOD A - FROM GITHUB

Clone the repository:

    git clone <YOUR_GITHUB_REPOSITORY_URL>

Then enter the project folder:

    cd YuvrajMedical


METHOD B - FROM GOOGLE DRIVE ZIP

1. Download YuvrajMedical.zip.
2. Extract the ZIP.
3. Open Command Prompt / Terminal inside the extracted folder.

============================================================
5. CHECK IMPORTANT PROJECT FILES
============================================================

Before starting the project, confirm that files similar to these exist:

    docker-compose.yml
    app.py
    requirements.txt
    Dockerfile

Depending on the final project version, you may also have:

    default.conf
    deploy.sh
    templates/
    static/
    uploads/
    backup.sql
    .env.example

Do NOT commit or publicly share real passwords, API keys, database passwords,
OTP credentials, Cloudflare tokens or other secrets.

If the project requires environment variables, create a local .env file from
.env.example and enter the required local values.

============================================================
6. START THE WEBSITE
============================================================

From inside the YuvrajMedical project directory run:

    docker compose up -d --build

Check containers:

    docker compose ps

Typical services in this project may include:

    mysql_container
    yuvraj_app
    nginx_container
    cloudflared

They should normally show Running or Healthy.

============================================================
7. OPEN THE WEBSITE
============================================================

Run:

    docker compose ps

Look under the PORTS column.

If Nginx exposes port 80, open:

    http://localhost

If it exposes another port, for example 8080, open:

    http://localhost:8080

Do not assume the port. Always confirm it using:

    docker compose ps

============================================================
8. VIEW LOGS IF THE WEBSITE DOES NOT OPEN
============================================================

View all logs:

    docker compose logs

Follow logs live:

    docker compose logs -f

Application logs:

    docker compose logs yuvraj_app

MySQL logs:

    docker compose logs mysql_container

Nginx logs:

    docker compose logs nginx_container

============================================================
9. STOP THE WEBSITE
============================================================

Stop and remove running containers:

    docker compose down

Start again later:

    docker compose up -d

Rebuild after source-code changes:

    docker compose up -d --build

============================================================
10. DATABASE ACCESS
============================================================

Check the MySQL container name first:

    docker compose ps

If the container is named mysql_container:

    docker exec -it mysql_container mysql -u root -p

Enter the MySQL root password configured for the project.

Then you can use commands such as:

    SHOW DATABASES;
    USE <database_name>;
    SHOW TABLES;

Exit MySQL:

    exit

============================================================
11. COMPLETE CLEAN START
============================================================

If containers/images need rebuilding:

    docker compose down
    docker compose up -d --build

WARNING:
Do NOT use:

    docker compose down -v

unless you intentionally want to remove Docker volumes and possibly stored
MySQL database data.

============================================================
12. RECOMMENDED BACKUP FILES
============================================================

Keep these backups:

1. GitHub repository
2. Complete YuvrajMedical ZIP
3. Complete extracted project folder on Google Drive
4. Database backup (.sql), if applicable
5. .env.example containing VARIABLE NAMES ONLY
6. Documentation / project report

Do NOT place actual secret credentials inside public GitHub repositories.

============================================================
13. QUICK START FOR ANOTHER PERSON
============================================================

After Git and Docker are installed:

    git clone <YOUR_GITHUB_REPOSITORY_URL>
    cd YuvrajMedical
    docker compose up -d --build
    docker compose ps

Then open the port displayed by Docker Compose in a browser.

============================================================
14. TROUBLESHOOTING
============================================================

Problem: docker command not found
Solution:
Install/start Docker Desktop on Windows or Docker Engine on Linux.

Problem: docker compose command not found
Solution:
Install a recent Docker version containing the Docker Compose plugin.

Problem: Cannot connect to Docker daemon
Solution:
Start Docker Desktop or Docker Engine.

Linux:

    sudo systemctl start docker
    sudo systemctl enable docker

Problem: Port already in use
Solution:

    docker compose ps

Check the configured host port in docker-compose.yml and stop the conflicting
application or change the host-side port.

Problem: MySQL is unhealthy
Solution:

    docker compose logs mysql_container

Confirm database credentials and environment variables.

Problem: Flask application is unhealthy
Solution:

    docker compose logs yuvraj_app

Check environment variables, database connection and Python application errors.

============================================================
15. FINAL NOTE
============================================================

For the Docker version of YuvrajMedical, the main host-PC requirements are:

    Git
    Docker
    Docker Compose
    Web Browser

Everything else should be provided by the Docker images defined in the project.

Keep this file in:
- GitHub repository
- Google Drive project folder
- YuvrajMedical ZIP

Suggested filename:

    YUVRAJMEDICAL_SETUP.md
