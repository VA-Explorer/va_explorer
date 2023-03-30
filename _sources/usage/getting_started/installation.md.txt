# Installation & Setup

VA Explorer is distributed and installed using Docker. Docker supports near
automatic configuration and installation of VA Explorer no matter where you
choose to install it. In general, you can expect an installation and hosting of
VA Explorer to involve these steps:

1. Obtain a server (either your own hardware or cloud provider)
1. Obtain a web address/domain name
1. Prepare server to host VA Explorer
1. Deploy and run VA Explorer via Docker
1. Create your first Admin account and log in

Depending on how many of these are already in place, feel free to skip to the
step most relevant to you.

## Obtain a server (either your own hardware or cloud provider)

A Linux Operating System ({term}`OS`) is recommended for best ease of use and for taking
maximal advantage of docker later. One such {term}`OS` that VA Explorer has been
reliably tested on is Ubuntu. To get a server:

- If using a cloud provider, select and provision one of their Ubuntu server
instances according to their instructions.

- If provisioning your own server, you may be able to do so through your
organization or hosting provider (see Step 2).

While not required, hardware specifications for the server that has successfully
hosted VA Explorer in the past had a reference baseline of 1 CPU, 16 GB RAM, and 1 TB Storage.

## Obtain a web address/domain name

A domain name such as `my-va-explorer.com` is required for users to navigate
to your server from a browser. If you already own a domain, a subdomain
(`my-va-explorer.my-website.com`) is a good approach too. If you already own a
domain name, please proceed to the next step.

For those wishing to acquire a domain name, your organization may be able to
provide one or you can pay a commercial domain registrar for one. Please note
that new domains can take some time to be accessible from the Internet. While
waiting, you need to direct this domain to the hosted server from Step 1:

- If using a cloud provider, please follow their instructions on connecting
domain names to their hosted server instances.
- If you’ve provisioned your own server through your organization or hosting
provider but they are not able to provide a domain name, that server should
have an IP address. You’ll need to follow the instructions of your domain
registrar to point the newly registered domain name to your server’s IP address.

## Prepare server to host VA Explorer

To bring your server from blank slate to ready-to-host, there are final some
steps to take before downloading VA Explorer.

- Install Docker Engine on Ubuntu

- Install Docker Compose Standalone

- Post Installation Setup for Docker Users on Linux

- Install a web server/ reverse proxy to direct web traffic to the VA Explorer
port. Two popular options are Nginx and Apache. An example Apache configuration
is provided in the [Troubleshooting](../../training/troubleshooting.md#frequently-asked-questions)
section

- If your hosting provider doesn’t already or automatically provide https
support, you should add it now. Let’s Encrypt is a free https certificate
provider that also provides a guides for adding https support to Apache or
Nginx web servers, among other configurations.

- Tools like git and text editors like vim will also be needed. You can install
them via `sudo apt install -y git vim` or your OS’s equivalent

## Deploy and run VA Explorer via Docker

VA Explorer itself is quick to deploy thanks to Docker and the default
configurations. More on customizing this configuration can be found in
[Configuration & Deployment](config).

- Assuming you’ve ssh’d into the server, navigate to the directory you’d like to
install VA Explorer in.

- Retrieve the latest version of VA Explorer via:
`git clone https://github.com/VA-Explorer/va_explorer.git` then navigate into
the created directory via `cd va_explorer`

- You can provide initial configuration to supplement defaults by creating a
`.env` file. Do so via `mv .env.template .env` and `vim .env`. One variable that
can be edited immediately is the `DJANGO_ALLOWED_HOSTS` variable by adding your
domain name from Step 2. For more information on this, see the mentioned
[Configuration & Deployment](config) section.

- Run `docker-compose up -d --build`. If you experience any issues here, please
consult the [Troubleshooting](../../training/troubleshooting) section.

- Additionally, the full and complete list of management commands is available
by running `manage.py help`. Only some of the popular commands are described
here or in [Management Commands](../../training/admin_guides.md#management-commands).

- VA Explorer should now be up and running. You can confirm services are running
as expected via `docker ps` which should output like below:

```{figure} ../../_static/img/build_output.png
:alt: Console output from `docker ps`

<small>docker ps output showing the pycrossva, clereryworker,
django, flower, interva5, redis, and postgres services running</small>
```

## Create your first Admin account and log in

Finally, to get started in the application you should create an admin account
for yourself. This can be done via built-in management command from within the
main web application container. To seed an admin user for yourself:

- Open a shell within the main web application docker container by running
`docker exec -it va_explorer_django_1 bash`

- Run the seed_admin_user command via `manage.py seed_admin_user <EMAIL_ADDRESS>`
filling in your own email for the email parameter
- A temporary password will print to the console. Copy it. In a browser,navigate
to the domain name you chose in Step 2 and log in with the email you provided
plus the password you copied.

- You should now be logged in and immediately prompted to reset your password
to something of your choosing. Take the opportunity to do so now.

Once you have one account you do not have to repeat this process as the
application provides admins an interface for creating and managing other users.

With this basic setup in place you are ready to get started. As mentioned, if
you are interested in reading more about basic or advanced configuration options
like allowing an email server to handle user password resets you can find that
in the next section [Configuration & Deployment](config). You may also want to
read over [IT Support Guides](../../training/it_guides) for information on
activities like setting up an email server, implementing server monitoring, and
preparing for regular backups.
