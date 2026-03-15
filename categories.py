from enum import Enum


class Category(str, Enum):
    RENT                   = 'RENT'
    INVESTMENT             = 'INVESTMENT'
    FOOD                   = 'FOOD'
    GROCERIES              = 'GROCERIES'
    LOCAL_TRAVEL           = 'LOCAL_TRAVEL'
    GROOMING               = 'GROOMING'
    OTHER_ESSENTIALS       = 'OTHER_ESSENTIALS'
    SUBSCRIPTION           = 'SUBSCRIPTION'
    REGULAR_PARTY_VACATION = 'REGULAR_PARTY_VACATION'
    TREATS_AND_GIFTS       = 'TREATS_AND_GIFTS'
    OTHER_NON_ESSENTIALS   = 'OTHER_NON_ESSENTIALS'
    GYM                    = 'GYM'
    MEDICAL                = 'MEDICAL'
    LONG_TRAVEL            = 'LONG_TRAVEL'
    HOME                   = 'HOME'
    SPECIAL                = 'SPECIAL'
    BIG_PARTY_VACATION     = 'BIG_PARTY_VACATION'
    PERSONAL               = 'PERSONAL'
    TRANSFER_EXTERNAL      = 'TRANSFER_EXTERNAL'
    TRANSFER_INTERNAL      = 'TRANSFER_INTERNAL'


CATEGORY_ALIASES: dict[str, Category] = {
    # investment
    'invest':        Category.INVESTMENT,
    'investment':    Category.INVESTMENT,
    'investments':   Category.INVESTMENT,
    # food / dining
    'food':          Category.FOOD,
    'dining':        Category.FOOD,
    'restaurant':    Category.FOOD,
    'zomato':        Category.FOOD,
    'biryani':        Category.FOOD,
    'south table':        Category.FOOD,
    # groceries
    'grocery':       Category.GROCERIES,
    'groceries':     Category.GROCERIES,
    # travel
    'transport':     Category.LOCAL_TRAVEL,
    'auto':     Category.LOCAL_TRAVEL,
    'travel':        Category.LOCAL_TRAVEL,
    'cab':           Category.LOCAL_TRAVEL,
    'uber':          Category.LOCAL_TRAVEL,
    'ola':           Category.LOCAL_TRAVEL,
    'airport':       Category.LONG_TRAVEL,
    'flight':        Category.LONG_TRAVEL,
    # medical
    'health':        Category.MEDICAL,
    'medical':       Category.MEDICAL,
    'medicine':      Category.MEDICAL,
    # rent
    'rent':          Category.RENT,
    # subscription
    'subscription':  Category.SUBSCRIPTION,
    # gym
    'gym':           Category.GYM,
    # GROOMING
    'iron':          Category.GROOMING,
    'haircut':       Category.GROOMING,
    'myntra':       Category.GROOMING,
    'clothes':       Category.GROOMING,
}


def normalise_category(raw: str) -> str:
    """Map bracket text to a canonical Category value, or '' if unrecognised."""
    key = raw.strip().lower()
    cat = CATEGORY_ALIASES.get(key)
    if cat:
        return cat.value
    for member in Category:
        if member.value.lower() == key:
            return member.value
    return ''
