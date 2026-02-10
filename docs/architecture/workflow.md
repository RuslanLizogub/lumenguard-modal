graph TD
    %% Шаг 1: Триггер
    Start((<b>1. ТАЙМЕР</b><br/>Раз в 5 минут)) --> LoadConfig[<b>2. ЗАГРУЗКА</b><br/>Бот берет список IP и ключи]
    
    %% Шаг 2: Цикл проверки
    LoadConfig --> CheckIP{<b>3. ПРОВЕРКА</b><br/>IP доступен?}
    
    %% Шаг 3: Сравнение
    CheckIP -- "ДА (Online)" --> Compare[<b>4. СРАВНЕНИЕ</b><br/>Что было 5 мин назад?]
    CheckIP -- "НЕТ (Offline)" --> Compare
    
    %% Шаг 4: Логика изменений
    Compare -- "Статус НЕ изменился" --> End((<b>КОНЕЦ</b><br/>Ждем 5 мин))
    Compare -- "Статус ИЗМЕНИЛСЯ" --> Calc[<b>5. РАСЧЕТ</b><br/>Считаем время и пишем текст на UA]
    
    %% Шаг 5: Действие
    Calc --> Notify[<b>6. ТЕЛЕГРАМ</b><br/>Отправляем уведомление в канал]
    Notify --> Save[<b>7. ПАМЯТЬ</b><br/>Запоминаем новый статус и время]
    Save --> End
    
    %% Стилизация
    style Start fill:#f9f,stroke:#333,stroke-width:2px
    style End fill:#eee,stroke:#333
    style CheckIP fill:#fff4dd,stroke:#d4a017,stroke-width:2px
    style Notify fill:#0088cc,stroke:#005580,color:#fff
    style Save fill:#90ee90,stroke:#006400