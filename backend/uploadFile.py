import threading
from stego_utils import upload_stego_to_supabase, insert_stego_record, get_perceptual_hash
from blockchain import store_image_on_chain, health_check, is_similar_to_existing


def check_duplicate_before_upload(image_path, similarity_threshold=10):
    """
    Check if image is duplicate BEFORE uploading.
    
    Returns:
        dict: {
            "is_duplicate": bool,
            "similar_images": list,
            "perceptual_hash": str
        }
    """
    try:
        # Check blockchain health
        if not health_check():
            raise Exception("Blockchain not connected")
        
        # Compute perceptual hash
        phash = get_perceptual_hash(image_path)
        if not phash:
            raise Exception("Failed to compute perceptual hash")
        
        print(f"[DUPLICATE CHECK] Computed perceptual hash: {phash}")
        
        # Check for similar images on blockchain
        similarity_result = is_similar_to_existing(phash, similarity_threshold)
        
        return {
            "is_duplicate": similarity_result["is_duplicate"],
            "similar_images": similarity_result["similar_images"],
            "min_distance": similarity_result["min_distance"],
            "perceptual_hash": phash
        }
        
    except Exception as e:
        print(f"[DUPLICATE CHECK] Error: {e}")
        raise


def async_upload_stego_and_insert(output_path, data_to_insert: dict, skip_blockchain: bool = False):
    """
    Run the upload task and database insert in a background thread.
    After DB insert succeeds, store hash & pHash on blockchain (unless skip_blockchain=True).
    
    Args:
        output_path: Path to the stego image file
        data_to_insert: Dictionary with upload data (username, hash, perceptual_hash, etc.)
        skip_blockchain: If True, skip blockchain storage (already done synchronously)
    
    NOTE: When skip_blockchain=True, blockchain storage was already done synchronously
    to prevent race conditions with duplicate detection.
    """
    def task():
        print(f"[UPLOAD THREAD] Starting upload for: {output_path}")
        public_url = None
        
        try:
            # Upload to Supabase
            public_url = upload_stego_to_supabase(output_path)
            print(f"[UPLOAD THREAD] SUCCESS - Uploaded to Supabase: {public_url}")
        except Exception as e:
            print(f"[UPLOAD THREAD] FAILED - Supabase upload error: {e}")
            return
        
        if public_url:
            # Insert record to database
            print(f"[DB INSERT THREAD] Starting record insert for: {public_url}")
            try:
                insert_data = {
                    "username": data_to_insert.get("username"),
                    "file_url": public_url,
                    "hash": data_to_insert.get("hash"),
                    "sentiment": data_to_insert.get("sentiment"),
                    "score": data_to_insert.get("score")
                }
                resp = insert_stego_record(insert_data)
                print(f"[DB INSERT THREAD] SUCCESS - Record inserted for: {public_url}")
            except Exception as e:
                print(f"[DB INSERT THREAD] FAILED - Supabase insert error: {e}")
                return
            
            # Store on blockchain (only if not already done)
            if skip_blockchain:
                print("[BLOCKCHAIN] Skipping - already stored synchronously to prevent race conditions")
            else:
                try:
                    print("[BLOCKCHAIN] Storing image hash on blockchain...")
                    
                    # Get perceptual hash (already computed in the route)
                    phash = data_to_insert.get("perceptual_hash", "")
                    if not phash:
                        print("[BLOCKCHAIN] WARNING: No perceptual hash provided, computing now...")
                        phash = get_perceptual_hash(output_path)
                        print(f"[BLOCKCHAIN] Computed perceptual hash: {phash}")
                    
                    # Store on blockchain (duplicate check already passed in the route)
                    tx_result = store_image_on_chain(
                        sha_hash=data_to_insert.get("hash"),
                        perceptual_hash=phash
                    )
                    print(f"[BLOCKCHAIN] ✅ Stored on chain - TX: {tx_result['txHash']}")
                    
                except Exception as e:
                    print(f"[BLOCKCHAIN] ❌ FAILED to store on chain: {e}")
    
    thread = threading.Thread(target=task)
    thread.start()
    return thread