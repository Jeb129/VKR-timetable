import { useState, useRef } from 'react';
import Select from 'react-select';
import type { SearchSelectProps, SelectOption } from "@/types/ui";
import "@/styles/SearchSelect.css";

const SearchSelect = ({ options, value, onChange, placeholder,isMulti  }: SearchSelectProps) => {
    // Реф для управления фокусом самого компонента
    const selectRef = useRef<any>(null);
    // Состояние для отслеживания, нажат ли сейчас поиск
    const [isFocused, setIsFocused] = useState(false);

    // Логика определения выбранных опций для одиночного и множественного режимов
    const getSelectedOption = () => {
        if (isMulti) {
            // Если это массив, фильтруем опции. Если нет (например, пришло ""), возвращаем пустой массив
            return options.filter(opt => (Array.isArray(value) ? value : []).includes(opt.value));
        }
        return options.find(opt => opt.value === value) || null;
    };

    const handleChange = (newValue: any) => {
        if (isMulti) {
            // 2. БЕЗОПАСНАЯ ПРОВЕРКА: Если newValue это массив — мапим, если null/undefined — отдаем []
            const selectedValues = Array.isArray(newValue) 
                ? newValue.map((v: SelectOption) => v.value) 
                : [];
            onChange(selectedValues);
        } else {
            // Одиночный выбор
            onChange(newValue ? (newValue as SelectOption).value : "");
            if (selectRef.current) {
                selectRef.current.blur();
            }
        }
    };

    return (
        <Select
            ref={selectRef}
            className="ksu-select-container"
            classNamePrefix="ksu-select"
            options={options}
            value={getSelectedOption()}
            onChange={handleChange}
            placeholder={placeholder || "Поиск..."}
            isMulti={isMulti}
            isSearchable={true}
            noOptionsMessage={() => "Ничего не найдено"}
            controlShouldRenderValue={isMulti ? true : !isFocused}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
        />
    );
};

export default SearchSelect;