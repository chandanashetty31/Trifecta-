import hashlib
import os
from stegano import lsb
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import numpy as np
from scipy.stats import chisquare
import uuid
from PIL import Image
from supabaseClient import supabase 
import imagehash

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def generate_key():
    return os.urandom(32)

KEY = generate_key()  # 32 bytes for AES-256        
# AES 
def encrypt_message(plaintext: str, key: bytes):
    aesgcm = AESGCM(key)
    iv = os.urandom(12)
    ciphertext = aesgcm.encrypt(iv, plaintext.encode(), None)
    return iv + ciphertext 

def decrypt_message(iv_and_ciphertext: bytes, key: bytes):
    aesgcm = AESGCM(key)
    iv = iv_and_ciphertext[:12]
    ciphertext = iv_and_ciphertext[12:]
    plaintext = aesgcm.decrypt(iv, ciphertext, None)
    return plaintext.decode()

def save_uploaded_image(image_file):
    """Save uploaded image and return file path"""
    file_id = str(uuid.uuid4()) + ".png"
    file_path = os.path.join(UPLOAD_FOLDER, file_id)
    image_file.save(file_path)
    return file_path

def get_image_hash(image_path: str) -> str:
    """Compute SHA-256 hash of an image file."""
    hash_sha256 = hashlib.sha256()
    with open(image_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def get_perceptual_hash(image_path: str) -> str:
    """
    Compute the perceptual hash (pHash) of an image file.
    Returns a hexadecimal string representing the hash.
    """
    image = Image.open(image_path)
    phash = imagehash.phash(image)
    return str(phash)


def embed_message(image_path, message):
    #Embed message into image and return stego image path
    stego_file_path = os.path.join(UPLOAD_FOLDER, "stego_" + os.path.basename(image_path))

    encrypted_msg = encrypt_message(message, KEY).hex()    # hex encode for embedding
    secret_image = lsb.hide(image_path, encrypted_msg)
    secret_image.save(stego_file_path)
    return stego_file_path

def upload_stego_to_supabase(local_path: str, bucket_name: str = "image"):
    """
    Uploads the file to Supabase Storage and returns the Public URL.
    """
    file_name = os.path.basename(local_path)
    remote_path = f"stego_uploads/{file_name}" 

    file_options = {
        "content-type": "image/png",
        "upsert": "true"
    }

    if supabase is None:
        raise Exception("Supabase client is not initialized.")

    try:
        with open(local_path, "rb") as f:
            # Execute the upload
            response = supabase.storage.from_(bucket_name).upload(
                path=remote_path, 
                file=f, 
                file_options=file_options
            )

        if hasattr(response, 'error') and response.error:
             raise Exception(f"Supabase API Error: {response.error}")

        # Get Public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(remote_path)

        print(f"Supabase public URL: {public_url}")
        return public_url

    except Exception as e:
        print(f"Error uploading to Supabase: {str(e)}")
        raise e

def get_perceptual_hash(image_path):
    img = Image.open(image_path)
    phash = str(imagehash.phash(img))
    return phash

# NEW FUNCTION TO INSERT RECORD
def insert_stego_record(record_data: dict):
    """
    Inserts a record into the 'stego_uploads' table.
    """
    if supabase is None:
        raise Exception("Supabase client is not initialized.")
    
    # Ensure mandatory fields are present based on your table schema
    if not all(k in record_data for k in ["username", "file_url", "hash", "sentiment", "score"]):
        raise ValueError("Missing required fields for stego_uploads table insert.")

    try:
        # Note: 'score' is a JSONB type, so we pass the Python dictionary
        resp = supabase.table("stego_uploads").insert(record_data).execute()
    except Exception as e:
        print(f"Error inserting record into stego_uploads: {str(e)}")
        raise e
    
    # Simple check for error on insert response
    if hasattr(resp, 'error') and resp.error:
        raise Exception(f"Supabase DB Insert Error: {resp.error}")
    
    return resp

def detect_steganography(image_path, threshold=0.2):

    #chi-square steganalysis
    
    img = Image.open(image_path).convert("L")
    pixels = np.array(img).flatten()

    even_freq = np.sum(pixels % 2 == 0)
    odd_freq = np.sum(pixels % 2 == 1)

    chi2, p_value = chisquare([even_freq, odd_freq])

    if p_value < threshold:
        hidden_message = lsb.reveal(image_path)
        return True, hidden_message
    else:
        return False, None