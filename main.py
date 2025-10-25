from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from webauthn import (
    options_to_json,
    generate_registration_options,
    generate_authentication_options,
    verify_registration_response,
    verify_authentication_response,
)
from webauthn.helpers.structs import (
    PublicKeyCredentialDescriptor,
    AuthenticatorTransport,
)

from webauthn.helpers import options_to_json_dict
import secrets
import time
import json
import base64

app = FastAPI()

# Add CORS middleware, this is for DEV only and allows https://localhost:8000 to work with 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

## demo databases in memory only , for prod use a database
users = {} 
challenges = {} ## for example use redis here

RP_ID = "localhost"
ORIGIN = "http://localhost:8000" 

########################################################
### step 1 registration 


@app.get("/webauthn/register/options")
def begin_register(email: str):
    # Check if user already exists, if not create new user
    if email not in users:
        user_id = secrets.token_bytes(16)
        users[email] = {"id": user_id, "credentials": []}
    else:
        # Use existing user_id for additional devices
        user_id = users[email]["id"]
    
    registration_options = generate_registration_options(
        rp_name= "MyWebauthnAPP",
        rp_id = RP_ID,
        ## we include the user_id from above (either new or existing)
        user_id =user_id,
        user_name = email,
        user_display_name= email
    )

    # we save the challenge in our in memory database , we use the challange to prevent replay attacks from outside the orign browser sesion 
    challenges[email] =  registration_options.challenge

    # now we return it as a json object using a 2-step conversion:
    # 1. options_to_json() converts WebAuthn object (with bytes) to JSON string (with base64url)
    # 2. json.loads() converts JSON string back to Python dict for FastAPI serialization
    # this ensures proper base64url encoding while keeping FastAPI happy
    #return json.loads(options_to_json(registration_options))

    ## this seem to be a better sollution lets try this 
    return options_to_json_dict(registration_options)


################
### step 2 complete the registration

@app.post("/webauthn/register/verify")
async def finish_register(request: Request):
    ## get the request and make it a json
    body = await request.json()
    # get email from the json 
    email = body["Email"]
    # get the challange from the in memory challenges , if there is no challenge get a error (the process must have started)
    registration_challenge = challenges.get(email)
    if not registration_challenge:
        raise HTTPException(400,f"No registration in process for {email}")

    ## now check the request from the device, again we use the body from above 
    registration_verification = verify_registration_response(
        credential = body["credential"],
        expected_challenge=registration_challenge,
        expected_rp_id = RP_ID,
        expected_origin= ORIGIN
    )

    ### now we store the device credential 
    device_credential = {
        ## webauthn doesnt add = as padding to the string if needed causing errors, so we strip away any right side padding if present
        # unsure if this is a dirty fix or just normal ?
        "id": base64.urlsafe_b64encode(registration_verification.credential_id).decode().rstrip('='),
        "public_key": registration_verification.credential_public_key,
        # we also use a counter to prevent replay attacks 
        "counter": registration_verification.sign_count
    }

    ## here we store it in the user table 
    users[email]["credentials"].append(device_credential)
    # and we dont need the challenges anymore so we can delete it
    del challenges[email]

    #finaly we respond with a status registered so the browser knows we did it !
    return {"status": "registered"}


########################################
## now we can start the login process 

@app.get("/webauthn/login/options")
def begin_login(email: str):
    # first we check if the users is already registered in the database and has at least 1 device in their table
    user = users.get(email)
    if not user or not user["credentials"]:
        raise HTTPException(404, f"there is a issue login in with {email}")
    
    # then we check if the credentials match ! we loop through user[credentials] and append to the publickeycredentialdescriptor
    allow_credentials = [
        PublicKeyCredentialDescriptor(
            id=base64.urlsafe_b64decode(credential["id"] + '=' * (4 - len(credential["id"]) % 4)),
            transports=[AuthenticatorTransport.INTERNAL]
        ) for credential in user["credentials"]
    ]
    
    ## we fill the authenticiaton_options with the RP ID the correct item foudn in the credentials user list
    authentication_options = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=allow_credentials
    )

    # we add the challlenge to the challenges again to prevent replay attkcs
    challenges[email] = authentication_options.challenge
    ## return the json of the authentication options to the browser
    #return json.loads(options_to_json(authentication_options))
    return options_to_json_dict(authentication_options)


############
## now we can verify the login
@app.post("/webauthn/login/verify")
async def finish_login(request: Request):
    ## we do the same thing as above, get the body and details from the body
    body = await request.json()
    email = body["email"]
    
    # and get the user again from the user db
    user = users.get(email)

    # check to make sure the user exists
    if not user:
        raise HTTPException(400, f"There was a issue with login {email}")


    # lets check the challenge to prevent relay attacks
    authentication_challenge = challenges.get(email)    
    if not authentication_challenge:
        raise HTTPException(400, f"There was a issue with login {email}")

    ## now we can start login with the existing credential
    # store the credential id from the body (already base64url string)
    credential_id = body["credential"]["id"]

    ## find the credential id in the user object from above
    used_device_credential = None
    for credential in user["credentials"]:
        if credential["id"] == credential_id:
            used_device_credential = credential 
            break

    # if no valid credential is found the ask to register again 
    if used_device_credential is None:
        raise HTTPException(401, "no credential registered, please register this device" )

    ## next we verify the signature
    verification = verify_authentication_response(
        credential=body["credential"],
        expected_challenge=authentication_challenge,
        expected_rp_id=RP_ID,
        expected_origin=ORIGIN,
        credential_public_key=used_device_credential["public_key"],
        credential_current_sign_count=used_device_credential["counter"],
    )

    # Update de counter van dit device, this will stop replay attacks 
    used_device_credential["counter"] = verification.new_sign_count

    # after succes then the challenge is no longer needed 
    del challenges[email]

    # return a successful device login 
    return {
        "status": "ok",
        "user": email,
        "login_time": int(time.time())
    }


# Mount static files AFTER all API routes to avoid conflicts
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# lets run fastapi 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",      # "filename:app_instance"
        host="localhost",
        port=8000,
        reload=True     # auto-reload when code changes
    )