from collections import Counter, defaultdict
import json

def load_units(filepath):
    """
    Load units JSON file. Expects a list of dicts,
    each having at least 'Name' and 'Trait' keys.
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def load_traits_thresholds(filepath):
    """
    Load trait threshold JSON file. Expects a dict
    mapping trait names to integer thresholds.
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def build_filtered_units(units, trait_thresholds):
    trait_to_units = defaultdict(list)
    for unit in units:
        for trait in unit.get('Trait', []):
            trait_to_units[trait].append(unit['Name'])

    activatable_traits = {trait for trait, ulist in trait_to_units.items() if len(ulist) >= trait_thresholds[trait]}

    filtered_units = []
    for unit in units:
        filtered_traits = [trait for trait in unit["Trait"] if trait in activatable_traits]
        if filtered_traits:
            filtered_units.append({"Name": unit["Name"], "Traits": filtered_traits})

    filtered_units.sort(key=lambda x: len(x['Traits']), reverse=True)
    return filtered_units


def compute_potential_active(current_trait_count, remaining_units, trait_thresholds):
    remaining_count = Counter()
    for unit in remaining_units:
        remaining_count.update(unit["Traits"])
    current_active = {trait for trait, count in current_trait_count.items() if count >= trait_thresholds[trait]}
    potential = len(current_active)
    for trait in trait_thresholds:
        if trait in current_active:
            continue
        if current_trait_count[trait] + remaining_count[trait] >= trait_thresholds[trait]:
            potential += 1
    return potential


def find_valid_groups(units, trait_thresholds,
                      group_size=7, min_active_traits=8):
    filtered_units = build_filtered_units(units, trait_thresholds)
    solutions = []

    def dfs(current_group, current_trait_count, start=0):
        # base case
        if len(current_group) == group_size:
            active = {trait for trait, cnt in current_trait_count.items() if cnt >= trait_thresholds[trait]}
            if len(active) >= 8:
                solutions.append(list(current_group))
            return

        remaining_units = filtered_units[start:]
        potential = compute_potential_active(current_trait_count, remaining_units, trait_thresholds)
        if potential < min_active_traits:
            return # prune

        for i in range(start, len(filtered_units)):
            unit = filtered_units[i]
            new_count = current_trait_count.copy()
            for t in unit["Traits"]:
                new_count[t] += 1
            current_group.append(unit)
            dfs(current_group, new_count, i+1)
            current_group.pop()

    dfs([], {}, 0)
    return solutions