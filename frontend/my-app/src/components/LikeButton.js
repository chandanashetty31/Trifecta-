
import { useState } from "react";
import { Button } from "react-bootstrap";

export default function LikeButton({ initialLikes = 0 }) {
  const [likes, setLikes] = useState(initialLikes);
  const [liked, setLiked] = useState(false);

  const toggleLike = () => {
    setLiked(!liked);
    setLikes(liked ? likes - 1 : likes + 1);
  };

  return (
    <Button
      variant={liked ? "danger" : "outline-danger"}
      onClick={toggleLike}
    >
      ❤️ {likes}
    </Button>
  );
}
