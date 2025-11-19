import os
import json
import logging
import smtplib
import random
import requests
import secrets
from datetime import datetime
from google.cloud import secretmanager
from google.cloud import firestore
from email.mime.text import MIMEText
from urllib.parse import urlencode
from flask import Flask, request, redirect, jsonify, abort
from flask import Response
from urllib.parse import unquote

app = Flask(__name__)

# Check if there are not any states in the DB
def is_states_collection_empty():
    docs = states_ref.limit(1).stream()
    return not any(docs)

# Generate a random six digit state
def generate_state():
    return random.randint(100000, 999999)

# Store the state in Firestore
def store_state(state):
    states_ref.document(str(state)).set({
        "used": False,
        "created_at": datetime.utcnow()
    })

# Check if the state is valid and unused
def is_valid_state(state):
    doc = states_ref.document(str(state)).get()
    return doc.exists and not doc.to_dict().get("used", True)

# Mark the state as used
def mark_state_as_used(state):
    doc = states_ref.document(str(state)).get()
    if doc.exists:
        states_ref.document(str(state)).update({
            "used": True
        })

# Required environment variables:
# LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, REDIRECT_URI
CLIENT_ID = os.environ.get("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI")  # must match LinkedIn app setting
STATE = os.environ.get("STATE")
STATES_COLLECTION = os.environ.get("STATES_COLLECTION")
CLIENT_NAME = os.environ.get("CLIENT_NAME")

# Optional: path where tokens will be saved during testing (not recommended for prod)
TOKEN_SAVE_PATH = os.environ.get("TOKEN_SAVE_PATH", "/tmp/linkedin_tokens.json")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL")

# Email configuration
SMTP_SERVER = os.environ.get("SMTP_SERVER")
SMTP_PORT = os.environ.get("SMTP_PORT")
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
    app.logger.warning("Missing one of LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, REDIRECT_URI env vars")

# Initialize Firestore DB
db = firestore.Client()
states_ref = db.collection(STATES_COLLECTION)
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET"])
def index():
    """
    Helpful status route. You can visit the service root in a browser to verify it's up.
    """
    params = request.args
    code = request.args.get("code")
   
  # ➤ Send code by email
    recipient_email = RECIPIENT_EMAIL
    subject = "LinkedIn Code Received"
    body = f"LinkedIn Authorization Code: {code}\n"

    send_email(recipient_email, subject, body)
    linkedin_callback()

    return jsonify({
        "status": "ok",
        "note": "This service accepts GET requests to /callback with LinkedIn code",
        "received_params": params
    })

def send_email(recipient, subject, body):
    msg = MIMEText(body)
    msg["From"] = EMAIL_USER
    msg["To"] = recipient
    msg["Subject"] = subject

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, recipient, msg.as_string())


@app.route("/callback", methods=["GET"])
def linkedin_callback():
    """
    LinkedIn will redirect here with ?code=...&state=...
    This endpoint exchanges the code for an access token (and refresh token if available).
    """
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")

    if not STATE or state != STATE:
        app.logger.error("Invalid or missing state parameter")
        recipient_email = RECIPIENT_EMAIL
        subject = f"Attempt to OAUTH using an expired state for {CLIENT_NAME if CLIENT_NAME else 'Unknown Client'}"
        body = f"Invalid_state: {state} (Deploy your callback source again using this as the state env variable value)\nClient Name: {CLIENT_NAME if CLIENT_NAME else 'Unknown Client'}"
        send_email(recipient_email, subject, body)
        return jsonify({"error": "invalid_state"}), 400

    if error:
        desc = request.args.get("error_description", "")
        app.logger.error("OAuth returned error: %s %s", error, desc)
        return jsonify({"error": error, "error_description": desc}), 400

    if not code:
        app.logger.error("No code parameter found in request")
        return jsonify({"error": "missing_code"}), 400

    if not is_states_collection_empty():
        if not is_valid_state(state):
            app.logger.error("State parameter is invalid or has already been used")
            # Find a not used state within firestore
            unused_states = states_ref.where("used", "==", False).stream()
            unused_state = None
            for doc in unused_states:
                app.logger.info(f"Unused state found: {doc.id}")
                unused_state = doc.id
                break
            else:
                app.logger.info("No unused states found in the database.")
            # ➤ Send failed attempt email
            recipient_email = RECIPIENT_EMAIL
            subject = f"Attempt to OAUTH using an expired state for {CLIENT_NAME if CLIENT_NAME else 'Unknown Client'}"
            body = f"Expired_state: {state}\nNew_state: {unused_state if unused_state else 'No unused states available'} (Deploy your callback source again using this as the state env variable value) \nClient Name: {CLIENT_NAME if CLIENT_NAME else 'Unknown Client'}"
            send_email(recipient_email, subject, body)
            return jsonify({"error": "invalid_or_used_state"}), 400

    new_state = generate_state()
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"

    # Build form body per LinkedIn docs
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:
        resp = requests.post(token_url, data=payload, headers=headers, timeout=15)
    except requests.RequestException as e:
        app.logger.exception("Network error while exchanging code: %s", e)
        return jsonify({"error": "network_error", "detail": str(e)}), 502

    if resp.status_code != 200:
        # Helpful debug info (don't leak secrets to public logs in prod)
        app.logger.error("Token exchange failed: status=%s body=%s", resp.status_code, resp.text)
        return jsonify({"error": "token_exchange_failed", "status": resp.status_code, "body": resp.text}), resp.status_code

    token_data = resp.json()
    access_token = token_data.get("access_token")
    url = "https://api.linkedin.com/v2/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    callerInfo = r.json()

    # token_data typically contains: access_token, expires_in, (maybe) refresh_token
    app.logger.info("Token exchange success: %s", {k: v for k, v in token_data.items() if k != "access_token"})

    # For testing: save tokens to a temp file (NOT for production)
    try:
        with open(TOKEN_SAVE_PATH, "w") as fh:
            json.dump(token_data, fh)
        app.logger.info("Saved token to %s (for testing)", TOKEN_SAVE_PATH)
    except Exception:
        app.logger.exception("Failed saving token locally")

  # ➤ Send code by email
    recipient_email = RECIPIENT_EMAIL
    subject = "LinkedIn Code Received"
    body = f"LinkedIn Authorization Code: {code}\nToken Data: {json.dumps(token_data, indent=2)}\nFirstName: {callerInfo.get('localizedFirstName')}\nLastName: {callerInfo.get('localizedLastName')}\nID: {callerInfo.get('id')}\nNew_state: {new_state}"

    send_email(recipient_email, subject, body)

    mark_state_as_used(state)
    store_state(new_state)

    # TODO (recommended): store tokens in a secure store (Secret Manager, Cloud SQL, Firestore)
    # Example response shown to the browser (avoid showing raw tokens in production)
    safe = {k: v for k, v in token_data.items() if k != "access_token"}
    return Response(json.dumps({"message": "Thank you for granting access to Digital Yalo, inc., the LinkedIn API is now available for use.", 
        "scopes_granted": safe.get("scope", [])}, indent=4),
        mimetype="application/json",
        status=200)

@app.route("/tokens", methods=["GET"])
def show_tokens_for_testing():
    """
    A convenience route for debugging/testing only: reads tokens file and returns JSON.
    REMOVE or protect this in production (or require auth).
    """
    try:
        with open(TOKEN_SAVE_PATH, "r") as fh:
            data = json.load(fh)
        return jsonify({"tokens": data}), 200
    except FileNotFoundError:
        return jsonify({"error": "no_tokens_saved"}), 404
    except Exception as e:
        app.logger.exception("Error reading tokens file")
        return jsonify({"error": "read_failed", "detail": str(e)}), 500


if __name__ == "__main__":
    # Cloud Run expects the service to bind to 0.0.0.0 and $PORT
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
