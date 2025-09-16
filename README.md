# ai-incident-analyzer

# 1. Start your application
docker-compose up -d

# 2. Check if containers are running
docker-compose ps

# 3. View logs if needed
docker-compose logs -f backend

# 4. Make changes to your code...

# 5. Rebuild and restart
docker-compose up -d --build

# 6. When done, stop everything
docker-compose down
