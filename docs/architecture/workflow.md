graph TD
    %% Крок 1: Тригер
    Start((<b>1. ТАЙМЕР</b><br/>Кожні 5 хвилин)) --> LoadConfig[<b>2. ЗАВАНТАЖЕННЯ</b><br/>Сервіс читає список IP та ключі]

    %% Крок 2: Цикл перевірки
    LoadConfig --> CheckIP{<b>3. ПЕРЕВІРКА</b><br/>IP доступний?}

    %% Крок 3: Порівняння
    CheckIP -- "ТАК (Online)" --> Compare[<b>4. ПОРІВНЯННЯ</b><br/>Що було 5 хвилин тому?]
    CheckIP -- "НІ (Offline)" --> Compare

    %% Крок 4: Логіка змін
    Compare -- "Статус НЕ змінився" --> End((<b>КІНЕЦЬ</b><br/>Очікуємо 5 хвилин))
    Compare -- "Статус ЗМІНИВСЯ" --> Calc[<b>5. РОЗРАХУНОК</b><br/>Рахуємо тривалість та формуємо текст UA]

    %% Крок 5: Дія
    Calc --> Notify[<b>6. TELEGRAM</b><br/>Надсилаємо сповіщення в канал]
    Notify --> Save[<b>7. ПАМ'ЯТЬ</b><br/>Зберігаємо новий статус і час]
    Save --> End

    %% Стилізація
    style Start fill:#f9f,stroke:#333,stroke-width:2px
    style End fill:#eee,stroke:#333
    style CheckIP fill:#fff4dd,stroke:#d4a017,stroke-width:2px
    style Notify fill:#0088cc,stroke:#005580,color:#fff
    style Save fill:#90ee90,stroke:#006400
