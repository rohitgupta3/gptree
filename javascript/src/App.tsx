import { useState, useEffect } from "react";
import { Routes, Route, Link } from "react-router-dom";
import "./App.css";
import Signup from "./components/Signup";
import Login from "./components/Login";
import { auth } from "./config/firebase";
import { onAuthStateChanged, signOut } from "firebase/auth";

const apiHost = import.meta.env.VITE_API_HOST;

interface FirebaseUser {
  uid: string;
  email?: string;
  name?: string;
  picture?: string;
  email_verified?: boolean;
  claims: Record<string, any>;
}

const handleLogout = async () => {
  try {
    await signOut(auth);
    console.log("User signed out");
  } catch (err) {
    console.error("Logout error:", err);
  }
};

function Home() {
  const [userData, setUserData] = useState<FirebaseUser | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Set up Firebase auth state listener
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (!user) {
        console.log("User not logged in");
        setUserData(null); // clear any existing user
        return;
      }

      try {
        setLoading(true);
        const token = await user.getIdToken();

        const response = await fetch(`${apiHost}/api/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        console.log(response);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data: FirebaseUser = await response.json();
        setUserData(data);
      } catch (error) {
        console.error("Backend error:", error);
        setError(
          `Failure: ${error instanceof Error ? error.message : "Unknown error"}`
        );
      } finally {
        setLoading(false);
      }
    });

    return () => unsubscribe();
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
  // debugger;
  return (
    <div style={{ position: "relative", minHeight: "100vh" }}>
      {/* Auth buttons in top right */}
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
        {auth.currentUser ? (
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

      {/* Routes */}
      <div style={{ paddingTop: "60px" }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;
