export interface SelectOption {
    value: string | number;
    label: string;
}

export interface SearchSelectProps {
    options: SelectOption[];
    value: string | number | (string | number)[]; 
    onChange: (value: any) => void;
    placeholder?: string;
    isMulti?: boolean; // Новый проп
}