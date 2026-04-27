import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { privateApi } from "@/services/axios";
import type { ImportResult } from "@/types/academic_load";
import "@/styles/Editor.css";


const AcademicLoadImportPage = () => {
    const navigate = useNavigate();
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<ImportResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    const [uploadProgress, setUploadProgress] = useState(0);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setFile(e.target.files[0]);
            setResult(null);
            setError(null);
        }
    };

    const handleUpload = async () => {
        if (!file) return;
        const formData = new FormData();
        formData.append("file", file);

        setLoading(true);
        setError(null);
        setUploadProgress(0);

        try {
            const response = await privateApi.post("/api/academic-load/import/", formData, {
                headers: { "Content-Type": "multipart/form-data" },
                onUploadProgress: (progressEvent) => {
                    if (progressEvent.total) {
                        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                        setUploadProgress(percent);
                    }
                }
            });
            setResult(response.data);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Ошибка при обработке файла. Проверьте формат Excel.");
        } finally {
            setLoading(false);
        }
    };

    const downloadTemplate = async () => {
        try {
            const response = await privateApi.get("/api/academic-load/import/", { responseType: 'blob' });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `Текущая_нагрузка.xlsx`);
            document.body.appendChild(link);
            link.click();
        } catch (e) {
            setError("Не удалось скачать текущую нагрузку");
        }
    };

    return (
        <div className="flex-col bg-main min-h-screen">
            <nav className="navbar">
                <div className="logo-white" onClick={() => navigate("/schedule")}>КГУ • АДМИН</div>
                <button className="btn nav-btn" onClick={() => navigate("/profile")}>В профиль</button>
            </nav>

            {/* Центрирующий контейнер */}
            <div className="flex-col align-center justify-center flex-grow p-4">
                
                <div className="card slide-up" style={{ width: '100%', maxWidth: '600px' }}>
                    <div className="flex-col align-center gap-2">
                        <h2 className="text-primary text-center">Импорт учебного плана</h2>
                        
                        <div className="flex-col gap-2 w-100 mt-2 p-2 bg-main rounded-md" style={{ border: '1px dashed var(--p-blue)' }}>
                            <input 
                                type="file" 
                                id="excel-file"
                                accept=".xlsx" 
                                onChange={handleFileChange} 
                                className="input-styled" 
                                style={{ display: 'none' }}
                            />
                            <label 
                                htmlFor="excel-file" 
                                className="btn btn-outline w-100"
                                style={{ cursor: 'pointer', backgroundColor: 'white' }}
                            >
                                {file ? `Файл: ${file.name}` : "Выберите файл .xlsx"}
                            </label>

                             {(loading || uploadProgress > 0) && (
                                <div className="flex-col w-100 gap-1">
                                    <div className="progress-bg" style={{ height: '8px', backgroundColor: '#eee', borderRadius: '4px', overflow: 'hidden' }}>
                                        <div 
                                            className="progress-fill" 
                                            style={{ 
                                                width: `${uploadProgress}%`, 
                                                height: '100%', 
                                                backgroundColor: 'var(--p-blue)',
                                                transition: 'width 0.3s ease'
                                            }} 
                                        />
                                    </div>
                                    <span style={{ fontSize: '12px', textAlign: 'right', color: 'var(--p-blue)' }}>
                                        {uploadProgress < 100 ? `Загрузка: ${uploadProgress}%` : 'Обработка файла сервером...'}
                                    </span>
                                </div>
                            )}

                            <button 
                                className="btn btn-primary w-100" 
                                disabled={loading || !file} 
                                onClick={handleUpload}
                            >
                                {loading ? "Обработка данных..." : "Начать импорт"}
                            </button>
                        </div>

                        {error && <div className="error w-100 mt-1">{error}</div>}

                        {/* Кнопка выгрузки текущей нагрузки опустилась вниз */}
                        <div className="w-100 mt-2 pt-2" style={{ borderTop: '1px solid var(--border-color)' }}>
                            <button 
                                className="btn btn-outline w-100" 
                                onClick={downloadTemplate}
                            >
                                Скачать текущий план (Excel)
                            </button>
                        </div>
                    </div>
                </div>

                {/* БЛОК РЕЗУЛЬТАТОВ (тоже отцентрирован) */}
                {result && (
                    <div className="flex-col gap-2 fade-in mt-3" style={{ width: '100%', maxWidth: '800px' }}>
                        <div className="card" style={{ borderColor: 'var(--p-green)' }}>
                            <h3 className="text-green text-center">Отчет об импорте</h3>
                            <div className="flex-row space-between mt-2">
                                <div className="flex-col align-center">
                                    <span className="text-muted">Всего строк</span>
                                    <strong style={{fontSize: '1.4rem'}}>{result.rows}</strong>
                                </div>
                                <div className="flex-col align-center">
                                    <span className="text-muted text-green">Успешно</span>
                                    <strong className="text-green" style={{fontSize: '1.4rem'}}>{result.success}</strong>
                                </div>
                                <div className="flex-col align-center">
                                    <span className="text-muted text-red">Ошибки</span>
                                    <strong className="text-red" style={{fontSize: '1.4rem'}}>{result.errors}</strong>
                                </div>
                            </div>
                        </div>

                        <div className="flex-row gap-2">
                            <div className="card f-1">
                                <h4 className="text-center mb-1">Создано</h4>
                                <div className="flex-col gap-1" style={{ fontSize: '0.9rem' }}>
                                    <div className="flex-row space-between"><span>Направлений:</span> <b>{result.created.study_programs}</b></div>
                                    <div className="flex-row space-between"><span>Дисциплин:</span> <b>{result.created.disciplines}</b></div>
                                    <div className="flex-row space-between"><span>Групп:</span> <b>{result.created.groups}</b></div>
                                    <div className="flex-row space-between"><span>Преподавателей:</span> <b>{result.created.teachers}</b></div>
                                </div>
                            </div>
                            <div className="card f-1">
                                <h4 className="text-center mb-1">Уже были</h4>
                                <div className="flex-col gap-1" style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                                    <div className="flex-row space-between"><span>Направлений:</span> <span>{result.exists.study_programs}</span></div>
                                    <div className="flex-row space-between"><span>Дисциплин:</span> <span>{result.exists.disciplines}</span></div>
                                    <div className="flex-row space-between"><span>Групп:</span> <span>{result.exists.groups}</span></div>
                                    <div className="flex-row space-between"><span>Преподавателей:</span> <span>{result.exists.teachers}</span></div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AcademicLoadImportPage;