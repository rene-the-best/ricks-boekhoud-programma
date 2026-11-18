RULES: list[tuple[str, str, str]] = [
    ("hypotheek", "Woning / Hypotheek", "vast"),
    ("rentelasten", "Woning / Hypotheek", "vast"),
    ("huur", "Woning / Huur", "vast"),
    ("energie", "Energie & Water", "vast"),
    ("eneco", "Energie & Water", "vast"),
    ("essent", "Energie & Water", "vast"),
    ("vattenfall", "Energie & Water", "vast"),
    ("liander", "Energie & Water", "vast"),
    ("stedin", "Energie & Water", "vast"),
    ("waterleiding", "Energie & Water", "vast"),
    ("vitens", "Energie & Water", "vast"),
    ("zorgverzek", "Verzekeringen", "vast"),
    ("vgz", "Verzekeringen", "vast"),
    ("menzis", "Verzekeringen", "vast"),
    ("zilveren kruis", "Verzekeringen", "vast"),
    ("a.s.r", "Verzekeringen", "vast"),
    ("centraal beheer", "Verzekeringen", "vast"),
    ("inboedel", "Verzekeringen", "vast"),
    ("aansprakelijk", "Verzekeringen", "vast"),
    ("ziggo", "Telefoon & Internet", "vast"),
    ("kpn", "Telefoon & Internet", "vast"),
    ("t-mobile", "Telefoon & Internet", "vast"),
    ("odido", "Telefoon & Internet", "vast"),
    ("simyo", "Telefoon & Internet", "vast"),
    ("youfone", "Telefoon & Internet", "vast"),
    ("vodafone", "Telefoon & Internet", "vast"),
    ("netflix", "Abonnementen", "vast"),
    ("spotify", "Abonnementen", "vast"),
    ("disney", "Abonnementen", "vast"),
    ("videoland", "Abonnementen", "vast"),
    ("amazon prime", "Abonnementen", "vast"),
    ("albert heijn", "Boodschappen", "variabel"),
    ("jumbo", "Boodschappen", "variabel"),
    ("lidl", "Boodschappen", "variabel"),
    ("aldi", "Boodschappen", "variabel"),
    ("vomar", "Boodschappen", "variabel"),
    ("dirk van", "Boodschappen", "variabel"),
    ("hoogvliet", "Boodschappen", "variabel"),
    ("spar", "Boodschappen", "variabel"),
    ("shell", "Vervoer & Brandstof", "variabel"),
    ("bp ", "Vervoer & Brandstof", "variabel"),
    ("esso", "Vervoer & Brandstof", "variabel"),
    ("tinq", "Vervoer & Brandstof", "variabel"),
    ("parkeren", "Vervoer & Brandstof", "variabel"),
    ("parkeer", "Vervoer & Brandstof", "variabel"),
    ("ns groep", "Vervoer & Brandstof", "variabel"),
    ("gvb", "Vervoer & Brandstof", "variabel"),
    ("ret rotterdam", "Vervoer & Brandstof", "variabel"),
    ("anwb", "Vervoer & Brandstof", "variabel"),
    ("salaris", "Inkomsten", "inkomsten"),
    ("loon", "Inkomsten", "inkomsten"),
    ("vakantiegeld", "Inkomsten", "inkomsten"),
    ("rente bijgeschreven", "Inkomsten", "inkomsten"),
    ("rentebij", "Inkomsten", "inkomsten"),
    ("belastingdienst", "Belastingen", "variabel"),
    ("belasting", "Belastingen", "variabel"),
    ("waterschap", "Belastingen", "variabel"),
    ("gemeente", "Belastingen", "variabel"),
    ("kinderopvang", "Zorg & Kinderen", "variabel"),
    ("apotheek", "Zorg & Kinderen", "variabel"),
    ("huisarts", "Zorg & Kinderen", "variabel"),
    ("tandarts", "Zorg & Kinderen", "variabel"),
    ("ziekenhuis", "Zorg & Kinderen", "variabel"),
    ("gamma", "Woning & Inrichting", "variabel"),
    ("karwei", "Woning & Inrichting", "variabel"),
    ("praxis", "Woning & Inrichting", "variabel"),
    ("ikea", "Woning & Inrichting", "variabel"),
    ("action", "Woning & Inrichting", "variabel"),
    ("hema", "Woning & Inrichting", "variabel"),
    ("bol.com", "Overig", "variabel"),
    ("amazon", "Overig", "variabel"),
]


def apply(description: str) -> tuple[str, str]:
    text = description.lower()
    for needle, category, kind in RULES:
        if needle in text:
            return category, kind
    return "Overig", "variabel"


def all_categories() -> list[str]:
    cats = sorted({c for _, c, _ in RULES})
    cats.append("Overig")
    return cats


KINDS = ["vast", "variabel", "inkomsten"]
