import type { QueryParams, PaginatedResponse } from "@/types/ui";
import { privateApi, publicApi } from "./axios";

export const dbService = {
    /**
     * LIST - Получение списка объектов с пагинацией и фильтрами (GET)
     */
    list: async <T>(model: string, params: QueryParams = {}): Promise<PaginatedResponse<T>> => {
        const response = await publicApi.get(`/api/${model}/`, { params });
        return response.data;
    },

    /**
     * GET - Получение одной конкретной записи по ID (GET)
     */
    get: async <T>(model: string, id: number | string): Promise<T> => {
        const response = await publicApi.get(`/api/${model}/${id}/`);
        return response.data;
    },

    /**
     * SEARCH - Специализированный поиск (обычно POST /api/model/search/)
     * Используется, если логика поиска слишком сложная для GET-параметров
     */
    search: async <T>(model: string, data: Record<string, any>): Promise<T[]> => {
        const response = await publicApi.post(`/api/${model}/search/`, data);
        return response.data;
    },

    /**
     * CREATE - Создание новой записи (POST)
     */
    create: async <T>(model: string, data: Record<string, any>): Promise<T> => {
        const response = await privateApi.post(`/api/${model}/`, data);
        return response.data;
    },

    /**
     * UPDATE - Частичное обновление существующей записи (PATCH)
     */
    update: async <T>(model: string, id: number | string, data: Record<string, any>): Promise<T> => {
        const response = await privateApi.patch(`/api/${model}/${id}/`, data);
        return response.data;
    },

    /**
     * REMOVE - Удаление записи (DELETE)
     */
    remove: async (model: string, id: number | string): Promise<void> => {
        await privateApi.delete(`/api/${model}/${id}/`);
    },
};