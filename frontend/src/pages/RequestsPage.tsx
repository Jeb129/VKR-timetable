import { MyTable } from '@/components/requests/MyTable';
import { useModal } from '@/context/ModalContext';
import { requestService } from '@/services/request';
import { RequestStatus } from '@/types/enums';
import type { RequestInstance } from '@/types/request';
import { useEffect, useState } from 'react';

export const RequestsPage = () => {
    const [data, setData] = useState<RequestInstance[]>([]);
    const [totalCount, setTotalCount] = useState(0);
    const [currentPage, setCurrentPage] = useState(1);
    const [statusFilter, setStatusFilter] = useState<number | undefined>();
    const [loading, setLoading] = useState(false);

    const load = async () => {
        setLoading(true);
        try {
            const res = await requestService.getAll({
                page: currentPage,
                status: statusFilter
            });
            setData(res.results);
            setTotalCount(res.count);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { load(); }, [currentPage, statusFilter]);

    const totalPages = Math.ceil(totalCount / 10);

    return (
        <div className="flex-col w-100 min-h-screen">
            {/* Навигация уже встроена глобально, здесь контент */}
            <div className="p-3 flex-grow flex-col gap-2">
                <div className="space-between align-center flex-row">
                    <h3>Реестр заявок</h3>

                    <div className="flex-row gap-2 align-center">
                        <span className="text-muted">Фильтр:</span>
                        <select
                            className="select-styled"
                            style={{ width: '200px' }} // Исключение для ширины, если нет класса в App.css
                            onChange={(e) => {
                                const val = e.target.value;
                                // Если строка пустая - сбрасываем, иначе приводим к числу
                                setStatusFilter(val === "" ? undefined : Number(val));
                                setCurrentPage(1);
                            }}
                        >
                            <option value="">Все статусы</option>
                            <option value={RequestStatus.PENDING}>На модерации</option>
                            <option value={RequestStatus.VERIFIED}>Одобрены</option>
                            <option value={RequestStatus.REJECTED}>Отклонены</option>
                        </select>
                    </div>
                </div>

                <MyTable
                    data={data}
                    loading={loading}
                    onActionSuccess={load}
                />

                {/* Пагинация */}
                <div className="pagination-wrapper p-2 flex-row justify-center align-center gap-2">
                    <button
                        className="btn btn-outline"
                        disabled={currentPage === 1}
                        onClick={() => setCurrentPage(p => p - 1)}
                    >
                        Назад
                    </button>

                    <span className="font-bold">Страница {currentPage} из {totalPages || 1}</span>

                    <button
                        className="btn btn-outline"
                        disabled={currentPage >= totalPages}
                        onClick={() => setCurrentPage(p => p + 1)}
                    >
                        Вперед
                    </button>
                </div>
            </div>
        </div>
    );
};