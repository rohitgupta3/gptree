import { useState, useEffect } from "react";
import {
  Routes,
  Route,
  Link,
  useNavigate,
  useParams,
  useLocation,
} from "react-router-dom";
import "./App.css";
import Signup from "./components/Signup";
import Login from "./components/Login";
import { auth } from "./config/firebase";
import { onAuthStateChanged, signOut } from "firebase/auth";
import ReactMarkdown from "react-markdown";

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

function Home({
  userData,
  onNewConversation,
}: {
  userData: FirebaseUser | null;
  onNewConversation?: () => void;
}) {
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
      if (onNewConversation) {
        onNewConversation(); // ⬅ Trigger refresh of sidebar
      }
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
        {userData && (
          <>
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
                    maxWidth: "700px", // Increased from 500px
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
                    backgroundColor: "#6c757d",
                    color: "white",
                    padding: "10px 20px",
                    border: "none",
                    borderRadius: "4px",
                    cursor:
                      isCreatingConversation || !conversationText.trim()
                        ? "not-allowed"
                        : "pointer",
                    fontSize: "16px",
                    opacity:
                      isCreatingConversation || !conversationText.trim()
                        ? 0.6
                        : 1,
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

function Chat({ onNewConversation }: { onNewConversation?: () => void }) {
  const { identifyingTurnId } = useParams();
  const navigate = useNavigate();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [replyText, setReplyText] = useState("");
  const [isReplying, setIsReplying] = useState(false);
  const [replyMode, setReplyMode] = useState<"reply" | "branch">("reply");

  const handleReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyText.trim() || turns.length === 0) return;

    try {
      const user = auth.currentUser;
      if (!user) return;

      setIsReplying(true);
      const token = await user.getIdToken();

      const endpoint =
        replyMode === "branch"
          ? `${apiHost}/api/conversation/branch-reply`
          : `${apiHost}/api/conversation/reply`;

      const res = await fetch(endpoint, {
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
      if (replyMode === "branch") {
        navigate(`/chat/${newTurn.id}`);
        if (onNewConversation) {
          onNewConversation();
        }
      } else {
        setTurns((prev) => [...prev, newTurn]);
      }
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
                <div>
                  <strong>Bot:</strong>
                  <div
                    style={{
                      backgroundColor: "#f8f9fa",
                      padding: "10px",
                      borderRadius: "4px",
                      marginTop: "5px",
                      whiteSpace: "pre-wrap",
                    }}
                  >
                    <ReactMarkdown>{turn.bot_text}</ReactMarkdown>
                  </div>
                </div>
              )}
            </div>
          ))}
          <form onSubmit={handleReply} style={{ marginTop: "20px" }}>
            <div
              style={{ display: "flex", gap: "15px", alignItems: "flex-start" }}
            >
              <textarea
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                placeholder="Type your reply..."
                rows={3}
                cols={50}
                style={{
                  width: "100%",
                  maxWidth: "800px", // Increased from 600px
                  padding: "10px",
                  borderRadius: "4px",
                  border: "1px solid #ccc",
                  fontSize: "14px",
                  fontFamily: "inherit",
                  flex: "1",
                }}
                disabled={isReplying}
              />
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "10px",
                  minWidth: "120px",
                }}
              >
                <button
                  type="submit"
                  disabled={!replyText.trim() || isReplying}
                  style={{
                    backgroundColor: "#6c757d",
                    color: "white",
                    padding: "10px 20px",
                    border: "none",
                    borderRadius: "4px",
                    cursor:
                      isReplying || !replyText.trim()
                        ? "not-allowed"
                        : "pointer",
                    fontSize: "16px",
                    opacity: isReplying || !replyText.trim() ? 0.6 : 1,
                  }}
                  onClick={() => setReplyMode("reply")}
                >
                  {isReplying && replyMode === "reply"
                    ? "Replying..."
                    : "Send Reply"}
                </button>

                <button
                  type="submit"
                  disabled={!replyText.trim() || isReplying}
                  style={{
                    backgroundColor: "#6c757d",
                    color: "white",
                    padding: "10px 20px",
                    border: "none",
                    borderRadius: "4px",
                    cursor:
                      isReplying || !replyText.trim()
                        ? "not-allowed"
                        : "pointer",
                    fontSize: "16px",
                    opacity: isReplying || !replyText.trim() ? 0.6 : 1,
                  }}
                  onClick={() => setReplyMode("branch")}
                >
                  {isReplying && replyMode === "branch"
                    ? "Replying..."
                    : "Branch Reply"}
                </button>
              </div>
            </div>
          </form>
        </>
      )}
    </div>
  );
}

function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const currentTurnId = location.pathname.startsWith("/chat/")
    ? location.pathname.split("/chat/")[1]
    : null;

  const [userData, setUserData] = useState<FirebaseUser | null>(null);
  const [loadingUser, setLoadingUser] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [conversations, setConversations] = useState<ConversationListItem[]>(
    []
  );
  const [conversationFetchError, setConversationFetchError] = useState<
    string | null
  >(null);

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

  // Firebase auth listener
  // TODO: confirm this works if you manually clear cookies
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (!user) {
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
    if (userData) {
      fetchConversations();
    }
  }, [userData]);

  const handleLogout = async () => {
    try {
      await signOut(auth);
      console.log("Signed out successfully");
      setUserData(null);
      setConversations([]); // clear sidebar
      navigate("/"); // ⬅️ Redirect to Home
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

  const buttonStyle = {
    backgroundColor: "#6c757d",
    color: "white",
    padding: "8px 16px",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
    textDecoration: "none" as const,
    display: "inline-block" as const,
  };

  return (
    <div style={{ position: "relative", minHeight: "100vh" }}>
      {/* Top Header */}
      <div
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          height: "60px",
          backgroundColor: "#f8f9fa",
          borderBottom: "1px solid #dee2e6",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 20px",
          zIndex: 1000,
        }}
      >
        {/* Left: Home button */}
        <Link to="/" style={buttonStyle}>
          Home
        </Link>

        {/* Center: Admin buttons (positioned to the right of sidebar) */}
        <div
          style={{
            position: "absolute",
            left: "270px", // 250px sidebar width + 20px margin
            display: "flex",
            gap: "10px",
          }}
        >
          <button onClick={handleResetDatabase} style={buttonStyle}>
            Reset DB
          </button>
          <button onClick={handleResetTestDatabase} style={buttonStyle}>
            Reset test DB
          </button>
          <button onClick={handleSeedUsers} style={buttonStyle}>
            Seed Users
          </button>
        </div>

        {/* Right: Auth buttons */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {userData ? (
            <>
              {userData.email && (
                <span
                  style={{
                    fontSize: "14px",
                    color: "#6c757d",
                    fontWeight: "500",
                  }}
                >
                  {userData.email}
                </span>
              )}
              <button onClick={handleLogout} style={buttonStyle}>
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" style={buttonStyle}>
                Login
              </Link>
              <Link to="/signup" style={buttonStyle}>
                Sign Up
              </Link>
            </>
          )}
        </div>
      </div>

      {/* Left Sidebar */}
      <div
        style={{
          position: "fixed",
          top: "60px",
          left: 0,
          width: "250px",
          height: "calc(100% - 60px)",
          backgroundColor: "#f8f9fa",
          padding: "20px",
          overflowY: "auto",
          borderRight: "1px solid #dee2e6",
        }}
      >
        {/* New Chat button */}
        <Link
          to="/"
          style={{
            ...buttonStyle,
            display: "block",
            textAlign: "center" as const,
            marginBottom: "20px",
            width: "100%",
            boxSizing: "border-box" as const,
          }}
        >
          New Chat
        </Link>

        <h3 style={{ margin: "0 0 15px 0", color: "#495057" }}>Chats</h3>

        {!userData ? (
          <p
            style={{ fontStyle: "italic", color: "#6c757d", fontSize: "14px" }}
          >
            Please log in to see your chats.
          </p>
        ) : conversationFetchError ? (
          <p style={{ color: "#dc3545", fontSize: "14px" }}>
            {conversationFetchError}
          </p>
        ) : conversations.length === 0 ? (
          <p
            style={{ fontStyle: "italic", color: "#6c757d", fontSize: "14px" }}
          >
            No conversations yet.
          </p>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {conversations.map((conv) => (
              <li
                key={conv.identifying_turn_id}
                style={{ marginBottom: "8px" }}
              >
                <Link
                  to={`/chat/${conv.identifying_turn_id}`}
                  style={{
                    display: "block",
                    padding: "10px 12px",
                    borderRadius: "4px",
                    textDecoration: "none",
                    color: "#495057",
                    backgroundColor:
                      conv.identifying_turn_id === currentTurnId
                        ? "#e3f2fd"
                        : "transparent",
                    border:
                      conv.identifying_turn_id === currentTurnId
                        ? "1px solid #90caf9"
                        : "1px solid transparent",
                    fontSize: "14px",
                    transition: "all 0.2s ease",
                  }}
                  onMouseEnter={(e) => {
                    if (conv.identifying_turn_id !== currentTurnId) {
                      e.currentTarget.style.backgroundColor = "#f1f3f4";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (conv.identifying_turn_id !== currentTurnId) {
                      e.currentTarget.style.backgroundColor = "transparent";
                    }
                  }}
                >
                  {conv.title || "Untitled"}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Main content */}
      <div
        style={{
          paddingTop: "60px",
          marginLeft: "250px",
        }}
      >
        {loadingUser && <p style={{ padding: "20px" }}>Loading user...</p>}
        {error && (
          <p style={{ padding: "20px", color: "red" }}>Error: {error}</p>
        )}

        {!loadingUser && (
          <Routes>
            <Route
              path="/"
              element={
                <Home
                  userData={userData}
                  onNewConversation={fetchConversations}
                />
              }
            />

            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route
              path="/chat/:identifyingTurnId"
              element={<Chat onNewConversation={fetchConversations} />}
            />
          </Routes>
        )}
      </div>
    </div>
  );
}

export default App;
