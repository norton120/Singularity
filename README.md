# Singularity
A vortex that compresses infinite sources of information into two touch points

test tarball!
### stuff to respond to (tasks)
- jira tickets to work
- jira comments to reply to
- jira tickets I'm watching
- jira @mentions
- confluence @mentions
- confluence pages im watching
- github @mentions
- github pr reviews
- slack dms
- slack channels
- emails
- google docs @mentions and comments
- google docs shares
- google docs watching

### knowledge to capture
- google docs (drive, sheets, slides)
- confluence pages
- jira tickets
- slack messages
- github pr content
- email content

## Getting the Google auth token
1. You need to create an app in https://console.cloud.google.com/apis/credentials/consent
2. Give the token the Calendar scopes you need
3. Ignore the "authorized domains"
4. Set yourself as a test user
5. finish and create
6. Go to https://console.cloud.google.com/apis/credentials
7. Create oauth creds to the consent screen
8. Add `http://localhost:8080/` to the authorised redirect URIs. note the forward slash at the end! (this little shit cost me a day of anger)
9. download the credentials.json file
10. From **outside docker** install gcsa (`pip install gcsa`) and create a client by pointing it to the credentials.json. There is a chicken-egg with Localhost that won't work via docker.
11. Grab the url from the terminal, open that in a browser with your user in context.
12. The library will fire up a webserver at localhost:8080/ and create a pickled token in the same location as the credentials.json. save that token not in git
13. Use that token from now on for auth!
