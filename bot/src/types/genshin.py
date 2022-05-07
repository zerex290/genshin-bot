from enum import Enum


class Characters(Enum):
    venti = 'Венти'
    rosaria = 'Розария'
    hutao = 'Ху Тао'
    xiao = 'Сяо'
    ganyu = 'Гань Юй'
    albedo = 'Альбедо'
    zhongli = 'Чжун Ли'
    xinyan = 'Синь Янь'
    tartaglia = 'Тарталья'
    diona = 'Диона'
    klee = 'Кли'
    keqing = 'Кэ Цин'
    mona = 'Мона'
    qiqi = 'Ци Ци'
    diluc = 'Дилюк'
    sucrose = 'Сахароза'
    chongyun = 'Чунь Юнь'
    bennett = 'Беннет'
    fischl = 'Фишль'
    ningguang = 'Нин Гуан'
    xingqiu = 'Син Цю'
    beidou = 'Бей Доу'
    xiangling = 'Сян Лин'
    razor = 'Рейзор'
    barbara = 'Барбара'
    lisa = 'Лиза'
    kaeya = 'Кэйа'
    eula = 'Эола'
    yoimiya = 'Йоимия'
    sayu = 'Саю'
    aloy = 'Элой'
    itto = 'Итто'
    gorou = 'Горо'

    shenhe = 'Шэнь Хэ'
    yae = 'Яэ'
    shinobu = 'Куки Синобу'

    jean = 'Джинн'
    qin = 'Джинн'

    noelle = 'Ноэлль'
    noel = 'Ноэлль'

    amber = 'Эмбер'
    ambor = 'Эмбер'

    yanfei = 'Янь Фэй'
    feiyan = 'Янь Фэй'

    ayaka = 'Аяка'
    kamisato_ayaka = 'Аяка'

    kazuha = 'Казуха'
    kaedehara_kazuha = 'Казуха'

    kokomi = 'Кокоми'
    sangonomiya_kokomi = 'Кокоми'

    sara = 'Сара'
    kujou_sara = 'Сара'

    shougun = 'Райден'
    shougun_raiden = 'Райден'
    raiden_shougun = 'Райден'
    shogun = 'Райден'
    shogun_raiden = 'Райден'
    raiden_shogun = 'Райден'

    playerboy = 'Итер'
    traveler_boy_anemo = 'Итер'
    traveler_boy_geo = 'Итер'
    traveler_boy_electro = 'Итер'
    traveler = 'Путешественник'
    playergirl = 'Люмин'
    traveler_girl_anemo = 'Люмин'
    traveler_girl_geo = 'Люмин'
    traveler_girl_electro = 'Люмин'

    thoma = 'Тома'
    tohma = 'Тома'

    yunjin = 'Юнь Цзинь'
    yun_jin = 'Юнь Цзинь'

    ayato = 'Аято'
    kamisato_ayato = 'Аято'

    yelan = 'Е Лань'
    yeblan = 'Еблань'

    @staticmethod
    def format_character_name(character: str) -> str:
        sub = {
            'хутао': 'Ху Тао',
            'ганьюй': 'Гань Юй',
            'чжунли': 'Чжун Ли',
            'синьянь': 'Синь Янь',
            'кэцин': 'Кэ Цин',
            'цици': 'Ци Ци',
            'чуньюнь': 'Чунь Юнь',
            'нингуан': 'Нин Гуан',
            'синцю': 'Син Цю',
            'бейдоу': 'Бей Доу',
            'сянлин': 'Сян Лин',
            'яньфэй': 'Янь Фэй',
            'юньцзинь': 'Юнь Цзинь',
            'шэньхэ': 'Шэнь Хэ',
            'елань': 'Е Лань',
            'кукисинобу': 'Куки Синобу'
        }
        return sub.get(character, character.capitalize())


class Weapons(Enum):
    catalyst = 'Катализатор'
    polearm = 'Древковое'
    bow = 'Лук'
    sword = 'Одноручное'
    claymore = 'Двуручное'


class Artifacts(Enum):
    quality_of_life_sets = 'Здоровье'
    attack_sets = 'Урон'
    elemental_attack_sets = 'Элем. Урон'
    defense_sets = 'Защита'
    elemental_resistance_sets = 'Элем. Защита'
    support_sets = 'Поддержка'
    one_piece_tiara_sets = 'Тиары'
    uncategorized = 'Вне категории'


class Enemies(Enum):
    elemental_lifeforms = 'Элементали'
    hilichurls = 'Хиличурлы'
    the_abyss_order = 'Бездна'
    fatui = 'Фатуи'
    automaton = 'Автоматоны'
    other_human_factions = 'Люди'
    magical_beasts = 'Магзвери'
    bosses = 'Боссы'
    uncategorized = 'Вне категории'


class Elements(Enum):
    pyro = 'Пиро'
    anemo = 'Анемо'
    electro = 'Электро'
    hydro = 'Гидро'
    cryo = 'Крио'
    geo = 'Гео'
    dendro = 'Дендро'


class ElementSymbols(Enum):
    pyro = '🔥'
    anemo = '💨'
    electro = '⚡'
    hydro = '💧'
    cryo = '❄'
    geo = '🌕'
    dendro = '☘'


class Regions(Enum):
    enkanomiya = 'Энканомия'
    inazuma = 'Инадзума'
    dragonspine = 'Драконий Хребет'
    liyue = 'Ли Юэ'
    mondstadt = 'Мондштадт'
    the_chasm = 'Разлом'
    the_chasm_underground_mines = 'Разлом: Подземные шахты'


class Rewards(Enum):
    primogem = 'Камни Истока'
    mora = 'Мора'
    fine_enhancement_ore = 'Превосходная руда усиления'
    adventurer_experience = 'Опыт искателя приключений'
    fried_radish_balls = 'Редисовые шарики'
    sweet_madame = 'Цыпленок в медовом соусе'
    hero_wit = 'Опыт героя'
    almond_tofu = 'Миндальный тофу'
    fisherman_toast = 'Рыбацкий бутерброд'
