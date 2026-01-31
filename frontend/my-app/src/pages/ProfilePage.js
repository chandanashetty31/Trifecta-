import { useState, useEffect } from "react";
import { Button, Card, Col, Container, Form, Image, Modal, Row } from "react-bootstrap";

export default function ProfilePage() {
  const [profile, setProfile] = useState({
    name: sessionStorage.getItem("username") || "Priya",
    username: sessionStorage.getItem("username") || "Priya",
    bio: "Your bio here...",
    profilePic:
      "https://media.istockphoto.com/id/1550071750/photo/green-tea-tree-leaves-camellia-sinensis-in-organic-farm-sunlight-fresh-young-tender-bud.jpg?s=1024x1024&w=is&k=20&c=7tIplxfEDBzXiWRahv9ZI0AXK8GF1Pkrbs_KjPLjK8A=",
  });

  const [userPosts, setUserPosts] = useState([]);

  // ---------------------------
  //  FETCH USER'S POSTS
  // ---------------------------
  useEffect(() => {
    const token = sessionStorage.getItem("token");

    fetch("http://localhost:8000/my-posts", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => {
        console.log("MY POSTS:", data);
        if (data.posts) {
          setUserPosts(data.posts);
        }
      })
      .catch((err) => console.error("Error fetching user posts:", err));
  }, []);

  const [showEditModal, setShowEditModal] = useState(false);
  const handleShow = () => setShowEditModal(true);
  const handleClose = () => setShowEditModal(false);

  // Edit inputs
  const [editName, setEditName] = useState(profile.name);
  const [editBio, setEditBio] = useState(profile.bio);
  const [editProfilePic, setEditProfilePic] = useState(profile.profilePic);

  // Image Upload Preview
  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setEditProfilePic(URL.createObjectURL(file));
    }
  };

  // Save Profile Updates
  const handleSaveChanges = () => {
    setProfile({
      ...profile,
      name: editName,
      bio: editBio,
      profilePic: editProfilePic,
    });
    handleClose();
  };

  return (
    <Container className="mt-4">

      {/* Profile Section */}
      <Row className="align-items-center mb-4">
        <Col xs={12} md={4} className="text-center">
          <Image src={profile.profilePic} roundedCircle width={150} height={150} />
        </Col>

        <Col xs={12} md={8}>
          <h2>{profile.name}</h2>
          <p>@{profile.username}</p>
          <p>{profile.bio}</p>

          <div className="d-flex gap-4 mb-3">
            <div><strong>{userPosts.length}</strong> Posts</div>
            <div><strong>0</strong> Followers</div>
            <div><strong>0</strong> Following</div>
          </div>

          <Button variant="primary" onClick={handleShow}>Edit Profile</Button>
        </Col>
      </Row>

      {/* User Posts */}
      <h4 className="mb-3">Your Posts</h4>

      <Row>
  {userPosts.length === 0 ? (
    <p>No posts yet.</p>
  ) : (
    userPosts.map((post) => (
      <Col xs={6} md={4} lg={3} key={post.id} className="mb-3">
        <Card>
          <Card.Img
            variant="top"
            src={post.file_url}
            style={{
              width: "100%",
              height: "250px",
              objectFit: "cover",
              borderRadius: "8px"
            }}
          />
        </Card>
      </Col>
    ))
  )}
</Row>

      {/* Edit Modal */}
      <Modal show={showEditModal} onHide={handleClose} centered>
        <Modal.Header closeButton>
          <Modal.Title>Edit Profile</Modal.Title>
        </Modal.Header>

        <Modal.Body>
          <Form>
            <Form.Group className="mb-3 text-center">
              <Image src={editProfilePic} roundedCircle width={120} height={120} />
              <Form.Control type="file" accept="image/*" className="mt-3" onChange={handleImageUpload} />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Full Name</Form.Label>
              <Form.Control type="text" value={editName} onChange={(e) => setEditName(e.target.value)} />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Bio</Form.Label>
              <Form.Control as="textarea" rows={3} value={editBio} onChange={(e) => setEditBio(e.target.value)} />
            </Form.Group>
          </Form>
        </Modal.Body>

        <Modal.Footer>
          <Button variant="secondary" onClick={handleClose}>Cancel</Button>
          <Button variant="success" onClick={handleSaveChanges}>Save Changes</Button>
        </Modal.Footer>
      </Modal>

    </Container>
  );
}
