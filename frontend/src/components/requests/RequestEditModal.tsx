import React, { useState } from 'react';
import '@/styles/Forms.css';
import { isBookingRequest, requestService, isExcludedTimeslotRequest, isScheduleAdjustmentRequest } from '@/services/request';
import type { RequestInstance } from '@/types/request';

interface EditProps {
    request: RequestInstance;
    onSuccess: () => void;
    onClose: () => void;
}

export const RequestEditModal: React.FC<EditProps> = ({ request, onSuccess, onClose }) => {
    const [loading, setLoading] = useState(false);
    
    // Начальное состояние на основе текущих данных
    const [description, setDescription] = useState(request.description);
    const [details, setDetails] = useState<any>(() => {
        // Упрощаем: для записи в БД нам нужны ID, а не объекты
        if (isBookingRequest(request)) return { 
            classroom: request.details.classroom.id,
            booking_type: 1, // Здесь должен быть ID из констант или пришедший с бэка
            date_start: request.details.date_start,
            date_end: request.details.date_end
        };
        // Для остальных типов аналогично извлекаем ID из объектов
        return request.details;
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const payload: any = { description, details };
            await requestService.update(request.id, payload);
            onSuccess();
            onClose();
        } catch (error) {
            alert("Ошибка при сохранении");
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="flex-col w-100">
            {/* Общее поле для всех типов */}
            <div className="form-group">
                <label className="form-label">Причина / Описание</label>
                <textarea 
                    className="input-styled"
                    value={description}
                    onChange={e => setDescription(e.target.value)}
                    required
                />
            </div>

            <div className="mt-1 mb-1 border-bottom" />

            {/* Специфичные поля для Бронирования */}
            {isBookingRequest(request) && (
                <div className="flex-col gap-1">
                    <div className="form-group">
                        <label className="form-label">Дата начала</label>
                        <input 
                            type="datetime-local" 
                            className="input-styled"
                            value={details.date_start.substring(0, 16)} 
                            onChange={e => setDetails({...details, date_start: e.target.value})}
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Дата окончания</label>
                        <input 
                            type="datetime-local" 
                            className="input-styled"
                            value={details.date_end.substring(0, 16)} 
                            onChange={e => setDetails({...details, date_end: e.target.value})}
                        />
                    </div>
                </div>
            )}

            {/* Специфичные поля для Исключенных слотов */}
            {isExcludedTimeslotRequest(request) && (
                <div className="form-group">
                    <label className="form-label">Преподаватель (ID)</label>
                    <input 
                        type="number" 
                        className="input-styled"
                        value={details.teacher.id}
                        onChange={e => setDetails({...details, teacher: Number(e.target.value)})}
                    />
                </div>
            )}

            {/* Специфичные поля для Корректировок (Массив) */}
            {isScheduleAdjustmentRequest(request) && (
                <div className="flex-col gap-1">
                    <span className="form-label">Список корректировок:</span>
                    {details.map((adj: any, idx: number) => (
                        <div key={idx} className="adjustment-edit-item flex-col gap-1">
                            <div className="form-grid">
                                <div className="flex-col">
                                    <span className="small italic">Дата:</span>
                                    <input 
                                        type="date" 
                                        className="input-styled"
                                        value={adj.date}
                                        onChange={e => {
                                            const newDetails = [...details];
                                            newDetails[idx].date = e.target.value;
                                            setDetails(newDetails);
                                        }}
                                    />
                                </div>
                                <div className="flex-col">
                                    <span className="small italic">Новое время (ID):</span>
                                    <input 
                                        type="number" 
                                        className="input-styled"
                                        value={adj.timeslot || ''}
                                        onChange={e => {
                                            const newDetails = [...details];
                                            newDetails[idx].timeslot = Number(e.target.value) || null;
                                            setDetails(newDetails);
                                        }}
                                    />
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <div className="flex-row justify-end gap-2 mt-2">
                <button type="button" className="btn btn-outline" onClick={onClose}>Отмена</button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                    {loading ? 'Сохранение...' : 'Сохранить'}
                </button>
            </div>
        </form>
    );
};