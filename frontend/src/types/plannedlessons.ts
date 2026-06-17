import type { SimpleEntity } from "./ui";

export interface PlannedCheckResult {
    status: 'ok' | 'warning';
    details: string;
    uncovered_data?: SimpleEntity[];
}

export interface PlannedGenerateResult {
    details: string;
    error?: string;
    count: number;
}