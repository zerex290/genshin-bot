from enum import Enum


class Characters(Enum):
    VENTI = 'Венти'
    ROSARIA = 'Розария'
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
    GOROU = 'Горо'
    SHENHE = 'Шэнь Хэ'
    YELAN = 'Е Лань'
    DORI = 'Дори'
    COLLEI = 'Коллеи'
    TIGHNARI = 'Тигнари'
    NILOU = 'Нилу'
    CYNO = 'Сайно'
    CANDACE = 'Кандакия'

    HEIZO = 'Хэйдзо'
    SHIKANOIN_HEIZOU = 'Хэйдзо'

    SHINOBU = 'Синобу'
    KUKI_SHINOBU = 'Синобу'

    ITTO = 'Итто'
    ARATAKI_ITTO = 'Итто'

    HUTAO = 'Ху Тао'
    HU_TAO = 'Ху Тао'

    JEAN = 'Джинн'
    QIN = 'Джинн'

    NOELLE = 'Ноэлль'
    NOEL = 'Ноэлль'

    AMBER = 'Эмбер'
    AMBOR = 'Эмбер'

    FEIYAN = 'Янь Фэй'
    YANFEI = 'Янь Фэй'

    YAEMIKO = 'Яэ Мико'
    YAE_MIKO = 'Яэ Мико'
    YAE = 'Яэ Мико'

    AYAKA = 'Аяка'
    KAMISATO_AYAKA = 'Аяка'

    KAZUHA = 'Казуха'
    KAEDEHARA_KAZUHA = 'Казуха'

    KOKOMI = 'Кокоми'
    SANGONOMIYA_KOKOMI = 'Кокоми'

    SARA = 'Сара'
    KUJOU_SARA = 'Сара'

    SHOUGUN = 'Райден'
    RAIDEN_SHOGUN = 'Райден'

    TRAVELER = 'Путешественник'
    PLAYERBOY = 'Итер'
    PLAYERGIRL = 'Люмин'

    THOMA = 'Тома'
    TOHMA = 'Тома'

    YUNJIN = 'Юнь Цзинь'
    YUN_JIN = 'Юнь Цзинь'

    AYATO = 'Аято'
    KAMISATO_AYATO = 'Аято'


class Weapons(Enum):
    CATALYST = 'Катализатор'
    POLEARM = 'Древковое'
    BOW = 'Лук'
    SWORD = 'Одноручное'
    CLAYMORE = 'Двуручное'


class Stats(Enum):
    ATK = 'Сила атаки'
    BONUS_ATK = 'Бонус силы атаки'

    HP = 'Макс. здоровье'
    BONUS_HP = 'Бонус макс. здоровья'
    BONUS_HEAL = 'Бонус лечения'

    DEF = 'Защита'
    BONUS_DEF = 'Бонус защиты'

    CRR = 'Крит. шанс'
    BONUS_CRITRATE = 'Бонус крит. шанса'

    CRD = 'Крит. урон'
    BONUS_CRITDMG = 'Бонус крит. урона'

    EM = 'Мастерство стихий'
    BONUS_EM = 'Бонус мастерства стихий'

    ER = 'Восст. энергии'
    BONUS_ER = 'Бонус восст. энергии'

    PHYS = 'Физ. урон'
    BONUS_PHYS = 'Бонус физ. урона'
    BONUS_PYRO = 'Бонус пиро урона'
    BONUS_ANEMO = 'Бонус анемо урона'
    BONUS_ELEC = 'Бонус электро урона'
    BONUS_HYDRO = 'Бонус гидро урона'
    BONUS_CRYO = 'Бонус крио урона'
    BONUS_GEO = 'Бонус гео урона'
    BONUS_DENDRO = 'Бонус дендро урона'


class Enemies(Enum):
    ELEMENTAL_LIFEFORMS = 'Элементали'
    HILICHURLS = 'Хиличурлы'
    THE_ABYSS_ORDER = 'Бездна'
    FATUI = 'Фатуи'
    AUTOMATON = 'Автоматоны'
    OTHER_HUMAN_FACTIONS = 'Люди'
    MAGICAL_BEASTS = 'Магзвери'
    BOSSES = 'Боссы'


class Grades(Enum):
    REGULAR = 'Обычный'
    BOSS = 'Босс'
    ELITE = 'Элитный'


class Domains(Enum):
    ARTIFACT = 'Артефакты'
    TALENT_MATERIAL = 'Возвышение талантов'
    WEAPON_MATERIAL = 'Возвышение оружия'
    BOSS = 'Подземелья наказания'


class Elements(Enum):
    PYRO = 'Пиро'
    ANEMO = 'Анемо'
    ELECTRO = 'Электро'
    HYDRO = 'Гидро'
    CRYO = 'Крио'
    GEO = 'Гео'
    DENDRO = 'Дендро'
    NONE = 'Мульти'


class ElementSymbols(Enum):
    PYRO = '🔥'
    ANEMO = '💨'
    ELECTRO = '⚡'
    HYDRO = '💧'
    CRYO = '❄'
    GEO = '🌕'
    DENDRO = '☘'


class Regions(Enum):
    SUMERU = 'Сумеру'
    ENKANOMIYA = 'Энканомия'
    INAZUMA = 'Инадзума'
    DRAGONSPINE = 'Драконий Хребет'
    LIYUE = 'Ли Юэ'
    MONDSTADT = 'Мондштадт'
    THE_CHASM = 'Разлом'
    THE_CHASM_UNDERGROUND_MINES = 'Разлом: Подземные шахты'
    MAINACTOR = ''  #: Not a real region; placed for association of main characters of the game


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
