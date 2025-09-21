import { useState, useEffect } from "react";
import { Routes, Route, Link, useNavigate, useParams } from "react-router-dom";
import "./App.css";
import Signup from "./components/Signup";
import Login from "./components/Login";
import { auth } from "./config/firebase";
import { onAuthStateChanged, signOut } from "firebase/auth";

// API host from .env
const apiHost = import.meta.env.VITE_API_HOST;

// Perhaps synchronize this a bit better with the SQLModel User model
interface FirebaseUser {
  uid: string;
  email?: string;
  name?: string;
  picture?: string;
  email_verified?: boolean;
  claims: Record<string, any>;
}

interface ConversationListItem {
  root_turn_id: string;
  identifying_turn_id: string;
  title: string;
  created_at: string; // ISO date string
}

interface Turn {
  id: string;
  parent_id: string | null;
  primary_child_id: string | null;
  branched_child_ids: string[];
  human_text: string | null;
  bot_text: string | null;
  created_at: string;
}

function Home({ userData }: { userData: FirebaseUser | null }) {
  const [count, setCount] = useState(0);
  const [conversationText, setConversationText] = useState("");
  const [isCreatingConversation, setIsCreatingConversation] = useState(false);
  const navigate = useNavigate();

  const handleCreateConversation = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!conversationText.trim() || !userData) {
      return;
    }

    setIsCreatingConversation(true);

    try {
      const user = auth.currentUser;
      if (!user) {
        throw new Error("No authenticated user");
      }

      const token = await user.getIdToken();

      const response = await fetch(`${apiHost}/api/conversation/create`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          text: conversationText,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to create conversation");
      }

      const data = await response.json();

      // Redirect to chat/{conversation_UUID}/{turn_UUID}
      // Since this is the first turn, conversation_UUID and turn_UUID are the same
      navigate(`/chat/${data.turn_id}`);
    } catch (error) {
      console.error("Error creating conversation:", error);
      alert(
        `Failed to create conversation: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      );
    } finally {
      setIsCreatingConversation(false);
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
          <>
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

            <div className="new-conversation">
              <h3>Start a New Conversation</h3>
              <form onSubmit={handleCreateConversation}>
                <textarea
                  value={conversationText}
                  onChange={(e) => setConversationText(e.target.value)}
                  placeholder="What would you like to talk about?"
                  rows={4}
                  cols={50}
                  style={{
                    width: "100%",
                    maxWidth: "500px",
                    padding: "10px",
                    margin: "10px 0",
                    borderRadius: "4px",
                    border: "1px solid #ccc",
                    fontSize: "14px",
                    fontFamily: "inherit",
                  }}
                  disabled={isCreatingConversation}
                />
                <br />
                <button
                  type="submit"
                  disabled={!conversationText.trim() || isCreatingConversation}
                  style={{
                    backgroundColor:
                      isCreatingConversation || !conversationText.trim()
                        ? "#6c757d"
                        : "#007bff",
                    color: "white",
                    padding: "10px 20px",
                    border: "none",
                    borderRadius: "4px",
                    cursor:
                      isCreatingConversation || !conversationText.trim()
                        ? "not-allowed"
                        : "pointer",
                    fontSize: "16px",
                  }}
                >
                  {isCreatingConversation
                    ? "Creating..."
                    : "Start Conversation"}
                </button>
              </form>
            </div>
          </>
        )}
      </div>
    </>
  );
}

function Chat() {
  const { identifyingTurnId } = useParams();
  const navigate = useNavigate();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [replyText, setReplyText] = useState("");
  const [isReplying, setIsReplying] = useState(false);

  const handleReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyText.trim() || turns.length === 0) return;

    try {
      const user = auth.currentUser;
      if (!user) return;

      setIsReplying(true);
      const token = await user.getIdToken();
      const res = await fetch(`${apiHost}/api/conversation/reply`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          parent_turn_id: turns[turns.length - 1].id,
          text: replyText,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const newTurn: Turn = await res.json();
      setTurns((prev) => [...prev, newTurn]);
      setReplyText("");
    } catch (err) {
      console.error("Failed to reply:", err);
      alert("Failed to send reply.");
    } finally {
      setIsReplying(false);
    }
  };

  useEffect(() => {
    const fetchConversation = async () => {
      try {
        const user = auth.currentUser;
        if (!user || !identifyingTurnId) return;

        const token = await user.getIdToken();
        const res = await fetch(
          `${apiHost}/api/conversation/${identifyingTurnId}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }

        const data: Turn[] = await res.json();
        setTurns(data);
        setError(null);
      } catch (err) {
        console.error("Error fetching conversation:", err);
        setError("Failed to load conversation.");
      } finally {
        setLoading(false);
      }
    };

    fetchConversation();
  }, [identifyingTurnId]);

  return (
    <div style={{ padding: "20px" }}>
      <h1>Chat</h1>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      {!loading && !error && (
        <>
          {turns.map((turn) => (
            <div
              key={turn.id}
              style={{
                border: "1px solid #ccc",
                padding: "10px",
                marginBottom: "10px",
                borderRadius: "4px",
              }}
            >
              {turn.human_text && (
                <p>
                  <strong>You:</strong> {turn.human_text}
                </p>
              )}
              {turn.bot_text && (
                <p>
                  <strong>Bot:</strong> {turn.bot_text}
                </p>
              )}
            </div>
          ))}
          <form onSubmit={handleReply} style={{ marginTop: "20px" }}>
            <textarea
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              placeholder="Type your reply..."
              rows={3}
              cols={50}
              style={{
                width: "100%",
                maxWidth: "600px",
                padding: "10px",
                borderRadius: "4px",
                border: "1px solid #ccc",
                fontSize: "14px",
                fontFamily: "inherit",
              }}
              disabled={isReplying}
            />
            <br />
            <button
              type="submit"
              disabled={!replyText.trim() || isReplying}
              style={{
                backgroundColor:
                  isReplying || !replyText.trim() ? "#6c757d" : "#28a745",
                color: "white",
                padding: "10px 20px",
                border: "none",
                borderRadius: "4px",
                cursor:
                  isReplying || !replyText.trim() ? "not-allowed" : "pointer",
                fontSize: "16px",
              }}
            >
              {isReplying ? "Replying..." : "Send Reply"}
            </button>
          </form>
        </>
      )}

      <button
        onClick={() => navigate("/")}
        style={{
          backgroundColor: "#6c757d",
          color: "white",
          padding: "10px 20px",
          border: "none",
          borderRadius: "4px",
          cursor: "pointer",
        }}
      >
        Back to Home
      </button>
    </div>
  );
}

function App() {
  const [userData, setUserData] = useState<FirebaseUser | null>(null);
  const [loadingUser, setLoadingUser] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [conversations, setConversations] = useState<ConversationListItem[]>(
    []
  );
  const [conversationFetchError, setConversationFetchError] = useState<
    string | null
  >(null);

  // Firebase auth listener
  // TODO: confirm this works if you manually clear cookies
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

  useEffect(() => {
    const fetchConversations = async () => {
      const user = auth.currentUser;
      if (!user) return;

      try {
        const token = await user.getIdToken();

        const response = await fetch(`${apiHost}/api/conversations`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data: ConversationListItem[] = await response.json();

        // Sort client-side by created_at DESC
        const sorted = data.sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );

        setConversations(sorted);
        setConversationFetchError(null);
      } catch (err) {
        console.error("Failed to fetch conversations:", err);
        setConversationFetchError("Failed to load conversations.");
      }
    };

    if (userData) {
      fetchConversations();
    }
  }, [userData]);

  const handleLogout = async () => {
    try {
      await signOut(auth);
      console.log("Signed out successfully");
      setUserData(null);
    } catch (err) {
      console.error("Logout error:", err);
    }
  };

  const handleResetDatabase = async () => {
    try {
      const res = await fetch(`${apiHost}/api/reset-db`, {
        method: "POST",
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to reset DB");
      }

      const data = await res.json();
      alert(data.message || "Database reset successfully!");
    } catch (err: any) {
      console.error("DB Reset Error:", err);
      alert("Database reset failed: " + err.message);
    }
  };

  const handleResetTestDatabase = async () => {
    try {
      const res = await fetch(`${apiHost}/api/reset-test-db`, {
        method: "POST",
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to reset test DB");
      }

      const data = await res.json();
      alert(data.message || "Test database reset successfully!");
    } catch (err: any) {
      console.error("Test DB Reset Error:", err);
      alert("Test database reset failed: " + err.message);
    }
  };

  const handleSeedUsers = async () => {
    try {
      const res = await fetch(`${apiHost}/api/seed-users`, {
        method: "POST",
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to seed users");
      }

      const data = await res.json();
      alert(data.message || "Users seeded successfully!");
    } catch (err: any) {
      console.error("Seed Users Error:", err);
      alert("Seed users failed: " + err.message);
    }
  };

  return (
    <div style={{ position: "relative", minHeight: "100vh" }}>
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "20px",
          zIndex: 1000,
        }}
      >
        {/* Admin buttons on the left */}
        <div style={{ display: "flex", gap: "10px" }}>
          <button
            onClick={handleResetDatabase}
            style={{
              backgroundColor: "#ffc107",
              color: "black",
              padding: "8px 16px",
              borderRadius: "4px",
              border: "none",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            Reset DB
          </button>
          <button
            onClick={handleResetTestDatabase}
            style={{
              backgroundColor: "#ffc107",
              color: "black",
              padding: "8px 16px",
              borderRadius: "4px",
              border: "none",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            Reset test DB
          </button>
          <button
            onClick={handleSeedUsers}
            style={{
              backgroundColor: "#28a745",
              color: "white",
              padding: "8px 16px",
              borderRadius: "4px",
              border: "none",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            Seed Users
          </button>
        </div>

        {/* Auth buttons on the right */}
        <div style={{ display: "flex", gap: "10px" }}>
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
      </div>

      {conversations.length > 0 && (
        <div
          style={{
            position: "fixed",
            top: "60px",
            left: 0,
            width: "250px",
            height: "calc(100% - 60px)",
            backgroundColor: "#f1f1f1",
            padding: "20px",
            overflowY: "auto",
            borderRight: "1px solid #ccc",
          }}
        >
          <h3>Conversations</h3>
          {conversationFetchError ? (
            <p style={{ color: "red" }}>{conversationFetchError}</p>
          ) : conversations.length === 0 ? (
            <p style={{ fontStyle: "italic", color: "#666" }}>
              No conversations yet.
            </p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0 }}>
              {conversations.map((conv) => (
                <li
                  key={conv.identifying_turn_id}
                  style={{ marginBottom: "10px" }}
                >
                  <Link to={`/chat/${conv.identifying_turn_id}`}>
                    {conv.title || "Untitled"}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Main content */}
      <div
        style={{
          paddingTop: "60px",
          marginLeft: conversations.length > 0 ? "250px" : "0",
        }}
      >
        {loadingUser && <p style={{ padding: "20px" }}>Loading user...</p>}
        {error && (
          <p style={{ padding: "20px", color: "red" }}>Error: {error}</p>
        )}

        {!loadingUser && (
          <Routes>
            <Route path="/" element={<Home userData={userData} />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/chat/:identifyingTurnId" element={<Chat />} />
          </Routes>
        )}
      </div>
    </div>
  );
}

export default App;
