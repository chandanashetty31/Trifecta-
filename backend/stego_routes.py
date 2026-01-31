from flask import Blueprint, request, jsonify
from flask_cors import CORS  
from stegano import lsb
import os
import re
from uploadFile import async_upload_stego_and_insert
from stego_utils import get_image_hash, save_uploaded_image, embed_message
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
from flask_jwt_extended import jwt_required, get_jwt_identity
from supabaseClient import supabase
from stego_utils import get_perceptual_hash
from blockchain import is_similar_to_existing, health_check


upload_bp = Blueprint("upload_bp", __name__)
CORS(upload_bp) 


try:
    from supabaseClient import supabase
except Exception as e:
    supabase = None
    print("Warning: supabase client not available in comments_routes:", e)
    
_analyzer = SentimentIntensityAnalyzer()
_emoji_scores = {}
try:
    df = pd.read_csv("Datasets/Emoji_trimmed.csv")
    df['Score'] = df['Positive'] - df['Negative']
    _emoji_scores = dict(zip(df['Emoji'], df['Score']))
except Exception as e:
    print("Emoji dataset not loaded in stego_routes:", e)

def _analyze_sentiment(text: str):
    score = _analyzer.polarity_scores(text)
    compound = score["compound"]

    for ch in text:
        if ch in _emoji_scores:
            compound += _emoji_scores[ch]

    score["compound"] = compound
    if compound > 0.05:
        label = "positive"
    elif compound < -0.05:
        label = "negative"
    else:
        label = "neutral"
    return label, score


@upload_bp.route("/check-duplicate", methods=["POST"])
@jwt_required()
def check_duplicate():
    """
    Check if uploaded image is a duplicate BEFORE processing.
    This is called when user selects an image.
    """
    if "image" not in request.files:
        return jsonify({
            "status": "error",
            "message": "Image required"
        }), 400

    image_file = request.files["image"]
    username = get_jwt_identity()
    
    # Step 1: Blockchain health check
    try:
        if not health_check():
            return jsonify({
                "status": "error",
                "message": "Blockchain connection unavailable"
            }), 503
    except Exception as e:
        print(f"[DUPLICATE CHECK] Health check failed: {e}")
        return jsonify({
            "status": "error",
            "message": f"Blockchain health check failed: {str(e)}"
        }), 503
    
    # Step 2: Save uploaded image temporarily
    image_path = None
    try:
        image_path = save_uploaded_image(image_file)
        print(f"[DUPLICATE CHECK] Image saved to: {image_path}")
    except Exception as e:
        print(f"[DUPLICATE CHECK] Failed to save image: {e}")
        return jsonify({
            "status": "error",
            "message": "Failed to save image"
        }), 500
    
    # Step 3: Compute perceptual hash
    phash = None
    try:
        phash = get_perceptual_hash(image_path)
        print(f"[DUPLICATE CHECK] Computed perceptual hash: {phash}")
    except Exception as e:
        print(f"[DUPLICATE CHECK] Failed to compute perceptual hash: {e}")
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except:
                pass
        return jsonify({
            "status": "error",
            "message": "Failed to compute perceptual hash",
            "error": str(e)
        }), 500
    
    # Step 4: Check for similar images on blockchain
    try:
        print(f"[DUPLICATE CHECK] Starting blockchain similarity check...")
        
        # Use threading for timeout
        from threading import Thread
        import queue
        
        result_queue = queue.Queue()
        
        def blockchain_check():
            try:
                result = is_similar_to_existing(phash, similarity_threshold=10)
                result_queue.put(("success", result))
            except Exception as e:
                result_queue.put(("error", e))
        
        check_thread = Thread(target=blockchain_check)
        check_thread.daemon = True
        check_thread.start()
        check_thread.join(timeout=10)
        
        if check_thread.is_alive():
            print(f"[DUPLICATE CHECK] Blockchain call timed out after 10 seconds")
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except:
                    pass
            return jsonify({
                "status": "error",
                "message": "Blockchain call timed out",
                "hint": "Check if Ganache is running on http://127.0.0.1:8545"
            }), 503
        
        try:
            status, result = result_queue.get_nowait()
        except queue.Empty:
            raise Exception("Blockchain check completed but no result returned")
        
        if status == "error":
            raise result
        
        similarity_result = result
        print(f"[DUPLICATE CHECK] Similarity result: {similarity_result}")
        
        # Clean up temporary file
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as cleanup_err:
                print(f"[DUPLICATE CHECK] Failed to cleanup temp file: {cleanup_err}")
        
        if similarity_result["is_duplicate"]:
            similar_images_info = []
            for img in similarity_result["similar_images"]:
                similar_images_info.append({
                    "index": img["index"],
                    "timestamp": img["timestamp"],
                    "distance": img["distance"],
                    "uploader": img["uploader"]
                })
            
            return jsonify({
                "status": "duplicate",
                "is_duplicate": True,
                "message": "Similar image already exists on blockchain",
                "similar_images": similar_images_info,
                "min_distance": similarity_result["min_distance"],
                "perceptual_hash": phash
            }), 200
        else:
            return jsonify({
                "status": "unique",
                "is_duplicate": False,
                "message": "Image is unique",
                "perceptual_hash": phash,
                "min_distance": similarity_result["min_distance"]
            }), 200
            
    except Exception as e:
        print(f"[DUPLICATE CHECK] Blockchain similarity check failed: {e}")
        import traceback
        traceback.print_exc()
        
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except:
                pass
        return jsonify({
            "status": "error",
            "message": "Failed to check for duplicates on blockchain",
            "error": str(e),
            "hint": "Make sure Ganache is running and contract is deployed"
        }), 500


@upload_bp.route("/upload", methods=["POST"])
@jwt_required()
def embed_route():
    """
    Upload route with integrated duplicate checking.
    Now checks blockchain BEFORE uploading!
    """
    if "image" not in request.files or "message" not in request.form:
        return jsonify({"status": "error", "message": "Image and message required"}), 400

    image_file = request.files["image"]
    message = request.form["message"]
    username = get_jwt_identity()
    
    # Step 1: Sentiment analysis
    sentiment, score = _analyze_sentiment(message)
    if sentiment == "negative":
        return jsonify({
            "status": "rejected",
            "message": "Cannot embed secret message is not positive.",
            "sentiment": sentiment,
            "score": score
        }), 400
    
    # Step 2: Save uploaded image
    image_path = save_uploaded_image(image_file)
    
    # Step 3: Check for hidden message
    hidden_message = None
    try:
        hidden_message = lsb.reveal(image_path)
    except IndexError:
        hidden_message = None
    except Exception as e:
        print(f"Reveal error: {e}")
        hidden_message = None

    if hidden_message:
        # Clean up
        if os.path.exists(image_path):
            os.remove(image_path)
        return jsonify({
            "status": "hidden data detected",
            "hidden_message": hidden_message
        }), 400
    
    # === NEW: DUPLICATE CHECK BEFORE EMBEDDING ===
    print("[UPLOAD] Checking for duplicates on blockchain...")
    
    try:
        # Check blockchain health
        if not health_check():
            if os.path.exists(image_path):
                os.remove(image_path)
            return jsonify({
                "status": "error",
                "message": "Blockchain connection unavailable"
            }), 503
        
        # Compute perceptual hash of original image
        phash = get_perceptual_hash(image_path)
        print(f"[UPLOAD] Computed perceptual hash: {phash}")
        
        # Check for duplicates
        similarity_result = is_similar_to_existing(phash, similarity_threshold=10)
        
        if similarity_result["is_duplicate"]:
            # DUPLICATE FOUND - REJECT UPLOAD
            similar = similarity_result["similar_images"][0]
            print(f"[UPLOAD] DUPLICATE DETECTED - Upload blocked!")
            print(f"[UPLOAD] Similar to image #{similar['index']} (distance: {similar['distance']})")
            
            # Clean up
            if os.path.exists(image_path):
                os.remove(image_path)
            
            return jsonify({
                "status": "duplicate",
                "message": "This image is too similar to an existing image on the blockchain",
                "is_duplicate": True,
                "details": {
                    "distance": similar["distance"],
                    "threshold": 10,
                    "existing_image_index": similar["index"],
                    "existing_uploader": similar["uploader"],
                    "timestamp": similar["timestamp"]
                }
            }), 409  # 409 Conflict
        
        print("[UPLOAD] Image is unique - Proceeding with embedding and upload")
        
    except Exception as e:
        print(f"[UPLOAD] Duplicate check failed: {e}")
        if os.path.exists(image_path):
            os.remove(image_path)
        return jsonify({
            "status": "error",
            "message": "Failed to verify image uniqueness on blockchain",
            "error": str(e)
        }), 500
    
    # === IMAGE IS UNIQUE - PROCEED WITH EMBEDDING ===
    
    # Step 4: Embed message
    output_path = None
    try:
        output_path = embed_message(image_path, message)
        print(f"[UPLOAD] Message embedded successfully: {output_path}")
    except Exception as e:
        print(f"[UPLOAD] Embedding error: {e}")
        if os.path.exists(image_path):
            os.remove(image_path)
        return jsonify({
            "status": "error",
            "message": "Failed to embed message.",
            "error": str(e)
        }), 500
    
    # Step 5: Compute hash of embedded image
    image_hash = None
    try:
        image_hash = get_image_hash(output_path)
        print(f"[UPLOAD] Computed hash: {image_hash}")
    except Exception as e:
        print(f"[UPLOAD] Hash computation error: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return jsonify({
            "status": "error",
            "message": "Failed to compute image hash after embedding."
        }), 500

    # Step 6: Store on blockchain SYNCHRONOUSLY to prevent race conditions
    # This ensures duplicate detection works even for rapid re-uploads
    try:
        from blockchain import store_image_on_chain
        print("[UPLOAD] Storing perceptual hash on blockchain BEFORE returning success...")
        tx_result = store_image_on_chain(
            sha_hash=image_hash,
            perceptual_hash=phash
        )
        print(f"[UPLOAD] Stored on blockchain - TX: {tx_result['txHash']}")
    except Exception as e:
        print(f"[UPLOAD] FAILED to store on blockchain: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return jsonify({
            "status": "error",
            "message": "Failed to store image on blockchain",
            "error": str(e)
        }), 500
    
    # Step 7: Start async upload to Supabase (DB record insert)
    # Blockchain storage already done, so Supabase upload can be async
    data_to_insert = {
        "username": username,
        "hash": image_hash,
        "perceptual_hash": phash,  # Pass the already computed phash
        "sentiment": sentiment,
        "score": score,
        "blockchain_stored": True  # Flag that blockchain storage is complete
    }
    
    async_upload_stego_and_insert(output_path, data_to_insert, skip_blockchain=True)

    return jsonify({
        "status": "ok",
        "message": "Message embedded and uploaded successfully!",
        "saved_path": output_path,
        "sha256": image_hash,
        "perceptual_hash": phash,
        "sentiment": sentiment,
        "score": score,
        "blockchain_tx": tx_result['txHash']
    }), 200


def _extract_supabase_result(resp):
    """
    Normalizes supabase-py return shapes.
    Returns (data, error)
    """
    if resp is None:
        return None, "No supabase client response"
    if isinstance(resp, dict):
        return resp.get("data"), resp.get("error")
    data = getattr(resp, "data", None)
    error = getattr(resp, "error", None)
    return data, error


@upload_bp.route("/upload", methods=["GET"])
@jwt_required()
def list_uploads():
    if supabase is None:
        return jsonify({"error": "Supabase not configured"}), 500

    try:
        resp = supabase.table("stego_uploads").select("*").order("created_at", desc=True).execute()
    except Exception as e:
        return jsonify({"error": "Supabase fetch failed", "detail": str(e)}), 500

    data, error = _extract_supabase_result(resp)
    if error:
        return jsonify({"error": error}), 500

    return jsonify({"uploads": data}), 200