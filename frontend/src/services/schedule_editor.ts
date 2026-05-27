// services/schedule_editor.ts
import type { LessonError } from "@/types/constraint";
import { privateApi } from "./axios";
import type { Lesson } from "@/types/schedule";

export const scheduleDraftService = {
    // Получение уроков с учетом черновиков
    getLessons: async (scenarioId: number, params: { 
            group_id?: number; 
            teacher_id?: number; 
            room_id?: number,
            with_errors?: boolean
        }): Promise<{lessons: Lesson[], errors?: LessonError[]}> => {

        const query = new URLSearchParams(params as any).toString();
        const res = await privateApi.get(`/api/scenario/${scenarioId}/draft/lessons/?${query}`);
        return res.data;
    },

    // Универсальное обновление (перенос или смена аудитории)
    updateLesson: async (scenarioId: number, lessonId: string, diff: Record<string, any>): Promise<LessonError[]> => {
        const res = await privateApi.patch(`/api/scenario/${scenarioId}/draft/lessons/${lessonId}/`, diff);
        return res.data || [];
    },

    bulkUpdateLessons: async (scenario_id: number, updates: {id: string, [key: string]: any}[]): Promise<LessonError[]> => {
        return (await privateApi.patch(`/api/scenario/${scenario_id}/draft/lessons/bulk-patch/`, updates)).data;
    },

    // Создание нового урока в черновике
    createLesson: async (scenarioId: number, data: Partial<Lesson>): Promise<LessonError> => {
        const res = await privateApi.post(`/api/scenario/${scenarioId}/draft/lessons/`, data);
        return res.data; // Предполагаем, что бэк вернет созданный объект и ошибки
    },

    // Удаление (пометка на удаление)
    deleteLesson: async (scenarioId: number, lessonId: string): Promise<void> => {
        await privateApi.delete(`/api/scenario/${scenarioId}/draft/lessons/${lessonId}/`);
    },

    // Сохранение всех изменений в БД
    commitDraft: async (scenarioId: number, lessonId?: string): Promise<LessonError[]> => {
        const res = await privateApi.post(`/api/scenario/${scenarioId}/draft/lessons/${lessonId ? lessonId + "/" : ""}apply/`);
        return res.data || [];
    },

    //получение корзины с парами 
    getTrash: async (scenarioId: number): Promise<Lesson[]> => {
        const res = await privateApi.get(`/api/scenario/${scenarioId}/draft/lessons/trash/`);
        return res.data;
    },

    clearDraft: async (scenarioId: number, lessonId?: string): Promise<Lesson | null> => {
        const res = await privateApi.delete(`/api/scenario/${scenarioId}/draft/lessons/${lessonId ? lessonId + "/" : ""}clear/`)
        console.log(res.data)
        return res.data
    },

    //Получить только измененные занятия (добавим флаг only_changes)
    getAllDraftLessons: async (scenarioId: number): Promise<{lessons: Lesson[]}> => {
        const res = await privateApi.get(`/api/scenario/${scenarioId}/draft/lessons/`);
        return res.data;
    },
    //глобальная проверка всего сценария на конфликты 
    getSummary: async (scenarioId: number): Promise<{
        changes: Lesson[], 
        deleted: Lesson[], 
        errors: LessonError[] 
    }> => {
        const res = await privateApi.get(`/api/scenario/${scenarioId}/draft/lessons/summary/`);
        return res.data;
    },
    // Опубликовать всё (Насрать из редиса в БД)
    applyAll: async (scenarioId: number): Promise<void> => {
        await privateApi.post(`/api/scenario/${scenarioId}/draft/lessons/apply/`);
    },
    // Сбросить всё
    clearAllDrafts: async (scenarioId: number): Promise<void> => {
        await privateApi.delete(`/api/scenario/${scenarioId}/draft/lessons/clear/`);
    }
};