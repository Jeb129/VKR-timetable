export interface BookingRequest {
    id: number;
    classroom: number;
    user: string;
    classroom_num: string;
    date_start: string;
    date_end: string;
    description: string;
    status: number; // 0 - модерация, 1 - одобрено, 2 - отказ
    admin_comment?: string;
}