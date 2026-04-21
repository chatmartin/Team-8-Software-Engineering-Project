"use client";

import { useEffect, useMemo, useState } from "react";
import styles from "./page.module.css";

const DIET_OPTIONS = [
  "vegetarian",
  "vegan",
  "glutenFree",
  "ketogenic",
  "pescetarian",
  "halal",
  "kosher",
  "dairy free",
  "egg free",
];

const STARTER_GOALS = ["calories", "protein", "fiber", "sodium", "sugar"];
const KEY_NUTRIENTS = ["calories", "protein", "carbohydrates", "fat"];
const STARTER_CHAT_MESSAGES = [
  {
    role: "assistant",
    text: "Ask me about the current recommendations, ingredients, macros, or what to log next.",
  },
];

function nutrientAmount(value) {
  if (value && typeof value === "object") {
    return value.amount ?? value.total ?? value.avg_per_day ?? 0;
  }
  return value ?? 0;
}

function nutrientUnit(value) {
  if (value && typeof value === "object") {
    return value.unit ?? "";
  }
  return "";
}

function formatNutrient(value) {
  const amount = Number(nutrientAmount(value));
  if (!Number.isFinite(amount)) {
    return "0";
  }
  return amount >= 10 ? Math.round(amount) : amount.toFixed(1);
}

function getMealNutrient(meal, nutrient) {
  return meal?.nutrients?.[nutrient] ?? { amount: 0, unit: nutrient === "calories" ? "kcal" : "g" };
}

async function requestJson(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    ...options,
  });
  const data = await response.json();
  return { response, data };
}

export default function CtrlEatApp() {
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState({ username: "", email: "", password: "" });
  const [status, setStatus] = useState("Checking session...");
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState("dashboard");
  const [adminUsers, setAdminUsers] = useState([]);
  const [adminLoading, setAdminLoading] = useState(false);
  const [settingsTab, setSettingsTab] = useState("profile");
  const [profile, setProfile] = useState({});
  const [profileForm, setProfileForm] = useState({
    gender: "female",
    height: 66,
    weight: 150,
    body_fat: 25,
    age: 25,
    activity: "moderate",
  });
  const [preferences, setPreferences] = useState({ diets: [], sensitivities: [] });
  const [sensitivityForm, setSensitivityForm] = useState({
    allergen: "",
    severity: "low",
  });
  const [goalForm, setGoalForm] = useState({
    nutrient: "protein",
    amount: 100,
    min_max: "min",
  });
  const [goals, setGoals] = useState({ goals: [], recommended: {} });
  const [progress, setProgress] = useState({});
  const [meals, setMeals] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [searchQuery, setSearchQuery] = useState("grain bowl");
  const [searchResults, setSearchResults] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatMessages, setChatMessages] = useState(STARTER_CHAT_MESSAGES);

  const profileComplete = Boolean(profile?.onboarding_complete);
  const isAdmin = user?.role === "admin";
  const pageTitle =
    activeView === "dashboard" ? "Recommendations" : activeView === "admin" ? "Admin" : "Settings";
  const activeRecommendations = searchResults.length ? searchResults : recommendations;
  const progressMetrics = useMemo(
    () =>
      KEY_NUTRIENTS.map((name) => [
        name,
        progress[name] ?? { total: 0, unit: name === "calories" ? "kcal" : "g" },
      ]),
    [progress]
  );

  useEffect(() => {
    async function bootstrap() {
      try {
        const { response, data } = await requestJson("/api/auth/current");
        if (response.ok) {
          setUser(data.data);
          await loadAppData();
        } else {
          setStatus("");
        }
      } catch {
        setStatus("Unable to check session.");
      } finally {
        setLoading(false);
      }
    }
    bootstrap();
  }, []);

  function resetChat() {
    setChatInput("");
    setChatLoading(false);
    setChatMessages(STARTER_CHAT_MESSAGES);
  }

  async function loadAppData() {
    const calls = await Promise.allSettled([
      requestJson("/api/profile"),
      requestJson("/api/preferences"),
      requestJson("/api/goals"),
      requestJson("/api/progress?period=daily"),
      requestJson("/api/meals"),
      requestJson("/api/recommendations"),
    ]);

    const [profileRes, prefRes, goalRes, progressRes, mealRes, recRes] = calls.map((item) =>
      item.status === "fulfilled" ? item.value.data : null
    );

    if (profileRes?.success) {
      setProfile(profileRes.data ?? {});
      if (profileRes.data?.onboarding_complete) {
        setProfileForm((current) => ({ ...current, ...profileRes.data }));
      }
    }
    if (prefRes?.success) {
      setPreferences(prefRes.data ?? { diets: [], sensitivities: [] });
    }
    if (goalRes?.success) {
      setGoals(goalRes.data ?? { goals: [], recommended: {} });
    }
    if (progressRes?.success) {
      setProgress(progressRes.data ?? {});
    }
    if (mealRes?.success) {
      setMeals(mealRes.data ?? []);
    }
    if (recRes?.success) {
      setRecommendations(recRes.data ?? []);
    }
    const failed = calls.find((item) => item.status === "fulfilled" && !item.value.data?.success);
    setStatus(failed ? failed.value.data.message : "");
  }

  async function loadAdminUsers() {
    if (!isAdmin) {
      return;
    }
    setAdminLoading(true);
    try {
      const { data } = await requestJson("/api/admin/users");
      setStatus(data.message);
      setAdminUsers(data.success ? data.data ?? [] : []);
    } catch {
      setStatus("Unable to load admin users.");
      setAdminUsers([]);
    } finally {
      setAdminLoading(false);
    }
  }

  async function updateAdminRole(targetUsername, role) {
    setAdminLoading(true);
    try {
      const { data } = await requestJson("/api/admin/users/role", {
        method: "PUT",
        body: JSON.stringify({ target_username: targetUsername, role }),
      });
      setStatus(data.message);
      if (data.success) {
        await loadAdminUsers();
      }
    } catch {
      setStatus("Unable to update user role.");
    } finally {
      setAdminLoading(false);
    }
  }

  async function resetAdminPassword(targetUsername, password) {
    setAdminLoading(true);
    try {
      const { data } = await requestJson("/api/admin/users/password", {
        method: "PUT",
        body: JSON.stringify({ target_username: targetUsername, password }),
      });
      setStatus(data.message);
      if (data.success) {
        await loadAdminUsers();
      }
      return data.success;
    } catch {
      setStatus("Unable to update user password.");
      return false;
    } finally {
      setAdminLoading(false);
    }
  }

  async function deleteAdminUser(targetUsername) {
    const confirmed = window.confirm(`Delete ${targetUsername} and their app data?`);
    if (!confirmed) {
      return;
    }
    setAdminLoading(true);
    try {
      const { data } = await requestJson("/api/admin/users/delete", {
        method: "DELETE",
        body: JSON.stringify({ target_username: targetUsername }),
      });
      setStatus(data.message);
      if (data.success) {
        await loadAdminUsers();
      }
    } catch {
      setStatus("Unable to delete user.");
    } finally {
      setAdminLoading(false);
    }
  }

  async function submitAuth(event) {
    event.preventDefault();
    setStatus(authMode === "login" ? "Logging in..." : "Creating account...");
    const path = authMode === "login" ? "/api/auth/login" : "/api/auth/create-account";
    const { response, data } = await requestJson(path, {
      method: "POST",
      body: JSON.stringify(authForm),
    });
    setStatus(data.message);
    if (response.ok && data.success) {
      resetChat();
      setUser(data.data);
      await loadAppData();
    }
  }

  async function logout() {
    await requestJson("/api/auth/logout", { method: "POST" });
    setUser(null);
    setStatus("");
    resetChat();
    setActiveView("dashboard");
    setAdminUsers([]);
    setSearchResults([]);
  }

  async function saveProfile(event) {
    event.preventDefault();
    const { data } = await requestJson("/api/profile", {
      method: "POST",
      body: JSON.stringify(profileForm),
    });
    setStatus(data.message);
    await loadAppData();
  }

  async function addDiet(restriction) {
    const { data } = await requestJson("/api/preferences/diet", {
      method: "POST",
      body: JSON.stringify({ restriction }),
    });
    setStatus(data.message);
    await loadAppData();
  }

  async function removeDiet(restriction) {
    const { data } = await requestJson("/api/preferences/diet", {
      method: "DELETE",
      body: JSON.stringify({ restriction }),
    });
    setStatus(data.message);
    await loadAppData();
  }

  async function addSensitivity(event) {
    event.preventDefault();
    const { data } = await requestJson("/api/preferences/sensitivity", {
      method: "POST",
      body: JSON.stringify(sensitivityForm),
    });
    setStatus(data.message);
    setSensitivityForm({ allergen: "", severity: "low" });
    await loadAppData();
  }

  async function removeSensitivity(allergen) {
    const { data } = await requestJson("/api/preferences/sensitivity", {
      method: "DELETE",
      body: JSON.stringify({ allergen }),
    });
    setStatus(data.message);
    await loadAppData();
  }

  async function searchMeals(event) {
    event.preventDefault();
    const { data } = await requestJson("/api/recommendations", {
      method: "POST",
      body: JSON.stringify({ query: searchQuery }),
    });
    if (!data.success) {
      setStatus(data.message);
    }
    setSearchResults(data.success ? data.data ?? [] : []);
  }

  async function logMeal(recipeId) {
    const { data } = await requestJson("/api/meals", {
      method: "POST",
      body: JSON.stringify({ recipe_id: recipeId, eaten_at: new Date().toISOString() }),
    });
    if (!data.success) {
      setStatus(data.message);
    }
    await loadAppData();
  }

  async function removeMeal(meal) {
    const { data } = await requestJson("/api/meals", {
      method: "DELETE",
      body: JSON.stringify({ recipe_id: meal.recipe_id, eaten_at: meal.eaten_at }),
    });
    if (!data.success) {
      setStatus(data.message);
    }
    await loadAppData();
  }

  async function saveGoal(event) {
    event.preventDefault();
    const { data } = await requestJson("/api/goals", {
      method: "POST",
      body: JSON.stringify(goalForm),
    });
    setStatus(data.message);
    await loadAppData();
  }

  async function removeGoal(nutrient) {
    const { data } = await requestJson("/api/goals", {
      method: "DELETE",
      body: JSON.stringify({ nutrient }),
    });
    setStatus(data.message);
    await loadAppData();
  }

  async function recommendationFeedback(recipeId, action) {
    const { data } = await requestJson("/api/recommendations", {
      method: "POST",
      body: JSON.stringify({ recipe_id: recipeId, action }),
    });
    if (!data.success) {
      setStatus(data.message);
    }
    if (action === "logged") {
      await logMeal(recipeId);
    } else {
      await loadAppData();
    }
  }

  async function sendChatMessage(event) {
    event.preventDefault();
    const text = chatInput.trim();
    if (!text) {
      return;
    }
    const nextMessages = [...chatMessages, { role: "user", text }];
    setChatMessages(nextMessages);
    setChatInput("");
    setChatLoading(true);

    try {
      const { data } = await requestJson("/api/chat", {
        method: "POST",
        body: JSON.stringify({
          message: text,
          history: chatMessages,
          recommendations: activeRecommendations,
        }),
      });
      if (!data.success) {
        setStatus(data.message);
      }
      setChatMessages((current) => [
        ...current,
        {
          role: "assistant",
          text: data.success
            ? data.data.reply
            : data.message || "I could not reach the AI chat service. Check the backend logs and GEMINI_API_KEY.",
        },
      ]);
    } catch {
      setStatus("Chat request failed.");
      setChatMessages((current) => [
        ...current,
        {
          role: "assistant",
          text: "I could not reach the AI chat service. Make sure the backend is running.",
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  }

  if (loading) {
    return (
      <main className={styles.shell}>
        <section className={styles.centerPanel}>
          <h1>Ctrl+Eat</h1>
          <p>{status}</p>
        </section>
      </main>
    );
  }

  if (!user) {
    return (
      <main className={styles.authShell}>
        <section className={styles.authHero}>
          <p className={styles.eyebrow}>Ctrl+Eat</p>
          <h1>Food tracking that learns your appetite.</h1>
          <p>
            Track meals, store preferences, and get ranked recommendations built from
            nutrition goals, allergies, dislikes, and recipe data.
          </p>
        </section>
        <section className={styles.authPanel}>
          <div className={styles.segmented}>
            <button
              className={authMode === "login" ? styles.activeSegment : ""}
              onClick={() => setAuthMode("login")}
              type="button"
            >
              Login
            </button>
            <button
              className={authMode === "create" ? styles.activeSegment : ""}
              onClick={() => setAuthMode("create")}
              type="button"
            >
              Create
            </button>
          </div>
          <form className={styles.form} onSubmit={submitAuth}>
            <label htmlFor="username">Username</label>
            <input
              id="username"
              value={authForm.username}
              onChange={(event) => setAuthForm({ ...authForm, username: event.target.value })}
              required
            />
            {authMode === "create" ? (
              <>
                <label htmlFor="email">Email</label>
                <input
                  id="email"
                  type="email"
                  value={authForm.email}
                  onChange={(event) => setAuthForm({ ...authForm, email: event.target.value })}
                />
              </>
            ) : null}
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={authForm.password}
              onChange={(event) => setAuthForm({ ...authForm, password: event.target.value })}
              required
            />
            <button className={styles.primaryButton}>
              {authMode === "login" ? "Login" : "Create account"}
            </button>
          </form>
          {status ? <p className={styles.status}>{status}</p> : null}
        </section>
      </main>
    );
  }

  return (
    <main className={styles.shell}>
      <header className={styles.topbar}>
        <div>
          <p className={styles.eyebrow}>Ctrl+Eat</p>
          <h1>{pageTitle}</h1>
        </div>
        <div className={styles.userCluster}>
          <div className={styles.navTabs}>
            <button
              className={activeView === "dashboard" ? styles.activeNav : ""}
              onClick={() => setActiveView("dashboard")}
              type="button"
            >
              Dashboard
            </button>
            <button
              className={activeView === "settings" ? styles.activeNav : ""}
              onClick={() => setActiveView("settings")}
              type="button"
            >
              Settings
            </button>
            {isAdmin ? (
              <button
                className={activeView === "admin" ? styles.activeNav : ""}
                onClick={() => {
                  setActiveView("admin");
                  loadAdminUsers();
                }}
                type="button"
              >
                Admin
              </button>
            ) : null}
          </div>
          <span>{user.username}</span>
          <button className={styles.ghostButton} onClick={loadAppData} type="button">
            Refresh
          </button>
          <button className={styles.ghostButton} onClick={logout} type="button">
            Logout
          </button>
        </div>
      </header>

      {activeView === "dashboard" ? (
        <DashboardView
          activeRecommendations={activeRecommendations}
          chatInput={chatInput}
          chatLoading={chatLoading}
          chatMessages={chatMessages}
          meals={meals}
          onChatInput={setChatInput}
          onDismiss={(recipeId) => recommendationFeedback(recipeId, "dismissed")}
          onLog={logMeal}
          onRemoveMeal={removeMeal}
          onSearch={searchMeals}
          onSendChat={sendChatMessage}
          progressMetrics={progressMetrics}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
        />
      ) : activeView === "admin" && isAdmin ? (
        <AdminView
          currentUsername={user.username}
          loading={adminLoading}
          onDeleteUser={deleteAdminUser}
          onPasswordReset={resetAdminPassword}
          onRefresh={loadAdminUsers}
          onRoleChange={updateAdminRole}
          users={adminUsers}
        />
      ) : (
        <SettingsView
          addDiet={addDiet}
          addSensitivity={addSensitivity}
          goalForm={goalForm}
          goals={goals}
          preferences={preferences}
          profileComplete={profileComplete}
          profileForm={profileForm}
          removeDiet={removeDiet}
          removeGoal={removeGoal}
          removeSensitivity={removeSensitivity}
          saveGoal={saveGoal}
          saveProfile={saveProfile}
          sensitivityForm={sensitivityForm}
          setGoalForm={setGoalForm}
          setProfileForm={setProfileForm}
          setSensitivityForm={setSensitivityForm}
          setSettingsTab={setSettingsTab}
          settingsTab={settingsTab}
        />
      )}
    </main>
  );
}

function AdminView({
  currentUsername,
  loading,
  onDeleteUser,
  onPasswordReset,
  onRefresh,
  onRoleChange,
  users,
}) {
  return (
    <section className={styles.adminLayout}>
      <article className={styles.panel}>
        <div className={styles.panelHeader}>
          <h2>User management</h2>
          <button className={styles.ghostButton} disabled={loading} onClick={onRefresh} type="button">
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>
        <div className={styles.tableWrap}>
          <table className={styles.adminTable}>
            <thead>
              <tr>
                <th>User</th>
                <th>Email</th>
                <th>Meals</th>
                <th>Role</th>
                <th>Created</th>
                <th>Password</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((account) => {
                const isCurrentUser = account.username === currentUsername;
                return (
                  <tr key={account.user_id}>
                    <td>{account.username}</td>
                    <td>{account.email_address || "None"}</td>
                    <td>{account.meal_count ?? 0}</td>
                    <td>
                      <select
                        aria-label={`Role for ${account.username}`}
                        disabled={loading || isCurrentUser}
                        onChange={(event) => onRoleChange(account.username, event.target.value)}
                        value={account.role}
                      >
                        <option value="user">user</option>
                        <option value="admin">admin</option>
                      </select>
                      {isCurrentUser ? <small className={styles.muted}>Current admin</small> : null}
                    </td>
                    <td>{account.created_at ? new Date(account.created_at).toLocaleString() : "Unknown"}</td>
                    <td>
                      <PasswordResetForm
                        disabled={loading}
                        onPasswordReset={(password) => onPasswordReset(account.username, password)}
                        username={account.username}
                      />
                    </td>
                    <td>
                      <button
                        className={styles.dangerButton}
                        disabled={loading || isCurrentUser}
                        onClick={() => onDeleteUser(account.username)}
                        type="button"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {!users.length ? <p className={styles.muted}>No users loaded yet.</p> : null}
      </article>
    </section>
  );
}

function PasswordResetForm({ disabled, onPasswordReset, username }) {
  const [password, setPassword] = useState("");

  async function submitPassword(event) {
    event.preventDefault();
    const success = await onPasswordReset(password);
    if (success) {
      setPassword("");
    }
  }

  return (
    <form className={styles.passwordResetForm} onSubmit={submitPassword}>
      <input
        aria-label={`New password for ${username}`}
        disabled={disabled}
        minLength={12}
        onChange={(event) => setPassword(event.target.value)}
        placeholder="New password"
        type="password"
        value={password}
      />
      <button className={styles.ghostButton} disabled={disabled || !password} type="submit">
        Reset
      </button>
    </form>
  );
}

function DashboardView({
  activeRecommendations,
  chatInput,
  chatLoading,
  chatMessages,
  meals,
  onChatInput,
  onDismiss,
  onLog,
  onRemoveMeal,
  onSearch,
  onSendChat,
  progressMetrics,
  searchQuery,
  setSearchQuery,
}) {
  return (
    <section className={styles.mainGrid}>
      <article className={`${styles.panel} ${styles.recommendationsPanel}`}>
        <div className={styles.panelHeader}>
          <h2>Recommendations</h2>
          <form onSubmit={onSearch} className={styles.inlineForm}>
            <input
              aria-label="Meal search"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
            />
            <button className={styles.iconButton} title="Search meals">
              Search
            </button>
          </form>
        </div>
        <div className={styles.cardList}>
          {activeRecommendations.map((meal) => (
            <MealCard
              key={meal.recipe_id}
              meal={meal}
              onDismiss={() => onDismiss(meal.recipe_id)}
              onLog={() => onLog(meal.recipe_id)}
            />
          ))}
          {!activeRecommendations.length ? (
            <p className={styles.muted}>Search for a meal to seed recommendations.</p>
          ) : null}
        </div>
      </article>

      <aside className={styles.sideStack}>
        <article className={styles.panel}>
          <div className={styles.panelHeader}>
            <h2>Progress</h2>
            <span>{meals.length} meals</span>
          </div>
          <div className={styles.metricGrid}>
            {progressMetrics.map(([name, value]) => (
              <div className={styles.metric} key={name}>
                <strong>{formatNutrient(value)}</strong>
                <span>{name}</span>
                <small>{nutrientUnit(value)}</small>
              </div>
            ))}
          </div>
        </article>

        <article className={styles.panel}>
          <div className={styles.panelHeader}>
            <h2>Meal log</h2>
          </div>
          <div className={styles.logList}>
            {meals.map((meal) => (
              <div className={styles.logItem} key={meal.user_meal_id ?? `${meal.recipe_id}-${meal.eaten_at}`}>
                <div>
                  <strong>{meal.meal}</strong>
                  <span>{new Date(meal.eaten_at).toLocaleString()}</span>
                </div>
                <button
                  className={styles.dangerButton}
                  onClick={() => onRemoveMeal(meal)}
                  type="button"
                >
                  Remove
                </button>
              </div>
            ))}
            {!meals.length ? <p className={styles.muted}>No meal history yet.</p> : null}
          </div>
        </article>

        <article className={styles.panel}>
          <div className={styles.panelHeader}>
            <h2>Recommendation chat</h2>
          </div>
          <div className={styles.chatLog}>
            {chatMessages.map((message, index) => (
              <div
                className={message.role === "user" ? styles.userMessage : styles.assistantMessage}
                key={`${message.role}-${index}`}
              >
                {message.text}
              </div>
            ))}
          </div>
          <form className={styles.chatForm} onSubmit={onSendChat}>
            <input
              aria-label="Recommendation chat"
              placeholder="Ask about macros, ingredients, or what to pick"
              value={chatInput}
              onChange={(event) => onChatInput(event.target.value)}
            />
            <button className={styles.primaryButton} disabled={chatLoading}>
              {chatLoading ? "Thinking..." : "Send"}
            </button>
          </form>
        </article>
      </aside>
    </section>
  );
}

function SettingsView({
  addDiet,
  addSensitivity,
  goalForm,
  goals,
  preferences,
  profileComplete,
  profileForm,
  removeDiet,
  removeGoal,
  removeSensitivity,
  saveGoal,
  saveProfile,
  sensitivityForm,
  setGoalForm,
  setProfileForm,
  setSensitivityForm,
  setSettingsTab,
  settingsTab,
}) {
  return (
    <section className={styles.settingsLayout}>
      <aside className={styles.settingsTabs}>
        <button
          className={settingsTab === "profile" ? styles.activeSettingsTab : ""}
          onClick={() => setSettingsTab("profile")}
          type="button"
        >
          Profile
        </button>
        <button
          className={settingsTab === "preferences" ? styles.activeSettingsTab : ""}
          onClick={() => setSettingsTab("preferences")}
          type="button"
        >
          Preferences
        </button>
        <button
          className={settingsTab === "goals" ? styles.activeSettingsTab : ""}
          onClick={() => setSettingsTab("goals")}
          type="button"
        >
          Goals
        </button>
      </aside>

      <article className={styles.panel}>
        {settingsTab === "profile" ? (
          <>
            <div className={styles.panelHeader}>
              <h2>Profile</h2>
              <span className={profileComplete ? styles.goodBadge : styles.warnBadge}>
                {profileComplete ? "Complete" : "Needed"}
              </span>
            </div>
            <form className={styles.compactGrid} onSubmit={saveProfile}>
              <label>
                Gender
                <select
                  value={profileForm.gender}
                  onChange={(event) => setProfileForm({ ...profileForm, gender: event.target.value })}
                >
                  <option value="female">Female</option>
                  <option value="male">Male</option>
                </select>
              </label>
              <label>
                Height in
                <input
                  type="number"
                  value={profileForm.height}
                  onChange={(event) => setProfileForm({ ...profileForm, height: event.target.value })}
                />
              </label>
              <label>
                Weight lb
                <input
                  type="number"
                  value={profileForm.weight}
                  onChange={(event) => setProfileForm({ ...profileForm, weight: event.target.value })}
                />
              </label>
              <label>
                Body fat %
                <input
                  type="number"
                  value={profileForm.body_fat}
                  onChange={(event) => setProfileForm({ ...profileForm, body_fat: event.target.value })}
                />
              </label>
              <label>
                Age
                <input
                  type="number"
                  value={profileForm.age}
                  onChange={(event) => setProfileForm({ ...profileForm, age: event.target.value })}
                />
              </label>
              <label>
                Activity
                <select
                  value={profileForm.activity}
                  onChange={(event) => setProfileForm({ ...profileForm, activity: event.target.value })}
                >
                  <option value="sedentary">Sedentary</option>
                  <option value="light">Light</option>
                  <option value="moderate">Moderate</option>
                  <option value="active">Active</option>
                </select>
              </label>
              <button className={styles.primaryButton}>Save profile</button>
            </form>
          </>
        ) : null}

        {settingsTab === "preferences" ? (
          <>
            <div className={styles.panelHeader}>
              <h2>Preferences</h2>
            </div>
            <div className={styles.chipGrid}>
              {DIET_OPTIONS.map((diet) => {
                const selected = preferences.diets?.includes(diet);
                return (
                  <button
                    className={selected ? styles.selectedChip : styles.chip}
                    key={diet}
                    onClick={() => (selected ? removeDiet(diet) : addDiet(diet))}
                    type="button"
                  >
                    {diet}
                  </button>
                );
              })}
            </div>
            <form className={styles.inlineForm} onSubmit={addSensitivity}>
              <input
                placeholder="Ingredient"
                value={sensitivityForm.allergen}
                onChange={(event) =>
                  setSensitivityForm({ ...sensitivityForm, allergen: event.target.value })
                }
                required
              />
              <select
                value={sensitivityForm.severity}
                onChange={(event) =>
                  setSensitivityForm({ ...sensitivityForm, severity: event.target.value })
                }
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
              <button className={styles.primaryButton}>Add</button>
            </form>
            <div className={styles.tagList}>
              {preferences.sensitivities?.map((item) => (
                <button
                  className={styles.tag}
                  key={`${item.ingredient}-${item.severity}`}
                  onClick={() => removeSensitivity(item.ingredient)}
                  type="button"
                >
                  {item.ingredient} - {item.severity}
                </button>
              ))}
            </div>
          </>
        ) : null}

        {settingsTab === "goals" ? (
          <>
            <div className={styles.panelHeader}>
              <h2>Goals</h2>
            </div>
            <form className={styles.inlineForm} onSubmit={saveGoal}>
              <select
                value={goalForm.nutrient}
                onChange={(event) => setGoalForm({ ...goalForm, nutrient: event.target.value })}
              >
                {[...new Set([...STARTER_GOALS, ...Object.keys(goals.recommended ?? {})])].map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </select>
              <input
                type="number"
                value={goalForm.amount}
                onChange={(event) => setGoalForm({ ...goalForm, amount: event.target.value })}
              />
              <select
                value={goalForm.min_max}
                onChange={(event) => setGoalForm({ ...goalForm, min_max: event.target.value })}
              >
                <option value="min">Min</option>
                <option value="max">Max</option>
              </select>
              <button className={styles.primaryButton}>Save</button>
            </form>
            <div className={styles.goalList}>
              {goals.goals?.map((goal) => (
                <div className={styles.goalItem} key={goal.nutrient}>
                  <strong>{goal.nutrient}</strong>
                  <span>
                    {goal.min_max} {goal.target} {goal.unit}
                  </span>
                  <button
                    className={styles.dangerButton}
                    onClick={() => removeGoal(goal.nutrient)}
                    type="button"
                  >
                    Remove
                  </button>
                </div>
              ))}
              {!goals.goals?.length ? <p className={styles.muted}>No custom goals saved.</p> : null}
            </div>
          </>
        ) : null}
      </article>
    </section>
  );
}

function MealCard({ meal, onLog, onDismiss }) {
  const [showRecipe, setShowRecipe] = useState(false);
  const [showIngredients, setShowIngredients] = useState(false);

  return (
    <article className={styles.mealCard}>
      <div className={styles.mealTopline}>
        <h3>{meal.meal}</h3>
        {meal.score ? <span className={styles.score}>{meal.score}</span> : null}
      </div>
      <p>{meal.explanation ?? "Matched from your current profile and meal search."}</p>
      {meal.flags?.length ? <small className={styles.flag}>Flags: {meal.flags.join(", ")}</small> : null}
      <div className={styles.nutrientPills}>
        {KEY_NUTRIENTS.map((name) => {
          const value = getMealNutrient(meal, name);
          const label = name === "carbohydrates" ? "carbs" : name;
          return (
            <span key={name}>
              {label}: {formatNutrient(value)}
              {nutrientUnit(value)}
            </span>
          );
        })}
      </div>
      <div className={styles.buttonRow}>
        <button className={styles.primaryButton} onClick={onLog} type="button">
          Log
        </button>
        <button className={styles.ghostButton} onClick={() => setShowRecipe((value) => !value)} type="button">
          {showRecipe ? "Hide recipe" : "Show recipe"}
        </button>
        <button className={styles.ghostButton} onClick={() => setShowIngredients((value) => !value)} type="button">
          {showIngredients ? "Hide ingredients" : "Show ingredients"}
        </button>
        <button className={styles.ghostButton} onClick={onDismiss} type="button">
          Dismiss
        </button>
      </div>
      {showRecipe ? <RecipeDetails meal={meal} /> : null}
      {showIngredients ? <IngredientDetails ingredients={meal.ingredients ?? []} /> : null}
    </article>
  );
}

function RecipeDetails({ meal }) {
  const recipe = meal.recipe ?? {};
  const steps = recipe.steps?.length
    ? recipe.steps
    : [
        "Gather the listed ingredients.",
        "Prepare and combine the ingredients to match the recommendation.",
        "Taste, adjust seasoning, and serve.",
      ];

  return (
    <div className={styles.detailPanel}>
      <strong>Recipe</strong>
      <p>{recipe.summary ?? meal.explanation ?? "This recipe matched your current recommendations."}</p>
      <div className={styles.recipeFacts}>
        <span>Recipe ID: {meal.recipe_id}</span>
        {meal.score ? <span>Match score: {meal.score}</span> : null}
        {recipe.servings ? <span>Servings: {recipe.servings}</span> : null}
        {recipe.ready_in_minutes ? <span>Ready in: {recipe.ready_in_minutes} min</span> : null}
      </div>
      <ol>
        {steps.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>
      {recipe.source_url ? (
        <a className={styles.recipeLink} href={recipe.source_url} rel="noreferrer" target="_blank">
          Open original recipe
        </a>
      ) : null}
      {meal.score_signals?.length ? (
        <ul className={styles.signalList}>
          {meal.score_signals.map((signal) => (
            <li key={signal}>{signal}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function IngredientDetails({ ingredients }) {
  return (
    <div className={styles.detailPanel}>
      <strong>Ingredients</strong>
      {ingredients.length ? (
        <ul className={styles.ingredientList}>
          {ingredients.map((ingredient, index) => (
            <li key={`${ingredient.name}-${index}`}>
              <span>{ingredient.name}</span>
              <small>
                {[ingredient.amount, ingredient.unit].filter(Boolean).join(" ") || "as needed"}
              </small>
            </li>
          ))}
        </ul>
      ) : (
        <p>No ingredients are available for this recommendation yet.</p>
      )}
    </div>
  );
}
