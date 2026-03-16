from enum import Enum


class Category(str, Enum):
    RENT                   = 'RENT'
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
    INVESTMENT             = 'INVESTMENT'


# Keyword → category map. Add your own keywords and #hashtag shortcuts here.
USER_OVERRIDES: dict[str, Category] = {
    'invest':            Category.INVESTMENT,
    'investment':        Category.INVESTMENT,
    'investments':       Category.INVESTMENT,
    'mutual fund':       Category.INVESTMENT,

    'food':              Category.FOOD,
    'dining':            Category.FOOD,
    'restaurant':        Category.FOOD,
    'zomato':            Category.FOOD,
    'biryani':           Category.FOOD,
    'south table':       Category.FOOD,
    'southtable':        Category.FOOD,
    'lunch':             Category.FOOD,
    'dinner':            Category.FOOD,
    'breakfast':         Category.FOOD,
    'burger':            Category.FOOD,
    'ramen':             Category.FOOD,
    'sushi':             Category.FOOD,
    'meghana':           Category.FOOD,

    'grocery':           Category.GROCERIES,
    'groceries':         Category.GROCERIES,
    'zepto':             Category.GROCERIES,
    'blinkit':           Category.GROCERIES,
    'mangomart':         Category.GROCERIES,
    'mango mart':        Category.GROCERIES,
    'stationary':        Category.GROCERIES,

    'transport':         Category.LOCAL_TRAVEL,
    'auto':              Category.LOCAL_TRAVEL,
    'travel':            Category.LOCAL_TRAVEL,
    'cab':               Category.LOCAL_TRAVEL,
    'uber':              Category.LOCAL_TRAVEL,
    'ola':               Category.LOCAL_TRAVEL,
    'parking':           Category.LOCAL_TRAVEL,
    'petrol':            Category.LOCAL_TRAVEL,

    'airport':           Category.LONG_TRAVEL,
    'flight':            Category.LONG_TRAVEL,

    'health':            Category.MEDICAL,
    'medical':           Category.MEDICAL,
    'medicine':          Category.MEDICAL,
    'doctor':            Category.MEDICAL,
    'blood test':        Category.MEDICAL,
    'bloodtest':         Category.MEDICAL,
    'dentist':           Category.MEDICAL,

    'rent':              Category.RENT,
    'cook':              Category.RENT,
    'maid':              Category.RENT,
    'insta help':        Category.RENT,
    'instahelp':         Category.RENT,
    'plumber':           Category.RENT,
    'electrician':       Category.RENT,
    'carpenter':         Category.RENT,
    'asma':              Category.RENT,
    'cylinder':          Category.RENT,


    'subscription':      Category.SUBSCRIPTION,
    'youtube':           Category.SUBSCRIPTION,
    'icloud':            Category.SUBSCRIPTION,
    'netflix':           Category.SUBSCRIPTION,
    'prime':             Category.SUBSCRIPTION,
    'jio':               Category.SUBSCRIPTION,
    'jiofiber':          Category.SUBSCRIPTION,
    'recharge':          Category.SUBSCRIPTION,
    'zerodha':           Category.SUBSCRIPTION,

    'gym':               Category.GYM,
    'protein':           Category.GYM,
    'vitamin':           Category.GYM,
    'training':          Category.GYM,

    'iron':              Category.GROOMING,
    'haircut':           Category.GROOMING,
    'myntra':            Category.GROOMING,
    'clothes':           Category.GROOMING,
    'tshirt':            Category.GROOMING,
    'sweatshirt':        Category.GROOMING,
    'jeans':             Category.GROOMING,
    'socks':             Category.GROOMING,
    'vest':              Category.GROOMING,
    'bra':               Category.GROOMING,
    'shorts':            Category.GROOMING,

    'salary':            Category.TRANSFER_EXTERNAL,
    'externaltransfer':  Category.TRANSFER_EXTERNAL,
    'poker':             Category.TRANSFER_EXTERNAL,
    'tax':               Category.TRANSFER_EXTERNAL,
    'ITR':               Category.TRANSFER_EXTERNAL,
    'donate':            Category.TRANSFER_EXTERNAL,

    'internaltransfer':  Category.TRANSFER_INTERNAL,
    'pnb':               Category.TRANSFER_INTERNAL,
    'cash':              Category.TRANSFER_INTERNAL,

    'flowers':           Category.TREATS_AND_GIFTS,
    'gift':              Category.TREATS_AND_GIFTS,
    'treat':             Category.TREATS_AND_GIFTS,

    'home':              Category.HOME,

    'book':              Category.OTHER_NON_ESSENTIALS,

    'party':             Category.REGULAR_PARTY_VACATION,
    'movie':             Category.REGULAR_PARTY_VACATION,
    'show':              Category.REGULAR_PARTY_VACATION,
    'concert':           Category.REGULAR_PARTY_VACATION,
}

# Personal name aliases — maps nickname/shorthand to the name as it appears
# in the WhatsApp chat (case-insensitive). The target must match an actual
# sender, otherwise the override is rejected and goes to needs_review.
PERSON_ALIASES: dict[str, str] = {
    # 'priya': 'priyasha',
    # 'piyu':  'priyasha',
}


def normalise_category(raw: str) -> str:
    """Map a #hashtag to a canonical Category value, or '' if unrecognised."""
    key = raw.strip().lower()

    # 1. USER_OVERRIDES
    cat = USER_OVERRIDES.get(key)
    if cat:
        return cat.value

    # 2. Exact enum match (case-insensitive)
    for member in Category:
        if member.value.lower() == key:
            return member.value

    # 4. Underscore-normalised match (e.g. #internaltransfer → TRANSFER_INTERNAL)
    key_flat = key.replace('_', '').replace(' ', '')
    for member in Category:
        if member.value.lower().replace('_', '') == key_flat:
            return member.value

    return ''
