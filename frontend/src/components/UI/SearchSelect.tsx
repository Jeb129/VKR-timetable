import { useState, useRef } from 'react';
import type { SelectOption } from "@/types/ui";
import "@/styles/SearchSelect.css";
import { dbService } from '@/services/crud';
import type { OptionsOrGroups, GroupBase } from 'react-select';
import AsyncSelect from 'react-select/async';

interface AsyncSearchSelectProps {
    model: string;
    // Значение ID (одиночное или массив)
    value: number | string | (number | string)[] | null;
    // Начальные данные для отображения label
    initialOptions?: SelectOption | SelectOption[] | null;
    onChange: (value: any) => void;
    placeholder?: string;
    isClearable?: boolean;
    isMulti?: boolean;
}

const AsyncSearchSelect: React.FC<AsyncSearchSelectProps> = ({
    model,
    value,
    onChange,
    placeholder,
    initialOptions,
    isClearable = true,
    isMulti = false
}) => {
    const selectRef = useRef<any>(null);
    const [selectedOption, setSelectedOption] = useState<SelectOption | readonly SelectOption[] | null>(null);
    /**
     * loadOptions ожидает возврата Promise с типом OptionsOrGroups<SelectOption, GroupBase<SelectOption>>
     */


    const loadOptions = async (
        inputValue: string
    ): Promise<OptionsOrGroups<SelectOption, GroupBase<SelectOption>>> => {
        try {
            const data = await dbService.list<any>(model, {
                search: inputValue,
                page_size: 20
            });

            return data.results.map((item) => ({
                value: item.id,
                label: item.name || `ID: ${item.id}`
            }));
        } catch (e) {
            console.error(`Ошибка справочника ${model}:`, e);
            return [];
        }
    };

    /**
     * Приведение текущего value (ID) к объекту SelectOption для отображения
     */
    const getSelectedValue = (): SelectOption | SelectOption[] | null => {
        if (!value || (Array.isArray(value) && value.length === 0)) return null;

        if (isMulti && Array.isArray(value)) {
            if (Array.isArray(initialOptions)) return initialOptions;
            return value.map(v => ({ value: v, label: `ID: ${v}` }));
        }

        if (!Array.isArray(value)) {
            if (initialOptions && !Array.isArray(initialOptions)) return initialOptions;
            return { value, label: String(value) };
        }

        return null;
    };

    /**
     * Типизация newValue зависит от того, включен ли isMulti
     */
    const handleChange = (newValue: SelectOption | readonly SelectOption[] | null) => {
        setSelectedOption(newValue)
        if (isMulti) {
            const options = newValue as SelectOption[];
            onChange(options ? options.map(opt => opt.value) : []);
        } else {
            const option = newValue as SelectOption;
            onChange(option ? option.value : null);
        }
    };

    return (
        <AsyncSelect<SelectOption, boolean, GroupBase<SelectOption>>
            ref={selectRef}
            cacheOptions
            defaultOptions
            loadOptions={loadOptions}
            value={selectedOption}
            onChange={handleChange}
            placeholder={placeholder || (isMulti ? "Выберите несколько..." : "Поиск...")}
            isMulti={isMulti}
            isClearable={isClearable}

            className="ksu-select-container"
            classNamePrefix="ksu-select"

            // Типизируем inputValue в функции сообщения
            noOptionsMessage={({ inputValue }: { inputValue: string }) =>
                !inputValue ? "Начните вводить текст..." : "Ничего не найдено"
            }
            loadingMessage={() => "Загрузка..."}
            closeMenuOnSelect={!isMulti}
        />
    );
};

export default AsyncSearchSelect;