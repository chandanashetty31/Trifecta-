from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import traceback

try:
    from supabaseClient import supabase
except Exception as e:
    supabase = None
    print("Warning: supabase client not available in comments_routes:", e)

comments_bp = Blueprint("comments_bp", __name__)
def _extract_supabase_result(resp):
    """
    Normalize various supabase-py return shapes.
    Returns (data, error)
    """
    if resp is None:
        return None, "No response from supabase client"

    if hasattr(resp, "data") or hasattr(resp, "error"):
        data = getattr(resp, "data", None)
        error = getattr(resp, "error", None)
        return data, error

    if isinstance(resp, dict):
        return resp.get("data"), resp.get("error")

    try:
       
        if isinstance(resp, (list, tuple)) and len(resp) >= 2:
            maybe_error = resp[-1]
            maybe_data = resp[0]
            if maybe_error:
                return maybe_data, maybe_error
            return maybe_data, None
    except Exception:
        pass

    return resp, None


@comments_bp.route("/comments", methods=["POST"])
@jwt_required()
def add_comment():
    if supabase is None:
        return jsonify({"error": "Supabase client not configured"}), 500

    payload = request.get_json(silent=True) or {}
    post_id = payload.get("post_id")
    text = payload.get("text")
    avatar_url = payload.get("avatar_url")
    image_url = payload.get("image_url")

    current_app.logger.debug("add_comment payload: %r", payload)

    if post_id is None or text is None:
        return jsonify({"error": "post_id and text are required"}), 400

    try:
        post_id_val = int(post_id)
    except Exception:
    
        post_id_val = post_id
    username = get_jwt_identity() or payload.get("username") or "Anonymous"

    row = {
        "post_id": post_id_val,
        "username": username,
        "image_url": image_url,
        "text": text
    }

    if avatar_url:
        row["avatar_url"] = avatar_url

    try:
       
        resp = supabase.table("comments").insert(row).execute()
    except Exception as e:
        current_app.logger.error("Supabase insert exception: %s", traceback.format_exc())
        return jsonify({"error": "Supabase insert failed", "detail": str(e)}), 500

    data, error = _extract_supabase_result(resp)
    if error:
        current_app.logger.error("Supabase returned error on insert: %s", error)
        return jsonify({"error": error}), 500

    created = None
    if isinstance(data, list) and len(data) > 0:
        created = data[0]
    else:
        created = data

    current_app.logger.debug("Inserted comment row: %r", created)

    return jsonify({"status": "ok", "comment": created})


@comments_bp.route("/comments", methods=["GET"])
def get_comments():
    if supabase is None:
        return jsonify({"error": "Supabase client not configured"}), 500

    post_id = request.args.get("post_id")
    if post_id is None:
        return jsonify({"error": "post_id query parameter required"}), 400

    try:
        pid_val = int(post_id)
    except Exception:
        pid_val = post_id

    current_app.logger.debug("get_comments: post_id param=%r normalized=%r", post_id, pid_val)

    try:
        resp = (
            supabase.table("comments")
            .select("*")
            .eq("post_id", pid_val)
            .order("created_at")
            .execute()
        )
    except Exception as e:
        current_app.logger.error("Supabase select exception: %s", traceback.format_exc())
        return jsonify({"error": "Supabase select failed", "detail": str(e)}), 500

    data, error = _extract_supabase_result(resp)
    if error:
        current_app.logger.error("Supabase returned error on select: %s", error)
        return jsonify({"error": error}), 500

    comments = data or []
    return jsonify({"comments": comments})

