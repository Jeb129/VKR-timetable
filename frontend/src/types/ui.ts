export interface SelectOption {
    value: string | number;
    label: string;
}

export interface SearchSelectProps {
    options: SelectOption[];
    value: string | number;
    onChange: (value: string | number) => void;
    placeholder?: string;
}