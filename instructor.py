"""
instructor.py

The answer key for verif_evidence() and policy_checker() (more than one solution may be correct)
"""

from rot.verify import verify_signature

# Energy readings are noisy (~ +/-5%), so a job can read just under the energy limit while being over it. Treat anything
# within one noise-width of the limit as over. The cost is some honest jobs just under the limit get blocked.
ENERGY_MARGIN = 0.05

# FLOPs per kJ identifies the kind of work, but it varies from run to run, so allow 10% beyond the reference band.
RATIO_MARGIN = 0.1

"""
Return true if the record can be trusted. Return false if it cannot. Does not change any state.
"""
def verify_evidence(record, context):
    measured = record["measured"]
    chip = measured["chip_id"]
    registry = context["registry"]

    # the chip must be in the registry
    if chip not in registry:
        return False

    # the signature must match that chip's public key
    if not verify_signature(record, registry[chip]["public_key"]):
        return False

    # the counter must be higher than the chip's last accepted report
    last_report = context["state"].get("last_counter", {})
    if measured["counter"] <= last_report.get(chip, 0):
        return False

    return True

"""
Return 'allow' if a record is legitimate. Return 'block' if it is not.
"""
def policy_checker(record, context):
    state = context["state"]
    config = context["config"]
    measured = record["measured"]

    # records that fail evidence verification are blocked immediately
    if not verify_evidence(record, context):
        return "block"

    chip = measured["chip_id"]
    owner = context["registry"][chip]["owner"]
    state.setdefault("last_counter", {})[chip] = measured["counter"]

    # charge the job to the chip's registered owner
    totals = state.setdefault("totals", {}).setdefault(
        owner, {"flops": 0, "energy_kj": 0.0})
    totals["flops"] += measured["flops"]
    totals["energy_kj"] += measured["energy_kj"]

    # cumulative limits per owner, energy gets noise margin
    if totals["flops"] > config["flop_limit"]:
        return "block"
    if totals["energy_kj"] > config["energy_limit_kj"] * (1 - ENERGY_MARGIN):
        return "block"

    # check declared workload type against measured profile, FLOPs per kJ must fit reference band for that type
    reference = context["ranges"].get(record["declared_type"])
    if reference is None: # unknown type
        return "block"
    low, high = reference["flops_per_kj"]
    ratio = measured["flops"] / measured["energy_kj"] if measured["energy_kj"] > 0 else float("inf")
    if not low * (1 - RATIO_MARGIN) <= ratio <= high * (1 + RATIO_MARGIN):
        return "block"

    return "allow"