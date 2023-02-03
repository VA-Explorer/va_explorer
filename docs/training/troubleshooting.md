# Troubleshooting

Not everything can go right all the time. If VA Explorer is acting in an
unexpected way, troubleshooting can help determine, and perhaps solve, the
problem.

## Reading and Interpreting VA Explorer Logs

Logs are often the most helpful to operators, and even developers fielding
questions, when attempting to diagnose a potential issue.

- For local instances of VA Explorer, logs should be readily available and
printing to the console of the program used to run `runserver_plus`

- For operators, you can view logs through Docker. Run
`docker logs --tail <quantity> va_explorer_django _1` where quanity can be
something like 100 to see the last 100 lines of logs or 1m to see the last minute.

As mentioned in Configuration & Deployment (link), `DJANGO_DEBUG` can be set to `True`
for even more useful troubleshooting information in those logs. Running commands
like `docker ps` will also help you determine if all docker services are running
as expected.

## Frequently Asked Questions

1. Is VA Explorer free?

Yes, VA Explorer is free to download and use as you please under the terms of
the open-source Apache V2 license. If installed on a linux-based OS, users also
do not need to worry about any costs associated with using docker. We expect the
only costs associated with VA Explorer to be hosting and domain name registration.

2. I’m getting an error related to psycopg2 when setting up VA Explorer. What
does this mean?

It is possible that psycopg2 is pointing at the wrong SSL installation on your
system it is attempting to set itself up during the pip install process. Adding
this environment variable has worked as a potential fix:

```shell
export LDFLAGS='-L/usr/local/lib -L/usr/local/opt/openssl/lib -L/usr/local/opt/readline/lib'
```

3. I’m getting an error related to scipy when setting up VA Explorer. What does
this mean?

Some MacOS users have reported getting the error
`numpy.distutils.system_info.NotFoundError: No lapack/blas resources found. Note: Accelerate is no longer supported.`
If you get this error, this thread (external link) may be a helpful resource.
Ensuring that pip is upgraded `pip install --upgrade pip` may also help.

4. What is an easy configuration to use for my reverse proxy?

This is a simple example apache config that utilizes letsencrypt https certificates

```apache
<VirtualHost *:80>
    ServerName myhost.com
    ServerAdmin admin@myhost.com
    ServerAlias *.myhost.com

    Redirect permanent / https://myhost.com/

    ErrorLog ${APACHE_LOG_DIR}/http-myhost-error.log
    CustomLog ${APACHE_LOG_DIR}/http-myhost-access.log combined
</VirtualHost>

<IfModule mod_ssl.c>
    <VirtualHost *:443>
        ServerName myhost.com
        ServerAdmin admin@myhost.com
        ServerAlias *.myhost.com
        SSLProxyEngine on

        ProxyPreserveHost on
        ProxyVia on
        ProxyPass / http://localhost:5000/
        ProxyPassReverse / http://localhost:5000/

        ErrorLog ${APACHE_LOG_DIR}/https-myhost-error.log
        CustomLog ${APACHE_LOG_DIR}/https-myhost-access.log combined

        SSLCertificateFile /etc/letsencrypt/live/myhost.com/fullchain.pem
        SSLCertificateKeyFile /etc/letsencrypt/live/myhost.com/privkey.pem
        Include /etc/letsencrypt/options-ssl-apache.conf
    </VirtualHost>
 </IfModule>
```

5. Why are my users not receiving email?

Email technology can unfortunately encounter issues delivering messages sometimes.
By default, VA Explorer prints to the console and can be configured to work with
an existing mail server. This mail server, once VA Explorer is configure to use
it may not work if:

- You or your organization are using a cloud provider that restricts the usage
of simple mail servers as a spam-prevention strategy. The cloud provider may
offer a mail service you can use instead

- You or your organization could be assigned an IP address that was previously
used for sending spam and is therefore blocked by many mail recipients

- You or your organization’s domain may not be recognized by mail recipients, so
messages from it may be blocked or marked as spam

If you want to troubleshoot sending emails from your mail server, the mail-tester
service recommended by ODK Central may help identify your email delivery issues.
