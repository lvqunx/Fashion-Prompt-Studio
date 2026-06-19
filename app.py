import json
import os
import sys
import random
import webbrowser
import webview

# Handle frozen mode
if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, _base)
from fashion_data import CATEGORIES


# ── Key grouping (same logic as before) ────────────
KEY_GROUP = {
    "classic_style": "style", "trend_style": "style",
    "scene_style": "style", "season_style": "style",
    "skin_tone": "skin_tone", "skin_undertone": "skin_undertone",
    "body_type": "body_type", "age_range": "age_range", "aura": "aura",
    "hair_length": "hair", "hair_texture": "hair",
    "hair_updo": "hair", "bangs": "hair", "hair_color": "hair_color",
    "base_makeup": "makeup", "eye_makeup": "makeup",
    "lip_makeup": "makeup", "blush": "makeup",
    "contour_highlight": "makeup", "eyebrow": "makeup",
    "top_type": "top", "neckline": "neckline",
    "sleeve_type": "sleeve", "fabric": "fabric",
    "structural_detail": "detail",
    "outerwear_type": "outerwear", "outerwear_silhouette": "outerwear",
    "outerwear_detail": "outerwear",
    "pants_type": "bottom", "skirt_type": "bottom",
    "waist_type": "bottom", "bottom_detail": "bottom",
    "bottom_length": "bottom",
    "dress_type": "dress", "dress_length": "dress",
    "dress_detail": "dress",
    "heels_type": "shoes", "flats_type": "shoes",
    "sneakers_type": "shoes", "boots_type": "shoes",
    "sandals_type": "shoes", "other_shoes": "shoes",
    "heel_height": "shoes", "toe_shape": "shoes",
    "bag_type": "bag",
    "necklace": "acc", "earrings": "acc",
    "hand_accessories": "acc", "head_accessories": "acc",
    "waist_accessories": "acc", "face_accessories": "acc",
    "other_accessories": "acc",
    "color_basic": "color", "color_trend": "color",
    "color_macaron": "color", "color_earth": "color",
    "color_scheme": "color",
    "pattern": "pattern",
}

IMPORTANT_GROUPS = {"neckline", "fabric", "sleeve", "dress", "shoes", "bag", "pattern", "detail"}

TAG_ORDER = [
    "quality", "style", "body_type", "skin_tone", "skin_undertone",
    "age_range", "aura", "hair", "hair_color", "makeup",
    "top", "neckline", "sleeve", "fabric", "detail",
    "outerwear", "bottom", "dress",
    "shoes", "bag", "acc", "color", "pattern",
]

EXCLUSIVE_GROUPS = {
    "shoe_type": ["heels_type", "flats_type", "sneakers_type",
                  "boots_type", "sandals_type", "other_shoes"],
}

# ── Module mutually exclusive routes ─────────────────
OUTFIT_ROUTES = {
    "dress": ["dress_type", "dress_length", "dress_detail"],
    "separate": ["top_type", "neckline", "sleeve_type", "fabric", "structural_detail",
                 "pants_type", "skirt_type", "waist_type", "bottom_detail", "bottom_length"],
}

# ── Curated outfit random config ────────────────────
# Instead of letting every module fire independently, we define
# "outfit zones" that each contribute a controlled amount.

# Style zone: pick exactly ONE style direction, not all four
STYLE_MODULES = ["classic_style", "trend_style", "scene_style", "season_style"]

# Hair zone: mandatory length + optionally 1-2 other hair details
HAIR_MANDATORY = "hair_length"
HAIR_OPTIONAL = ["hair_texture", "hair_updo", "bangs", "hair_color"]
HAIR_OPTIONAL_MAX = 2  # pick 0-2 from these

# Makeup zone: pick 2-3 sub-modules max (not all 6)
MAKEUP_MODULES = ["base_makeup", "eye_makeup", "lip_makeup", "blush",
                   "contour_highlight", "eyebrow"]
MAKEUP_MANDATORY = ["base_makeup", "lip_makeup"]  # always pick these two
MAKEUP_OPTIONAL_MAX = 1  # add 0-1 more makeup detail

# Person zone: body type mandatory, optionally 1 other
PERSON_MODULES = ["skin_tone", "skin_undertone", "body_type", "age_range", "aura"]
PERSON_MANDATORY = "body_type"
PERSON_OPTIONAL_MAX = 2

# Color zone: pick ONE color module, not all five
COLOR_MODULES = ["color_basic", "color_trend", "color_macaron", "color_earth", "color_scheme"]
COLOR_OPTION_MAX = 2  # 1-2 colors from the chosen module

# Accessory zone: pick 1-2 sub-modules max, not all 7
ACC_MODULES = ["necklace", "earrings", "hand_accessories", "head_accessories",
               "waist_accessories", "face_accessories", "other_accessories"]
ACC_MAX_MODULES = 2  # how many acc sub-modules to activate
ACC_MODULE_PROB = {  # probability each sub-module gets picked when eligible
    "necklace": 0.40, "earrings": 0.35,
    "hand_accessories": 0.20, "head_accessories": 0.25,
    "waist_accessories": 0.10, "face_accessories": 0.15,
    "other_accessories": 0.15,
}

# Outerwear: optional, 0.5 probability of including any
OUTERWEAR_MODULES = ["outerwear_type", "outerwear_silhouette", "outerwear_detail"]
OUTERWEAR_PROB = 0.50
OUTERWEAR_MAX_MODULES = 2  # pick 1-2 outerwear details if activated

# Shoe extras: optional detail modules
SHOE_DETAIL_MODULES = ["heel_height", "toe_shape"]
SHOE_DETAIL_PROB = 0.50

# Multi-select modules: curated count limits
MULTI_COUNT = {
    "classic_style": (1, 1), "trend_style": (1, 1), "scene_style": (1, 1),
    "season_style": (1, 1),
    "structural_detail": (1, 1), "dress_detail": (1, 1),
    "eye_makeup": (1, 1), "contour_highlight": (1, 1),
    "aura": (1, 2),
    "color_basic": (1, 2), "color_trend": (1, 2), "color_macaron": (1, 2),
    "color_earth": (1, 2), "color_scheme": (1, 1),
}

# Option probability boost for common/popular items
OPTION_BOOST = {
    "scene_style": {"日常出行": 2.0, "通勤干练": 1.8, "休闲放松": 1.5},
    "classic_style": {"法式慵懒": 1.5, "意式优雅": 1.3, "北欧极简": 1.2},
    "trend_style": {"极简利落风": 1.5, "老钱风": 1.3, "静奢风": 1.4},
    "body_type": {"匀称身材": 1.5, "纤细修长": 1.3},
    "hair_length": {"长发": 1.5, "中长发": 1.3},
    "hair_texture": {"直发": 1.3, "微卷": 1.2},
    "color_basic": {"黑色": 1.3, "白色": 1.3, "米色": 1.2, "灰色": 1.1},
    "pattern": {"纯色": 2.0, "条纹": 1.3, "格纹": 1.2},
}


def _get_group_en(selections, group):
    result = []
    for k, opts in selections.items():
        if KEY_GROUP.get(k) == group:
            result.extend(o["en"] for o in opts if o.get("en"))
    return result

def _get_group_desc(selections, group):
    result = []
    for k, opts in selections.items():
        if KEY_GROUP.get(k) == group:
            result.extend(o["desc"] for o in opts if o.get("desc"))
    return result

# ── Prompt generators ──────────────────────────────
def generate_zimage(selections):
    """Z-Image structured natural language Chinese prompt.
    Format: 画质前缀 + 人物主体 + 服装搭配 + 细节补充 + 风格色调
    Uses (关键词:权重) for emphasis, per Z-Image official recommendation."""
    parts = []

    # ── 画质前缀 ──
    parts.append("(杰作:1.3)，(最佳画质:1.2)，超精细，8k分辨率，单人女性")

    # ── 人物主体：体型+肤色+气质 ──
    body_d = _get_group_desc(selections, "body_type")
    skin_d = _get_group_desc(selections, "skin_tone")
    skinu_d = _get_group_desc(selections, "skin_undertone")
    age_d = _get_group_desc(selections, "age_range")
    aura_d = _get_group_desc(selections, "aura")

    person_parts = []
    if age_d: person_parts.append(age_d[0])
    if body_d: person_parts.append(body_d[0])
    skin_combo = []
    if skin_d: skin_combo.append(skin_d[0])
    if skinu_d: skin_combo.append(skinu_d[0])
    if skin_combo: person_parts.append("".join(skin_combo))
    if person_parts:
        parts.append("一位" + "，".join(person_parts) + "的女性")
    if aura_d:
        parts.append("散发出" + "与".join(aura_d) + "的气质")

    # ── 发型 ──
    hair_d = _get_group_desc(selections, "hair")
    hair_c = _get_group_desc(selections, "hair_color")
    hair_all = hair_d + hair_c
    if hair_all:
        parts.append("".join(hair_all))

    # ── 妆容 ──
    mu_d = _get_group_desc(selections, "makeup")
    if mu_d:
        parts.append("".join(mu_d))

    # ── 服装搭配：连衣裙路线 vs 上+下路线 ──
    nk_d = _get_group_desc(selections, "neckline")
    fb_d = _get_group_desc(selections, "fabric")
    sl_d = _get_group_desc(selections, "sleeve")
    dt_d = _get_group_desc(selections, "detail")
    dr_d = _get_group_desc(selections, "dress")
    tp_d = _get_group_desc(selections, "top")
    ow_d = _get_group_desc(selections, "outerwear")
    bm_d = _get_group_desc(selections, "bottom")

    # 服装修饰词
    mods = []
    if nk_d: mods.append(nk_d[0].replace("设计", ""))
    if fb_d: mods.append(fb_d[0].replace("面料", "").replace("设计", ""))
    if sl_d: mods.append(sl_d[0].replace("设计", ""))
    mod_prefix = "".join(mods)

    cloth_parts = []
    if dr_d:
        cloth_parts.append("身穿" + mod_prefix + (dr_d[0]))
    else:
        if tp_d: cloth_parts.append("身穿" + mod_prefix + (tp_d[0]))
        if bm_d: cloth_parts.append("搭配" + bm_d[0])
    if dt_d: cloth_parts.append("带有" + "、".join(dt_d) + "细节")
    if ow_d: cloth_parts.append("外搭" + ow_d[0])
    if cloth_parts:
        parts.append("，".join(cloth_parts))

    # ── 配饰与鞋包 ──
    sh_d = _get_group_desc(selections, "shoes")
    bg_d = _get_group_desc(selections, "bag")
    ac_d = _get_group_desc(selections, "acc")
    acc_parts = []
    if sh_d: acc_parts.append("脚踩" + "、".join(sh_d[:2]))
    if bg_d: acc_parts.append("手持" + bg_d[0])
    if ac_d: acc_parts.append("佩戴" + "、".join(ac_d))
    if acc_parts:
        parts.append("，".join(acc_parts))

    # ── 风格 + 色调 ──
    st_d = _get_group_desc(selections, "style")
    co_d = _get_group_desc(selections, "color")
    pt_d = _get_group_desc(selections, "pattern")
    style_color = []
    if st_d: style_color.append("".join(st_d) + "风格")
    color_parts = []
    if co_d: color_parts.append("以" + "、".join(co_d[:3]) + "为主色调")
    if pt_d: color_parts.append("搭配" + "、".join(pt_d) + "元素")
    if color_parts: style_color.append("，".join(color_parts))
    if style_color:
        parts.append("，".join(style_color))

    # ── 对重要元素加权 ──
    # Re-wrap important groups with weight syntax
    result = "，".join(parts)
    for g in IMPORTANT_GROUPS:
        group_descs = _get_group_desc(selections, g)
        for d in group_descs:
            # Only add weight if the desc appears in result and hasn't been weighted already
            plain = d
            if plain in result and f"({plain}" not in result:
                result = result.replace(plain, f"({plain}:1.2)", 1)

    return result

def generate_qwen(selections):
    p = []
    style_d = _get_group_desc(selections, "style")
    aura_d = _get_group_desc(selections, "aura")
    body_d = _get_group_desc(selections, "body_type")
    skin_d = _get_group_desc(selections, "skin_tone")
    age_d = _get_group_desc(selections, "age_range")
    ps = []
    if body_d: ps.append(body_d[0])
    if skin_d: ps.append(skin_d[0])
    pstr = "".join(ps) if ps else "优雅"
    if style_d:
        p.append(f"一位{pstr}的女性，{age_d[0] if age_d else ''}{'，'.join(style_d)}风格。")
    else:
        p.append(f"一位{pstr}的女性。")
    if aura_d:
        p.append(f"散发出{'、'.join(aura_d)}的气质。")
    hair_d = _get_group_desc(selections, "hair")
    hair_c = _get_group_desc(selections, "hair_color")
    ha = hair_d + hair_c
    if ha: p.append(f"{'，'.join(ha)}。")
    mu_d = _get_group_desc(selections, "makeup")
    if mu_d: p.append(f"{'，'.join(mu_d)}。")
    nk_d = _get_group_desc(selections, "neckline")
    fb_d = _get_group_desc(selections, "fabric")
    sl_d = _get_group_desc(selections, "sleeve")
    dt_d = _get_group_desc(selections, "detail")
    dr_d = _get_group_desc(selections, "dress")
    tp_d = _get_group_desc(selections, "top")
    ow_d = _get_group_desc(selections, "outerwear")
    bt_d = _get_group_desc(selections, "bottom")
    mods = []
    if nk_d: mods.append(nk_d[0].replace("设计",""))
    if fb_d: mods.append(fb_d[0].replace("面料","").replace("设计",""))
    if sl_d: mods.append(sl_d[0].replace("设计",""))
    mod = "".join(mods)
    cp = []
    if dr_d:
        cp.append(f"身穿{mod}{dr_d[0]}")
    else:
        if tp_d: cp.append(f"身穿{mod}{tp_d[0]}")
        if bt_d: cp.append(f"搭配{bt_d[0]}")
    if dt_d: cp.append(f"带有{'、'.join(dt_d)}细节")
    if ow_d: cp.append(f"外搭{ow_d[0]}")
    if cp: p.append("，".join(cp) + "。")
    sh_d = _get_group_desc(selections, "shoes")
    if sh_d: p.append(f"脚踩{'、'.join(sh_d[:2])}。")
    bg_d = _get_group_desc(selections, "bag")
    if bg_d: p.append(f"手持{bg_d[0]}。")
    ac_d = _get_group_desc(selections, "acc")
    if ac_d: p.append(f"佩戴{'、'.join(ac_d)}。")
    co_d = _get_group_desc(selections, "color")
    pt_d = _get_group_desc(selections, "pattern")
    cc = []
    if co_d: cc.append(f"整体以{'、'.join(co_d[:3])}为主色调")
    if pt_d: cc.append(f"搭配{'、'.join(pt_d)}元素")
    if cc: p.append("，".join(cc) + "。")
    return "".join(p)

def generate_flux(selections):
    sents = []
    bt = _get_group_en(selections, "body_type")
    sk = _get_group_en(selections, "skin_tone")
    ag = _get_group_en(selections, "age_range")
    au = _get_group_en(selections, "aura")
    bs = bt[0].replace(" figure","").replace(" body","").replace(" skin","") if bt else "slender"
    ss = sk[0].replace(" skin","") if sk else "fair"
    ags = ag[0] if ag else ""
    he = _get_group_en(selections, "hair")
    hc = _get_group_en(selections, "hair_color")
    if he and hc:
        hs = f"{hc[0]} {he[0]}"
    elif he: hs = he[0]
    elif hc: hs = hc[0]
    else: hs = "styled hair"
    nk = _get_group_en(selections, "neckline")
    fb = _get_group_en(selections, "fabric")
    sl = _get_group_en(selections, "sleeve")
    dt = _get_group_en(selections, "detail")
    tp = _get_group_en(selections, "top")
    dr = _get_group_en(selections, "dress")
    ow = _get_group_en(selections, "outerwear")
    bm = _get_group_en(selections, "bottom")
    sh = _get_group_en(selections, "shoes")
    bg = _get_group_en(selections, "bag")
    ac = _get_group_en(selections, "acc")
    adj = []
    if nk: adj.append(nk[0])
    if fb: adj.append(fb[0].replace(" fabric",""))
    if sl: adj.append(sl[0])
    cpfx = " ".join(adj)
    if cpfx: cpfx += " "
    wp = []
    if dr: wp.append(f"a {cpfx}{dr[0]}")
    else:
        if tp: wp.append(f"a {cpfx}{tp[0]}")
        if bm: wp.append(f"paired with {bm[0]}")
    if dt: wp.append(f"with {' and '.join(dt[:3])} details")
    if ow: wp.append(f"layered with {ow[0]}")
    ws = ", ".join(wp) if wp else "stylish clothing"
    extras = []
    if sh: extras.append(sh[0])
    if bg: extras.append(f"carrying a {bg[0]}")
    if ac: extras.append(f"accessorized with {', '.join(ac[:3])}")
    es = ", ".join(extras)
    agp = f"{ags} " if ags else ""
    main = f"A {agp}{bs} woman with {ss} skin, {hs}, wearing {ws}"
    if es: main += f", {es}"
    main += "."
    sents.append(main)
    st = _get_group_en(selections, "style")
    if st:
        aup = f" with a {' and '.join(au[:2])} atmosphere" if au else ""
        sents.append(f"{st[0].capitalize()} style{aup}.")
    co = _get_group_en(selections, "color")
    pt = _get_group_en(selections, "pattern")
    cc = []
    if co: cc.append(", ".join(co[:3]))
    if pt: cc.append(f"with {', '.join(pt)} accents")
    if cc: sents.append(f"{' and '.join(cc)} color palette.")
    return " ".join(sents)

def do_generate(selections, model):
    if model == "Z-Image":
        return generate_zimage(selections)
    elif model == "Qwen-Image":
        return generate_qwen(selections)
    elif model == "Flux":
        return generate_flux(selections)
    return ""

def _weighted_choice(options, weights=None):
    """Pick one option with optional weights."""
    if weights is None:
        return random.choice(options)
    # Build weighted list
    weighted = []
    for opt in options:
        w = weights.get(opt.get("zh", ""), 1.0)
        weighted.append((opt, w))
    total = sum(w for _, w in weighted)
    r = random.uniform(0, total)
    cum = 0
    for opt, w in weighted:
        cum += w
        if r <= cum:
            return opt
    return options[-1]


def _weighted_sample(options, count, weights=None):
    """Sample multiple options with weights, without replacement."""
    if weights is None:
        return random.sample(options, min(count, len(options)))
    pool = list(options)
    result = []
    for _ in range(min(count, len(pool))):
        if not pool:
            break
        w_list = [weights.get(opt.get("zh", ""), 1.0) for opt in pool]
        total = sum(w_list)
        r = random.uniform(0, total)
        cum = 0
        chosen_idx = 0
        for i, w in enumerate(w_list):
            cum += w
            if r <= cum:
                chosen_idx = i
                break
        result.append(pool.pop(chosen_idx))
    return result


def do_random(model, zones_enabled=None, locked=None, current_selections=None):
    """Curated outfit random — each zone contributes a controlled amount.
    zones_enabled: dict of zone_key→bool, controls which zones participate.
    locked: dict of module_key→bool, modules to preserve current selections.
    current_selections: dict of module_key→[opts], selections to preserve for locked modules."""
    if zones_enabled is None:
        zones_enabled = {}
    if locked is None:
        locked = {}
    if current_selections is None:
        current_selections = {}

    def zone_on(key):
        return zones_enabled.get(key, True)

    def is_locked(key):
        """Check if module is locked AND has current selections to preserve."""
        return locked.get(key, False) and key in current_selections and bool(current_selections.get(key))

    # Build module map
    mod_map = {}
    for cat in CATEGORIES:
        for m in cat["modules"]:
            mod_map[m["key"]] = m

    selections = {}

    def _pick(key, cnt=None):
        """Pick options for a module key. cnt overrides multi count.
        If module is locked and has current selections, preserve them."""
        if is_locked(key):
            selections[key] = current_selections[key]
            return
        m = mod_map[key]
        opts = m["options"]
        if not opts:
            return
        weights = OPTION_BOOST.get(key, {})
        if m["multi"]:
            min_c, max_c = MULTI_COUNT.get(key, (1, 2))
            if cnt:
                max_c = cnt
                min_c = max(1, cnt - 1)
            n = random.randint(min_c, max_c)
            n = min(n, len(opts))
            if weights:
                selections[key] = _weighted_sample(opts, n, weights)
            else:
                selections[key] = random.sample(opts, n)
        else:
            if weights:
                selections[key] = [_weighted_choice(opts, weights)]
            else:
                selections[key] = [random.choice(opts)]

    # ── Zone 1: Style — locked styles always used, otherwise pick ONE ──
    if zone_on("style"):
        locked_styles = [k for k in STYLE_MODULES if is_locked(k)]
        if locked_styles:
            for k in locked_styles:
                _pick(k, cnt=1)
        else:
            chosen_style = random.choice(STYLE_MODULES)
            _pick(chosen_style, cnt=1)
            # Season is a bonus: 30% chance to also add season
            if chosen_style != "season_style" and random.random() < 0.30:
                _pick("season_style", cnt=1)

    # ── Zone 2: Person — body_type always, locked extras forced ──
    if zone_on("person"):
        _pick("body_type")
        person_pool = [k for k in PERSON_MODULES if k != PERSON_MANDATORY]
        locked_person = [k for k in person_pool if is_locked(k)]
        for k in locked_person:
            _pick(k)
        n_person = max(0, random.randint(0, PERSON_OPTIONAL_MAX) - len(locked_person))
        remaining_pool = [k for k in person_pool if k not in locked_person]
        chosen_person = random.sample(remaining_pool, min(n_person, len(remaining_pool)))
        for k in chosen_person:
            _pick(k)

    # ── Zone 3: Hair — length always, locked extras forced ──
    if zone_on("hair"):
        _pick(HAIR_MANDATORY)
        locked_hair_opts = [k for k in HAIR_OPTIONAL if is_locked(k)]
        for k in locked_hair_opts:
            _pick(k)
        n_hair = max(0, random.randint(0, HAIR_OPTIONAL_MAX) - len(locked_hair_opts))
        remaining_hair = [k for k in HAIR_OPTIONAL if k not in locked_hair_opts]
        chosen_hair = random.sample(remaining_hair, min(n_hair, len(remaining_hair)))
        for k in chosen_hair:
            _pick(k)

    # ── Zone 4: Makeup — mandatory always, locked extras forced ──
    if zone_on("makeup"):
        for k in MAKEUP_MANDATORY:
            _pick(k)
        makeup_pool = [k for k in MAKEUP_MODULES if k not in MAKEUP_MANDATORY]
        locked_makeup = [k for k in makeup_pool if is_locked(k)]
        for k in locked_makeup:
            _pick(k)
        remaining_makeup = [k for k in makeup_pool if k not in locked_makeup]
        if remaining_makeup and random.random() < 0.60:
            extra = random.choice(remaining_makeup)
            _pick(extra)

    # ── Zone 5: Outfit route — locked modules influence dress/separate choice ──
    dress_on = zone_on("dress")
    separate_on = zone_on("separate")
    has_locked_dress = any(is_locked(k) for k in OUTFIT_ROUTES["dress"])
    has_locked_separate = any(is_locked(k) for k in OUTFIT_ROUTES["separate"])

    if has_locked_dress and not has_locked_separate:
        go_dress = True
    elif has_locked_separate and not has_locked_dress:
        go_dress = False
    elif has_locked_dress and has_locked_separate:
        go_dress = True  # both have locks, prefer dress
    elif dress_on and separate_on:
        go_dress = random.random() < 0.5
    elif dress_on:
        go_dress = True
    elif separate_on:
        go_dress = False
    else:
        go_dress = False  # fallback: separate when both off

    if go_dress:
        for k in OUTFIT_ROUTES["dress"]:
            _pick(k, cnt=1)
    else:
        _pick("top_type")
        # Locked modules forced, others probabilistic
        if is_locked("neckline") or random.random() < 0.60:
            _pick("neckline")
        if is_locked("sleeve_type") or random.random() < 0.50:
            _pick("sleeve_type")
        if is_locked("fabric") or random.random() < 0.40:
            _pick("fabric")
        if is_locked("structural_detail") or random.random() < 0.25:
            _pick("structural_detail", cnt=1)
        if is_locked("pants_type"):
            _pick("pants_type")
        elif is_locked("skirt_type"):
            _pick("skirt_type")
        elif random.random() < 0.55:
            _pick("pants_type")
        else:
            _pick("skirt_type")
        if is_locked("waist_type") or random.random() < 0.30:
            _pick("waist_type")
        if is_locked("bottom_detail") or random.random() < 0.25:
            _pick("bottom_detail", cnt=1)
        if is_locked("bottom_length") or random.random() < 0.20:
            _pick("bottom_length")

    # ── Zone 6: Shoes — locked type used, locked details forced ──
    if zone_on("shoes"):
        shoe_candidates = EXCLUSIVE_GROUPS["shoe_type"]
        locked_shoes = [k for k in shoe_candidates if is_locked(k)]
        if locked_shoes:
            _pick(locked_shoes[0])
        else:
            chosen_shoe = random.choice(shoe_candidates)
            _pick(chosen_shoe)
        # Locked shoe details always included
        for k in SHOE_DETAIL_MODULES:
            if is_locked(k):
                _pick(k)
        # Random detail only if no locked ones
        if not any(is_locked(k) for k in SHOE_DETAIL_MODULES) and random.random() < SHOE_DETAIL_PROB:
            detail = random.choice(SHOE_DETAIL_MODULES)
            _pick(detail)

    # ── Zone 7: Outerwear — locked always included, otherwise 50% ──
    if zone_on("outerwear"):
        locked_ow = [k for k in OUTERWEAR_MODULES if is_locked(k)]
        if locked_ow:
            for k in locked_ow:
                _pick(k)
        elif random.random() < OUTERWEAR_PROB:
            _pick("outerwear_type")
            n_ow = random.randint(0, OUTERWEAR_MAX_MODULES - 1)
            ow_pool = [k for k in OUTERWEAR_MODULES if k != "outerwear_type"]
            for k in random.sample(ow_pool, min(n_ow, len(ow_pool))):
                _pick(k)

    # ── Zone 8: Bag — always one ──
    if zone_on("bag"):
        _pick("bag_type")

    # ── Zone 9: Accessories — locked always included, then fill remaining ──
    if zone_on("accessories"):
        locked_acc = [k for k in ACC_MODULES if is_locked(k)]
        for k in locked_acc:
            _pick(k)
        n_acc_remaining = max(0, ACC_MAX_MODULES - len(locked_acc))
        if n_acc_remaining > 0:
            acc_candidates = []
            remaining_acc = [k for k in ACC_MODULES if not is_locked(k)]
            for k in remaining_acc:
                if random.random() < ACC_MODULE_PROB.get(k, 0.2):
                    acc_candidates.append(k)
            if len(acc_candidates) > n_acc_remaining:
                acc_candidates = random.sample(acc_candidates, n_acc_remaining)
            for k in acc_candidates:
                _pick(k)

    # ── Zone 10: Color — locked module always used, otherwise random ──
    if zone_on("color"):
        locked_colors = [k for k in COLOR_MODULES if is_locked(k)]
        if locked_colors:
            for k in locked_colors:
                _pick(k)
        else:
            chosen_color = random.choice(COLOR_MODULES)
            _pick(chosen_color)

    # ── Zone 11: Pattern — single pick ──
    if zone_on("pattern"):
        _pick("pattern")

    prompt = do_generate(selections, model)
    return {"selections": selections, "prompt": prompt}


# ── PyWebView API ──────────────────────────────────
class Api:
    def get_categories(self):
        return json.dumps(CATEGORIES, ensure_ascii=False)

    def generate_prompt(self, selections_json, model):
        selections = json.loads(selections_json)
        return do_generate(selections, model)

    def random_generate(self, model, zones_json=None, locked_json=None, current_selections_json=None):
        zones = json.loads(zones_json) if zones_json else None
        locked = json.loads(locked_json) if locked_json else {}
        current_sel = json.loads(current_selections_json) if current_selections_json else {}
        result = do_random(model, zones_enabled=zones, locked=locked, current_selections=current_sel)
        return json.dumps(result, ensure_ascii=False)

    def open_url(self, url):
        webbrowser.open(url)


# ── Entry point ────────────────────────────────────
if __name__ == "__main__":
    html_path = os.path.join(_base, "index.html")

    # Read HTML content
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    window = webview.create_window(
        "FASHION PROMPT STUDIO",
        html=html_content,
        js_api=Api(),
        width=1500,
        height=900,
        min_size=(1100, 650),
        text_select=True,
    )
    webview.start(debug=False)
