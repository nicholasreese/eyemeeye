import React, { useEffect, useMemo, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";

import type {
  ManagedUser,
  ManagedUserDetails,
  Notification,
  NotificationKind,
  PhoneStatusValue,
  StatusHistoryEntry,
  UserProfile,
} from "./types";

const STATUS_LABELS: Record<PhoneStatusValue, string> = {
  online: "Online",
  sold: "Sold",
  stolen: "Stolen",
  disposed: "Disposed",
};

const getStatusLabel = (status: PhoneStatusValue | ""): string => {
  if (!status) {
    return "";
  }

  return STATUS_LABELS[status] ?? status;
};

export default function App() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [statusOptions, setStatusOptions] = useState<PhoneStatusValue[]>([]);
  const [statusHistory, setStatusHistory] = useState<StatusHistoryEntry[]>([]);
  const [newStatus, setNewStatus] = useState<PhoneStatusValue | "">("");
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [selectedUser, setSelectedUser] = useState<ManagedUserDetails | null>(
    null,
  );
  const [adminForm, setAdminForm] = useState<ManagedUser | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const isManager = useMemo(
    () => profile?.role === "manager" || profile?.role === "admin",
    [profile?.role],
  );
  const isAdmin = profile?.role === "admin";

  useEffect(() => {
    const loadProfile = async () => {
      try {
        setLoading(true);
        const response = await fetch("/api/users/me", {
          credentials: "include",
        });
        if (!response.ok) {
          throw new Error("Failed to fetch profile");
        }
        const data: UserProfile = await response.json();
        setProfile(data);
        await Promise.all([
          fetchStatusOptions(),
          fetchStatusHistory(),
          data.role !== "user" ? fetchManagerUsers() : Promise.resolve(),
        ]);
      } catch (error) {
        handleError(error);
      } finally {
        setLoading(false);
      }
    };

    loadProfile();
  }, []);

  const addNotification = (notification: Omit<Notification, "id">): void => {
    const enhancedNotification: Notification = {
      id: crypto.randomUUID(),
      ...notification,
    };
    setNotifications((prev: Notification[]) => [...prev, enhancedNotification]);
    setTimeout(() => {
      setNotifications((prev: Notification[]) =>
        prev.filter((note) => note.id !== enhancedNotification.id),
      );
    }, 5000);
  };

  const handleError = (error: unknown) => {
    const message =
      error instanceof Error ? error.message : "Unexpected error occurred";
    addNotification({ kind: "error", message });
  };

  const fetchStatusOptions = async (): Promise<void> => {
    try {
      const response = await fetch("/api/users/status/options", {
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error("Failed to load status options");
      }
      const payload: { statuses: PhoneStatusValue[] } = await response.json();
      setStatusOptions(payload.statuses);
      setNewStatus(
        (currentStatus: PhoneStatusValue | "") =>
          currentStatus || payload.statuses[0] || "",
      );
    } catch (error) {
      handleError(error);
    }
  };

  const fetchStatusHistory = async (): Promise<void> => {
    try {
      const response = await fetch("/api/users/status/history", {
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error("Failed to load status history");
      }
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
      if (!response.ok) {
        throw new Error("Failed to load users");
      }
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
      if (!response.ok) {
        throw new Error("Failed to load user details");
      }
      const payload: ManagedUserDetails = await response.json();
      setSelectedUser(payload);
      if (isAdmin) {
        setAdminForm({ ...payload.user });
      }
    } catch (error) {
      handleError(error);
    }
  };

  const handleStatusUpdate = async (
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> => {
    event.preventDefault();
    if (!newStatus) {
      return;
    }

    try {
      const response = await fetch("/api/users/status", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      if (!response.ok) {
        throw new Error("Unable to update status");
      }
      addNotification({
        kind: "info",
        message: `Status updated to ${getStatusLabel(newStatus)}`,
      });
      await fetchStatusHistory();
    } catch (error) {
      handleError(error);
    }
  };

  const handleSelectUser = (username: string): void => {
    void fetchUserDetails(username);
  };

  const handleAdminFormChange = (
    event: ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ): void => {
    const { name, value } = event.target;
    setAdminForm((prev: ManagedUser | null) =>
      prev ? { ...prev, [name]: value } : prev,
    );
  };

  const handleAdminUpdate = async (
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> => {
    event.preventDefault();
    if (!adminForm) {
      return;
    }

    try {
      const response = await fetch(`/api/manager/users/${adminForm.username}`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: adminForm.email,
          phone_number: adminForm.phone_number,
          imei: adminForm.imei,
          role: adminForm.role,
        }),
      });
      if (!response.ok) {
        const payload = await response.json();
        throw new Error(payload.message || "Failed to update user");
      }
      const payload: { user: ManagedUser } = await response.json();
      addNotification({
        kind: "info",
        message: `User ${payload.user.username} updated successfully`,
      });
      setUsers((prev: ManagedUser[]) =>
        prev.map((user: ManagedUser) =>
          user.username === payload.user.username ? payload.user : user,
        ),
      );
      await fetchUserDetails(payload.user.username);
    } catch (error) {
      handleError(error);
    }
  };

  return (
    <main style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>Phone Management Portal</h1>
      {notifications.map((note: Notification) => (
        <div
          key={note.id}
          role={note.kind === "error" ? "alert" : "status"}
          style={{
            backgroundColor: note.kind === "error" ? "#fee" : "#eef",
            border: "1px solid #ccd",
            borderRadius: "4px",
            padding: "0.75rem",
            marginBottom: "0.5rem",
          }}
        >
          {note.message}
        </div>
      ))}

      {loading && <p>Loading...</p>}

      {profile && (
        <section style={{ marginBottom: "2rem" }}>
          <h2>Welcome, {profile.username}</h2>
          <ul>
            <li>Email: {profile.email}</li>
            <li>Phone Number: {profile.phone_number}</li>
            <li>IMEI: {profile.imei}</li>
            <li>Role: {profile.role}</li>
          </ul>

          <form onSubmit={handleStatusUpdate} style={{ marginTop: "1rem" }}>
            <label>
              Update Status:
              <select
                value={newStatus}
                onChange={(event: ChangeEvent<HTMLSelectElement>) => {
                  const { value } = event.target;
                  setNewStatus(value ? (value as PhoneStatusValue) : "");
                }}
                style={{ marginLeft: "0.5rem" }}
              >
                {statusOptions.map((option: PhoneStatusValue) => (
                  <option key={option} value={option}>
                    {getStatusLabel(option)}
                  </option>
                ))}
              </select>
            </label>
            <button type="submit" style={{ marginLeft: "0.5rem" }}>
              Save
            </button>
          </form>

          <section style={{ marginTop: "1.5rem" }}>
            <h3>Status History</h3>
            {statusHistory.length === 0 ? (
              <p>No status updates yet.</p>
            ) : (
              <ul>
                {statusHistory.map((entry: StatusHistoryEntry) => (
                  <li key={entry.noted_at}>
                    {getStatusLabel(entry.status)} at {" "}
                    {new Date(entry.noted_at).toLocaleString()}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </section>
      )}

      {isManager && (
        <section style={{ marginBottom: "2rem" }}>
          <h2>Managed Users</h2>
          <table
            style={{
              borderCollapse: "collapse",
              width: "100%",
              marginBottom: "1rem",
            }}
          >
            <thead>
              <tr>
                <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
                  Username
                </th>
                <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
                  Email
                </th>
                <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
                  Role
                </th>
                <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {users.map((user: ManagedUser) => (
                <tr key={user.username}>
                  <td>{user.username}</td>
                  <td>{user.email}</td>
                  <td>{user.role}</td>
                  <td>
                    <button type="button" onClick={() => handleSelectUser(user.username)}>
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {selectedUser && (
            <div>
              <h3>Details for {selectedUser.user.username}</h3>
              <ul>
                <li>Email: {selectedUser.user.email}</li>
                <li>Phone: {selectedUser.user.phone_number}</li>
                <li>IMEI: {selectedUser.user.imei}</li>
                <li>Role: {selectedUser.user.role}</li>
              </ul>
              <h4>Status History</h4>
              {selectedUser.status_history.length === 0 ? (
                <p>No status updates recorded.</p>
              ) : (
                <ul>
                  {selectedUser.status_history.map(
                    (entry: StatusHistoryEntry) => (
                      <li key={entry.noted_at}>
                        {getStatusLabel(entry.status)} at {" "}
                        {new Date(entry.noted_at).toLocaleString()}
                      </li>
                    ),
                  )}
                </ul>
              )}

              {isAdmin && adminForm && (
                <form onSubmit={handleAdminUpdate} style={{ marginTop: "1rem" }}>
                  <fieldset
                    style={{
                      border: "1px solid #ccc",
                      borderRadius: "4px",
                      padding: "1rem",
                    }}
                  >
                    <legend>Edit User</legend>
                    <label style={{ display: "block", marginBottom: "0.5rem" }}>
                      Email
                      <input
                        type="email"
                        name="email"
                        value={adminForm.email}
                        onChange={handleAdminFormChange}
                        style={{ marginLeft: "0.5rem", width: "60%" }}
                        required
                      />
                    </label>
                    <label style={{ display: "block", marginBottom: "0.5rem" }}>
                      Phone Number
                      <input
                        type="tel"
                        name="phone_number"
                        value={adminForm.phone_number}
                        onChange={handleAdminFormChange}
                        style={{ marginLeft: "0.5rem", width: "60%" }}
                        required
                      />
                    </label>
                    <label style={{ display: "block", marginBottom: "0.5rem" }}>
                      IMEI
                      <input
                        type="text"
                        name="imei"
                        value={adminForm.imei}
                        onChange={handleAdminFormChange}
                        style={{ marginLeft: "0.5rem", width: "60%" }}
                        required
                      />
                    </label>
                    <label style={{ display: "block", marginBottom: "0.5rem" }}>
                      Role
                      <select
                        name="role"
                        value={adminForm.role}
                        onChange={handleAdminFormChange}
                        style={{ marginLeft: "0.5rem" }}
                      >
                        <option value="user">user</option>
                        <option value="manager">manager</option>
                        <option value="admin">admin</option>
                      </select>
                    </label>
                    <button type="submit">Save Changes</button>
                  </fieldset>
                </form>
              )}
            </div>
          )}
        </section>
      )}
    </main>
  );
}
