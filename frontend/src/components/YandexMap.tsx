import React from 'react';

interface YandexMapProps {
    /** Ключ карты из конструктора Яндекса (параметр um=constructor:...) */
    ymapKey: string;
    /** Опциональный заголовок для доступности (aria-label) */
    title?: string;
}

const YandexMap: React.FC<YandexMapProps> = ({ ymapKey }) => {

    const mapUrl = `https://yandex.ru/map-widget/v1/?um=constructor%${ymapKey}&amp;source=constructor`;
    if (ymapKey)
        return (<iframe className='f-1 w-100 h-100 ratio54' src={mapUrl}></iframe>)
    else
        return (<p>Карта недоступна</p>)
};

export default YandexMap;