import os
import rsa
from dotenv import load_dotenv

load_dotenv(".env")

# Define file paths inside the Docker volume
PRIVATE_KEY_FILE = os.environ["PRIVATE_KEY_FILE"]
PUBLIC_KEY_FILE = os.environ["PUBLIC_KEY_FILE"]


def key_generator():
    """Generate new RSA keys or load existing ones from /certs volume.
        Implements Asymmetric auth (use of two keys to verify encoded/encrypted data) vs symmetric auth which uses the same key to verify itself giving one secret key
        rsa keys are a pair,
        - 1 private only we are aware of the plain text key stored securely on our os/network
        - 1 public key used to verify encoded/encrypted data signed with its corresponding private key (our applications private key) (the public key can be shared with other apps that may accept jwts or encrypted data signed with our private key)
            when we create jwt (jwt_token.py) we sign the jwt with the private key now any request sent to our application with the jwt is decoded using the public key
            the public key knows its corresponding private key and can verify this jwt is signed with our apps private key and says this is ok, give access (if someone alters the jwt in anyway it is invalid and rejected)
            the rsa keys are of size 2048 (the larger the more secure the smaller the faster the key gen process,
            larger is good for a one time/periodic gen use case since we are generating keys in the background, in an encrypted chat application you may want a smaller key size)
        * this application generates the rsa keys if no /certs/private.pem or no /certs/public.pem file is found, this certs dir is created on a volume (docker-compose.yml)
            and that volume content is mapped back to our application so we write and/or read the keys files from there
    """

    # check if private and public key files exists
    if os.path.exists(PRIVATE_KEY_FILE) and os.path.exists(PUBLIC_KEY_FILE):
        # if true, open files and, read contents and assign public an private key with content to be returned later
        with open(PUBLIC_KEY_FILE, "rb") as pub_file:
            public_key = rsa.PublicKey.load_pkcs1(pub_file.read())

        with open(PRIVATE_KEY_FILE, "rb") as priv_file:
            private_key = rsa.PrivateKey.load_pkcs1(priv_file.read())
    else:
        # generate rsa keys
        public_key, private_key = rsa.newkeys(2048)

        # Ensure the certs directory exists
        os.makedirs("/certs", exist_ok=True)

        # save keys to the certs volume
        with open(PUBLIC_KEY_FILE, "wb") as pub_file:
            pub_file.write(public_key.save_pkcs1("PEM"))

        with open(PRIVATE_KEY_FILE, "wb") as priv_file:
            priv_file.write(private_key.save_pkcs1("PEM"))

    return private_key, public_key
