import { privateApi } from "./axios";

const update = async (model: string, id: number, data: Record<string,any>) => {
    const response = await privateApi.patch(
        `/${model}/?id=${id}`,
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
const get = async (model: string, id: number) => {
    const response = await privateApi.get(
        `/${model}/?id=${id}`
    )
    return response.data
}

export const dbService = {
    update,
    get,
    search
}