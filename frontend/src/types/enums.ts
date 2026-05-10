export const  CONSTRAINT_ERROR_TYPES: Record<number,string> = {
    0: "Ошибка",
    1: "Предупреждение"
}
export type ErrorKey = keyof typeof CONSTRAINT_ERROR_TYPES; 

export const DAYS = [
    { id: 1, name: "Понедельник", short_name: "Пн" },
    { id: 2, name: "Вторник", short_name: "Вт" },
    { id: 3, name: "Среда", short_name: "Ср" },
    { id: 4, name: "Четверг", short_name: "Чт" },
    { id: 5, name: "Пятница", short_name: "Пт" },
    { id: 6, name: "Суббота", short_name: "Сб" },
    { id: 6, name: "Воскресенье", short_name: "Вс" },
] as const;