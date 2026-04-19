"use client";

import { useState } from "react";
import styles from "./page.module.css";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setMessage("");

    const safeUsername = username
      .trim()
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: safeUsername, password }),
      });

      const data = await response.json();
      setMessage(data.message ?? "Unexpected response.");
    } catch {
      setMessage(
        "Unable to reach auth service. Make sure Flask backend is running."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className={styles.page}>
      <div className={`${styles.space} ${styles.stars1}`} />
      <div className={`${styles.space} ${styles.stars2}`} />
      <div className={`${styles.space} ${styles.stars3}`} />
      <div className={`${styles.space} ${styles.stars4}`} />
      <div className={`${styles.space} ${styles.stars5}`} />

      <h1 className={styles.logo}>Ctrl+Eat</h1>
      <div className={styles.backdrop} />

      <section className={styles.loginSquare}>
        <form className={styles.loginInputs} onSubmit={handleSubmit}>
          <label htmlFor="username">Username</label>
          <input
            id="username"
            className={styles.textBox}
            type="text"
            placeholder="Please Enter Username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            required
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            className={styles.textBox}
            type="password"
            placeholder="Please Enter Password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />

          <button id="login_button" className={styles.loginButton} disabled={loading}>
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>

        {message ? <p className={styles.message}>{message}</p> : null}
      </section>
    </main>
  );
}
