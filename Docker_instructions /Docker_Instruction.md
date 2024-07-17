# Instructions to run code on local machine 



## 1. login into Github in CML

- go to your account settings on [GitHub](https://github.com)
- on the left side bar scroll all the way down to "Developer settings"
- on the left side bar inside Developer settings click "Personal access tokens" and then "Tokens (classic)"
- on right side of the page click "Generate new token (classic)"
- write anything in the "Note" text bar
- in the "Select scopes" option you want to select the following scopes: **repo, write:packages, and delete:packages.** (don't worry about the other scopes that are automaticcaly selected)
- scroll to the bottom of the page and click the green button that says "Generate token"
- make sure to copy the token (once the tab is closed you won't be able to see it but can always generate a new one)
- in the Command Line copy and paste the following with your Personall access token and your Github username
    `echo <YOUR PERSONAL ACCESS TOKEN>  | docker login ghcr.io -u <YOUR USERNAME>  --password-stdi`
- if you get the message "Login Succeeded", you are now logged in and ready to pull the image



## 2. Pull the docker image from ghcr.io in the CML

- in the CML copy and past the follwoing,
    `docker pull ghcr.io/jacobborenstein/rt-trade-and-risk-v2/project:latest`
- you should see the image being pulled from docker



## 3. start up the image
- in a direcotry of your choice save the docker compose file located in the same directroy as this .md file
- open up a Command Line in that directory and enter `docker compose up`



