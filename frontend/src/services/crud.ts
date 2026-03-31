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
const list = async (model: string, params: Record<string, any> = {}) => {
    const response = await privateApi.get(`/api/${model}/`, { params });
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
    search
}