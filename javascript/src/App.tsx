import { useState, useEffect } from "react";
import { Routes, Route, Link } from "react-router-dom";
import "./App.css";
import Signup from "./components/Signup";

const apiHost = import.meta.env.VITE_API_HOST;

interface UserData {
  user_id: string;
}

function Home() {
  const [userData, setUserData] = useState<UserData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${apiHost}/api/user/random`);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data: UserData = await response.json();
        setUserData(data);
      } catch (error) {
        console.error("DB failed:", error);
        setError(
          `Failure: ${error instanceof Error ? error.message : "Unknown error"}`
        );
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, []);

  return (
    <>
      <h1>GPTree</h1>

      {loading && <p>Loading...</p>}

      {error && <p className="error">Error: {error}</p>}

      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count tester ({count})
        </button>

        {userData && (
          <div className="user-info">
            <h2>User Information</h2>
            <p>
              <strong>User ID:</strong> {userData.user_id}
            </p>
          </div>
        )}
      </div>
    </>
  );
}

function App() {
  return (
    <div style={{ position: "relative", minHeight: "100vh" }}>
      {/* Sign up button in top right */}
      <div
        style={{
          position: "absolute",
          top: "20px",
          right: "20px",
          zIndex: 1000,
        }}
      >
        <Link
          to="/signup"
          style={{
            backgroundColor: "#007bff",
            color: "white",
            padding: "8px 16px",
            textDecoration: "none",
            borderRadius: "4px",
            fontSize: "14px",
          }}
        >
          Sign Up
        </Link>
      </div>

      {/* Routes */}
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/signup" element={<Signup />} />
      </Routes>
    </div>
  );
}

export default App;
