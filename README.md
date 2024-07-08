# Webhooks

Install the gunicorn WSGI and Flask:

```
sudo apt install gunicorn python3-flask
```

Create an NGINX endpoint for this webhook:

```
location /webhook {
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Host $http_host;

    # We don't want nginx trying to do something clever with
    # redirects, we set the Host: header above already.
    proxy_redirect off;

    # Send the HTTP request to gunicorn through its UNIX socket.
    # fail_timeout=0 means we always retry an upstream even if it failed
    proxy_pass http://unix:/tmp/gunicorn.sock;
}
```

Finally, run your application with gunicorn by specifying the UNIX socket to bind to:

```
gunicorn --bind unix:/tmp/gunicorn.sock handle_github_webhook:app
```
