// TypeScript interfaces mirroring the backend contract (docs/CONTRACT.md).
// These are the canonical client-side shapes.

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

// ---- Response envelopes ----
export interface Pagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface ApiSuccess<T> {
  success: true;
  data: T;
  pagination?: Pagination;
}

export interface ApiErrorBody {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface ApiError {
  success: false;
  error: ApiErrorBody;
}

export type ApiEnvelope<T> = ApiSuccess<T> | ApiError;

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

// ---- User ----
export interface User {
  id: string;
  email: string;
  phone: string | null;
  role: Role;
  status: string;
  company_id: string | null;
  last_login_at: string | null;
}

// ---- Company / Location ----
export interface Company {
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

export interface Location {
  id: string;
  company_id: string;
  name: string;
  address: string | null;
  latitude: number;
  longitude: number;
  allowed_radius_meters: number;
  is_primary: boolean;
  status: string;
}

export interface CompanyCreatePayload {
  name: string;
  code: string;
  timezone?: string;
  admin_email: string;
  admin_password: string;
  location: {
    name: string;
    address?: string;
    latitude: number;
    longitude: number;
    allowed_radius_meters?: number;
  };
}

export interface CompanyUpdatePayload {
  name?: string;
  status?: string;
  timezone?: string;
  max_accuracy_meters?: number;
  work_start_time?: string;
  work_end_time?: string;
  late_grace_minutes?: number;
  standard_work_minutes?: number;
}

export interface LocationCreatePayload {
  name: string;
  address?: string;
  latitude: number;
  longitude: number;
  allowed_radius_meters?: number;
}

export interface LocationUpdatePayload {
  name?: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  allowed_radius_meters?: number;
  is_primary?: boolean;
  status?: string;
}

// ---- Employee ----
export interface Employee {
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

export interface EmployeeCreatePayload {
  email: string;
  password: string;
  phone?: string;
  first_name: string;
  last_name: string;
  employee_code: string;
  department?: string;
  designation?: string;
  joining_date?: string;
}

export interface EmployeeUpdatePayload {
  phone?: string;
  first_name?: string;
  last_name?: string;
  department?: string;
  designation?: string;
  joining_date?: string;
  status?: string;
}

// ---- Attendance ----
export interface Break {
  id: string;
  break_type: string;
  started_at: string;
  ended_at: string | null;
  duration_minutes: number | null;
}

export interface Attendance {
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
  status: string;
  breaks: Break[];
}

// Admin list row (flattened with employee identity for tables/CSV)
export interface AttendanceAdminRow {
  id: string;
  employee_id: string;
  employee_code: string;
  employee_name: string;
  department: string | null;
  attendance_date: string;
  punch_in_at: string | null;
  punch_out_at: string | null;
  break_minutes: number;
  total_work_minutes: number | null;
  status: string;
}

// ---- Dashboard / System ----
export interface DashboardSummary {
  date: string;
  total_employees: number;
  present: number;
  absent: number;
  in_progress: number;
  on_break: number;
  completed: number;
}

export interface SystemStats {
  companies: number;
  users: number;
  employees: number;
  attendance_today: number;
}

// ---- /me ----
export interface MeResponse {
  user: User;
  employee: Employee | null;
  company: Company | null;
}

// ---- Reports ----
export type ReportType = 'daily' | 'monthly' | 'employee' | 'late' | 'missing' | 'hours';

export interface ReportRow {
  attendance_date: string;
  employee_code: string;
  employee_name: string;
  department: string;
  punch_in_at: string;
  punch_out_at: string;
  break_minutes: number;
  total_work_minutes: number | '';
  status: string;
}
