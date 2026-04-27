export const  CONSTRAINT_ERROR_TYPES: Record<number,string> = {
    0: "Ошибка",
    1: "Предупреждение"
}
export type ErrorKey = keyof typeof CONSTRAINT_ERROR_TYPES; 

export const  WEEK_DAYS: Record<number,string[]> = {
    1: ["Понедельник","Пн"],
    2: ["Вторник","Вт"],
    3: ["Среда","Ср"],
    4: ["Четверг","Чт"],
    5: ["Пятница","Пт"],
    6: ["Суббота","Сб"],
    7: ["Воскресенье","Вс"],
}
export type DayKey = keyof typeof WEEK_DAYS; 