-- Демо-матч и составы (идемпотентно: TRUNCATE + INSERT)
-- team_id 1 = РК «Стрела», team_id 2 = РК «Ак Барс» (составы вымышленные, в стиле клубов)

TRUNCATE TABLE rugby.players;
TRUNCATE TABLE rugby.matches;

INSERT INTO rugby.matches VALUES
(1001, 1, 2, 'Чемпионат России', 2026, 'Санкт-Петербург, «Газпром Арена»', '2026-04-20', 24, 21);

INSERT INTO rugby.players VALUES
(101, 'Никита Орлов', 1, 'fly_half', 'backs'),
(102, 'Максим Громов', 1, 'centre', 'backs'),
(103, 'Артём Кузнецов', 1, 'wing', 'backs'),
(104, 'Павел Соколов', 1, 'fullback', 'backs'),
(105, 'Илья Морозов', 1, 'scrum_half', 'backs'),
(106, 'Денис Лебедев', 1, 'number_8', 'forwards'),
(107, 'Сергей Волков', 1, 'flanker', 'forwards'),
(108, 'Андрей Новиков', 1, 'lock', 'forwards'),
(109, 'Роман Фёдоров', 1, 'hooker', 'forwards'),
(110, 'Виталий Пономарёв', 1, 'loosehead_prop', 'forwards'),
(111, 'Егор Зайцев', 1, 'tighthead_prop', 'forwards'),
(112, 'Константин Беляев', 1, 'flanker', 'forwards'),
(201, 'Дамир Хасанов', 2, 'fly_half', 'backs'),
(202, 'Рустам Гарифуллин', 2, 'centre', 'backs'),
(203, 'Айрат Сафиуллин', 2, 'wing', 'backs'),
(204, 'Марсель Ганиев', 2, 'fullback', 'backs'),
(205, 'Ильдар Фахрутдинов', 2, 'scrum_half', 'backs'),
(206, 'Ренат Бикмухаметов', 2, 'number_8', 'forwards'),
(207, 'Альберт Габдрахманов', 2, 'flanker', 'forwards'),
(208, 'Радик Зарипов', 2, 'lock', 'forwards'),
(209, 'Азат Зиганшин', 2, 'hooker', 'forwards'),
(210, 'Динар Хабибуллин', 2, 'loosehead_prop', 'forwards'),
(211, 'Руслан Латыпов', 2, 'tighthead_prop', 'forwards'),
(212, 'Тимур Мустафин', 2, 'flanker', 'forwards');
