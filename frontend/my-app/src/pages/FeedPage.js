import { useEffect, useState } from "react";
import axios from "axios";
import { Card, Container } from "react-bootstrap";
import CommentSection from "../components/CommentSection";
import LikeButton from "../components/LikeButton";

export default function FeedPage() {
  const [posts, setPosts] = useState([]);

  useEffect(() => {
    fetchUploads();
  }, []);

  async function fetchUploads() {
    try {
      const token = sessionStorage.getItem("token");
      console.log("FETCHING UPLOADS WITH TOKEN:", token);

      const res = await axios.get("http://localhost:8000/upload", {
        headers: { Authorization: `Bearer ${token}` }
      });

      setPosts(res.data.uploads);
    } catch (err) {
      console.error("UPLOAD FETCH ERROR:", err);
    }
  }

  return (
    <Container className="mt-4">
  {posts.map((post) => (
    <Card key={post.id} className="mb-4" style={{ width: "500px", margin: "0 auto" }}>
      <Card.Img variant="top" src={post.file_url} style={{ maxHeight: "500px",maxWidth:"500px", objectFit: "cover" }} />l̥
      <Card.Body>
        <Card.Text><b>User:</b> {post.username}</Card.Text>
        <LikeButton initialLikes={0} />
        <CommentSection
          postId={post.id}
          username={post.username}
          imageUrl={post.file_url}
        />
      </Card.Body>
    </Card>
  ))}
</Container>
  );
}
