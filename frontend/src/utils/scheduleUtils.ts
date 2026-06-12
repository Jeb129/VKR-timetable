// utils/scheduleUtils.ts
import { type Lesson } from "@/types/schedule";

/**
 * Проверяет, изменено ли конкретное поле в занятии
 */
export const isFieldModified = (lesson: Lesson, fieldName: string): boolean => {
    return !!lesson.draft_info?.changes.some(change => change.field === fieldName);
};

/**
 * Возвращает объект изменения для поля, если оно есть
 */
export const getFieldChange = (lesson: Lesson, fieldName: string) => {
    return lesson.draft_info?.changes.find(change => change.field === fieldName);
};

/**
 * Статус занятия для стилизации
 */
export const getLessonDraftStatus = (lesson: Lesson) => {
    if (!lesson.draft_info) return 'none';
    if (lesson.draft_info.is_new) return 'new';
    if (lesson.draft_info.changes.length > 0) return 'modified';
    return 'none';
};