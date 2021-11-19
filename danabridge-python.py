#!/usr/bin/env python3


from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session
import requests
import json
import time

my_username = "[username]"
my_password = "[password]"


def danalock_initialise(user_id, secret):
    client_id = "danalock-web"
    BASE_URL = "https://api.danalock.com/oauth2/token"

    oauth = OAuth2Session(client=LegacyApplicationClient(client_id=client_id))

    token = oauth.fetch_token(token_url=BASE_URL,
                              username=user_id, password=secret, client_id=client_id,
                              client_secret="")

    if "access_token" not in token:
        print(f"error getting danalock token - response was {token}")
        exit()

    return token["access_token"], token["refresh_token"]


# returns a dict of each lock's name and its serial number (needed for commands)
def get_all_danalocks(token):

    url = "https://api.danalock.com/locks/v1"
    r = requests.get(url, headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json', 'content-type': 'application/json'})

    if r.status_code != 200:
        print(f"error getting list of danalocks - error {r.status_code} and response {r.text}")
        exit()

    results = json.loads(r.text)

    danalocks = {}
    for x in results:
        danalocks[x["name"].lower()] = x["afi"]["serial_number"]
    return danalocks

def get_danalock_status(token, serial):

    execute_url = "https://bridge.danalockservices.com/bridge/v1/execute"

    payload = json.dumps({"device": serial, "operation": "afi.lock.get-state"})

    r = requests.post(execute_url, headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json', 'content-type': 'application/json'}, data=payload)

    if r.status_code != 200:
        print(f"error getting job ID - error {r.status_code} and response {r.text}")
        return None

    job_id = json.loads(r.text)["id"]
    # print(f"Got job ID {job_id}. Will now poll for status")

    # try ten times
    for i in range(0, 10):
        time.sleep(2)

        poll_url = "https://bridge.danalockservices.com/bridge/v1/poll"

        payload = json.dumps({"id": job_id})

        # print(f"Attempt {i}")
        r = requests.post(poll_url, headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json', 'content-type': 'application/json'}, data=payload)

        if r.status_code == 404:
            print(f"Lock either not on danabridge, lock out of battery, danabridge disconnected, or lock out of danabridge bluetooth range")
            return None
        elif r.status_code != 200:
            print(f"error getting lock status - error {r.status_code} and response {r.text}")
            return None

        if "Succeeded" in r.text:
            return json.loads(r.text)["result"]["state"]

    print(f"did not succeed getting lock status after {i*2}s - final response was {r.text}")
    return None

# resturns a list of pincodes, each item being a dict with the following keys
# [{'identifier': [the pin code identifier, 1 thru 20],
# 'status': [something to do with the timer function - haven't investigated[],
# 'digits': 'CODE'},
def get_pin_codes(token, serial):

    execute_url = "https://bridge.danalockservices.com/bridge/v1/execute"

    payload = json.dumps({"device": serial, "operation": "afi.pin-codes.get-pin-codes", "arguments": ["20"]})

    r = requests.post(execute_url, headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json', 'content-type': 'application/json'}, data=payload)

    if r.status_code != 200:
        print(f"error getting job ID - error {r.status_code} and response {r.text}")
        return None

    job_id = json.loads(r.text)["id"]
    print(f"Got job ID {job_id}. Will now poll for status")

    # try ten times
    for i in range(0, 30):
        time.sleep(2)

        poll_url = "https://bridge.danalockservices.com/bridge/v1/poll"

        payload = json.dumps({"id": job_id})

        r = requests.post(poll_url, headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json', 'content-type': 'application/json'}, data=payload)

        if r.status_code == 404:
            print(f"Lock either not on danabridge, lock out of battery, danabridge disconnected, or lock out of danabridge bluetooth range")
            return None
        elif r.status_code != 200:
            print(f"error getting lock PINs - error {r.status_code} and response {r.text}")
            return None

        if "Succeeded" in r.text:
            pin_codes = json.loads(r.text)["result"]["pin_codes"]

            # this returns many blank pins - remove all blanks from list
            for x in range(len(pin_codes), 0, -1):
                if pin_codes[x - 1]["digits"] == "":
                    pin_codes.pop(x - 1)

            return pin_codes

        else:
            print(f"Attempt {i}: {json.loads(r.text)}")

    print(f"did not succeed getting lock PINs after {i*2}s - final response was {r.text}")
    return None


# sets pin code #identifier for lock #serial to #new_code
# if new_code is "" then deletees that PIN
def set_pin_code(token, serial, identifier, new_code):

    execute_url = "https://bridge.danalockservices.com/bridge/v1/execute"

    if new_code == "":
        payload = json.dumps({"device": serial, "operation": "afi.pin-codes.set-pin-code", "arguments": [str(identifier), "Cleared", ""]})
    else:
        payload = json.dumps({"device": serial, "operation": "afi.pin-codes.set-pin-code", "arguments": [str(identifier), "Enabled", new_code]})

    r = requests.post(execute_url, headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json', 'content-type': 'application/json'}, data=payload)

    if r.status_code != 200:
        print(f"error getting job ID - error {r.status_code} and response {r.text}")
        return None

    job_id = json.loads(r.text)["id"]
    print(f"Got job ID {job_id}. Will now poll for status")

    # try ten times
    for i in range(0, 30):
        time.sleep(2)

        poll_url = "https://bridge.danalockservices.com/bridge/v1/poll"

        payload = json.dumps({"id": job_id})

        r = requests.post(poll_url, headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json', 'content-type': 'application/json'}, data=payload)

        if r.status_code == 404:
            print(f"Lock either not on danabridge, lock out of battery, danabridge disconnected, or lock out of danabridge bluetooth range")
            return False
        elif r.status_code != 200:
            print(f"error setting lock status - error {r.status_code} and response {r.text}")
            return False

        if "Succeeded" in r.text:
            result = json.loads(r.text)["result"]
            if result["afi_status_text"] == "Ok" and result["dmi_status_text"] == "Ok":
                if new_code == "":
                    print(f"Successfully deleted lock {serial} pin #{identifier}")
                else:
                    print(f"Successfully changed lock {serial} pin #{identifier} to {new_code}")
                return True
            else:
                print(f"Error changing lock {serial} pin #{identifier} to {new_code} - message was '{r.text}'")
                return False

        else:
            print(f"Attempt {i}: {json.loads(r.text)}")

    print(f"did not succeed setting lock status after {i*2}s - final response was {r.text}")
    return False


def operate_danalock(token, serial, command):

    execute_url = "https://bridge.danalockservices.com/bridge/v1/execute"

    payload = json.dumps({"device": serial, "operation": "afi.lock.operate", "arguments": [command]})

    r = requests.post(execute_url, headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json', 'content-type': 'application/json'}, data=payload)

    if r.status_code != 200:
        print(f"error getting job ID - error {r.status_code} and response {r.text}")
        return None
    elif "id" in r.text:
        print(f"Succesfully sent command {command} to lock {serial}")
    else:
        print(f"Unexpected response to command {command} was {r.text}")


# start here
access_token, refresh_token = danalock_initialise(my_username, my_password)
print(f"got access token {access_token}")

danalocks = get_all_danalocks(access_token)

print(f"Dict with all danalocks on the account: {danalocks}")

# gets all the pincodes for the danalock named "front door"
pin_codes = get_pin_codes(access_token, danalocks["front door"])
print(f"Front door pin codes: {pin_codes}")

# to create a new PIN #2 or change existing PIN #2
# set_pin_code(access_token, danalocks["front door"], 2, "1234")

# to delete existing PIN #2
# set_pin_code(access_token, danalocks["front door"], 2, "")

# to lock the front door
# operate_danalock(access_token, danalocks["front door"], "lock")

# to unlock the front door
# operate_danalock(access_token, danalocks["front door"], "unlock")

