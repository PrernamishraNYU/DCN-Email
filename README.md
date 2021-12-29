# AliceBob HTTP+SMTP+POP3

## Local setup

First, build each image:
```
$ cd AU/ && docker build -t au .
$ cd AE/ && docker build -t ae .
$ cd BE/ && docker build -t be .
$ cd BU/ && docker build -t bu .
```

Next, create a local docker network:
```
$ docker network create alicebob
```

Then, in separate terminal windows, start each container:

**Alice User server (AU):**
```
$ cd AU && docker run --network alicebob --name au -p 127.0.0.1:8080:8080 au
```
_Note here we have to do manual port forwarding on 127.0.0.1 so the local browser can reach the container's port 80._

**Alice SMTP server (AE):**
```
$ cd AE && docker run --network alicebob --name ae ae
```

**Bob SMTP+POP3 server (BE):**
```
$ cd BE && docker run --network alicebob --name be be
```

**Bob User server (BU):**
```
$ cd BU && docker run --network alicebob --name bu -p 127.0.0.1:8081:8081 bu
```
_Note here we have to do manual port forwarding similar to au_

## Local Usage
Now that everything is set up, we need to know the IP addresses of the containers.  In a new terminal, run `docker container ls`.  You should get output like this:
```
$ docker container ls
CONTAINER ID   IMAGE     COMMAND                  CREATED          STATUS          PORTS                      NAMES
e08921d7cd20   be        "/bin/sh -c 'python3…"   15 minutes ago   Up 15 minutes   5000/tcp                   be
f87d68944109   ae        "/bin/sh -c 'python3…"   29 minutes ago   Up 29 minutes   4000/tcp                   ae
11210c603982   au        "/bin/sh -c 'flask r…"   29 minutes ago   Up 29 minutes   127.0.0.1:8080->8080/tcp     au
94897fa98ea9   bu        "/bin/sh -c 'flask r…"   10 minutes ago   Up 10 minutes   127.0.0.1:8081->8081/tcp     bu
```

Then, run `docker inspect alicebob`.  You should get output like this:
```
$ docker inspect alicebob
[
    {
        "Name": "alicebob",
        "Id": "5644590cb08e479cce9d8010251da2ba6d36c674aeef5f5c101271137ddd104d",
        "Created": "2021-04-29T23:22:55.5960762Z",
        "Scope": "local",
        "Driver": "bridge",
        "EnableIPv6": false,
        "IPAM": {
            "Driver": "default",
            "Options": {},
            "Config": [
                {
                    "Subnet": "172.18.0.0/16",
                    "Gateway": "172.18.0.1"
                }
            ]
        },
        "Internal": false,
        "Attachable": false,
        "Ingress": false,
        "ConfigFrom": {
            "Network": ""
        },
        "ConfigOnly": false,
        "Containers": {
            "11210c603982601a45732182319b4b8b623a2016122c043e7f965585c6913f0d": {
                "Name": "au",
                "EndpointID": "5e7ee0445130560d1836a2375b7f932dbee659e9427abf7d3898687f12b07451",
                "MacAddress": "02:42:ac:12:00:02",
                "IPv4Address": "172.18.0.2/16",
                "IPv6Address": ""
            },
            "94897fa98ea9af91dc0571f0b15732182319b4b8b623aec67aea490982601a45": {
                "Name": "bu",
                "EndpointID": "ee659e945e7ee0445130560d1836a2375b7f932db27abf7d3898687f12b07451",
                "MacAddress": "18:42:be:15:00:02",
                "IPv4Address": "172.18.0.5/16",
                "IPv6Address": ""
     
            "e08921d7cd207486f2346a3f9e2f63253a04f60af91dc0571f0b1c5cfb5639f5": {
                "Name": "be",
                "EndpointID": "4989cb00c7a792246dc7c477b44cbbda82e20a2e82cebd0670e36bb1d3631e46",
                "MacAddress": "02:42:ac:12:00:04",
                "IPv4Address": "172.18.0.4/16",
                "IPv6Address": ""
            },
            "f87d68944109ceab9f37a926c49ec67aea490bd8c4aac880988becaaefbfa15c": {
                "Name": "ae",
                "EndpointID": "d4c09c38a66883fd6afd102d505f63ee3834034b473cca90cb9d21911f2facd7",
                "MacAddress": "02:42:ac:12:00:03",
                "IPv4Address": "172.18.0.3/16",
                "IPv6Address": ""
            }
        },
        "Options": {},
        "Labels": {}
    }
]
```

**Send an email from AU**

Copy the `IPv4Address` for `ae` and `be` into the `from` and `to` query string parameters, respectively:
```
$ curl http://127.0.0.1:8080/email?from=172.18.0.3:4000\&to=172.18.0.4:5000\&message=testing
Message sent!<br>
<br>
From: 172.18.0.3:4000<br>
To: 172.18.0.4:5000<br>
Message:<br>
testing
<br>
```
Or load that URL in a browser: http://127.0.0.1:8080?from=172.18.0.3:4000&to=172.18.0.4:5000&message=testing

**Read a message from BU/BE**

Copy the `IPV4Address` from `be` (same as above) into the `from` query string parameter:
```
$ curl http://127.0.0.1:8081/email?from=172.18.0.4:5000
```
Or load that URL in a browser to see it formatted: http://127.0.0.1:8081/email?from=172.18.0.4:5000

## Kubernetes

IBM Cloud public ip: `169.57.99.223`

To access sending mail: http://169.57.99.223:30001/email?from=0.0.0.0:4000&to=0.0.0.0:5000&message=TESTING

To access retrieving mail: http://169.57.99.223:30002/email?from=0.0.0.0:5000
