"""
play.py

Terminal runner for the compliance game

python play.py 1 -> play level 1

Needs game_data.json and answer_keys.json in the same folder.
game_data.json (config + chip registry + signed records) is built from
levels.json and game_config.json by: python -m rot.sign_levels
"""

import argparse
import json
import sys

GAME_DATA = "game_data.json"
ANSWER_KEYS = "answer_keys.json"

parser = argparse.ArgumentParser()
parser.add_argument("level", type=int, choices=[1, 2, 3, 4])
args = parser.parse_args()

sys.path.insert(0, ".")
try:
    import student
except ModuleNotFoundError as e:
    sys.exit(f"Could not import student.py: {e}. "
             "Make sure verify.py and the rot/ package are in this folder.")

level = str(args.level)
game = json.load(open(GAME_DATA))
records = game["levels"][level]
key = json.load(open(ANSWER_KEYS))[level]
config = game["config"]

# everything the policy is allowed to know
context = {
    "config": {"flop_limit": config["flop_limit"], "energy_limit_kj": config["energy_limit_kj"]},
    "ranges": config["reference_ranges"],
    "registry": game["registry"],   # chip_id -> {"public_key", "owner"}
    "state": {}                     # the student's memory -> persists across records
}

print(f"--- Level {level}: {len(records)} records ---\n")

caught = missed = legit_ok = false_blocks = 0
mistakes = []

for record in records:
    verdict = student.policy_checker(record, context)
    if verdict not in ("allow", "block"):
        sys.exit(f"policy_checker must return 'allow' or 'block', not {verdict!r}")
    if record["record_id"] not in key:
        sys.exit(f"record_id {record['record_id']!r} is missing from {ANSWER_KEYS}")

    truth = key[record["record_id"]]
    should_block = truth["verdict"] == "block"

    if should_block and verdict == "block":
        caught += 1
    elif should_block and verdict == "allow":
        missed += 1
        mistakes.append(f"{record['record_id']}: allowed, should have been blocked"
                        + (f"({truth['reason']})" if "reason" in truth else ""))
    elif verdict == "allow":
        legit_ok += 1
    else:
        false_blocks += 1
        mistakes.append(f"{record['record_id']}: blocked, but it was legitimate")

    m = record["measured"]
    mark = "ok   " if verdict == truth["verdict"] else "WRONG"
    print(f"{mark} {record['record_id']} {m['chip_id']} counter={m['counter']:<3} "
          f"flops={m['flops']:>16} energy_kJ={m['energy_kj']:<8} "
          f"declared={record['declared_type']:<9} -> {verdict}")

print("\n--- RESULTS ---")
print(f"Violations blocked: {caught}/{caught+missed}")
print(f"Legitimate allowed: {legit_ok}/{legit_ok+false_blocks}")
if mistakes:
    print("\nMistakes:")
    for line in mistakes:
        print(f"  {line}")

if missed == 0 and false_blocks == 0:
    print("\nPERFECT! Level cleared.")
elif missed == 0:
    print("\nAll violations caught, but you blocked legitimate jobs. Loosen your policy.")
else:
    print("\nSome violations got through. Tighten your policy.")