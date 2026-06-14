import { useState, useRef , useEffect } from 'react';
import type { SelectOption, SimpleEntity } from "@/types/ui";
import "@/styles/SearchSelect.css";
import { dbService } from '@/services/crud';
import type { OptionsOrGroups, GroupBase } from 'react-select';
import AsyncSelect from 'react-select/async';

interface SearchSelectProps {
    model: string;
    // @ts-ignore
    value?: number | string | null; 
    onChange: (value: any) => void;
    placeholder?: string;
    isClearable?: boolean;
    isMulti?: boolean;
    pageSize?: number;
}

const SearchSelect: React.FC<SearchSelectProps> = ({
    model,
    onChange,
    value,
    placeholder,
    isClearable = true,
    isMulti = false,
    pageSize = 20 
}) => {
    // @ts-ignore
    const selectRef = useRef<any>(null);
    const [selectedOption, setSelectedOption] = useState<SelectOption | readonly SelectOption[] | null>(null);
    /**
     * loadOptions ожидает возврата Promise с типом OptionsOrGroups<SelectOption, GroupBase<SelectOption>>
     */

    useEffect(() => {
        if (!value) {
            setSelectedOption(null);
        }
    }, [value]);

    const loadOptions = async (
        inputValue: string
    ): Promise<OptionsOrGroups<SelectOption, GroupBase<SelectOption>>> => {
        try {
            const data = await dbService.list<SimpleEntity>(model, {
                search: inputValue,
                page_size: pageSize
            });

            return data.results.map((item) => ({
                value: item.id,
                label: item.name ?? `ID: ${item.id}`
            }));
        } catch (e) {
            console.error(`Ошибка справочника ${model}:`, e);
            return [];
        }
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
            placeholder={placeholder ?? (isMulti ? "Выберите несколько..." : "Поиск...")}
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

export default SearchSelect;