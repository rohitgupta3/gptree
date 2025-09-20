import { useState, useEffect } from "react";
import "./App.css";

const apiHost = import.meta.env.VITE_API_HOST;

interface UserData {
  user_id: string;
}

function App() {
  const [userData, setUserData] = useState<UserData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    console.log("run once");
    const fetchUser = async () => {
      try {
        setLoading(true);
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

export default App;
