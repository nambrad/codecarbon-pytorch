"""
sign_levels.py

Turns the hand-written levels.json into game_data.json: every record signed by
its lab's chip, plus the chip registry and the game config, all in one file.

python -m rot.sign_levels        (run from the repo root)

INSTRUCTOR ONLY.

Inputs:  levels.json, game_config.json, answer_keys.json (checked, not changed)
Output:  game_data.json -> everything play.py and students need

Each lab gets one chip: lab_04 -> chip-04, owned by lab_04 in the registry.
The signed record drops "actor": the owner comes from the registry instead.

Attack records in levels.json are marked with "attack":
    "edited"        signed with the true values, then the "edited" values swapped in
    "unregistered"  signed by "chip_id", a chip left out of the registry
    "replay"        an exact copy of the earlier record "copy_of" (same level)

Seed: set ROT_SEED to get the same keys every run. Without it a random seed is
used, so keys and signatures change each run. That's fine: the registry and
records are always rebuilt together.
"""

import copy
import json
import os
import secrets

from rot.manufacturer import make_chip
from rot.registry import build_registry
from rot.reference import verify_evidence

seed = os.environ.get("ROT_SEED") or secrets.token_hex(16)
levels = json.load(open("levels.json"))
config = json.load(open("game_config.json"))
answer_keys = json.load(open("answer_keys.json"))


def chip_id_for(actor):          # "lab_04" -> "chip-04"
    return "chip-" + actor.split("_")[1]


# -- one chip per lab, made ONCE so its counter keeps rising across all levels ----
actors = sorted({r["actor"] for recs in levels.values() for r in recs if "actor" in r})
chips = {actor: make_chip(seed, chip_id_for(actor)) for actor in actors}
registry = build_registry([(chips[actor], actor) for actor in actors])
rogue_chips = {}                 # chip_id -> chip made with a different seed

# -- sign every record ------------------------------------------------------------
signed_levels = {}
for level, recs in levels.items():
    out, by_id = [], {}
    for src in recs:
        attack = src.get("attack")

        if attack == "replay":
            if src["copy_of"] not in by_id:
                raise SystemExit(f'{src["record_id"]}: copy_of {src["copy_of"]} must come earlier in level {level}')
            rec = copy.deepcopy(by_id[src["copy_of"]])
            rec["record_id"] = src["record_id"]

        else:
            if attack == "unregistered":
                cid = src["chip_id"]
                chip = rogue_chips.setdefault(cid, make_chip(seed + "-rogue", cid))
            else:
                chip = chips[src["actor"]]
            rec = {"record_id": src["record_id"],
                   **chip.report(src["job_id"], src["flops"], src["energy_kj"]),
                   "declared_type": src["declared_type"]}
            if attack == "edited":
                rec["measured"].update(src["edited"])   # changed AFTER signing

        by_id[src["record_id"]] = rec
        out.append(rec)
    signed_levels[level] = out

# -- self-check: honest records must pass, attack records must fail ---------------
for level, recs in signed_levels.items():
    last_counter = {}
    for src, rec in zip(levels[level], recs):
        ok, reason = verify_evidence(rec, registry, last_counter)
        if ok == ("attack" in src):
            raise SystemExit(f'{src["record_id"]}: unexpected evidence result "{reason}"')
        if src["record_id"] not in answer_keys.get(level, {}):
            print(f'warning: {src["record_id"]} has no entry in answer_keys.json')

# -- write one file with everything ------------------------------------------------
game_data = {"config": config, "registry": registry, "levels": signed_levels}
with open("game_data.json", "w") as f:
    json.dump(game_data, f, indent=2)
    f.write("\n")

counts = ", ".join(f"level {lv}: {len(r)}" for lv, r in signed_levels.items())
print(f"Wrote game_data.json ({len(registry)} chips; {counts})")
if "ROT_SEED" not in os.environ:
    print("Used a random seed. Set ROT_SEED to get the same signatures every run.")
