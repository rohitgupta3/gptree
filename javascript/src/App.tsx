import { useState, useEffect } from "react";
import "./App.css";

const apiHost = import.meta.env.VITE_API_HOST;

interface UserData {
  userId: string;
}

function App() {
  const [userData, setUserData] = useState<UserData | null>(null);
  const [count, setCount] = useState(0);
  const [status, setStatus] = useState<string>("Not hydrated");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    console.log("run once");
  }, []);

  const fetchUser = async () => {
    setLoading(true);
    setStatus("Fetching...");

    try {
      // Use relative URL - will work both locally and on Heroku
      // const response = await fetch(`${apiHost}/api/test`);
      const response = await fetch(`${apiHost}/api/user/random`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: UserData = await response.json();
      setUserData(data);
    } catch (error) {
      console.error("DB failed:", error);
      setStatus(
        `Failure: ${error instanceof Error ? error.message : "Unknown error"}`
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <h1>GPTree</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count tester ({count})
        </button>

        {userData && (
          <div className="user-info">
            <h2>User Information</h2>
            <p>
              <strong>User ID:</strong> {userData.userId}
            </p>
          </div>
        )}

        <div style={{ marginTop: "20px" }}>
          <button
            onClick={fetchUser}
            disabled={loading}
            style={{
              padding: "10px 20px",
              marginBottom: "10px",
              backgroundColor: loading ? "#ccc" : "#007bff",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Testing..." : "Test Backend Connection"}
          </button>

          <div
            style={{
              padding: "10px",
              marginTop: "10px",
              backgroundColor: "#f8f9fa",
              border: "1px solid #dee2e6",
              borderRadius: "4px",
              fontFamily: "monospace",
            }}
          >
            Status: {status}
          </div>
        </div>
      </div>
    </>
  );
}

export default App;
