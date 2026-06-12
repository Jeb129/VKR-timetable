import React from 'react';
import type { RequestInstance } from '@/types/request';
import '@/styles/Requests.css'; // Локальные стили
import {
    requestService,
    isBookingRequest,
    isScheduleAdjustmentRequest,
    isExcludedTimeslotRequest,
    isClassroomPreferenceRequest
} from '@/services/request';
import { RequestStatus } from '@/types/enums';
import { useModal } from '@/context/ModalContext';
import { RequestViewModal } from './RequestViewModal';
import { RequestEditModal } from './RequestEditModal';

interface MyTableProps {
    data: RequestInstance[];
    loading: boolean;
    onActionSuccess: () => void;
}

export const MyTable: React.FC<MyTableProps> = ({ data, loading, onActionSuccess }) => {
    const { openModal, closeModal } = useModal();

    const handleView = (request: RequestInstance) => {
        openModal({
            title: `Заявка #${request.id} - ${request.type.name}`,
            width: '600px',
            content: <RequestViewModal request={request} />,
            footer: <button className="btn btn-primary" onClick={closeModal}>Закрыть</button>
        });
    };
    const handleApprove = async (id: number) => {
        if (window.confirm("Одобрить эту заявку?")) {
            await requestService.approve(id);
            onActionSuccess();
        }
    };

    const handleReject = async (id: number) => {
        const comment = prompt("Укажите причину отказа:");
        if (comment) {
            await requestService.reject(id, comment);
            onActionSuccess();
        }
    };
    const handleEdit = (req: RequestInstance) => {
        openModal({
            title: `Редактирование заявки #${req.id}`,
            width: '550px',
            content: (
                <RequestEditModal
                    request={req}
                    onSuccess={onActionSuccess}
                    onClose={closeModal}
                />
            )
        });
    };
    if (loading) return <div className="p-4 justify-center flex-row">Загрузка данных...</div>;

    return (
        <div className="card w-100 p-0 no-scroll">
            <table className="requests-table">
                <thead>
                    <tr>
                        <th>ID / Дата</th>
                        <th>Автор</th>
                        <th>Тип заявки</th>
                        <th>Детали</th>
                        <th>Статус</th>
                        <th className="justify-end flex-row">Действия</th>
                    </tr>
                </thead>
                <tbody>
                    {data.map((req) => {
                        console.log(req)
                        console.log(isBookingRequest(req))
                        console.log(isScheduleAdjustmentRequest(req))
                        console.log(isExcludedTimeslotRequest(req))
                        console.log(isClassroomPreferenceRequest(req))
                        return (
                            <tr key={req.id}>
                                <td>
                                    <div className="flex-col pointer" onClick={() => handleView(req)}>
                                        <span className="text-primary font-bold">#{req.id}</span>
                                        <span className="text-muted small">{new Date(req.created_at).toLocaleDateString()}</span>
                                    </div>
                                </td>

                                <td>
                                    <div className="flex-col">
                                        <strong>{req.user.name}</strong>
                                        <span className="text-muted italic">{req.description}</span>
                                    </div>
                                </td>

                                <td>{req.type.name}</td>

                                <td>
                                    <div className="details-box p-1 flex-col gap-1">
                                        {isBookingRequest(req) && (
                                            <>
                                                <span><strong>Ауд:</strong> {req.details.classroom.name}</span>
                                                <span><strong>Тип:</strong> {req.details.booking_type}</span>
                                            </>
                                        )}
                                        {isScheduleAdjustmentRequest(req) && (
                                            <span className="text-primary">Изменений в сетке: {req.details.length}</span>
                                        )}
                                        {isExcludedTimeslotRequest(req) && (
                                            <span><strong>Слот:</strong> {req.details.timeslot}</span>
                                        )}
                                        {isClassroomPreferenceRequest(req) && (
                                            <span><strong>Желаемая ауд:</strong> {req.details.classroom.name}</span>
                                        )}
                                    </div>
                                </td>

                                <td>
                                    <div className="flex-col align-start gap-1">
                                        <span className={`badge ${req.status.id === RequestStatus.PENDING ? 'badge-pending' :
                                            req.status.id === RequestStatus.VERIFIED ? 'badge-verified' : 'badge-rejected'
                                            }`}>
                                            {req.status.name}
                                        </span>
                                        {req.admin_comment && (
                                            <span className="text-red small">{req.admin_comment}</span>
                                        )}
                                    </div>
                                </td>

                                <td>
                                    <div className="flex-row justify-end gap-1">
                                        {req.can_approve && (
                                            <>
                                                <button onClick={() => handleApprove(req.id)} className="btn btn-green p-1">Одобрить</button>
                                                <button onClick={() => handleReject(req.id)} className="btn btn-red p-1">Отказ</button>
                                            </>
                                        )}
                                        {req.can_edit && (
                                            <button
                                                className="btn btn-outline p-1"
                                                onClick={() => handleEdit(req)}
                                            >
                                                Правка
                                            </button>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        )
                    })}
                </tbody>
            </table>
        </div>
    );
};