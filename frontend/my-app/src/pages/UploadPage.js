import { Container } from "react-bootstrap";
import ImageUploadForm from "../components/ImageUploadForm";
import { useRef } from "react";

export default function UploadPage() {
  const formRef = useRef();

  const handleUpload = async (data) => {
    const formData = new FormData();
    formData.append("image", data.image);
    formData.append("message", data.message);

    const token = sessionStorage.getItem("token");

    try {
      const response = await fetch("http://localhost:8000/upload", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.status === 401) {
        sessionStorage.removeItem("token");
        window.location.href = "/login";
        return;
      }

      let text = null;
      try {
        text = await response.text();
      } catch (err) {
        console.error("Failed to read response text:", err);
        alert("Upload failed: could not read server response.");
        return;
      }

      let result = null;
      try {
        result = text ? JSON.parse(text) : null;
      } catch (parseErr) {
        result = null;
      }

      console.log("Upload response:", {
        status: response.status,
        ok: response.ok,
        result,
        text,
      });

      // Handle duplicate image FIRST (HTTP 409 Conflict - perceptual hash match)
      if (response.status === 409 && result && result.status === "duplicate") {
        alert("⛔ Similar image found!\n\nThis image cannot be uploaded. Please upload a different image.");
        return;
      }

      if (response.ok && result) {
        if (result.status === "ok") {
          alert(result.message || "Upload successful");
          if (formRef.current) {
            formRef.current.resetForm();
          }
          return;
        }

        if (result.status === "hidden data detected") {
          alert("Hidden message detected: " + result.hidden_message);
          return;
        }

        if (result.status === "rejected") {
          let message = "Upload rejected: " + result.message;
          if (result.similar_images && result.similar_images.length > 0) {
            const match = result.similar_images[0];
            message += `\n\nMatched with image uploaded by: ${match.username}\nHamming distance: ${match.distance}`;
          }
          alert(message);
          return;
        }

        alert(result.message || JSON.stringify(result));
        return;
      }

      if (result && result.message) {
        alert("Upload failed: " + result.message);
        return;
      }

      if (text) {
        const preview = text.slice(0, 1200);
        alert("Upload failed (server response preview):\n\n" + preview);
        console.error("Full server response:", text);
        return;
      }

      alert(`Upload failed (HTTP ${response.status}).`);
    } catch (err) {
      console.error("Network/upload error:", err);
      alert("Error uploading: " + (err.message || err));
    }
  };

  return (
    <Container className="mt-4">
      <h2>Upload a Secure Post</h2>
      <ImageUploadForm ref={formRef} onUpload={handleUpload} />
    </Container>
  );
}
