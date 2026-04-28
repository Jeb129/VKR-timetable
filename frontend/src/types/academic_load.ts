export interface ImportResult {
    rows: number;
    success: number;
    errors: number;
    skipped: number;
    created: {
        study_programs: number;
        disciplines: number;
        groups: number;
        teachers: number;
    };
    exists: {
        study_programs: number;
        disciplines: number;
        groups: number;
        teachers: number;
    };
    messages: { message: string; type: string }[];
}