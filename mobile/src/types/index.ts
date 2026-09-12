// Types mirror the backend contract (docs/CONTRACT.md + backend/app/schemas).
// Timestamps are ISO-8601 UTC strings; ids are UUID strings.

export type Role = 'SUPER_ADMIN' | 'COMPANY_ADMIN' | 'EMPLOYEE';

export type AttendanceStatus =
  | 'IN_PROGRESS'
  | 'ON_BREAK'
  | 'COMPLETED'
  | 'ABSENT'
  | 'PRESENT'
  | 'MISSED_PUNCH'
  | 'MANUAL_ADJUSTMENT';

export type BreakType = 'REGULAR' | 'LUNCH' | 'OTHER';

// UX-level attendance state derived from TodayState (not a backend enum).
export type UiAttendanceState = 'NOT_STARTED' | 'IN_PROGRESS' | 'ON_BREAK' | 'COMPLETED';

// ---- Response envelopes ----
export interface SuccessEnvelope<T> {
  success: true;
  data: T;
  pagination?: PaginationMeta;
}

export interface ErrorEnvelope {
  success: false;
  error: ApiErrorPayload;
}

export interface ApiErrorPayload {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

// ---- Auth ----
export interface TokenUser {
  id: string;
  email: string;
  role: Role;
  company_id: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: TokenUser;
}

export interface TokenPairResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ---- Me ----
export interface UserOut {
  id: string;
  email: string;
  phone: string | null;
  role: Role;
  status: string;
  company_id: string | null;
  last_login_at: string | null;
}

export interface EmployeeOut {
  id: string;
  user_id: string;
  company_id: string;
  employee_code: string;
  email: string | null;
  first_name: string;
  last_name: string;
  phone: string | null;
  department: string | null;
  designation: string | null;
  joining_date: string | null;
  status: string;
  created_at: string;
}

export interface CompanyOut {
  id: string;
  name: string;
  code: string;
  status: string;
  timezone: string;
  max_accuracy_meters: number;
  work_start_time: string | null;
  work_end_time: string | null;
  late_grace_minutes: number;
  standard_work_minutes: number;
  created_at: string;
}

export interface MeResponse {
  user: UserOut;
  employee: EmployeeOut | null;
  company: CompanyOut | null;
}

// ---- Attendance ----
export interface BreakOut {
  id: string;
  break_type: string;
  started_at: string;
  ended_at: string | null;
  duration_minutes: number | null;
}

export interface AttendanceOut {
  id: string;
  employee_id: string;
  company_id: string;
  attendance_date: string;
  punch_in_at: string | null;
  punch_in_latitude: number | null;
  punch_in_longitude: number | null;
  punch_in_accuracy: number | null;
  punch_in_distance_meters: number | null;
  punch_out_at: string | null;
  punch_out_latitude: number | null;
  punch_out_longitude: number | null;
  punch_out_accuracy: number | null;
  punch_out_distance_meters: number | null;
  total_work_minutes: number | null;
  status: AttendanceStatus;
  breaks: BreakOut[];
}

export interface TodayState {
  date: string;
  status: AttendanceStatus;
  on_break: boolean;
  current_work_minutes: number;
  server_time: string;
  attendance: AttendanceOut | null;
}

export interface LocationInfo {
  distance_meters: number;
  allowed_radius_meters: number;
  accuracy: number;
  within_radius: boolean;
}

export interface PunchResult {
  attendance: AttendanceOut;
  location: LocationInfo;
  current_work_minutes: number;
  on_break: boolean;
}

// GPS payload sent to punch/break endpoints.
export interface LocationPayload {
  latitude: number;
  longitude: number;
  accuracy: number;
  client_timestamp?: string;
}
