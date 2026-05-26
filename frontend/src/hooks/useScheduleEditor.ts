// hooks/useScheduleEditor.ts
import { useState, useCallback, useMemo } from "react";
import { scheduleDraftService } from "@/services/schedule_editor";
import type { Lesson, Timeslot } from "@/types/schedule";
import type { LessonError } from "@/types/constraint";

export const useScheduleEditor = (scenarioId: number) => {
    const [lessons, setLessons] = useState<Lesson[]>([]);
    const [lessonErrors, setLessonErrors] = useState<LessonError[]>([]);
    const [isChecking, setIsChecking] = useState(false);
    const [pendingIds, setPendingIds] = useState<Set<string>>(new Set());

    const getLookupKey = (timeslot: Timeslot) => 
        `${String(timeslot.day)}-${String(timeslot.order_number)}-${String(timeslot.week_num)}`;

    const loadLessons = useCallback(async (filters: any) => {
        const data = await scheduleDraftService.getLessons(scenarioId, filters);
        setLessons(data.lessons || []);
        setLessonErrors(data.errors?.filter(er => er.errors != null) || []);
    }, [scenarioId]);

    const moveLesson = async (lessonId: string, targetSlot: Timeslot) => {
        // 1. Оптимистичное обновление
        setLessons(prev => prev.map(l => {
            if (String(l.id) !== String(lessonId)) return l;
            
            // Формируем временный draft_info для визуальной индикации (оранжевый цвет)
            // Мы не знаем 'was'/'now' объектов до ответа сервера, поэтому ставим заглушку
            const currentChanges = l.draft_info?.changes.filter(c => c.field !== 'timeslot') || [];
            
            return {
                ...l,
                timeslot: targetSlot,
                draft_info: {
                    is_new: l.draft_info?.is_new || false,
                    changes: [
                        ...currentChanges,
                        { field: 'timeslot', was: null, now: null } 
                    ]
                }
            };
        }));

        setPendingIds(prev => new Set(prev).add(lessonId));

        try {
            setIsChecking(true);
            const response = await scheduleDraftService.updateLesson(
                scenarioId,
                lessonId,
                { timeslot: targetSlot.id }
            );

            // Если сервер вернул обновленный объект занятия с правильным draft_info — обновляем его
            // (Предполагается, что updateLesson возвращает LessonError[], где есть актуальный lesson)
            if (response.length > 0) {
                const updatedLesson = response.find(e => String(e.lesson.id) === String(lessonId))?.lesson;
                if (updatedLesson) {
                    setLessons(prev => prev.map(l => String(l.id) === String(lessonId) ? updatedLesson : l));
                }
            }

            setLessonErrors(prev => {
                const checkedIds = new Set(response.map(e => String(e.lesson.id)));

                // Оставляем ошибки тех занятий, которые НЕ участвовали в текущей проверке
                const otherErrors = prev.filter(e => !checkedIds.has(String(e.lesson.id)));

                // Из ответа сервера берем ТОЛЬКО те LessonError, где реально есть ошибки
                const newActualErrors = response.filter(e => e.errors && e.errors.length > 0);

                return [...otherErrors, ...newActualErrors];
            });
        } catch (err) {
            alert("Ошибка соединения с сервером");
        } finally {
            setIsChecking(false);
            setPendingIds(prev => {
                const next = new Set(prev);
                next.delete(lessonId);
                return next;
            });
        }
    };

    const swapLessons = async (lessonId1: string, lessonId2: string) => {
        const lesson1 = lessons.find(l => String(l.id) === String(lessonId1));
        const lesson2 = lessons.find(l => String(l.id) === String(lessonId2));
        if (!lesson1 || !lesson2) return;

        const slot1 = { ...lesson1.timeslot };
        const slot2 = { ...lesson2.timeslot };

        // 1. Оптимистичный Swap
        setLessons(prev => prev.map(l => {
            const isL1 = String(l.id) === String(lessonId1);
            const isL2 = String(l.id) === String(lessonId2);
            if (!isL1 && !isL2) return l;

            return {
                ...l,
                timeslot: isL1 ? slot2 : slot1,
                draft_info: {
                    is_new: l.draft_info?.is_new || false,
                    changes: [
                        ...(l.draft_info?.changes.filter(c => c.field !== 'timeslot') || []),
                        { field: 'timeslot', was: null, now: null }
                    ]
                }
            };
        }));

        setIsChecking(true);
        try {
            const response = await scheduleDraftService.bulkUpdateLessons(scenarioId, [
                { id: lessonId1, timeslot: slot2.id },
                { id: lessonId2, timeslot: slot1.id }
            ]);

            setLessonErrors(prev => {
                const checkedIds = new Set(response.map(e => String(e.lesson.id)));

                // Оставляем ошибки тех занятий, которые НЕ участвовали в текущей проверке
                const otherErrors = prev.filter(e => !checkedIds.has(String(e.lesson.id)));

                // Из ответа сервера берем ТОЛЬКО те LessonError, где реально есть ошибки
                const newActualErrors = response.filter(e => e.errors && e.errors.length > 0);

                return [...otherErrors, ...newActualErrors];
            });
            // Важно: после bulkUpdate хорошо бы подтянуть актуальные draft_info
            // loadLessons({}); 
        } catch (err) {
            console.error("Bulk update failed", err);
        } finally {
            setIsChecking(false);
        }
    };

    const revertLesson = async (lessonId: string) => {
        try {
            const lesson = await scheduleDraftService.clearDraft(scenarioId, lessonId);
                console.log(lesson)
            if (lesson) {
                console.log("Обновление после удаления")
                setLessons(prev => prev.map(l => String(l.id) === String(lesson.id) ? lesson : l));
                // Очищаем ошибки для этого занятия, так как оно вернулось в исходное состояние
                setLessonErrors(prev => prev.filter(e => String(e.lesson.id) !== String(lessonId)));
            }
        } catch (err) {
            alert("Ошибка при отмене изменений");
        }
    };

    const lessonsLookup = useMemo(() => {
        const map: Record<string, Lesson> = {};
        lessons.forEach(l => {
            map[getLookupKey(l.timeslot)] = l;
        });
        return map;
    }, [lessons]);

    const checkAll = async () => {
        setIsChecking(true);
        try {
            const errors = await scheduleDraftService.checkScenario(scenarioId);
            setLessonErrors(errors.filter(e => e.errors && e.errors.length > 0));
        } finally {
            setIsChecking(false);
        }
    };
    const clearAll = async () => {
        await scheduleDraftService.clearAllDrafts(scenarioId);
        await loadLessons({}); // Перезагружаем "чистые" данные из БД
    };

    // Список всех измененных или новых занятий для Панели изменений
    const draftChanges = useMemo(() => {
        console.log("Обновляем список изменений")

        return lessons.filter(l => l.draft_info !== null);
    }, [lessons]);

    return {
        lessons,
        lessonsLookup,
        lessonErrors,
        draftChanges,
        pendingIds,
        isChecking,
        getLookupKey,
        loadLessons,
        moveLesson,
        swapLessons,
        setLessons,
        checkAll,
        clearAll,
        revertLesson
    };
};