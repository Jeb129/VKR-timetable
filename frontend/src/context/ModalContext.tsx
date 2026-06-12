import React, { createContext, useContext, useState } from "react";
import type { ModalOptions, ModalContextType } from "@/types/modal";
import "@/styles/Modal.css";

const ModalContext = createContext<ModalContextType | undefined>(undefined);

export const ModalProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [config, setConfig] = useState<ModalOptions | null>(null);

    const openModal = (newConfig: ModalOptions) => setConfig(newConfig);
    const closeModal = () => setConfig(null);

    return (
        <ModalContext.Provider value={{ openModal, closeModal }}>
            {children}
            
            {/* ГЛОБАЛЬНЫЙ КОМПОНЕНТ МОДАЛКИ */}
            {config && (
                <div className="modal-overlay fade-in" onClick={closeModal}>
                    <div 
                        className="modal-content slide-up" 
                        style={{ width: config.width || '500px' }}
                        onClick={e => e.stopPropagation()}
                    >
                        <div className="modal-header flex-row space-between align-center">
                            <h3>{config.title}</h3>
                            <button className="btn btn-outline" style={{padding: '5px 10px'}} onClick={closeModal}>×</button>
                        </div>
                        <div className="modal-body">
                            {config.content}
                        </div>
                        {config.footer && (
                            <div className="modal-footer">
                                {config.footer}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </ModalContext.Provider>
    );
};

export const useModal = () => {
    const context = useContext(ModalContext);
    if (!context) throw new Error("useModal must be used within ModalProvider");
    return context;
};