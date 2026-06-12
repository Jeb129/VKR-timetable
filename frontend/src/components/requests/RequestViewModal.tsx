import { isBookingRequest, isExcludedTimeslotRequest, isScheduleAdjustmentRequest } from '@/services/request';
import type { RequestInstance } from '@/types/request';
import React from 'react';


export const RequestViewModal: React.FC<{ request: RequestInstance }> = ({ request }) => {
    return (
        <div className="flex-col gap-2">
            <div className="info-grid">
                <div className="flex-col">
                    <span className="text-muted small">Автор:</span>
                    <strong>{request.user.name}</strong>
                </div>
                <div className="flex-col">
                    <span className="text-muted small">Дата создания:</span>
                    <strong>{new Date(request.created_at).toLocaleString()}</strong>
                </div>
            </div>

            <div className="flex-col mt-1">
                <span className="text-muted small">Описание:</span>
                <p className="card p-1" style={{ borderStyle: 'dashed' }}>{request.description}</p>
            </div>

            <h4 className="mt-2 mb-1">Детали запроса</h4>

            {isBookingRequest(request) && (
                <div className="info-grid card p-2 bg-beige">
                    <div><strong>Аудитория:</strong> {request.details.classroom.name}</div>
                    <div><strong>Вид:</strong> {request.details.booking_type}</div>
                    <div><strong>Начало:</strong> {new Date(request.details.date_start).toLocaleString()}</div>
                    <div><strong>Конец:</strong> {new Date(request.details.date_end).toLocaleString()}</div>
                </div>
            )}

            {isScheduleAdjustmentRequest(request) && (
                <div className="flex-col">
                    {request.details.map((adj, i) => (
                        <div key={i} className="adjustment-row p-1 flex-row space-between align-center">
                            <div className="flex-col">
                                <strong>Дата занятия: {adj.date}</strong>
                                <span className="small">{adj.lesson}</span>
                            </div>
                            <div className="flex-col align-end">
                                <span className="text-primary font-bold">{adj.timeslot || "Снятие"}</span>
                                <span className="small">{adj.classroom?.name || "Без ауд."}</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {isExcludedTimeslotRequest(request) && (
                <div className="card p-2">
                    <p><strong>Преподаватель:</strong> {request.details.teacher.name}</p>
                    <p><strong>Исключаемый слот:</strong> {request.details.timeslot}</p>
                </div>
            )}

            {request.admin_comment && (
                <div className="mt-2 p-1 border-red card">
                    <span className="text-red font-bold">Комментарий администратора:</span>
                    <p>{request.admin_comment}</p>
                </div>
            )}
        </div>
    );
};