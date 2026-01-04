"use client";

import { useEffect, useState } from "react";
import axios from "axios";

export default function Dashboard() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
  }

  useEffect(() => {
    axios
      .get(`${process.env.NEXT_PUBLIC_API_URL}/me/`, { withCredentials: true })
      .then((res) => setUser(res.data))
      .catch((err) => setError("Failed to load user data"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;

  async function handleUpgrade(plan) {
    const csrfToken = getCookie("csrftoken");

    try {
      const res = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/subscribe/`,
        { plan },
        {
          withCredentials: true,
          headers: {
            "X-CSRFToken": csrfToken,
          },
        }
      );

      if (res.data.checkout_url) {
        window.location.href = res.data.checkout_url;
      } else {
        setError("No checkout URL returned from server.");
      }
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail || "An error occurred during upgrade."
      );
    }
  }

  return (
    <div style={{ padding: "2rem" }}>
      <h1>Dashboard</h1>
      <p>
        <strong>Current Plan:</strong> {user.current_plan || "None"}
      </p>
      <p>
        <strong>Lifetime Spend:</strong> ${(user.total_amount_paid / 100).toFixed(2)}
      </p>
      <div style={{ marginTop: "1rem" }}>
        <button onClick={() => handleUpgrade("basic")} style={{ marginRight: "1rem" }}>
          Upgrade to Basic
        </button>
        <button onClick={() => handleUpgrade("pro")}>Upgrade to Pro</button>
      </div>
      {error && (
        <p style={{ color: "red", marginTop: "1rem" }}>
          {error}
        </p>
      )}
    </div>
  );
}
