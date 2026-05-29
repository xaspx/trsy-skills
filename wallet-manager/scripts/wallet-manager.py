#!/usr/bin/env python3
"""
TRSY Wallet Manager — Hermes Skill
Standalone Solana wallet management with AES-256-GCM encryption.
No dependency on bank-charity or external crypto libs beyond `cryptography`.

Capabilities:
  • Create new Ed25519 Solana keypairs
  • Import from base58-encoded private key
  • Import from BIP39 mnemonic phrase (12 or 24 words)
  • Export decrypted private key (base58 or JSON array)
  • List all stored wallets
  • Session-based unlock (5-minute auto-expire)
  • Audit logging (JSONL)
"""

import os, sys, json, time, hmac, hashlib, base64, struct, secrets, argparse
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

WALLETS_DIR = Path.home() / '.hermes' / 'skills-data' / 'trsy' / 'wallets'
AUDIT_LOG = WALLETS_DIR / 'audit.jsonl'
SESSION_FILE = WALLETS_DIR / '.session'
AES_KEY_LEN = 32
SALT_LEN = 16
NONCE_LEN = 12
SESSION_TIMEOUT = 300
MAX_AUDIT_LINES = 1000
PBKDF2_ITERATIONS = 200_000

BASE58_ALPHABET = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
BASE58_ALPHABET_DEC = {c: i for i, c in enumerate(BASE58_ALPHABET)}

BIP39_ENGLISH = (
    "abandon","ability","able","about","above","absent","absorb","abstract","absurd","abuse",
    "access","accident","account","accuse","achieve","acid","acoustic","acquire","across","act",
    "action","actor","actress","actual","adapt","add","addict","address","adjust","admit",
    "adult","advance","advice","aerobic","affair","afford","afraid","again","age","agent",
    "agree","ahead","aim","air","airport","aisle","alarm","album","alcohol","alert",
    "alien","all","alley","allow","almost","alone","alpha","already","also","alter",
    "always","amateur","amazing","among","amount","amused","analyst","anchor","ancient","anger",
    "angle","angry","animal","ankle","announce","annual","another","answer","antenna","antique",
    "anxiety","any","apart","apology","appear","apple","approve","april","arch","arctic",
    "area","arena","argue","arm","armed","armor","army","around","arrange","arrest",
    "arrive","arrow","art","artifact","artist","artwork","ask","aspect","assault","asset",
    "assist","assume","asthma","athlete","atom","attack","attend","attitude","attract","auction",
    "audit","august","aunt","author","auto","autumn","average","avocado","avoid","awake",
    "aware","away","awesome","awful","awkward","axis","baby","bachelor","bacon","badge",
    "bag","balance","balcony","ball","bamboo","banana","banner","bar","barely","bargain",
    "barrel","base","basic","basket","battle","beach","bean","beauty","because","become",
    "beef","before","begin","behave","behind","believe","below","belt","bench","benefit",
    "best","betray","better","between","beyond","bicycle","bid","bike","bind","biology",
    "bird","birth","bitter","black","blade","blame","blanket","blast","bleak","bless",
    "blind","blood","blossom","blouse","blue","blur","blush","board","boat","body",
    "boil","bomb","bone","bonus","book","boost","border","boring","borrow","boss",
    "bottom","bounce","box","boy","bracket","brain","brand","brass","brave","bread",
    "breeze","brick","bridge","brief","bright","bring","brisk","broccoli","broken","bronze",
    "broom","brother","brown","brush","bubble","buddy","budget","buffalo","build","bulb",
    "bulk","bullet","bundle","bunker","burden","burger","burst","bus","business","busy",
    "butter","buyer","buzz","cabbage","cabin","cable","cactus","cage","cake","call",
    "calm","camera","camp","can","canal","cancel","candy","cannon","canoe","canvas",
    "canyon","capable","capital","captain","car","carbon","card","cargo","carpet","carry",
    "cart","case","cash","casino","castle","casual","cat","catalog","catch","category",
    "cattle","caught","cause","caution","cave","ceiling","celery","cement","census","century",
    "ceremony","certain","chair","chalk","champion","change","chaos","chapter","charge","chase",
    "chat","cheap","check","cheese","chef","cherry","chest","chicken","chief","child",
    "chimney","choice","choose","chronic","chuckle","chunk","churn","cigar","cinnamon","circle",
    "citizen","city","civil","claim","clap","clarify","claw","clay","clean","clerk",
    "clever","click","client","cliff","climb","clinic","clip","clock","clog","close",
    "cloth","cloud","clown","club","clump","cluster","clutch","coach","coast","coconut",
    "code","coffee","coil","coin","collect","color","column","combine","come","comfort",
    "comic","common","company","concert","conduct","confirm","congress","connect","consider","control",
    "convince","cook","cool","copper","copy","coral","core","corn","correct","cost",
    "cotton","couch","country","couple","course","cousin","cover","coyote","crack","cradle",
    "craft","cram","crane","crash","crater","crawl","crazy","cream","credit","creek",
    "crew","cricket","crime","crisp","critic","crop","cross","crouch","crowd","crucial",
    "cruel","cruise","crumble","crunch","crush","cry","crystal","cube","culture","cup",
    "cupboard","curious","current","curtain","curve","cushion","custom","cute","cycle","dad",
    "damage","damp","dance","danger","daring","dash","daughter","dawn","day","deal",
    "debate","debris","decade","december","decide","decline","decorate","decrease","deer","defense",
    "define","defy","degree","delay","deliver","demand","demise","denial","dentist","deny",
    "depart","depend","deposit","depth","deputy","derive","describe","desert","design","desk",
    "despair","destroy","detail","detect","develop","device","devote","diagram","dial","diamond",
    "diary","dice","diesel","diet","differ","digital","dignity","dilemma","dinner","dinosaur",
    "direct","dirt","disagree","discover","disease","dish","dismiss","disorder","display","distance",
    "divert","divide","divorce","dizzy","doctor","document","dog","doll","dolphin","domain",
    "donate","donkey","donor","door","dose","double","dove","draft","dragon","drama",
    "drastic","draw","dream","dress","drift","drill","drink","drip","drive","drop",
    "drum","dry","duck","dumb","dune","during","dust","dutch","duty","dwarf",
    "dynamic","eager","eagle","early","earn","earth","easily","east","easy","echo",
    "ecology","economy","edge","edit","educate","effort","egg","eight","either","elbow",
    "elder","electric","elegant","element","elephant","elevator","elite","else","embark","embody",
    "embrace","emerge","emotion","employ","empower","empty","enable","enact","end","endless",
    "endorse","enemy","energy","enforce","engage","engine","enhance","enjoy","enlist","enough",
    "enrich","enroll","ensure","enter","entire","entry","envelope","episode","equal","equip",
    "era","erase","erode","erosion","error","erupt","escape","essay","essence","estate",
    "eternal","ethics","evidence","evil","evoke","evolve","exact","example","excess","exchange",
    "excite","exclude","excuse","execute","exercise","exhaust","exhibit","exile","exist","exit",
    "expand","expect","expire","explain","expose","express","extend","extra","eye","eyebrow",
    "fabric","face","faculty","fade","faint","faith","fall","false","fame","family",
    "famous","fan","fancy","fantasy","farm","fashion","fat","fatal","father","fatigue",
    "fault","favorite","feature","february","federal","fee","feed","feel","female","fence",
    "festival","fetch","fever","few","fiber","fiction","field","figure","file","film",
    "filter","final","find","fine","finger","finish","fire","firm","first","fiscal",
    "fish","fit","fitness","fix","flag","flame","flash","flat","flavor","flee",
    "flight","flip","float","flock","floor","flower","fluid","flush","fly","foam",
    "focus","fog","foil","fold","follow","food","foot","force","foreign","forest",
    "forget","fork","fortune","forum","forward","fossil","foster","found","fox","fragile",
    "frame","frequent","fresh","friend","fringe","frog","front","frost","frown","frozen",
    "fruit","fuel","fun","funny","furnace","fury","future","gadget","gain","galaxy",
    "gallery","game","gap","garage","garbage","garden","garlic","garment","gas","gasp",
    "gate","gather","gauge","gaze","general","genius","genre","gentle","genuine","gesture",
    "ghost","giant","gift","giggle","ginger","giraffe","girl","give","glad","glance",
    "glare","glass","glide","glimpse","globe","gloom","glory","glove","glow","glue",
    "goat","goddess","gold","good","goose","gorilla","gospel","gossip","govern","gown",
    "grab","grace","grain","grant","grape","grass","gravity","great","green","grid",
    "grief","grit","grocery","group","grow","grunt","guard","guess","guide","guilt",
    "guitar","gun","gym","habit","hair","half","hammer","hamster","hand","happy",
    "harbor","hard","harsh","harvest","hat","have","hawk","hazard","head","health",
    "heart","heavy","hedgehog","height","hello","helmet","help","hen","hero","hidden",
    "high","hill","hint","hip","hire","history","hobby","hockey","hold","hole",
    "holiday","hollow","home","honey","hood","hope","horn","horror","horse","hospital",
    "host","hotel","hour","hover","hub","huge","human","humble","humor","hundred",
    "hungry","hunt","hurdle","hurry","hurt","husband","hybrid","ice","icon","idea",
    "identify","idle","ignore","ill","illegal","illness","image","imitate","immense","immune",
    "impact","impose","improve","impulse","inch","include","income","increase","index","indicate",
    "indoor","industry","infant","inflict","inform","inhale","inherit","initial","inject","injury",
    "inmate","inner","innocent","input","inquiry","insane","insect","inside","inspire","install",
    "intact","interest","into","invest","invite","involve","iron","island","isolate","issue",
    "item","ivory","jacket","jaguar","jar","jazz","jealous","jeans","jelly","jewel",
    "job","join","joke","journey","joy","judge","juice","jump","jungle","junior",
    "junk","just","kangaroo","keen","keep","ketchup","key","kick","kid","kidney",
    "kind","kingdom","kiss","kit","kitchen","kite","kitten","kiwi","knee","knife",
    "knock","know","lab","label","labor","ladder","lady","lake","lamp","language",
    "laptop","large","later","latin","laugh","laundry","lava","law","lawn","lawsuit",
    "layer","lazy","leader","leaf","learn","leave","lecture","left","leg","legal",
    "legend","leisure","lemon","lend","length","lens","leopard","lesson","letter","level",
    "liar","liberty","library","license","life","lift","light","like","limb","limit",
    "link","lion","liquid","list","little","live","lizard","load","loan","lobster",
    "local","lock","logic","lonely","long","loop","lottery","loud","lounge","love",
    "loyal","lucky","luggage","lumber","lunar","lunch","luxury","lyrics","machine","mad",
    "magic","magnet","maid","mail","main","major","make","mammal","man","manage",
    "mandate","mango","mansion","manual","maple","marble","march","margin","marine","market",
    "marriage","mask","mass","master","match","material","math","matrix","matter","maximum",
    "maze","meadow","mean","measure","meat","mechanic","medal","media","melody","melt",
    "member","memory","mention","menu","mercy","merge","merit","merry","mesh","message",
    "metal","method","middle","midnight","milk","million","mimic","mind","minimum","minor",
    "minute","miracle","mirror","misery","miss","mistake","mix","mixed","mixture","mobile",
    "model","modify","mom","moment","monitor","monkey","monster","month","moon","moral",
    "more","morning","mosquito","mother","motion","motor","mountain","mouse","move","movie",
    "much","muffin","mule","multiply","muscle","museum","mushroom","music","must","mutual",
    "myself","mystery","myth","naive","name","napkin","narrow","nasty","nation","nature",
    "near","neck","need","negative","neglect","neither","nephew","nerve","nest","net",
    "network","neutral","never","news","next","nice","night","noble","noise","nominee",
    "noodle","normal","north","nose","notable","note","nothing","notice","novel","now",
    "nuclear","number","nurse","nut","oak","obey","object","oblige","obscure","observe",
    "obtain","obvious","occur","ocean","october","odor","off","offer","office","often",
    "oil","okay","old","olive","olympic","omit","once","one","onion","online",
    "only","open","opera","opinion","oppose","option","orange","orbit","orchard","order",
    "ordinary","organ","orient","original","orphan","ostrich","other","outdoor","outer","output",
    "outside","oval","oven","over","own","owner","oxygen","oyster","ozone","pact",
    "paddle","page","pair","palace","palm","panda","panel","panic","panther","paper",
    "parade","parent","park","parrot","party","pass","patch","path","patient","patrol",
    "pattern","pause","pave","payment","peace","peanut","pear","peasant","pelican","pen",
    "penalty","pencil","people","pepper","perfect","permit","person","pet","phone","photo",
    "phrase","physical","piano","picnic","picture","piece","pig","pigeon","pill","pilot",
    "pink","pioneer","pipe","pistol","pitch","pizza","place","planet","plastic","plate",
    "play","player","pleasure","plenty","plot","plug","plunge","poem","poet","point",
    "polar","pole","police","pond","pony","pool","popular","portion","position","possible",
    "post","potato","pottery","poverty","powder","power","practice","praise","predict","prefer",
    "prepare","present","pretty","prevent","price","pride","primary","print","priority","prison",
    "private","prize","problem","process","produce","profit","program","project","promote","proof",
    "property","prosper","protect","proud","provide","public","pudding","pull","pulp","pulse",
    "pumpkin","punch","pupil","puppy","purchase","purity","purpose","purse","push","put",
    "puzzle","pyramid","quality","quantum","quarter","question","quick","quit","quiz","quote",
    "rabbit","raccoon","race","rack","radar","radio","rail","rain","raise","rally",
    "ramp","ranch","random","range","rapid","rare","rate","rather","raven","raw",
    "razor","ready","real","reason","rebel","rebuild","recall","receive","recipe","record",
    "recycle","reduce","reflect","reform","refuse","region","regret","regular","reject","relax",
    "release","relief","rely","remain","remember","remind","remove","render","renew","rent",
    "reopen","repair","repeat","replace","report","require","rescue","resemble","resist","resource",
    "response","result","retire","retreat","return","reunion","reveal","review","reward","rhythm",
    "rib","ribbon","rice","rich","ride","ridge","rifle","right","rigid","ring",
    "riot","ripple","risk","ritual","rival","river","road","roast","robot","robust",
    "rocket","romance","roof","rookie","room","rose","rotate","rough","round","route",
    "royal","rubber","rude","rug","rule","run","runway","rural","sad","saddle",
    "sadness","safe","sail","salad","salmon","salon","salt","salute","same","sample",
    "sand","satisfy","satoshi","sauce","sausage","save","say","scale","scan","scare",
    "scatter","scene","scheme","school","science","scissors","scorpion","scout","scrap","screen",
    "script","scrub","sea","search","season","seat","second","secret","section","security",
    "seed","seek","segment","select","sell","seminar","senior","sense","sentence","series",
    "service","session","settle","setup","seven","shadow","shaft","shallow","share","shed",
    "shell","sheriff","shield","shift","shine","ship","shiver","shock","shoe","shoot",
    "shop","short","shoulder","shove","shrimp","shrug","shuffle","shy","sibling","sick",
    "side","siege","sight","sign","silent","silk","silly","silver","similar","simple",
    "since","sing","siren","sister","situate","six","size","skate","sketch","ski",
    "skill","skin","skirt","skull","slab","slam","sleep","slender","slice","slide",
    "slight","slim","slogan","slot","slow","slush","small","smart","smile","smoke",
    "smooth","snack","snake","snap","sniff","snow","soap","soccer","social","sock",
    "soda","soft","solar","soldier","solid","solution","solve","someone","song","soon",
    "sorry","sort","soul","sound","soup","source","south","space","spare","spatial",
    "spawn","speak","special","speed","spell","spend","sphere","spice","spider","spike",
    "spin","spirit","split","spoil","sponsor","spoon","sport","spot","spray","spread",
    "spring","spy","square","squeeze","squirrel","stable","stadium","staff","stage","stairs",
    "stamp","stand","start","state","stay","steak","steel","step","stereo","stick",
    "still","sting","stock","stomach","stone","stool","story","stove","strategy","street",
    "strike","strong","struggle","student","stuff","stumble","style","subject","submit","subway",
    "success","such","sudden","suffer","sugar","suggest","suit","sun","sunny","sunset",
    "super","supply","support","suppose","sure","surface","surge","surprise","surround","survey",
    "suspect","sustain","swallow","swamp","swap","swarm","swear","sweet","swift","swim",
    "swing","switch","sword","symbol","symptom","syrup","system","table","tackle","tag",
    "tail","talent","talk","tank","tape","target","task","taste","tattoo","taxi",
    "teach","team","tell","ten","tenant","tennis","tent","term","test","text",
    "thank","that","theme","then","theory","there","they","thing","this","thought",
    "three","thrive","throw","thumb","thunder","ticket","tide","tiger","tilt","timber",
    "time","tiny","tip","tired","tissue","title","toast","tobacco","today","toddler",
    "toe","together","toilet","token","tomato","tomorrow","tone","tongue","tonight","tool",
    "tooth","top","topic","topple","torch","tornado","tortoise","toss","total","tourist",
    "toward","tower","town","toy","track","trade","traffic","tragic","train","transfer",
    "trap","trash","travel","tray","treat","tree","trend","trial","tribe","trick",
    "trigger","trim","trip","trophy","trouble","truck","true","truly","trumpet","trust",
    "truth","try","tube","tuition","tumble","tuna","tunnel","turkey","turn","turtle",
    "twelve","twenty","twice","twin","twist","two","type","typical","ugly","umbrella",
    "unable","unaware","uncle","uncover","under","undo","unfair","unfold","unhappy","uniform",
    "unique","unit","universe","unknown","unlock","until","unusual","unveil","update","upgrade",
    "uphold","upon","upper","upset","urban","urge","usage","use","used","useful",
    "useless","usual","utility","vacant","vacuum","vague","valid","valley","valve","van",
    "vanish","vapor","various","vast","vault","vehicle","velvet","vendor","venture","venue",
    "verb","verify","version","very","vessel","veteran","viable","vibrant","vicious","victory",
    "video","view","village","vintage","violin","virtual","virus","visa","visit","visual",
    "vital","vivid","vocal","voice","void","volcano","volume","vote","voyage","wage",
    "wagon","wait","walk","wall","walnut","want","warfare","warm","warrior","wash",
    "wasp","waste","water","wave","way","wealth","weapon","wear","weasel","weather",
    "web","wedding","weekend","weird","welcome","west","wet","whale","what","wheat",
    "wheel","when","where","whip","whisper","wide","width","wife","wild","will",
    "win","window","wine","wing","wink","winner","winter","wire","wisdom","wise",
    "wish","witness","wolf","woman","wonder","wood","wool","word","work","world",
    "worry","worth","wrap","wreck","wrestle","wrist","write","wrong","yard","year",
    "yellow","you","young","youth","zebra","zero","zone","zoo",
)
BIP39_LOOKUP = {w: i for i, w in enumerate(BIP39_ENGLISH)}

def base58_encode(data: bytes) -> str:
    n = int.from_bytes(data, 'big')
    res = []
    while n > 0:
        n, r = divmod(n, 58)
        res.append(chr(BASE58_ALPHABET[r]))
    for b in data:
        if b == 0:
            res.append('1')
        else:
            break
    return ''.join(reversed(res))

def base58_decode(s: str) -> bytes:
    n = 0
    for c in s:
        if c not in BASE58_ALPHABET_DEC:
            raise ValueError(f"Invalid base58 character: {c!r}")
        n = n * 58 + BASE58_ALPHABET_DEC[c]
    prefix = b''
    for c in s:
        if c == '1':
            prefix += b'\x00'
        else:
            break
    return prefix + n.to_bytes((n.bit_length() + 7) // 8, 'big') if n > 0 else prefix

def ensure_dir():
    WALLETS_DIR.mkdir(parents=True, exist_ok=True)
    WALLETS_DIR.chmod(0o700)

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=AES_KEY_LEN,
                     salt=salt, iterations=PBKDF2_ITERATIONS)
    return kdf.derive(password.encode('utf-8'))

def encrypt_key(plaintext: bytes, aes_key: bytes) -> tuple[bytes, bytes]:
    aesgcm = AESGCM(aes_key)
    nonce = secrets.token_bytes(NONCE_LEN)
    return nonce, aesgcm.encrypt(nonce, plaintext, None)

def decrypt_key(ciphertext: bytes, nonce: bytes, aes_key: bytes) -> bytes:
    aesgcm = AESGCM(aes_key)
    return aesgcm.decrypt(nonce, ciphertext, None)

def audit_log(action: str, detail: str, wallet: str = ""):
    ensure_dir()
    entry = {"ts": datetime.now(timezone.utc).isoformat(), "action": action,
              "detail": detail, "wallet": wallet}
    with open(AUDIT_LOG, 'a') as f:
        f.write(json.dumps(entry) + '\n')
    lines = AUDIT_LOG.read_text().strip().split('\n')
    if len(lines) > MAX_AUDIT_LINES:
        AUDIT_LOG.write_text('\n'.join(lines[-MAX_AUDIT_LINES:]) + '\n')

def wallet_path(name: str) -> Path:
    return WALLETS_DIR / f"{name}.json"

def get_session() -> dict | None:
    if not SESSION_FILE.exists():
        return None
    try:
        data = json.loads(SESSION_FILE.read_text())
        if time.time() > data["expires_at"]:
            SESSION_FILE.unlink(missing_ok=True)
            return None
        return data
    except (json.JSONDecodeError, KeyError):
        SESSION_FILE.unlink(missing_ok=True)
        return None

def check_integrity(data: dict, aes_key_b64: str) -> bool:
    expected = hmac.new("TRSY_SESSION".encode(), aes_key_b64.encode(), 'sha256').hexdigest()
    return hmac.compare_digest(data.get("key_check", ""), expected)

def cmd_unlock(args):
    password = args.password or input("🔐 Enter session password: ")
    ensure_dir()
    salt = secrets.token_bytes(SALT_LEN)
    aes_key = derive_key(password, salt)
    expires_at = time.time() + SESSION_TIMEOUT
    aes_key_b64 = base64.b64encode(aes_key).decode()
    key_check = hmac.new("TRSY_SESSION".encode(), aes_key_b64.encode(), 'sha256').hexdigest()
    session = {"expires_at": expires_at, "salt": base64.b64encode(salt).decode(),
               "key_check": key_check, "aes_key_b64": aes_key_b64}
    SESSION_FILE.write_text(json.dumps(session))
    SESSION_FILE.chmod(0o600)
    print(f"✅ Session unlocked for {SESSION_TIMEOUT//60} minutes.")

def cmd_lock(args):
    SESSION_FILE.unlink(missing_ok=True)
    print("🔒 Session locked.")

def cmd_status(args):
    session = get_session()
    if session:
        remaining = int(session["expires_at"] - time.time())
        print(f"🔓 Session active — expires in {remaining//60}m {remaining%60}s")
    else:
        print("🔒 No active session. Run 'unlock' first.")
    ensure_dir()
    wallets = list(WALLETS_DIR.glob("*.json"))
    print(f"📁 Wallets directory: {WALLETS_DIR}")
    print(f"📊 Wallets stored: {len(wallets)}")

def cmd_create(args):
    session = get_session()
    if not session:
        print("❌ No active session. Run 'unlock' first.")
        return
    name = args.name
    if wallet_path(name).exists():
        print(f"❌ Wallet '{name}' already exists.")
        return
    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes_raw()
    public_bytes = private_key.public_key().public_bytes_raw()
    public_key = base58_encode(public_bytes)
    aes_key = base64.b64decode(session["aes_key_b64"])
    nonce, ciphertext = encrypt_key(private_bytes, aes_key)
    ensure_dir()
    wallet = {"name": name, "public_key": public_key,
              "encrypted_key": base64.b64encode(ciphertext).decode(),
              "nonce": base64.b64encode(nonce).decode(),
              "created_at": datetime.now(timezone.utc).isoformat(),
              "import_method": "create"}
    wallet_path(name).write_text(json.dumps(wallet, indent=2))
    wallet_path(name).chmod(0o600)
    audit_log("create", f"Created wallet {name}", name)
    print(f"✅ Wallet '{name}' created.")
    print(f"   Public key: {public_key}")

def cmd_import_private(args):
    session = get_session()
    if not session:
        print("❌ No active session. Run 'unlock' first.")
        return
    name = args.name
    if wallet_path(name).exists():
        print(f"❌ Wallet '{name}' already exists.")
        return
    try:
        raw = base58_decode(args.key.strip())
    except ValueError as e:
        print(f"❌ Invalid base58: {e}")
        return
    if len(raw) not in (32, 64):
        print(f"❌ Invalid key length: got {len(raw)} bytes, expected 32 or 64.")
        return
    seed = raw[:32]
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    private_key = Ed25519PrivateKey.from_private_bytes(seed)
    public_bytes = private_key.public_key().public_bytes_raw()
    public_key = base58_encode(public_bytes)
    aes_key = base64.b64decode(session["aes_key_b64"])
    nonce, ciphertext = encrypt_key(seed, aes_key)
    ensure_dir()
    wallet = {"name": name, "public_key": public_key,
              "encrypted_key": base64.b64encode(ciphertext).decode(),
              "nonce": base64.b64encode(nonce).decode(),
              "created_at": datetime.now(timezone.utc).isoformat(),
              "import_method": "private_key"}
    wallet_path(name).write_text(json.dumps(wallet, indent=2))
    wallet_path(name).chmod(0o600)
    audit_log("import_private", f"Imported wallet {name}", name)
    print(f"✅ Wallet '{name}' imported from base58 private key.")
    print(f"   Public key: {public_key}")

def cmd_import_mnemonic(args):
    session = get_session()
    if not session:
        print("❌ No active session. Run 'unlock' first.")
        return
    name = args.name
    if wallet_path(name).exists():
        print(f"❌ Wallet '{name}' already exists.")
        return
    words = args.phrase.strip().lower().split()
    word_count = len(words)
    if word_count not in (12, 15, 18, 21, 24):
        print(f"❌ Invalid word count: {word_count}. Expected 12, 15, 18, 21, or 24.")
        return
    for w in words:
        if w not in BIP39_LOOKUP:
            print(f"❌ '{w}' is not in the BIP39 English wordlist.")
            return
    bits = word_count * 11
    entropy_bits = bits - bits // 33
    entropy_bytes = entropy_bits // 8
    combined = 0
    for w in words:
        combined = (combined << 11) | BIP39_LOOKUP[w]
    entropy = (combined >> (bits - entropy_bits)).to_bytes(entropy_bytes, 'big')
    checksum_bits = bits // 33
    computed_checksum = hashlib.sha256(entropy).digest()[0] >> (8 - checksum_bits)
    actual_checksum = combined & ((1 << checksum_bits) - 1)
    if computed_checksum != actual_checksum:
        print(f"❌ Mnemonic checksum mismatch. Please verify the phrase.")
        return
    passphrase = args.passphrase or ""
    seed = hashlib.pbkdf2_hmac('sha512', ' '.join(words).encode(),
                                ("mnemonic" + passphrase).encode(), 2048, dklen=64)
    private_seed = seed[:32]
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    private_key = Ed25519PrivateKey.from_private_bytes(private_seed)
    public_bytes = private_key.public_key().public_bytes_raw()
    public_key = base58_encode(public_bytes)
    aes_key = base64.b64decode(session["aes_key_b64"])
    nonce, ciphertext = encrypt_key(private_seed, aes_key)
    ensure_dir()
    wallet = {"name": name, "public_key": public_key,
              "encrypted_key": base64.b64encode(ciphertext).decode(),
              "nonce": base64.b64encode(nonce).decode(),
              "created_at": datetime.now(timezone.utc).isoformat(),
              "import_method": "mnemonic"}
    wallet_path(name).write_text(json.dumps(wallet, indent=2))
    wallet_path(name).chmod(0o600)
    audit_log("import_mnemonic", f"Imported wallet {name} from mnemonic", name)
    print(f"✅ Wallet '{name}' imported from BIP39 mnemonic.")
    print(f"   Public key: {public_key}")

def cmd_export(args):
    session = get_session()
    if not session:
        print("❌ No active session. Run 'unlock' first.")
        return
    name = args.name
    path = wallet_path(name)
    if not path.exists():
        print(f"❌ Wallet '{name}' not found.")
        return
    wallet = json.loads(path.read_text())
    aes_key = base64.b64decode(session["aes_key_b64"])
    ciphertext = base64.b64decode(wallet["encrypted_key"])
    nonce = base64.b64decode(wallet["nonce"])
    try:
        private_bytes = decrypt_key(ciphertext, nonce, aes_key)
    except Exception:
        print("❌ Decryption failed. Wrong password?")
        return
    public_bytes_hex = bytes.fromhex("0000000000000000000000000000000000000000")
    fmt = args.format or "base58"
    if fmt == "base58":
        keypair_bytes = private_bytes + base58_decode(wallet["public_key"])
        key_str = base58_encode(keypair_bytes)
        print(f"🔑 Private key (base58): {key_str}")
    elif fmt == "json":
        pub_key = base58_decode(wallet["public_key"])
        full_keypair = list(private_bytes) + list(pub_key)
        print(f"🔑 Private key (JSON array): {json.dumps(full_keypair)}")
    elif fmt == "hex":
        print(f"🔑 Private key (hex): {private_bytes.hex()}")
    else:
        print(f"❌ Unknown format: {fmt}. Use: base58, json, hex")
    audit_log("export", f"Exported {name} in {fmt} format", name)

def cmd_list(args):
    ensure_dir()
    wallets = sorted(WALLETS_DIR.glob("*.json"))[:10]
    if not wallets:
        print("📋 No wallets stored.")
        return
    print(f"📋 Stored wallets ({len(wallets)}):")
    for w in wallets:
        data = json.loads(w.read_text())
        name = data.get("name", w.stem)
        pub = data.get("public_key", "?")
        created = data.get("created_at", "?")
        method = data.get("import_method", "?")
        print(f"  • {name}")
        print(f"    Public key : {pub}")
        print(f"    Created    : {created[:19]}")
        print(f"    Method     : {method}")

def cmd_audit(args):
    if not AUDIT_LOG.exists():
        print("📋 No audit entries.")
        return
    lines = AUDIT_LOG.read_text().strip().split('\n')
    limit = args.limit or 10
    entries = lines[-limit:]
    print(f"📋 Recent audit entries ({len(entries)}):")
    for line in entries:
        try:
            e = json.loads(line)
            ts = e.get("ts", "")[:19]
            act = e.get("action", "")
            w = e.get("wallet", "")
            detail = e.get("detail", "")
            print(f"  [{ts}] {act:20s} wallet={w}")
            print(f"    {detail}")
        except json.JSONDecodeError:
            pass

def main():
    parser = argparse.ArgumentParser(description="TRSY Wallet Manager")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("unlock").add_argument("-p", "--password", help="Session password")
    sub.add_parser("lock")
    sub.add_parser("status")
    create_p = sub.add_parser("create")
    create_p.add_argument("-n", "--name", required=True)
    imp_p = sub.add_parser("import-private")
    imp_p.add_argument("key")
    imp_p.add_argument("-n", "--name", required=True)
    imp_m = sub.add_parser("import-mnemonic")
    imp_m.add_argument("-n", "--name", required=True)
    imp_m.add_argument("-p", "--phrase", required=True)
    imp_m.add_argument("--passphrase", default="")
    exp_p = sub.add_parser("export")
    exp_p.add_argument("name")
    exp_p.add_argument("-f", "--format", choices=["base58", "json", "hex"], default="base58")
    sub.add_parser("list")
    aud_p = sub.add_parser("audit")
    aud_p.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    if args.command == "unlock":
        cmd_unlock(args)
    elif args.command == "lock":
        cmd_lock(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "create":
        cmd_create(args)
    elif args.command == "import-private":
        cmd_import_private(args)
    elif args.command == "import-mnemonic":
        cmd_import_mnemonic(args)
    elif args.command == "export":
        cmd_export(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "audit":
        cmd_audit(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
