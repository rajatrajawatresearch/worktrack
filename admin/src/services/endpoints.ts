// Typed endpoint wrappers. One function per contract endpoint used by the admin
// app. Never sends company_id in bodies; SUPER_ADMIN scoping is passed as the
// ?company_id= query param where the contract allows it.
import type {
  Attendance,
  AttendanceAdminRow,
  Company,
  CompanyCreatePayload,
  CompanyUpdatePayload,
  DashboardSummary,
  Employee,
  EmployeeCreatePayload,
  EmployeeUpdatePayload,
  Location,
  LocationCreatePayload,
  LocationUpdatePayload,
  ReportRow,
  ReportType,
  SystemStats,
} from '../types';
import { downloadBlob, get, getList, patch, post } from './api';
import type { ListResult, Query } from './api';

// ---- Dashboard & System ----
export function getDashboardSummary(params: {
  date?: string;
  company_id?: string;
}): Promise<DashboardSummary> {
  return get<DashboardSummary>('/dashboard/summary', params);
}

export function getSystemStats(): Promise<SystemStats> {
  return get<SystemStats>('/system/stats');
}

// ---- Admin attendance ----
export function listAttendance(params: {
  company_id?: string;
  date?: string;
  employee_id?: string;
  department?: string;
  status?: string;
  page?: number;
  page_size?: number;
}): Promise<ListResult<AttendanceAdminRow>> {
  return getList<AttendanceAdminRow>('/attendance', params as Query);
}

export function getAttendanceDetail(id: string, companyId?: string): Promise<Attendance> {
  return get<Attendance>(`/attendance/${id}`, companyId ? { company_id: companyId } : undefined);
}

// ---- Companies ----
export function listCompanies(params: {
  page?: number;
  page_size?: number;
}): Promise<ListResult<Company>> {
  return getList<Company>('/companies', params as Query);
}

export function createCompany(payload: CompanyCreatePayload): Promise<Company> {
  return post<Company>('/companies', payload);
}

export function getCompany(id: string): Promise<Company> {
  return get<Company>(`/companies/${id}`);
}

export function updateCompany(id: string, payload: CompanyUpdatePayload): Promise<Company> {
  return patch<Company>(`/companies/${id}`, payload);
}

export function listLocations(companyId: string): Promise<Location[]> {
  return get<Location[]>(`/companies/${companyId}/locations`);
}

export function createLocation(companyId: string, payload: LocationCreatePayload): Promise<Location> {
  return post<Location>(`/companies/${companyId}/locations`, payload);
}

export function updateLocation(
  companyId: string,
  locId: string,
  payload: LocationUpdatePayload,
): Promise<Location> {
  return patch<Location>(`/companies/${companyId}/locations/${locId}`, payload);
}

// ---- Employees ----
export function listEmployees(params: {
  company_id?: string;
  search?: string;
  department?: string;
  status?: string;
  page?: number;
  page_size?: number;
}): Promise<ListResult<Employee>> {
  return getList<Employee>('/employees', params as Query);
}

export function createEmployee(payload: EmployeeCreatePayload, companyId?: string): Promise<Employee> {
  return post<Employee>('/employees', payload, companyId ? { company_id: companyId } : undefined);
}

export function getEmployee(id: string, companyId?: string): Promise<Employee> {
  return get<Employee>(`/employees/${id}`, companyId ? { company_id: companyId } : undefined);
}

export function updateEmployee(
  id: string,
  payload: EmployeeUpdatePayload,
  companyId?: string,
): Promise<Employee> {
  return patch<Employee>(`/employees/${id}`, payload, companyId ? { company_id: companyId } : undefined);
}

export function resetEmployeePassword(
  id: string,
  newPassword: string,
  companyId?: string,
): Promise<{ reset: boolean }> {
  return post<{ reset: boolean }>(
    `/employees/${id}/reset-password`,
    { new_password: newPassword },
    companyId ? { company_id: companyId } : undefined,
  );
}

export function getEmployeeAttendance(
  id: string,
  params: { from?: string; to?: string; page?: number; page_size?: number; company_id?: string },
): Promise<ListResult<Attendance>> {
  return getList<Attendance>(`/employees/${id}/attendance`, params as Query);
}

// ---- Reports ----
export function getReportJson(params: {
  type: ReportType;
  from?: string;
  to?: string;
  employee_id?: string;
  company_id?: string;
  page?: number;
  page_size?: number;
}): Promise<ListResult<ReportRow>> {
  return getList<ReportRow>('/reports/attendance', { ...params, format: 'json' } as Query);
}

export function downloadReportCsv(params: {
  type: ReportType;
  from?: string;
  to?: string;
  employee_id?: string;
  company_id?: string;
}): Promise<void> {
  const filename = `attendance_${params.type}.csv`;
  return downloadBlob('/reports/attendance', { ...params, format: 'csv' } as Query, filename);
}
