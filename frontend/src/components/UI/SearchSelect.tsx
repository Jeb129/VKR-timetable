import { useState, useRef } from 'react';
import Select from 'react-select';
import type { SearchSelectProps, SelectOption } from "@/types/ui";
import "@/styles/SearchSelect.css";

const SearchSelect = ({ options, value, onChange, placeholder }: SearchSelectProps) => {
    // Реф для управления фокусом самого компонента
    const selectRef = useRef<any>(null);
    // Состояние для отслеживания, нажат ли сейчас поиск
    const [isFocused, setIsFocused] = useState(false);

    const selectedOption = options.find(opt => opt.value === value) || null;

    const handleChange = (opt: any) => {
        // Вызываем внешнюю функцию изменения (setSelectedTargetId)
        onChange(opt ? (opt as SelectOption).value : "");
        // Снимаем выделение с элемента после выбора
        if (selectRef.current) {
            selectRef.current.blur();
        }
    };

    return (
        <Select
            ref={selectRef}
            className="ksu-select-container"
            classNamePrefix="ksu-select"
            options={options}
            value={selectedOption}
            onChange={handleChange}
            placeholder={placeholder || "Поиск..."}
            isSearchable={true}
            noOptionsMessage={() => "Ничего не найдено"}
            controlShouldRenderValue={!isFocused}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
        />
    );
};

export default SearchSelect;