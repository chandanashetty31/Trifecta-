import { useState, forwardRef, useImperativeHandle } from "react";
import { Button, Form } from "react-bootstrap";

const ImageUploadForm = forwardRef(({ onUpload }, ref) => {
  const [image, setImage] = useState(null);
  const [message, setMessage] = useState("");

  // Expose resetForm() to parent
  useImperativeHandle(ref, () => ({
    resetForm() {
      setImage(null);
      setMessage("");

      // Clear file input manually
      const fileInput = document.getElementById("image-input");
      if (fileInput) fileInput.value = "";
    },
  }));

  // -----------------------------
  // Duplicate Check Here
  // -----------------------------
  const handleImageSelect = async (e) => {
    const file = e.target.files[0];
    setImage(file);

    if (!file) return;

    const formData = new FormData();
    formData.append("image", file);

    const token = sessionStorage.getItem("token");

    try {
      const response = await fetch("http://localhost:8000/check-duplicate", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      const result = await response.json();
      console.log("Duplicate check result:", result);

      if (result.status === "duplicate" || result.is_duplicate) {
        alert(
          `⚠️ Similar image found!\n\nClosest Match Distance: ${result.min_distance}`
        );
      } else {
        console.log("Image is unique.");
      }
    } catch (err) {
      console.error("Duplicate check failed:", err);
      alert("Error checking for duplicate image.");
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onUpload({ image, message });
  };

  return (
    <Form onSubmit={handleSubmit}>
      <Form.Group className="mb-3">
        <Form.Label>Select Image</Form.Label>
        <Form.Control
          id="image-input"
          type="file"
          onChange={handleImageSelect}  // Duplicate check on image selection
          required
        />
      </Form.Group>

      <Form.Group className="mb-3">
        <Form.Label>Secret Message</Form.Label>
        <Form.Control
          as="textarea"
          rows={3}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          maxLength={32}
          required
        />
      </Form.Group>

      <Button variant="success" type="submit">
        Upload
      </Button>
    </Form>
  );
});

export default ImageUploadForm;
