export type Role = "user" | "manager" | "admin";

export type PhoneStatusValue = "online" | "sold" | "stolen" | "disposed";

export interface UserProfile {
  username: string;
  email: string;
  phone_number: string;
  imei: string;
  role: Role;
}

export interface StatusHistoryEntry {
  status: PhoneStatusValue;
  noted_at: string;
}

export interface ManagedUser {
  username: string;
  email: string;
  phone_number: string;
  imei: string;
  role: Role;
}

export interface ManagedUserDetails {
  user: ManagedUser;
  status_history: StatusHistoryEntry[];
}

export type NotificationKind = "error" | "info";

export interface Notification {
  id: string;
  kind: NotificationKind;
  message: string;
}