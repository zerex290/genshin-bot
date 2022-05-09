from enum import Enum


class Characters(Enum):
    VENTI = 'Венти'
    ROSARIA = 'Розария'
    HUTAO = 'Ху Тао'
    XIAO = 'Сяо'
    GANYU = 'Гань Юй'
    ALBEDO = 'Альбедо'
    ZHONGLI = 'Чжун Ли'
    XINYAN = 'Синь Янь'
    TARTAGLIA = 'Тарталья'
    DIONA = 'Диона'
    KLEE = 'Кли'
    KEQING = 'Кэ Цин'
    MONA = 'Мона'
    QIQI = 'Ци Ци'
    DILUC = 'Дилюк'
    SUCROSE = 'Сахароза'
    CHONGYUN = 'Чунь Юнь'
    BENNETT = 'Беннет'
    FISCHL = 'Фишль'
    NINGGUANG = 'Нин Гуан'
    XINGQIU = 'Син Цю'
    BEIDOU = 'Бей Доу'
    XIANGLING = 'Сян Лин'
    RAZOR = 'Рейзор'
    BARBARA = 'Барбара'
    LISA = 'Лиза'
    KAEYA = 'Кэйа'
    EULA = 'Эола'
    YOIMIYA = 'Йоимия'
    SAYU = 'Саю'
    ALOY = 'Элой'
    ITTO = 'Итто'
    GOROU = 'Горо'

    SHENHE = 'Шэнь Хэ'
    YAE = 'Яэ'
    SHINOBU = 'Куки Синобу'

    JEAN = 'Джинн'
    QIN = 'Джинн'

    NOELLE = 'Ноэлль'
    NOEL = 'Ноэлль'

    AMBER = 'Эмбер'
    AMBOR = 'Эмбер'

    YANFEI = 'Янь Фэй'
    FEIYAN = 'Янь Фэй'

    AYAKA = 'Аяка'
    KAMISATO_AYAKA = 'Аяка'

    KAZUHA = 'Казуха'
    KAEDEHARA_KAZUHA = 'Казуха'

    KOKOMI = 'Кокоми'
    SANGONOMIYA_KOKOMI = 'Кокоми'

    SARA = 'Сара'
    KUJOU_SARA = 'Сара'

    SHOUGUN = 'Райден'
    SHOUGUN_RAIDEN = 'Райден'
    RAIDEN_SHOUGUN = 'Райден'
    SHOGUN = 'Райден'
    SHOGUN_RAIDEN = 'Райден'
    RAIDEN_SHOGUN = 'Райден'

    TRAVELER = 'Путешественник'
    TRAVELER_BOY_ANEMO = 'Итер'
    TRAVELER_BOY_GEO = 'Итер'
    TRAVELER_BOY_ELECTRO = 'Итер'
    TRAVELER_GIRL_ANEMO = 'Люмин'
    TRAVELER_GIRL_GEO = 'Люмин'
    TRAVELER_GIRL_ELECTRO = 'Люмин'

    THOMA = 'Тома'
    TOHMA = 'Тома'

    YUNJIN = 'Юнь Цзинь'
    YUN_JIN = 'Юнь Цзинь'

    AYATO = 'Аято'
    KAMISATO_AYATO = 'Аято'

    YELAN = 'Е Лань'
    YEBLAN = 'Еблань'

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
    CATALYST = 'Катализатор'
    POLEARM = 'Древковое'
    BOW = 'Лук'
    SWORD = 'Одноручное'
    CLAYMORE = 'Двуручное'


class Artifacts(Enum):
    QUALITY_OF_LIFE_SETS = 'Здоровье'
    ATTACK_SETS = 'Урон'
    ELEMENTAL_ATTACK_SETS = 'Элем. Урон'
    DEFENSE_SETS = 'Защита'
    ELEMENTAL_RESISTANCE_SETS = 'Элем. Защита'
    SUPPORT_SETS = 'Поддержка'
    ONE_PIECE_TIARA_SETS = 'Тиары'
    UNCATEGORIZED = 'Вне категории'


class Enemies(Enum):
    ELEMENTAL_LIFEFORMS = 'Элементали'
    HILICHURLS = 'Хиличурлы'
    THE_ABYSS_ORDER = 'Бездна'
    FATUI = 'Фатуи'
    AUTOMATON = 'Автоматоны'
    OTHER_HUMAN_FACTIONS = 'Люди'
    MAGICAL_BEASTS = 'Магзвери'
    BOSSES = 'Боссы'
    UNCATEGORIZED = 'Вне категории'


class Elements(Enum):
    PYRO = 'Пиро'
    ANEMO = 'Анемо'
    ELECTRO = 'Электро'
    HYDRO = 'Гидро'
    CRYO = 'Крио'
    GEO = 'Гео'
    DENDRO = 'Дендро'


class ElementSymbols(Enum):
    PYRO = '🔥'
    ANEMO = '💨'
    ELECTRO = '⚡'
    HYDRO = '💧'
    CRYO = '❄'
    GEO = '🌕'
    DENDRO = '☘'


class Regions(Enum):
    ENKANOMIYA = 'Энканомия'
    INAZUMA = 'Инадзума'
    DRAGONSPINE = 'Драконий Хребет'
    LIYUE = 'Ли Юэ'
    MONDSTADT = 'Мондштадт'
    THE_CHASM = 'Разлом'
    THE_CHASM_UNDERGROUND_MINES = 'Разлом: Подземные шахты'


class Rewards(Enum):
    PRIMOGEM = 'Камни Истока'
    MORA = 'Мора'
    FINE_ENHANCEMENT_ORE = 'Превосходная руда усиления'
    ADVENTURER_EXPERIENCE = 'Опыт искателя приключений'
    FRIED_RADISH_BALLS = 'Редисовые шарики'
    SWEET_MADAME = 'Цыпленок в медовом соусе'
    HERO_WIT = 'Опыт героя'
    ALMOND_TOFU = 'Миндальный тофу'
    FISHERMAN_TOAST = 'Рыбацкий бутерброд'


class DiaryCategories(Enum):
    SPIRAL_ABYSS = '🌀Витая бездна'
    DAILY_ACTIVITY = '🎁Ежедневная активность'
    EVENTS = '♨События'
    MAIL = '✉Почта'
    ADVENTURE = '🚲Приключения'
    QUESTS = '💡Задания'
    OTHER = '✨Другое'
