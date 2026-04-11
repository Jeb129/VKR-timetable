import { privateApi } from "./axios";

const update = async (model: string, id: number, data: Record<string,any>) => {
    const response = await privateApi.patch(
        `/api/${model}/${id}/`,
        data
    )
    return response.data
}
const search = async (model: string, data: Record<string,any>) => {
    const response = await privateApi.post(
        `/${model}/search/`,
        data
    )
    return response.data
}
const create = async (model: string, data: Record<string, any>) => {
    const response = await privateApi.post(`/api/${model}/`, data);
    return response.data;
};
const list = async (model: string, params: Record<string, any> = {}) => {
    const response = await privateApi.get(`/api/${model}/`, { params });
    return response.data;
};
// Специальный метод для черновика (/api/scenario/ID/draft/?lesson_id=ID)
const updateDraft = async (scenarioId: number, lessonId: number, data: Record<string, any>) => {
    const response = await privateApi.put(
        `/api/scenario/${scenarioId}/draft/?lesson_id=${lessonId}`, 
        data
    );
    return response.data;
};
// Метод для публикации (/api/scenario/ID/draft/commit/)
const commitDraft = async (scenarioId: number) => {
    const response = await privateApi.post(`/api/scenario/${scenarioId}/draft/commit/`);
    return response.data;
};
const get = async (model: string, id: number) => {
    const response = await privateApi.get(
        `/api/${model}/${id}/`
    )
    return response.data
}

export const dbService = {
    update,
    get,
    list,
    create,
    search,
    updateDraft,
    commitDraft
}