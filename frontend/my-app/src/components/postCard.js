
import { Button, Card } from "react-bootstrap";

 function PostCard({ post, onRequestShare }) {
  return (
    <Card className="mb-3">
      <Card.Img variant="top" src={post.imageUrl} />
      <Card.Body>
        <Card.Title>{post.title}</Card.Title>
        <Card.Text>By {post.owner}</Card.Text>
        <Button variant="primary" onClick={() => onRequestShare(post.id)}>
          Request Share
        </Button>
      </Card.Body>
    </Card>
  );
}
export default PostCard;
