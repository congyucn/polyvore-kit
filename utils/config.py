# number of categories
NumCate = 3
# Category name
CateName = ['top', 'bot', 'sho']
ClassName = ['top', 'bottom', 'shoe']
ClassIdx = {'top': 0, 'bottom': 1, 'shoe': 2}
NumPhase = 3
Phase = ['train', 'val', 'test']
PhaseIdx = {'train': 0, 'val': 1, 'test': 2}
# the base url for polyvore
BaseUrl = 'http://www.polyvore.com'

# only collect sets data for the 8 users in watch_users when True
WatchUsersFlag = False

IgnoreUsers = set(['pretty-girl-xo'])

WatchUsers = set([
    'fortheloveofpoly', 'hamaly', 'malenafashion27', 'colierollers', 'limass',
    'cutekawaiiandgoodlooking', 'raelee-xoxo', 'nadiasxox'])

# fashion words
FashionWords = set([
    "outerwear", "jacket", "blazer", "coat", "sweater", "top",
    "t-shirt", "shirt", "blouse", "tee", "tank", "pullover", "hoodie",
    "sweatshirt", "tunic", "cardigan", "skirt", "jeans", "jean", "pants",
    "pant", "trousers", "shorts", "dress", "jumpsuit", "leggings", "legging",
    "overalls", "overall", "shoe", "bootie", "boot", "clog", "flat", "loafer",
    "moccasin", "oxford", "pump", "sandal", "sneaker", "slipper", "shoes",
    "booties", "boots", "clogs", "flats", "loafers", "moccasins", "oxfords",
    "pumps", "sandals", "thongs", "sneakers", "slippers"])

# words for fashion categories
FashonCategories = set([
    "Clothing", "Dresses", "Skirts", "Tops", "Outerwear",
    "Jackets", "Blazers", "Coats", "Jeans", "Pants", "Shorts",
    "Jumpsuits & Rompers", "Sweatshirts & Hoodies", "Intimates", "Swimwear",
    "Activewear", "Shoes", "Athletic", "Boots", "Clogs", "Flats",
    "Loafers & Moccasins", "Oxfords", "Pumps", "Sandals", "Sneakers", "Bags",
    "Backpacks", "Handbags", "Messenger Bags", "Wallets"])

# words for nonfashion categorites
NonfashionCategories = set([
    "Jewelry", "Bracelets & Bangles", "Brooches",
    "Charms & Pendants", "Earrings", "Necklaces", "Rings", "Watches",
    "Accessories", "Belts", "Eyewear", "Gloves", "Hair Accessories", "Hats",
    "Scarves", "Tech Accessories", "Umbrellas", "Beauty", "Beauty Products",
    "Makeup", "Face Makeup", "Cheek Makeup", "Eye Makeup", "Lip Makeup",
    "Makeup Tools", "Skincare", "Face Care", "Eye Care", "Lip Care",
    "Fragrance", "Bath & Body", "Body Cleansers", "Body Moisturizers",
    "Body Treatments", "Deodorant", "Sun Care", "Haircare", "Hair Shampoo",
    "Hair Conditioner", "Styling Products", "Hair Styling Tools", "Nail Care",
    "Nail Polish", "Nail Treatments", "Manicure Tools", "Gift Sets & Kits",
    "Beauty Accessories", "Bags & Cases", "Home", "Furniture", "Lighting",
    "Rugs", "Home Decor", "Kitchen & Dining", "Bedding", "Bath", "Outdoors"])

# Top tags
_top_item_tag = set([
    "Tops", "Outerwear", "Jackets", "Blazers", "Coats",
    "Sweatshirts & Hoodies"])
# Bottom tags
_bot_item_tag = set([
    "Skirts", "Jeans", "Pants", "Shorts", "Dresses", "Jumpsuits"])
# Shoe tags
_sho_item_tag = set([
    "Shoes", "Boots", "Clogs", "Flats", "Pumps", "Sandals",
    "Loafers & Moccasins", "Athletic", "Oxfords", "Sneakers"])
# top name
ItemTag = [_top_item_tag, _bot_item_tag, _sho_item_tag]

_top_item_name = set([
    "top", "outerwear", "jacket", "blazer", "coat", "sweater", "t-shirt",
    "shirt", "blouse", "tee", "tank", "pullover", "hoodie", "sweatshirt",
    "tunic", "cardigan"])
# bottom name
_bot_item_name = set([
    "skirt", "jeans", "jean", "pants", "pant", "trousers", "shorts", "dress",
    "jumpsuit", "leggings", "legging", "overalls", "overall"])
# shoe name
_sho_item_name = set([
    "shoe", "bootie", "boot", "clog", "flat", "loafer", "moccasin", "oxford",
    "pump", "sandal", "clogs", "sandals", "thong", "sneaker", "slipper",
    "shoes", "booties", "boots", "flats", "loafers", "moccasins", "oxfords",
    "pumps", "thongs", "sneakers", "slippers"])

ItemName = [_top_item_name, _bot_item_name, _sho_item_name]

ItemKey = [ItemTag[i] | ItemName[i] for i in xrange(NumCate)]
