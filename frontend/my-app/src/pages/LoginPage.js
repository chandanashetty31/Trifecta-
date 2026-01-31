
import { useState } from "react";
import "./style.css";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();

    const body = JSON.stringify({ username, password });

    try {
      const res = await fetch("http://localhost:8000/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body
      });

      const data = await res.json();

      if (res.ok) {
        // store token and username for later use (comments, feed, etc.)
        // NOTE: the backend login route must return { access_token, username }
        sessionStorage.setItem("token", data.access_token);
        if (data.username) {
          sessionStorage.setItem("username", data.username);
        } else if (data.user && data.user.username) {
          // fallback if your backend returns nested structure
          sessionStorage.setItem("username", data.user.username);
        }

        alert("Login successful!");
        window.location.href = "/feed";
      } else {
        // prefer server-provided message keys
        const errMsg = data.msg || data.message || data.error || "Login failed";
        alert(errMsg);
      }
    } catch (err) {
      console.error(err);
      alert("Something went wrong. Check the console for details.");
    }
  };

  return (
    <div className="auth-page">
      <form onSubmit={handleLogin} className="auth-box">
        <h2>LOGIN</h2>
        <input
          className="auth-input"
          type="text"
          placeholder="Enter your username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <input
          className="auth-input"
          type="password"
          placeholder="Enter your password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button className="auth-submit" type="submit">
          Login
        </button>
        <a className="auth-link" href="/register">
          Sign Up
        </a>
      </form>
    </div>
  );
}
