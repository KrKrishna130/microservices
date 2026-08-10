1.Make first Eureka server
goto ->spring initializer->create normal spring boot project

add dependency -1.spring web 2.netflix eureka server

<dependency>
			<groupId>org.springframework.boot</groupId>
			<artifactId>spring-boot-starter-webmvc</artifactId>
		</dependency>
		<dependency>
			<groupId>org.springframework.cloud</groupId>
			<artifactId>spring-cloud-starter-netflix-eureka-server</artifactId>
		</dependency>

-----------------------------
application.properties file
-----------------------------
spring.application.name=EUREKA-SERVER

server.port=8761

eureka.client.register-with-eureka=false
eureka.client.fetch-registry=false

eureka.instance.hostname=localhost

---------Test service Up & Run-----------
http://localhost:8761/
==========================================================
2.make seperate services for each Requirements in Python
fastapi
uvicorn
httpx
py-eureka-client
tenacity
slowapi

3.make user service
 make main.py &requirements.txt files write logic what U want.
 -------------------------------
python -m venv venv
---------------------------------
venv\Scripts\activate
--------------------------------
python -m pip install --upgrade pip
------------------------------------
python -m pip install -r requirements.txt
--------------------------------------
----------Run User-service---------

python main.py
--------Test by Swagger-----------

http://localhost:8001/docs
==============================================================
 4.make Payment service
 make main.py &requirements.txt files write logic what U want.
  ------------------------------
python -m venv venv
---------------------------------
venv\Scripts\activate
--------------------------------
python -m pip install --upgrade pip
------------------------------------
python -m pip install -r requirements.txt
------------------------------------------
------Run Payment-service------------------

python main.py

--------Test by Swagger------------------

http://localhost:8002/docs
=========================================================
 5.make Order service
 make main.py &requirements.txt files write logic what U want.

----------------------------------
python -m venv venv
---------------------------------
venv\Scripts\activate
--------------------------------
python -m pip install --upgrade pip
------------------------------------------
python -m pip install -r requirements.txt
------------------------------------------
---------Run Order-service---------------

python main.py
----------Test by Swagger----------------

http://localhost:8003/docs
=====================================================
# ===========Micro services Communication================#

# Using Eureka Service Discovery, one service calls another by its registered service name.
# Use Eureka Service Discovery to find the target service.
# Call it using its service name, not hardcoded IP.
# Example: async_do_service("USER-SERVICE", "/users/1")


# ==============LoadBalancing======================#
# Eureka registers multiple instances of the same service.
# Client selects an available instance using service discovery.
# This provides client-side load balancing across instances.
# i.e:-
# response = await eureka_client.async_do_service(
#     "USER-SERVICE", "/users/1", method="GET", return_type="json"
# )

# Eureka automatically selects an available USER-SERVICE instance.
# Multiple instances can run on different ports for load balancing.


 
 
