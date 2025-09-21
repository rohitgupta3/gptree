import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { signInWithEmailAndPassword } from "firebase/auth";
import { auth } from "../config/firebase";

function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    signInWithEmailAndPassword(auth, email, password)
      .then((userCredential) => {
        // Signed in
        const user = userCredential.user;
        console.log("User signed in:", user);

        // Redirect to Home. TODO: should we refer to this by name of component instead?
        navigate("/");
      })
      .catch((error) => {
        const errorCode = error.code;
        const errorMessage = error.message;
        console.error("Error:", errorCode, errorMessage);
        setError(errorMessage);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  return (
    <div style={{ padding: "20px", maxWidth: "400px", margin: "0 auto" }}>
      <h1>Login</h1>

      <form onSubmit={handleSubmit}>
        {error && (
          <div
            style={{
              color: "#dc3545",
              marginBottom: "15px",
              padding: "10px",
              backgroundColor: "#f8d7da",
              border: "1px solid #f5c6cb",
              borderRadius: "4px",
            }}
          >
            {error}
          </div>
        )}

        <div style={{ marginBottom: "15px" }}>
          <label
            htmlFor="email"
            style={{ display: "block", marginBottom: "5px" }}
          >
            Email:
          </label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
            style={{
              width: "100%",
              padding: "8px",
              border: "1px solid #ccc",
              borderRadius: "4px",
              boxSizing: "border-box",
            }}
          />
        </div>

        <div style={{ marginBottom: "15px" }}>
          <label
            htmlFor="password"
            style={{ display: "block", marginBottom: "5px" }}
          >
            Password:
          </label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading}
            style={{
              width: "100%",
              padding: "8px",
              border: "1px solid #ccc",
              borderRadius: "4px",
              boxSizing: "border-box",
            }}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            backgroundColor: "#6c757d",
            color: "white",
            padding: "10px 20px",
            border: "none",
            borderRadius: "4px",
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: "16px",
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? "Signing In..." : "Login"}
        </button>
      </form>

      <div style={{ marginTop: "20px" }}>
        <Link
          to="/"
          style={{
            color: "#6c757d",
            textDecoration: "none",
            fontSize: "14px",
          }}
        >
          ← Back to Home
        </Link>
        {" | "}
        <Link
          to="/signup"
          style={{
            color: "#6c757d",
            textDecoration: "none",
            fontSize: "14px",
          }}
        >
          Need an account? Sign Up
        </Link>
      </div>
    </div>
  );
}

export default Login;
