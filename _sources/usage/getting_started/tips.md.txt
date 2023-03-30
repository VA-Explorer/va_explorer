# Tips & Best Practices

As a compliment to your new VA Explorer instance, there are several optional
steps you can also take to make server management easier and data more resilient.
This section covers some of these additional steps as a good starting set:

- Setting up a mail server
- Configuring for better security
- Implementing server monitoring

There are also further guides along these lines in [IT Support Guides](../../training/it_guides) for
those anxious to learn more about sustaining use of VA Explorer over time.

## Setting up a mail server

If a mail server is already available, customize the `EMAIL_URL` configuration
variable to point to it with the necessary authentication information. However,
if your organization or cloud provider do not provide a mail server, it is
recommended to set one up. A popular and readily compatible tool for this is
EXIM. Ubuntu provides documentation on installing and setting EXIM up locally.
Once this process has finished, `EMAIL_URL` can similarly be customized to point
to `localhost`.

```{note}
If users are reporting non-receipt of emails, the [Frequently Asked Questions](training/troubleshooting.md#frequently-asked-questions)
section may help.
```

## Implementing server monitoring

After installation and setup of VA Explorer, having visibility of system
statistics or alerts when things do not function as expected can help you
quickly address problems before they grow. If your organization or cloud
provider offers this functionality, consider following their instructions to
implement monitoring. If they do not already provide a way to do this, NetData
OSS Agent may meet your needs as a nice tool providing out-of-the-box monitoring
and visualization with low-to-no configuration. With some configuration, alerts
are also supported.

NetData and other monitoring solutions should cover metrics that provide insight
for common VA Explorer management questions like:

- Are backups, {term}`VA`s, etc. overflowing storage? – Monitor Disk Space Utilization
- Is software running efficiently? – Monitor CPU & RAM Usage
- How well is the network/ server handling user traffic? Monitor Network Traffic/ Latency
- Is VA Explorer accessible? – Monitor Endpoints (Health Checks/ Pings)

## Configuring things for better security

While VA Explorer is developed with security in mind and server software may have
a good security baseline, security is a broad and continuously evolving domain.
No set of things can fully reduce risk in this area, but some security best
practices to consider for your VA Explorer server include:

### Strengthening server authentication methods

If your server is using password authentication, ensure they are strong passwords
and consider enabling 2-Factor authentication. Also consider using ssh key pairs
instead of passwords.

### Regularly updating server software

Software that ships with your server, including VA Explorer, periodically release
updates, and sometimes these updates have the sole purpose of patching security
vulnerabilities. Failing to download these security updates leaves software open
to known vulnerabilities. To update server software, regularly run
`sudo apt update && sudo apt upgrade` or your {term}`OS` equivalent. To update VA
Explorer, refer to the [IT Support Guides > Upgrading VA Explorer](../../training/it_guides.md#upgrading-va-explorer)
guide.

You may also consider setting your server up for automatic security updates.
Debian-based Linux systems like Ubuntu provide the `unattended-upgrade` utility
for this, along with optional configuration to alert you if any problems arise
during automatic updates. See [Guide](https://help.ubuntu.com/community/AutomaticSecurityUpdates).

### Protecting against server attacks

Servers can come under attack within minutes of going online to the wider internet.
If you do not have an organization or cloud provider already protecting your
server, some small tweaks that can help with this include the following. Note
that this list is by no means exhaustive, and conducting a full cybersecurity
review is recommended.

- Reducing your "attack surface" by closing or blocking any open but unneeded
ports. You can do so through tools like ufw, netstat, chkconfig, and others.

- Consider switching popular services to non-standard ports. For example, ssh
is usually supported via port 22, and expected to be found there because of that.
Hosting it on another port could be a simple but effective method at reducing
attacks.

- Consider removing the ability to directly login as root and instead make other
users become root once logged in. This can be done by editing `/etc/passwd` root
config to `root:x:0:0:root:/root:/sbin/nologin`

- Finally, tools like Fail2Ban, an intrusion prevention framework, can monitor
for brute force attempts on services like ssh, Apache/ Nginx logs, etc. and then
block offending IP addresses from future attempts. Info on taking advantage of
its features is readily available from the community.
