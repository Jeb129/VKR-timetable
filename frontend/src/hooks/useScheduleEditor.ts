// hooks/useScheduleEditor.ts
import { useState, useCallback, useMemo } from "react";
import { scheduleDraftService } from "@/services/schedule_editor";
import type { Lesson, Timeslot } from "@/types/schedule";
import type { LessonError } from "@/types/constraint";
import { da } from "date-fns/locale";

export const useScheduleEditor = (scenarioId: number) => {
    const [lessons, setLessons] = useState<Lesson[]>([]);
    const [lessonErrors, setErrorsMap] = useState<LessonError[]>([]);
    const [isChecking, setIsChecking] = useState(false);

    // Множество ID уроков, которые сейчас находятся в процессе проверки на сервере
    const [pendingIds, setPendingIds] = useState<Set<string>>(new Set());

    const loadLessons = useCallback(async (filters: any) => {
        const data = await scheduleDraftService.getLessons(scenarioId, filters);
        setLessons(data.lessons || []);
        setErrorsMap(data.errors || [])
    }, [scenarioId]);

    const moveLesson = async (lessonId: string, targetSlot: Timeslot) => {

        // 1. Оптимистичное обновление
        // setLessons(prev => prev.map(l => {
        //     if (l.id !== lessonId) return l;
        //     console.log(l)
        //     // Формируем новые диффы локально
        //     const otherDiffs = l.draft_diffs?.filter(d => d.field !== 'timeslot') || [];
        //     const newDiffs = [...otherDiffs, { field: 'timeslot', value: targetSlot.id }];
        //     return {
        //         ...l,
        //         timeslot: targetSlot, // Сразу меняем объект таймслота
        //         draft_diffs: newDiffs
        //     };
        // }));


        setLessons(prev => prev.map(l => {
            if (l.id !== lessonId) return l;
            return {
                ...l,
                timeslot: { ...targetSlot }, // Глубокое копирование слота
                // Формируем диффы, чтобы карточка сразу стала "оранжевой"
                draft_diffs: [
                    ...(l.draft_diffs?.filter(d => d.field !== 'timeslot') || []),
                    { field: 'timeslot', value: targetSlot.id }
                ]
            };
        }));

        // Добавляем в очередь проверки
        setPendingIds(prev => new Set(prev).add(lessonId));

        try {
            // 3. Отправляем запрос (который идет 2-3 секунды)
            setIsChecking(true)
            const serverErrors = await scheduleDraftService.updateLesson(
                scenarioId,
                lessonId,
                { timeslot: targetSlot.id }
            );

            setErrorsMap(prev => {
                const updatedLessonIds = new Set(serverErrors.map(e => e.lesson.id));

                // 1. оставляем только ошибки, которых нет в полученном ответе
                const filtered = prev.filter(e => !updatedLessonIds.has(e.lesson.id));

                // 2. добавляем новые ошибки
                return [...filtered, ...serverErrors];
            });
        } catch (err) {
            // 5. Откат если сервер ответил жесткой ошибкой (например, 500)
            alert("Ошибка соединения с сервером");
        } finally {
            setIsChecking(false)

            // Убираем из очереди проверки
            setPendingIds(prev => {
                const next = new Set(prev);
                next.delete(lessonId);
                return next;
            });
        }
    };


    // Lookup теперь использует вложенный объект timeslot
    const lessonsLookup = useMemo(() => {
        const map: Record<string, Lesson> = {};
        lessons.map(l => {
            const key = `${String(l.timeslot.day)}-${String(l.timeslot.order_number)}-${String(l.timeslot.week_num)}`;
            map[key] = l;
        });
        return map;
    }, [lessons]);

    return {
        lessons,
        lessonsLookup,
        lessonErrors,
        isChecking,
        loadLessons,
        moveLesson,
        setLessons
    };
};