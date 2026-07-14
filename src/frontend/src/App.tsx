import React, { useEffect, useMemo, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";

import type {
  ManagedUser,
  ManagedUserDetails,
  Notification,
  PhoneStatusValue,
  StatusHistoryEntry,
  UserProfile,
} from "./types";

import "./App.css";

type View = "loading" | "login" | "register" | "otp" | "dashboard" | "forgot-password" | "reset-password" | "verify-email-pending" | "faq" | "howto" | "about-us";
type InfoView = "faq" | "howto" | "about-us";

interface LoginForm {
  username: string;
  password: string;
}

interface RegisterForm {
  username: string;
  email: string;
  phone_number: string;
  imei: string;
  password: string;
}

const STATUS_LABELS: Record<PhoneStatusValue, string> = {
  online: "Online",
  sold: "Sold",
  stolen: "Stolen",
  reported_stolen: "Reported Stolen",
  disposed: "Disposed",
};

const EMPTY_LOGIN: LoginForm = { username: "", password: "" };
const EMPTY_REGISTER: RegisterForm = {
  username: "",
  email: "",
  phone_number: "",
  imei: "",
  password: "",
};

const getStatusLabel = (status: PhoneStatusValue | ""): string =>
  status ? (STATUS_LABELS[status] ?? status) : "";

async function apiPost(
  path: string,
  body: Record<string, string>,
): Promise<Response> {
  return fetch(path, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export default function App() {
  const [view, setView] = useState<View>("loading");
  const [pendingUsername, setPendingUsername] = useState<string>("");
  const [otpCode, setOtpCode] = useState<string>("");
  const [forgotEmail, setForgotEmail] = useState<string>("");
  const [resetToken, setResetToken] = useState<string>("");
  const [resetNewPassword, setResetNewPassword] = useState<string>("");
  const [loginForm, setLoginForm] = useState<LoginForm>(EMPTY_LOGIN);
  const [registerForm, setRegisterForm] = useState<RegisterForm>(EMPTY_REGISTER);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [statusOptions, setStatusOptions] = useState<PhoneStatusValue[]>([]);
  const [statusHistory, setStatusHistory] = useState<StatusHistoryEntry[]>([]);
  const [newStatus, setNewStatus] = useState<PhoneStatusValue | "">("");
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [selectedUser, setSelectedUser] = useState<ManagedUserDetails | null>(null);
  const [adminForm, setAdminForm] = useState<ManagedUser | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [previousView, setPreviousView] = useState<View>("login");

  const isManager = useMemo(
    () => profile?.role === "manager" || profile?.role === "admin",
    [profile?.role],
  );
  const isAdmin = profile?.role === "admin";

  const handleEmailVerification = async (token: string): Promise<void> => {
    try {
      const response = await fetch(
        `/api/auth/verify-email?token=${encodeURIComponent(token)}`,
        { credentials: "include" },
      );
      const payload: { message: string } = await response.json();
      if (response.ok) {
        addNotification("info", "Email verified! You can now sign in.");
      } else {
        addNotification("error", payload.message ?? "Email verification failed.");
      }
    } catch {
      addNotification("error", "Email verification failed. Please try again.");
    }
    setView("login");
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const resetTok = params.get("reset_token");
    const verifyTok = params.get("verify_token");
    if (resetTok) {
      setResetToken(resetTok);
      window.history.replaceState({}, "", window.location.pathname);
      setView("reset-password");
      return;
    }
    if (verifyTok) {
      window.history.replaceState({}, "", window.location.pathname);
      void handleEmailVerification(verifyTok);
      return;
    }
    void loadProfile();
  }, []);

  const addNotification = (
    kind: Notification["kind"],
    message: string,
  ): void => {
    const id = crypto.randomUUID();
    setNotifications((prev) => [...prev, { id, kind, message }]);
    setTimeout(() => {
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    }, 5000);
  };

  const handleError = (error: unknown): void => {
    const message =
      error instanceof Error ? error.message : "Unexpected error occurred";
    addNotification("error", message);
  };

  const loadProfile = async (): Promise<void> => {
    const response = await fetch("/api/users/me", { credentials: "include" });
    if (response.status === 401) {
      setView("login");
      return;
    }
    if (!response.ok) {
      addNotification("error", "Failed to load profile");
      setView("login");
      return;
    }
    const data: UserProfile = await response.json();
    setProfile(data);
    await Promise.all([
      fetchStatusOptions(),
      fetchStatusHistory(),
      data.role !== "user" ? fetchManagerUsers() : Promise.resolve(),
    ]);
    setView("dashboard");
  };

  const handleLogin = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    try {
      const response = await apiPost("/api/auth/login", {
        username: loginForm.username,
        password: loginForm.password,
      });
      const payload: { message: string; requires_otp?: boolean } = await response.json();
      if (!response.ok) {
        addNotification("error", payload.message ?? "Login failed");
        return;
      }
      if (payload.requires_otp) {
        setPendingUsername(loginForm.username);
        setLoginForm(EMPTY_LOGIN);
        setOtpCode("");
        setView("otp");
        return;
      }
      setLoginForm(EMPTY_LOGIN);
      await loadProfile();
    } catch (error) {
      handleError(error);
    }
  };

  const handleVerifyOtp = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    try {
      const response = await apiPost("/api/auth/verify-otp", {
        username: pendingUsername,
        otp: otpCode,
      });
      const payload: { message: string } = await response.json();
      if (!response.ok) {
        addNotification("error", payload.message ?? "Verification failed");
        return;
      }
      setOtpCode("");
      setPendingUsername("");
      await loadProfile();
    } catch (error) {
      handleError(error);
    }
  };

  const handleRegister = async (
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> => {
    event.preventDefault();
    try {
      const response = await apiPost(
        "/api/auth/register",
        registerForm as unknown as Record<string, string>,
      );
      const payload: { message: string } = await response.json();
      if (!response.ok) {
        addNotification("error", payload.message ?? "Registration failed");
        return;
      }
      setRegisterForm(EMPTY_REGISTER);
      setView("verify-email-pending");
    } catch (error) {
      handleError(error);
    }
  };

  const navigateToInfoPage = (target: InfoView): void => {
    if (view !== "faq" && view !== "howto" && view !== "about-us") {
      setPreviousView(view);
    }
    setView(target);
  };

  const handleLogout = async (): Promise<void> => {
    try {
      await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
    } catch {
      // best-effort logout
    }
    setProfile(null);
    setStatusOptions([]);
    setStatusHistory([]);
    setNewStatus("");
    setUsers([]);
    setSelectedUser(null);
    setAdminForm(null);
    setView("login");
  };

  const fetchStatusOptions = async (): Promise<void> => {
    try {
      const response = await fetch("/api/users/status/options", {
        credentials: "include",
      });
      if (!response.ok) throw new Error("Failed to load status options");
      const payload: { statuses: PhoneStatusValue[] } = await response.json();
      setStatusOptions(payload.statuses);
      setNewStatus((cur) => cur || payload.statuses[0] || "");
    } catch (error) {
      handleError(error);
    }
  };

  const fetchStatusHistory = async (): Promise<void> => {
    try {
      const response = await fetch("/api/users/status/history", {
        credentials: "include",
      });
      if (!response.ok) throw new Error("Failed to load status history");
      const payload: { status_history: StatusHistoryEntry[] } =
        await response.json();
      setStatusHistory(payload.status_history);
    } catch (error) {
      handleError(error);
    }
  };

  const fetchManagerUsers = async (): Promise<void> => {
    try {
      const response = await fetch("/api/manager/users", {
        credentials: "include",
      });
      if (!response.ok) throw new Error("Failed to load users");
      const payload: { users: ManagedUser[] } = await response.json();
      setUsers(payload.users);
    } catch (error) {
      handleError(error);
    }
  };

  const fetchUserDetails = async (username: string): Promise<void> => {
    try {
      const response = await fetch(`/api/manager/users/${username}`, {
        credentials: "include",
      });
      if (!response.ok) throw new Error("Failed to load user details");
      const payload: ManagedUserDetails = await response.json();
      setSelectedUser(payload);
      if (isAdmin) setAdminForm({ ...payload.user });
    } catch (error) {
      handleError(error);
    }
  };

  const handleStatusUpdate = async (
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> => {
    event.preventDefault();
    if (!newStatus) return;
    try {
      const response = await apiPost("/api/users/status", { status: newStatus });
      if (!response.ok) throw new Error("Unable to update status");
      addNotification("info", `Status updated to ${getStatusLabel(newStatus)}`);
      await fetchStatusHistory();
    } catch (error) {
      handleError(error);
    }
  };

  const handleAdminUpdate = async (
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> => {
    event.preventDefault();
    if (!adminForm) return;
    try {
      const response = await fetch(
        `/api/manager/users/${adminForm.username}`,
        {
          method: "PATCH",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: adminForm.email,
            phone_number: adminForm.phone_number,
            imei: adminForm.imei,
            role: adminForm.role,
          }),
        },
      );
      if (!response.ok) {
        const err: { message?: string } = await response.json();
        throw new Error(err.message ?? "Failed to update user");
      }
      const payload: { user: ManagedUser } = await response.json();
      addNotification("info", `${payload.user.username} updated`);
      setUsers((prev) =>
        prev.map((u) =>
          u.username === payload.user.username ? payload.user : u,
        ),
      );
      await fetchUserDetails(payload.user.username);
    } catch (error) {
      handleError(error);
    }
  };

  const handleForgotPassword = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    try {
      const response = await apiPost("/api/auth/forgot-password", { email: forgotEmail });
      const payload: { message: string } = await response.json();
      addNotification("info", payload.message ?? "If that email is registered, a reset link has been sent.");
      setForgotEmail("");
      setView("login");
    } catch (error) {
      handleError(error);
    }
  };

  const handleResetPassword = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    try {
      const response = await apiPost("/api/auth/reset-password", {
        token: resetToken,
        new_password: resetNewPassword,
      });
      const payload: { message: string } = await response.json();
      if (!response.ok) {
        addNotification("error", payload.message ?? "Password reset failed.");
        return;
      }
      addNotification("info", payload.message ?? "Password reset successful. Please sign in.");
      setResetToken("");
      setResetNewPassword("");
      setView("login");
    } catch (error) {
      handleError(error);
    }
  };

  const updateLoginForm = (event: ChangeEvent<HTMLInputElement>): void => {
    const { name, value } = event.target;
    setLoginForm((prev) => ({ ...prev, [name]: value } as LoginForm));
  };

  const updateRegisterForm = (event: ChangeEvent<HTMLInputElement>): void => {
    const { name, value } = event.target;
    setRegisterForm((prev) => ({ ...prev, [name]: value } as RegisterForm));
  };

  const updateAdminField = (
    event: ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ): void => {
    const { name, value } = event.target;
    setAdminForm((prev) => (prev ? { ...prev, [name]: value } : prev));
  };

  return (
    <main className="app">
      <HamburgerMenu onNavigate={navigateToInfoPage} />
      <div className="site-logo-wrap">
        <img src="/images/logo2.svg" alt="Eye Me Eye logo" className="site-logo" />
      </div>
      <h1 className="page-title">EyeMeEye</h1>
      <p className="page-tagline">Stop Mobile Phone Theft</p>

      {notifications.map((note) => (
        <div
          key={note.id}
          role={note.kind === "error" ? "alert" : "status"}
          className={`notification notification--${note.kind}`}
        >
          {note.message}
        </div>
      ))}

      {view === "loading" && <p className="loading-text">Loading…</p>}

      {view === "login" && (
        <AuthCard
          title="Sign In"
          onSubmit={(e) => { void handleLogin(e); }}
          switchLabel="No account?"
          switchAction="Register"
          onSwitch={() => setView("register")}
          footer={
            <p className="auth-switch">
              <button
                type="button"
                className="auth-link"
                onClick={() => setView("forgot-password")}
              >
                Forgot password?
              </button>
            </p>
          }
        >
          <AuthField label="Username">
            <input
              type="text"
              name="username"
              value={loginForm.username}
              onChange={updateLoginForm}
              required
              autoFocus
            />
          </AuthField>
          <AuthField label="Password">
            <input
              type="password"
              name="password"
              value={loginForm.password}
              onChange={updateLoginForm}
              required
            />
          </AuthField>
        </AuthCard>
      )}

      {view === "register" && (
        <AuthCard
          title="Create Account"
          onSubmit={(e) => { void handleRegister(e); }}
          switchLabel="Have an account?"
          switchAction="Sign In"
          onSwitch={() => setView("login")}
        >
          <AuthField label="Username">
            <Tooltip content="Your username can be your email address.">
              <input
                type="text"
                name="username"
                value={registerForm.username}
                onChange={updateRegisterForm}
                required
                autoFocus
                minLength={3}
              />
            </Tooltip>
          </AuthField>
          <AuthField label="Email">
            <input
              type="email"
              name="email"
              value={registerForm.email}
              onChange={updateRegisterForm}
              required
            />
          </AuthField>
          <AuthField label="Phone Number">
            <input
              type="tel"
              name="phone_number"
              value={registerForm.phone_number}
              onChange={updateRegisterForm}
              required
              placeholder="7–15+ digits"
            />
          </AuthField>
          <AuthField label={<>IMEI <span className="imei-dial-code">*#06#</span></>}>
            <Tooltip content={
              <>
                <p>To display your phone's unique 15-digit IMEI number on the screen, simply open your device's Phone/Calling app, dial *#06#, and a pop-up will instantly appear with the information.</p>
                <p>If you need to find it in your phone's settings instead:</p>
                <ul>
                  <li><strong>iPhone:</strong> Go to Settings → General → About.</li>
                  <li><strong>Android:</strong> Go to Settings → About Phone (or Status).</li>
                </ul>
              </>
            }>
              <input
                type="text"
                name="imei"
                value={registerForm.imei}
                onChange={updateRegisterForm}
                required
                placeholder="14–15 digits"
                minLength={14}
                maxLength={15}
              />
            </Tooltip>
          </AuthField>
          <AuthField
            label="Password"
            hint="8–128 chars, uppercase, lowercase, digit &amp; special (@$!%*?&amp;)"
          >
            <input
              type="password"
              name="password"
              value={registerForm.password}
              onChange={updateRegisterForm}
              required
              minLength={8}
            />
          </AuthField>
        </AuthCard>
      )}

      {view === "verify-email-pending" && (
        <div className="auth-container">
          <div className="auth-form">
            <h2 className="auth-title">Check Your Email</h2>
            <p className="auth-hint">
              Your account has been created. We&apos;ve sent a verification link
              to your email address — please click it to activate your account
              before signing in.
            </p>
            <p className="auth-hint">
              If you don&apos;t see the email, check your spam or junk folder.
            </p>
            <p className="auth-switch">
              Already verified?{" "}
              <button
                type="button"
                className="auth-link"
                onClick={() => setView("login")}
              >
                Sign In
              </button>
            </p>
          </div>
        </div>
      )}

      {view === "otp" && (
        <div className="auth-container">
          <form
            onSubmit={(e) => { void handleVerifyOtp(e); }}
            className="auth-form"
          >
            <h2 className="auth-title">Check Your Email</h2>
            <p className="auth-hint">
              A 6-digit code was sent to the address for{" "}
              <strong>{pendingUsername}</strong>. Enter it below.
            </p>
            <label className="auth-field">
              Verification Code
              <input
                type="text"
                inputMode="numeric"
                pattern="\d{6}"
                maxLength={6}
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ""))}
                required
                autoFocus
                placeholder="123456"
              />
            </label>
            <button type="submit" className="button auth-submit">
              Verify
            </button>
            <p className="auth-switch">
              Wrong account?{" "}
              <button
                type="button"
                className="auth-link"
                onClick={() => {
                  setPendingUsername("");
                  setOtpCode("");
                  setView("login");
                }}
              >
                Back to sign in
              </button>
            </p>
          </form>
        </div>
      )}

      {view === "forgot-password" && (
        <div className="auth-container">
          <form
            onSubmit={(e) => { void handleForgotPassword(e); }}
            className="auth-form"
          >
            <h2 className="auth-title">Reset Password</h2>
            <p className="auth-hint">
              Enter your account email address and we'll send a reset link.
            </p>
            <label className="auth-field">
              Email
              <input
                type="email"
                value={forgotEmail}
                onChange={(e) => setForgotEmail(e.target.value)}
                required
                autoFocus
                placeholder="you@example.com"
              />
            </label>
            <button type="submit" className="button auth-submit">
              Send Reset Link
            </button>
            <p className="auth-switch">
              <button
                type="button"
                className="auth-link"
                onClick={() => { setForgotEmail(""); setView("login"); }}
              >
                Back to sign in
              </button>
            </p>
          </form>
        </div>
      )}

      {view === "reset-password" && (
        <div className="auth-container">
          <form
            onSubmit={(e) => { void handleResetPassword(e); }}
            className="auth-form"
          >
            <h2 className="auth-title">Set New Password</h2>
            <p className="auth-hint">
              Choose a new password for your account.
            </p>
            <label className="auth-field">
              New Password
              <input
                type="password"
                value={resetNewPassword}
                onChange={(e) => setResetNewPassword(e.target.value)}
                required
                autoFocus
                minLength={8}
                placeholder="8–128 chars, upper, lower, digit &amp; special"
              />
            </label>
            <button type="submit" className="button auth-submit">
              Reset Password
            </button>
            <p className="auth-switch">
              <button
                type="button"
                className="auth-link"
                onClick={() => { setResetToken(""); setResetNewPassword(""); setView("login"); }}
              >
                Back to sign in
              </button>
            </p>
          </form>
        </div>
      )}

      {view === "faq" && (
        <InfoPage title="FAQ" onBack={() => setView(previousView)} />
      )}
      {view === "howto" && (
        <InfoPage title="How To" onBack={() => setView(previousView)} />
      )}
      {view === "about-us" && (
        <InfoPage title="About Us" onBack={() => setView(previousView)} />
      )}

      {view === "dashboard" && profile && (
        <Dashboard
          profile={profile}
          statusOptions={statusOptions}
          statusHistory={statusHistory}
          newStatus={newStatus}
          users={users}
          selectedUser={selectedUser}
          adminForm={adminForm}
          isManager={isManager}
          isAdmin={isAdmin}
          onStatusChange={(v) => setNewStatus(v)}
          onStatusUpdate={(e) => { void handleStatusUpdate(e); }}
          onSelectUser={(u) => { void fetchUserDetails(u); }}
          onAdminFieldChange={updateAdminField}
          onAdminUpdate={(e) => { void handleAdminUpdate(e); }}
          onLogout={() => { void handleLogout(); }}
        />
      )}
    </main>
  );
}

// ─── Sub-components ──────────────────────────────────────────────────────────

const LOREM_1 =
  "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.";

const LOREM_2 =
  "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt.";

const LOREM_3 =
  "At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati cupiditate non provident, similique sunt in culpa qui officia deserunt mollitia animi, id est laborum et dolorum fuga. Et harum quidem rerum facilis est et expedita distinctio. Nam libero tempore, cum soluta nobis est eligendi optio cumque nihil impedit quo minus id quod maxime placeat facere possimus.";

interface HamburgerMenuProps {
  onNavigate: (target: InfoView) => void;
}

function HamburgerMenu({ onNavigate }: HamburgerMenuProps) {
  const [open, setOpen] = useState(false);

  const go = (target: InfoView): void => {
    onNavigate(target);
    setOpen(false);
  };

  return (
    <div className="hamburger-container">
      <button
        type="button"
        className="hamburger-btn"
        aria-label="Open menu"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        <span />
        <span />
        <span />
      </button>
      {open && (
        <>
          <div className="hamburger-backdrop" onClick={() => setOpen(false)} />
          <nav className="hamburger-nav" aria-label="Site menu">
            <button type="button" onClick={() => go("faq")}>FAQ</button>
            <button type="button" onClick={() => go("howto")}>How To</button>
            <button type="button" onClick={() => go("about-us")}>About Us</button>
          </nav>
        </>
      )}
    </div>
  );
}

interface InfoPageProps {
  title: string;
  onBack: () => void;
}

function InfoPage({ title, onBack }: InfoPageProps) {
  return (
    <div className="info-page">
      <h2 className="section-title">{title}</h2>
      <p>{LOREM_1}</p>
      <p>{LOREM_2}</p>
      <p>{LOREM_3}</p>
      <button type="button" className="button button--ghost" onClick={onBack}>
        ← Back
      </button>
    </div>
  );
}

interface AuthCardProps {
  title: string;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
  switchLabel: string;
  switchAction: string;
  onSwitch: () => void;
  footer?: React.ReactNode;
  children: React.ReactNode;
}

function AuthCard({
  title,
  onSubmit,
  switchLabel,
  switchAction,
  onSwitch,
  footer,
  children,
}: AuthCardProps) {
  return (
    <div className="auth-container">
      <form onSubmit={onSubmit} className="auth-form">
        <h2 className="auth-title">{title}</h2>
        {children}
        <button type="submit" className="button auth-submit">
          {title}
        </button>
        <p className="auth-switch">
          {switchLabel}{" "}
          <button type="button" className="auth-link" onClick={onSwitch}>
            {switchAction}
          </button>
        </p>
        {footer}
      </form>
    </div>
  );
}

interface AuthFieldProps {
  label: React.ReactNode;
  hint?: string;
  children: React.ReactNode;
}

function AuthField({ label, hint, children }: AuthFieldProps) {
  return (
    <label className="auth-field">
      {hint ? (
        <span>
          {label} <span className="auth-optional">({hint})</span>
        </span>
      ) : (
        label
      )}
      {children}
    </label>
  );
}

interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
}

function Tooltip({ content, children }: TooltipProps) {
  return (
    <span className="tooltip-wrap">
      {children}
      <span className="tooltip-content" role="tooltip">{content}</span>
    </span>
  );
}

interface DashboardProps {
  profile: UserProfile;
  statusOptions: PhoneStatusValue[];
  statusHistory: StatusHistoryEntry[];
  newStatus: PhoneStatusValue | "";
  users: ManagedUser[];
  selectedUser: ManagedUserDetails | null;
  adminForm: ManagedUser | null;
  isManager: boolean;
  isAdmin: boolean;
  onStatusChange: (v: PhoneStatusValue | "") => void;
  onStatusUpdate: (e: FormEvent<HTMLFormElement>) => void;
  onSelectUser: (username: string) => void;
  onAdminFieldChange: (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
  onAdminUpdate: (e: FormEvent<HTMLFormElement>) => void;
  onLogout: () => void;
}

function Dashboard({
  profile,
  statusOptions,
  statusHistory,
  newStatus,
  users,
  selectedUser,
  adminForm,
  isManager,
  isAdmin,
  onStatusChange,
  onStatusUpdate,
  onSelectUser,
  onAdminFieldChange,
  onAdminUpdate,
  onLogout,
}: DashboardProps) {
  return (
    <>
      <section className="section">
        <div className="section-header">
          <h2 className="section-title">Welcome, {profile.username}</h2>
        </div>
        <div style={{ marginBottom: "1em" }}>
          <button
            type="button"
            className="button button--ghost"
            onClick={onLogout}
          >
            Sign Out
          </button>
        </div>
        <ul className="detail-list">
          <li><strong>Email:</strong> {profile.email}</li>
          <li><strong>Phone Number:</strong> {profile.phone_number}</li>
          <li><strong>IMEI:</strong> {profile.imei}</li>
          <li><strong>Role:</strong> {profile.role}</li>
        </ul>

        <form onSubmit={onStatusUpdate} className="status-form">
          <label>
            Update Status:
            <select
              value={newStatus}
              onChange={(e) =>
                onStatusChange(
                  e.target.value ? (e.target.value as PhoneStatusValue) : "",
                )
              }
            >
              {statusOptions.map((option) => (
                <option key={option} value={option}>
                  {getStatusLabel(option)}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" className="button">
            Save
          </button>
        </form>

        <section className="status-history">
          <h3 className="section-title">Status History</h3>
          {statusHistory.length === 0 ? (
            <p>No status updates yet.</p>
          ) : (
            <ul>
              {statusHistory.map((entry) => (
                <li key={entry.noted_at}>
                  {getStatusLabel(entry.status)} at{" "}
                  {new Date(entry.noted_at).toLocaleString()}
                </li>
              ))}
            </ul>
          )}
        </section>
      </section>

      {isManager && (
        <ManagedUsersSection
          users={users}
          selectedUser={selectedUser}
          adminForm={adminForm}
          isAdmin={isAdmin}
          onSelectUser={onSelectUser}
          onAdminFieldChange={onAdminFieldChange}
          onAdminUpdate={onAdminUpdate}
        />
      )}
    </>
  );
}

interface ManagedUsersSectionProps {
  users: ManagedUser[];
  selectedUser: ManagedUserDetails | null;
  adminForm: ManagedUser | null;
  isAdmin: boolean;
  onSelectUser: (username: string) => void;
  onAdminFieldChange: (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
  onAdminUpdate: (e: FormEvent<HTMLFormElement>) => void;
}

function ManagedUsersSection({
  users,
  selectedUser,
  adminForm,
  isAdmin,
  onSelectUser,
  onAdminFieldChange,
  onAdminUpdate,
}: ManagedUsersSectionProps) {
  return (
    <section className="section">
      <h2 className="section-title">Managed Users</h2>
      <div className="table-wrapper">
        <table className="user-table">
          <thead>
            <tr>
              <th>Username</th>
              <th>Email</th>
              <th>Role</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.username}>
                <td>{user.username}</td>
                <td>{user.email}</td>
                <td>{user.role}</td>
                <td>
                  <button
                    type="button"
                    className="button button--ghost"
                    onClick={() => onSelectUser(user.username)}
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedUser && (
        <UserDetailCard
          selectedUser={selectedUser}
          adminForm={adminForm}
          isAdmin={isAdmin}
          onAdminFieldChange={onAdminFieldChange}
          onAdminUpdate={onAdminUpdate}
        />
      )}
    </section>
  );
}

interface UserDetailCardProps {
  selectedUser: ManagedUserDetails;
  adminForm: ManagedUser | null;
  isAdmin: boolean;
  onAdminFieldChange: (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
  onAdminUpdate: (e: FormEvent<HTMLFormElement>) => void;
}

function UserDetailCard({
  selectedUser,
  adminForm,
  isAdmin,
  onAdminFieldChange,
  onAdminUpdate,
}: UserDetailCardProps) {
  return (
    <div className="detail-card">
      <h3 className="section-title">Details for {selectedUser.user.username}</h3>
      <ul className="detail-list">
        <li>Email: {selectedUser.user.email}</li>
        <li>Phone: {selectedUser.user.phone_number}</li>
        <li>IMEI: {selectedUser.user.imei}</li>
        <li>Role: {selectedUser.user.role}</li>
      </ul>
      <h4 className="section-title">Status History</h4>
      {selectedUser.status_history.length === 0 ? (
        <p>No status updates recorded.</p>
      ) : (
        <ul>
          {selectedUser.status_history.map((entry) => (
            <li key={entry.noted_at}>
              {getStatusLabel(entry.status)} at{" "}
              {new Date(entry.noted_at).toLocaleString()}
            </li>
          ))}
        </ul>
      )}

      {isAdmin && adminForm && (
        <form onSubmit={onAdminUpdate} className="admin-form">
          <fieldset className="admin-fieldset">
            <legend>Edit User</legend>
            <label className="admin-field">
              Email
              <input
                type="email"
                name="email"
                value={adminForm.email}
                onChange={onAdminFieldChange}
                required
              />
            </label>
            <label className="admin-field">
              Phone Number
              <input
                type="tel"
                name="phone_number"
                value={adminForm.phone_number}
                onChange={onAdminFieldChange}
                required
              />
            </label>
            <label className="admin-field">
              IMEI
              <input
                type="text"
                name="imei"
                value={adminForm.imei}
                onChange={onAdminFieldChange}
                required
              />
            </label>
            <label className="admin-field">
              Role
              <select
                name="role"
                value={adminForm.role}
                onChange={onAdminFieldChange}
              >
                <option value="user">user</option>
                <option value="manager">manager</option>
                <option value="admin">admin</option>
              </select>
            </label>
            <button type="submit" className="button">
              Save Changes
            </button>
          </fieldset>
        </form>
      )}
    </div>
  );
}
