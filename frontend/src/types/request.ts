import type { RequestStatus, RequestType } from "./enums";
import type { SimpleEntity } from "./ui";


// Детали заявок (чтение)
export interface ExcludedTimeslotDetails {
  teacher: SimpleEntity;
  timeslot: string; // StringRelatedField
}

export interface ClassroomPreferenceDetails {
  teacher: SimpleEntity;
  discipline: string;
  lesson_type: string;
  classroom: SimpleEntity;
}

export interface BookingDetails {
  classroom: SimpleEntity;
  booking_type: string;
  date_start: string; // ISO DateTime
  date_end: string;   // ISO DateTime
}

export interface ScheduleAdjustmentDetails {
  date: string;       // ISO Date
  lesson: string;
  timeslot: string;
  classroom: SimpleEntity | null;
}

interface BaseRequest {
  id: number;
  user: SimpleEntity;
  description: string;
  status: { id: RequestStatus; name: string };
  admin_comment: string | null;
  created_at: string;
  can_approve: boolean;
  can_edit: boolean;
  can_delete: boolean;

}

export type RequestInstance =
  | (BaseRequest & { type: { id: RequestType.EXCLUDED_TIMESLOT; name: string }; details: ExcludedTimeslotDetails })
  | (BaseRequest & { type: { id: RequestType.CLASSROOM_PREFERENCE; name: string }; details: ClassroomPreferenceDetails })
  | (BaseRequest & { type: { id: RequestType.BOOKING; name: string }; details: BookingDetails })
  | (BaseRequest & { type: { id: RequestType.SCHEDULE_ADJUSTMENT; name: string }; details: ScheduleAdjustmentDetails[] }); 


// Создание заявок
export interface ExcludedTimeslotCreate {
  teacher: number;
  timeslot: number;
}

export interface ClassroomPreferenceCreate {
  teacher: number;
  discipline: number;
  lesson_type: number;
  classroom: number;
}

export interface BookingCreate {
  classroom: number;
  booking_type: number;
  date_start: string;
  date_end: string;
}

export interface ScheduleAdjustmentCreate {
  date: string;
  lesson: number;
  timeslot: number | null;
  classroom: number | null;
}

// Тип для отправки на сервер
export interface RequestCreatePayload {
  description: string;
  type: RequestType;
  details: 
    | ExcludedTimeslotCreate 
    | ClassroomPreferenceCreate 
    | BookingCreate 
    | ScheduleAdjustmentCreate[]; // Для корректировок — массив объектов
}