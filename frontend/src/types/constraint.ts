import type { Lesson } from "./schedule";

export interface ConstraintError {
    name: string;
    penalty: number;
    message: string;
    data: any;
    // data: Record<string,any> | any[] | null
}

export interface LessonError {
    lesson: Lesson;
    errors?: ConstraintError[]
}

