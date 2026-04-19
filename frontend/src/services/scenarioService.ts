import { privateApi } from "./axios";
import type { Scenario } from "@/types/schedule";

export const scenarioService = {
    // Получить список всех сценариев
    getAll: async (): Promise<Scenario[]> => {
        const response = await privateApi.get("/api/scenarios/");
        return response.data;
    },

    // Создать новый сценарий
    create: async (name: string): Promise<Scenario> => {
        const response = await privateApi.post("/api/scenarios/", { name });
        return response.data;
    },

    // Обновить (например, переименовать или сделать активным)
    update: async (id: number, data: Partial<Scenario>): Promise<Scenario> => {
        const response = await privateApi.patch(`/api/scenarios/${id}/`, data);
        return response.data;
    },

    // Удалить сценарий
    remove: async (id: number): Promise<void> => {
        await privateApi.delete(`/api/scenarios/${id}/`);
    },

    // Копирование (клонирование) сценария
    copy: async (id: number): Promise<Scenario> => {
        const response = await privateApi.post(`/api/scenarios/${id}/copy/`);
        return response.data;
    },

    // Специальный метод для активации одной версии (сброс остальных сделает бэк)
    setActive: async (id: number): Promise<Scenario> => {
        const response = await privateApi.patch(`/api/scenarios/${id}/`, { is_active: true });
        return response.data;
    }
};