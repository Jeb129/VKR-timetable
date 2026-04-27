import type { ConstraintError, Lesson } from "@/types/schedule"
import { privateApi } from "./axios"

const getGroupLessons = async (scenario_id: number, group_id:number): Promise<Lesson[]> => {
    return (await privateApi.get(`/api/scenario/${scenario_id}/draft/lessons/?group_id=${group_id}`)).data
}
const getTeacherLessons = async (scenario_id: number, teacher_id:number): Promise<Lesson[]> => {
    return (await privateApi.get(`/api/scenario/${scenario_id}/draft/lessons/?teacher_id=${teacher_id}`)).data
}



const moveLesson = async (scenario_id: number, lesson_id: number, new_timeslot_id: number): Promise<ConstraintError[]> => {
    return (await privateApi.patch(`/api/scenario/${scenario_id}/draft/lessons/${lesson_id}/`,
        {
            timeslot: new_timeslot_id
        }
    )).data.errors
}

const createLesson = async (scenario_id: number, data: Record<string,any>) => {
    return (await privateApi.post(`/scenario_id/${scenario_id}/draft/`,data)).data
}

export const scheduleDraftService = {
    getGroupLessons,
    getTeacherLessons,
    createLesson,
    moveLesson
} 