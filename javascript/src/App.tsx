import { useState, useEffect } from "react";
import { Routes, Route, Link } from "react-router-dom";
import "./App.css";
import Signup from "./components/Signup";
import Login from "./components/Login";
import { auth } from "./config/firebase";
import { onAuthStateChanged, signOut } from "firebase/auth";

// API host from .env
const apiHost = import.meta.env.VITE_API_HOST;

interface FirebaseUser {
  uid: string;
  email?: string;
  name?: string;
  picture?: string;
  email_verified?: boolean;
  claims: Record<string, any>;
}

function Home({ userData }: { userData: FirebaseUser | null }) {
  const [count, setCount] = useState(0);

  return (
    <>
      <h1>GPTree</h1>

      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count tester ({count})
        </button>

        {userData && (
          <div className="user-info">
            <h2>User Info</h2>
            <p>
              <strong>UID:</strong> {userData.uid}
            </p>
            {userData.email && (
              <p>
                <strong>Email:</strong> {userData.email}
              </p>
            )}
            {userData.name && (
              <p>
                <strong>Name:</strong> {userData.name}
              </p>
            )}
            {userData.picture && (
              <p>
                <strong>Picture:</strong>{" "}
                <img src={userData.picture} alt="User" width="50" />
              </p>
            )}
          </div>
        )}
      </div>
    </>
  );
}

function App() {
  const [userData, setUserData] = useState<FirebaseUser | null>(null);
  const [loadingUser, setLoadingUser] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Firebase auth listener
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (!user) {
        console.log("No user logged in");
        setUserData(null);
        setLoadingUser(false);
        return;
      }

      try {
        const token = await user.getIdToken();
        const response = await fetch(`${apiHost}/api/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data: FirebaseUser = await response.json();
        setUserData(data);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch user data:", err);
        setUserData(null);
        setError("Failed to fetch user data");
      } finally {
        setLoadingUser(false);
      }
    });

    return () => unsubscribe();
  }, []);

  const handleLogout = async () => {
    try {
      await signOut(auth);
      console.log("Signed out successfully");
      setUserData(null);
    } catch (err) {
      console.error("Logout error:", err);
    }
  };

  return (
    <div style={{ position: "relative", minHeight: "100vh" }}>
      {/* Auth buttons */}
      <div
        style={{
          position: "absolute",
          top: "20px",
          right: "20px",
          zIndex: 1000,
          display: "flex",
          gap: "10px",
        }}
      >
        {userData ? (
          <button
            onClick={handleLogout}
            style={{
              backgroundColor: "#dc3545",
              color: "white",
              padding: "8px 16px",
              borderRadius: "4px",
              border: "none",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            Logout
          </button>
        ) : (
          <>
            <Link
              to="/login"
              style={{
                backgroundColor: "#6c757d",
                color: "white",
                padding: "8px 16px",
                textDecoration: "none",
                borderRadius: "4px",
                fontSize: "14px",
              }}
            >
              Login
            </Link>
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
          </>
        )}
      </div>

      {/* Main content */}
      <div style={{ paddingTop: "60px" }}>
        {loadingUser && <p style={{ padding: "20px" }}>Loading user...</p>}
        {error && (
          <p style={{ padding: "20px", color: "red" }}>Error: {error}</p>
        )}

        {!loadingUser && (
          <Routes>
            <Route path="/" element={<Home userData={userData} />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
          </Routes>
        )}
      </div>
    </div>
  );
}

export default App;
