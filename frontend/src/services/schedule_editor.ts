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
    commitDraft: async (scenarioId: number): Promise<LessonError[]> => {
        const res = await privateApi.post(`/api/scenario/${scenarioId}/draft/lessons/apply/`);
        return res.data || [];
    }
};