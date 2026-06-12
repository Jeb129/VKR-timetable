import { privateApi } from "@/services/axios"; // импорт вашего клиента
import { RequestType } from "@/types/enums";
import type { 
  RequestInstance, 
  RequestCreatePayload,
} from "@/types/request"; 
import type { RequestParams, RequestsPagination } from "@/types/ui";

export const requestService = {
  /**
   * Получить список всех заявок (с учетом прав доступа на бэкенде)
   */
  getAll: async (params: RequestParams): Promise<RequestsPagination> => {
    const response = await privateApi.get<RequestsPagination>("/api/requests/", {
      params: params // Передаем параметры здесь
    });
    return response.data;
  },
  /**
   * Получить детальную информацию об одной заявке
   */
  getById: async (id: number): Promise<RequestInstance> => {
    const response = await privateApi.get<RequestInstance>(`/api/requests/${id}/`);
    return response.data;
  },

  /**
   * Создать новую заявку. 
   * Payload должен содержать description, type и объект details.
   */
  create: async (payload: RequestCreatePayload): Promise<RequestInstance> => {
    const response = await privateApi.post<RequestInstance>("/api/requests/", payload);
    return response.data;
  },

  /**
   * Обновить заявку
   */
  update: async (id: number, data: Partial<RequestCreatePayload>): Promise<RequestInstance> => {
    const response = await privateApi.patch<RequestInstance>(`/api/requests/${id}/`, data);
    return response.data;
  },

  /**
   * Удалить заявку
   */
  remove: async (id: number): Promise<void> => {
    await privateApi.delete(`/api/requests/${id}/`);
  },

  /**
   * Одобрить заявку (для модераторов)
   * @param adminComment - необязательный комментарий
   */
  approve: async (id: number, adminComment?: string): Promise<RequestInstance> => {
    const response = await privateApi.post<RequestInstance>(`/api/requests/${id}/approve/`, {
      admin_comment: adminComment
    });
    return response.data;
  },

  /**
   * Отклонить заявку (для модераторов)
   * @param adminComment - обязательный комментарий
   */
  reject: async (id: number, adminComment: string): Promise<RequestInstance> => {
    const response = await privateApi.post<RequestInstance>(`/api/requests/${id}/reject/`, {
      admin_comment: adminComment
    });
    return response.data;
  }
};

/**
 * Проверка на тип "Исключенный временной слот"
 */
export const isExcludedTimeslotRequest = (req: RequestInstance): req is Extract<RequestInstance, { type: { id: RequestType.EXCLUDED_TIMESLOT } }> => {
  return req.type.id === RequestType.EXCLUDED_TIMESLOT;
};

/**
 * Проверка на тип "Предпочтение по аудитории"
 */
export const isClassroomPreferenceRequest = (req: RequestInstance): req is Extract<RequestInstance, { type: { id: RequestType.CLASSROOM_PREFERENCE } }> => {
  return req.type.id === RequestType.CLASSROOM_PREFERENCE;
};

/**
 * Проверка на тип "Бронирование"
 */
export const isBookingRequest = (req: RequestInstance): req is Extract<RequestInstance, { type: { id: RequestType.BOOKING } }> => {
  return req.type.id === RequestType.BOOKING;
};

/**
 * Проверка на тип "Корректировка расписания" (ВАЖНО: здесь details — массив)
 */
export const isScheduleAdjustmentRequest = (req: RequestInstance): req is Extract<RequestInstance, { type: { id: RequestType.SCHEDULE_ADJUSTMENT } }> => {
  return req.type.id === RequestType.SCHEDULE_ADJUSTMENT;
};