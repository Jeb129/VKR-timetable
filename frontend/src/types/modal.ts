import type { ReactNode } from "react";

export interface ModalOptions {
    title: string;
    content: ReactNode;
    footer?: ReactNode;
    width?: string;
}

export interface ModalContextType {
    openModal: (options: ModalOptions) => void;
    closeModal: () => void;
}