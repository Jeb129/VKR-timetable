import type { ConstraintError } from "@/types/schedule"
import { privateApi } from "./axios"

const moveLesson = async (scenario_id: number, lesson_id: number, new_timeslot_id: number): Promise<ConstraintError[]> => {
    return (await privateApi.put(`/scenario_id/${scenario_id}/draft/?lesson_id=${lesson_id}`,
        {
            timeslot: new_timeslot_id
        }
    )).data
}

const createLesson = async (scenario_id: number, data: Record<string,any>) => {
    return (await privateApi.post(`/scenario_id/${scenario_id}/draft/`,data)).data
}

export const scheduleDraftService = {
    createLesson,
    moveLesson
} 