import type { RequestInstance } from "./request";

export interface SelectOption {
    value: string | number;
    label: string;
}

export interface SimpleEntity {
    id: number;
    name: string;
}

export interface RequestsPagination {
  count: number;
  results: RequestInstance[]
}

export interface RequestParams {
  page?: number;
  page_size?: number;
  status?: number;
  type?: number;
}

export interface PaginatedResponse<T> {
    count: number;
    next: string | null;
    previous: string | null;
    results: T[];
}

export type QueryParams = Record<string, string | number | boolean | undefined | null>;