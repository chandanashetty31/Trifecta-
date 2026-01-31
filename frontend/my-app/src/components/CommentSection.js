
import axios from "axios";
import { useEffect, useState } from "react";
import { Button, Form, ListGroup } from "react-bootstrap";

export default function CommentSection({ postId, username = "Anonymous", initialComments = [] }) {
  const [comments, setComments] = useState(initialComments || []);
  const [newComment, setNewComment] = useState("");
  const apiBase = "http://localhost:8000"; 

  // Fetch comments from backend on mount or when postId changes
  useEffect(() => {
    if (!postId) return;
    const token = sessionStorage.getItem("token");
    axios.get(`${apiBase}/comments`, {
      params: { post_id: postId },
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    .then(res => {
      setComments(res.data.comments || []);
    })
    .catch(err => {
      console.error("Failed to fetch comments:", err.response?.data || err.message);
     
    });
  }, [postId]);

  const addComment = async (e) => {
    e.preventDefault();
    const text = newComment.trim();
    if (!text) return;

    const token = sessionStorage.getItem("token");
    if (!token) {
      alert("You must be signed in to post a comment.");
      return;
    }

    try {   
   
      const analyze = await axios.post(
        `${apiBase}/analyze`,
        { comment: text },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const sentiment = analyze.data.sentiment;
      if (sentiment === "negative") {
        alert("Your comment seems negative. Please revise it.");
        return;
      }
      
      const resp = await axios.post(
        `${apiBase}/comments`,
        {
          post_id: postId,
          text
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      const created = resp.data?.comment;
      if (created) {
       
        setComments((c) => [...c, created]);
        setNewComment("");
      } else {
        
        setComments((c) => [...c, { text, username }]);
        setNewComment("");
      }
    } catch (error) {
      console.error("Error posting comment:", error.response?.data || error.message);
      alert("Failed to post comment. Try again.");
    }
  };

  return (
    <div>
      <ListGroup className="mb-3">
        {comments.map((c, i) => (
          <ListGroup.Item key={c.id ?? i}>
            <strong>{c.username ?? c.user ?? "User"}: </strong>{c.text}
            <div style={{ fontSize: "0.8em", color: "#666" }}>
              {c.created_at ? new Date(c.created_at).toLocaleString() : null}
            </div>
          </ListGroup.Item>
        ))}
      </ListGroup>

      <Form onSubmit={addComment}>
        <Form.Control
          type="text"
          placeholder="Add a comment..."
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
        />
        <Button type="submit" className="mt-2">Post</Button>
      </Form>
    </div>
  );
}


