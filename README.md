# Foodgram - Your Personal Recipe Hub

[![Main Foodgram Workflow](https://github.com/Akhmedkhanov-Gasan/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/Akhmedkhanov-Gasan/foodgram/actions/workflows/main.yml)

### Project Description
Foodgram is a platform where users can share, discover, and save recipes. Users can create their own recipes, add recipes to favorites, download shopping lists, and subscribe to other users to stay updated on their recipes.

### Installation
<i>Note: All examples are provided for Linux</i><br>

1. Clone the repository to your computer:
    ```
    git clone git@github.com:Akhmedkhanov-Gasan/foodgram.git
    ```

2. Create a `.env` file and fill it with your configuration data. All required variables are listed in the `.env.example` file located in the project's root directory.

### Building Docker Images

1. Replace `YOUR_USERNAME` with your DockerHub username:

    ```
    cd frontend
    docker build -t YOUR_USERNAME/foodgram_frontend .
    cd ../backend
    docker build -t YOUR_USERNAME/foodgram_backend .
    cd ../nginx
    docker build -t YOUR_USERNAME/foodgram_gateway .
    ```

2. Upload the images to DockerHub:

    ```
    docker push YOUR_USERNAME/foodgram_frontend
    docker push YOUR_USERNAME/foodgram_backend
    docker push YOUR_USERNAME/foodgram_gateway
    ```

### Server Deployment

1. Connect to the remote server:

    ```
    ssh -i PATH_TO_SSH_KEY/SSH_KEY_NAME YOUR_USERNAME@SERVER_IP_ADDRESS 
    ```

2. Create a `foodgram` directory on the server:

    ```
    mkdir foodgram
    ```

3. Install Docker Compose on the server:

    ```
    sudo apt update
    sudo apt install curl
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo apt install docker-compose
    ```

4. Copy the `docker-compose.yml` and `.env` files to the `foodgram/` directory on the server:

    ```
    scp -i PATH_TO_SSH_KEY/SSH_KEY_NAME docker-compose.yml YOUR_USERNAME@SERVER_IP_ADDRESS:/home/YOUR_USERNAME/foodgram/docker-compose.yml
    scp -i PATH_TO_SSH_KEY/SSH_KEY_NAME .env YOUR_USERNAME@SERVER_IP_ADDRESS:/home/YOUR_USERNAME/foodgram/.env
    ```
    
    **Parameters:**
    - `PATH_TO_SSH_KEY` - path to your SSH key file
    - `SSH_KEY_NAME` - SSH key file name
    - `YOUR_USERNAME` - your server username
    - `SERVER_IP_ADDRESS` - your server's IP address

5. Run Docker Compose in detached mode:

    ```
    sudo docker compose -f docker-compose.yml up -d
    ```

6. Run migrations, collect static files for the backend, and copy them to `/backend_static/static/`:

    ```
    sudo docker compose -f docker-compose.yml exec backend python manage.py migrate
    sudo docker compose -f docker-compose.yml exec backend python manage.py collectstatic
    sudo docker compose -f docker-compose.yml exec backend cp -r /app/collected_static/. /backend_static/static/
    ```

7. Open the Nginx configuration file with `nano`:

    ```
    sudo nano /etc/nginx/sites-enabled/default
    ```

8. Modify the location settings in the server section to route requests correctly:

    ```
    location / {
        proxy_set_header Host $http_host;
        proxy_pass http://127.0.0.1:8080;
    }
    ```

9. Test the Nginx configuration:

    ```
    sudo nginx -t
    ```

    If successful, you should see:

    ```
    nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
    nginx: configuration file /etc/nginx/nginx.conf test is successful
    ```

10. Restart Nginx:

    ```
    sudo service nginx reload
    ```

### CI/CD Setup

1. The workflow file is already written and located at:

    ```
    foodgram/.github/workflows/main.yml
    ```

2. To adapt it to your server, add secrets to GitHub Actions:

    ```
    DOCKER_USERNAME                # DockerHub username
    DOCKER_PASSWORD                # DockerHub password
    HOST                           # Server IP address
    USER                           # Server username
    SSH_KEY                        # Content of the private SSH key
    SSH_PASSPHRASE                 # SSH key passphrase

    TELEGRAM_TO                    # Your Telegram account ID (use @userinfobot, command /start)
    TELEGRAM_TOKEN                 # Bot token (get it from @BotFather, command /token, bot name)
    ```

### Technologies
- Python 3.10
- Django 4.2
- djangorestframework 3.14
- PostgreSQL 13.10
- Docker/Docker Compose
- Nginx
