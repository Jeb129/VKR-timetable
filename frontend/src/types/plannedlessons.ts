import type { SimpleEntity } from "./ui";

export interface PlannedCheckResult {
    status: 'ok' | 'warning';
    message: string;
    uncovered_data?: SimpleEntity[];
}

export interface PlannedGenerateResult {
    message: string;
    error?: string;
    count: number;
}