import type { PlannedCheckResult, PlannedGenerateResult } from "@/types/plannedlessons";
import { privateApi } from "./axios";
import type { GenerationStatusResponse, Scenario } from "@/types/schedule";

export const scenarioService = {
    // Запуск генерации
    startGeneration: async (id: number, config: any): Promise<Scenario> => {
        const response = await privateApi.post(`/api/scenarios/${id}/generation/start/`, config);
        return response.data;
    },

    // Остановка
    stopGeneration: async (id: number): Promise<void> => {
        await privateApi.post(`/api/scenarios/${id}/generation/stop/`);
    },

    // Поллинг статуса
    getGenStatus: async (id: number): Promise<GenerationStatusResponse> => {
        const response = await privateApi.get(`/api/scenarios/${id}/generation/status/`);
        return response.data;
    },

    // Копирование (клонирование) сценария
    copy: async (id: number): Promise<Scenario> => {
        const response = await privateApi.post(`/api/scenarios/${id}/copy/`);
        return response.data;
    },

    // Специальный метод для активации одной версии (сброс остальных сделает бэк)
    setActive: async (id: number,force: boolean = false): Promise<Scenario> => {
        const response = await privateApi.post(`/api/scenarios/${id}/activate`);
        return response.data;
    }
};

export const semesterService = {
    // Проверка готовности нагрузки
    checkPlanned: async (id: number): Promise<PlannedCheckResult> => {
        const response = await privateApi.get(`/api/semesters/${id}/plannedlessons/check/`);
        return response.data;
    },

    // Синхронизация нагрузки (generate)
    syncPlanned: async (id: number,force: boolean = false): Promise<PlannedGenerateResult> => {
        // УДАЛЯЕТ СУЩЕСТВУЮЩИЕ ПЛАНОВЫЕ ЗАНЯТИЯ!!!!!!
        const response = await privateApi.post(`/api/semesters/${id}/plannedlessons/generate/${force ? "?force=true" : ""}`);
        return response.data
    },
}