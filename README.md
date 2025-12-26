# Cloud Journal API
## Explanation
This is second phase of our [Journal API](https://github.com/Berke-mekatronik/journal-fastapi) project, called Cloud Journal API. 

Cloud Journal API is a FastAPI-based journaling backend deployed on AWS using a secure, production-style network architecture. The API allows users to create, read, update, and delete daily journal entries, while persisting data in a PostgreSQL database hosted in a private subnet. The project demonstrates real-world cloud concepts such as VPC design, subnet isolation, security groups, IAM least privilege, and API deployment.

## Architecture Diagram
![Arch_Diagram](/img/Arch_Diagram.png)

The architecture follows a two-tier design:

* A public subnet hosting the FastAPI API server, accessible from the internet.
* A private subnet hosting the PostgreSQL database, isolated from direct internet access.
* Communication between the API and database is restricted using security groups.
* Outbound internet access from the private subnet is routed through a NAT Gateway.

## Infrastructure Components Created 
1. Created a dedicated IAM user with limited permissions for infrastructure and deployment.
2. Designed and created a custom VPC with public and private subnets.
3. Deployed the FastAPI application on an EC2 instance in the public subnet.
4. Deployed a PostgreSQL database server on an EC2 instance in the private subnet.
5. Configured Internet Gateway, route tables, and NAT Gateway for controlled outbound access.
6. Security Groups enforcing least privilege access
7. AWS Systems Manager (SSM) for secure instance access
8. Elastic IP for stable public access to the API server

## Security Considerations
### API Server Security Group
#### Inbound:
* HTTP (80) and HTTPS (443) from the internet
* SSH (22) restricted to the developer’s IP address
#### Outbound:
* PostgreSQL (5432) traffic to the database security group
* Internet access for updates and package installation

### Database Server Security Group
#### Inbound:
* PostgreSQL (5432) only from the API server security group
* HTTPS (443) for AWS SSM acces
#### Outbound:
* Internet access via NAT Gateway for system updates
* This setup ensures least privilege and prevents direct database exposure to the internet.

## Deploy and Configure the Database Server
### Server Setup
First, we need to set up secure remote access using Amazon SSM to protect cloud resources from unauthorized access. This allows us to access the database server (located in the private subnet) and configure it securely without exposing it to the public internet.

Create an IAM role for the EC2 instance:

![IAM_Role](/img/IAM_Role.png) 

The following policy will be attached automatically:

![Policy](/img/Policy.png)

Then, attach the role to the EC2 instance:

![SSM_Policy](/img/SSM_Policy.png) 

![Attach_Policy](/img/Attach_Policy.png)

Create the following VPC endpoints for AWS Systems Manager:

![SSM_Endpoints](/img/SSM_Endpoints.png)

### PostgreSQL Installation and Configuration
Run the following commands to install the PostgreSQL database:
``` 
sudo dnf update 
sudo dnf install -y postgresql15 postgresql15-server 
sudo postgresql-setup --initdb 
sudo systemctl start postgresql 
sudo systemctl enable postgresql 
sudo systemctl status postgresql 
```

Take a backup of the following file:
```
sudo cp /var/lib/pgsql/data/postgresql.conf /var/lib/pgsql/data/postgresql.conf.bak 
```

Modify the file to accept connections
```
sudo vi /var/lib/pgsql/data/postgresql.conf 
```
![postgresql.conf](/img/postgresql.conf.png)

Now, change the password of the postgres system user: 
```
sudo passwd postgres 
```

Log in using the PostgreSQL system account: 
```
su - postgres 
```

Change the PostgreSQL database password: 
```
psql -c "ALTER USER postgres WITH PASSWORD '<your_password>';" 
```

After that, exit from the postgres user. Modify the following file to allow remote connections:
```
sudo vi /var/lib/pgsql/data/pg_hba.conf 
```
![pg_hba.conf](/img/pg_hba.conf.png)

Restart the database service: 
```
sudo systemctl restart postgresql 
```

## Deploy and Configure the API Server
### Server Setup
Each time the instance is stopped and restarted, the public IP address changes. Therefore, it is recommended to associate an Elastic IP with the instance.

![ElasticIP](/img/ElasticIP.png)

#### Requirements for fastapi server: 
The following commands are valid for Amazon Linux–based servers. If your EC2 instance is Ubuntu-based, the commands may differ. 
```
sudo yum update -y 
sudo yum install python3-pip –y 
sudo yum install nginx 
```
 
#### Nginx configurations: 
In a typical FastAPI deployment where Nginx is used as a reverse proxy, the configuration file (e.g., fastapi.conf) includes directives to:

* Listen on a specific port (e.g., 80 for HTTP)

* Define the server_name (domain or public IP address)

* Proxy incoming requests to the FastAPI application, which usually runs on port 8000 and is served by an ASGI server such as Uvicorn or Gunicorn

The following configuration is specific to Amazon Linux. It may differ for Debian/Ubuntu-based systems.
```
sudo vi /etc/nginx/conf.d/fastapi.conf 
```
Create config

![fastapi.conf](/img/fastapi.conf.png)
```
server { 

listen 80; 
    server_name 100.27.43.113; 
    location / { 
    proxy_pass http://127.0.0.1:8000; 
        } 
} 
```
Enable the configuration and verify it. Finally, test the Nginx configuration and restart the service to apply the changes: 
```
sudo nginx -t 
sudo systemctl restart nginx 
```

#### Clone the FastAPI project repository:
Clone repository
```
git clone https://github.com/Berke-mekatronik/journal-fastapi.git journal-fastapi 
```

Install the required dependencies:
```
pip3 install -r requirements.txt 
```
![requirements](/img/requirements.png)

#### Environment Variable Configuration
Configure environment variables on the FastAPI server:
```
sudo vi /etc/environment 
```
```
DATABASE_URL=postgresql://username:password@<private-db-ip>:5432/databasename
```

## Testing Cloud Deployment
The deployment was validated by testing the API endpoints directly from the public internet using FastAPI Swagger UI.

```
python3  –m uvicorn api.main:app
```
![uvicorn](/img/uvicorn.png)

Check your ip address (with http)

![http](/img/2HTTP.png)

FastAPI accessible

![fastapi](/img/3FastAPI.png)

#### Authentication
The request is rejected because the endpoint is protected by the authentication middleware and no access token is provided.

![authorize](/img/4Authorize.png)

A valid access token is generated using the login endpoint and the user is successfully authenticated.

![authorize](/img/4Authorize2.png)

#### Create entry
A new journal entry was created successfully using the POST endpoint.

![createEntry](/img/5Create1.png)

![createEntry](/img/5Create2.png)

![createEntry](/img/5Create3.png)

#### Get all entries
All journal entries are retrieved using the GET endpoint.

![getAll](/img/6GetAll.png)

The same entries are verified directly in the database, confirming data persistence.

![getAll](/img/6GetAll2.png)

#### Get with id
A single journal entry is fetched using its unique entry ID.

![getWithId](/img/7GetwithId.png)

#### Delete with id
A specific journal entry is deleted using its entry ID.

![deleteWithId](/img/8DeleteWithId.png)

#### Delete all entries
All journal entries are deleted using the DELETE endpoint.

![deleteAll](/img/9DeleteAll1.png)

The database is checked directly to confirm that all entries have been removed.

![deleteAll](/img/9DeleteAll2.png)

#### Update entry
A new journal entry is created to demonstrate the update operation.

![updateEntry](/img/10Update1.png)

The newly created entry is verified directly in the database.

![updateEntry](/img/10Update2.png)

The entry is updated using its ID and the PATCH endpoint.

![updateEntry](/img/10Update3.png)

The updated entry is confirmed in the database, showing the changes were applied successfully.

![updateEntry](/img/10Update4.png)

