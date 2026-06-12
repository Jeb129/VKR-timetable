
import type { MappedEvent } from "@/types/schedule";
import { publicApi } from "./axios";

export const scheduleViewService = {
    /**
     * LIST - Получение списка объектов с пагинацией и фильтрами (GET)
     */
    teacher: async (id:number, date_from:string,date_to:string): Promise<MappedEvent[]> => {
        const response = await publicApi.get(`/api/schedule/teacher/?teacher_id=${id}&date_from=${date_from}&date_to=${date_to}`);
        return response.data;
    },
    group: async (id:number, date_from:string,date_to:string): Promise<MappedEvent[]> => {
        const response = await publicApi.get(`/api/schedule/group/?group_id=${id}&date_from=${date_from}&date_to=${date_to}`);
        return response.data;
    },
    classroom: async (id:number, date_from:string,date_to:string): Promise<MappedEvent[]> => {
        const response = await publicApi.get(`/api/schedule/classroom/?classroom_id=${id}&date_from=${date_from}&date_to=${date_to}`);
        return response.data;
    },
};