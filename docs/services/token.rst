=============
Token Service
=============

This is for logging in so you can start using the services hosted by Boundless.

You need a username and password, which are submitted in a JSON body.

If those are wrong, you get a 403.

Otherwise, you get back an Auth0 token.

You put that in an Authorization header in HTTP requests.
