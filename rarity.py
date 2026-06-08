from collections import defaultdict

import pandas as pd


def compute_trait_frequencies(tokens):
    """
    Count how often each trait value shows up across the whole collection.
    Returns nested counts: {trait_type: {value: count}}.
    We need the full collection first, because rarity only means anything
    relative to everything else.
    """
    counts = defaultdict(lambda: defaultdict(int))
    for token in tokens:
        for attr in token["attributes"]:
            counts[attr["trait_type"]][attr["value"]] += 1
    return counts


def raw_rarity_score(token, counts, total):
    """Sum of 1 / trait fraction across a single token's traits."""
    score = 0.0
    for attr in token["attributes"]:
        fraction = counts[attr["trait_type"]][attr["value"]] / total
        score += 1 / fraction
    return score


def score_rarity(tokens):
    """
    Main entry point. Takes a list of token metadata dicts shaped like:

        {"token_id": "7495",
         "attributes": [{"trait_type": "Fur", "value": "Gold"}, ...]}

    Returns a DataFrame ranked rarest first with:
        token   — eg. "#7495"
        traits  — human readable trait summary
        rarity  — 0 to 100 score (percentile, so 99 means top 1% rarest)
    """
    total = len(tokens)
    if total == 0:
        return pd.DataFrame(columns=["token", "traits", "rarity"])

    counts = compute_trait_frequencies(tokens)

    rows = []
    for token in tokens:
        raw = raw_rarity_score(token, counts, total)
        traits = " · ".join(a["value"] for a in token["attributes"])
        rows.append({
            "token": f"#{token['token_id']}",
            "traits": traits,
            "raw_score": round(raw, 2),
        })

    df = pd.DataFrame(rows)

    # turn raw scores into an easy to read 0 to 100 scale using percentile rank.
    df["rarity"] = (df["raw_score"].rank(pct=True) * 100).round(1)
    df = df.sort_values("rarity", ascending=False).reset_index(drop=True)
    return df



def generate_sample_tokens(n=200, seed=42):
    import random
    random.seed(seed)

    trait_pool = {
        "Background": {"Blue": 40, "Gray": 30, "Yellow": 20, "Purple": 9, "Gold": 1},
        "Fur": {"Brown": 50, "Black": 25, "Cream": 18, "Gold": 5, "Rainbow": 2},
        "Eyes": {"Bored": 45, "Sleepy": 30, "Wide": 18, "Cyborg": 5, "Laser": 2},
        "Hat": {"None": 50, "Beanie": 25, "Cap": 18, "Cowboy": 6, "Crown": 1},
    }

    tokens = []
    for i in range(n):
        attributes = []
        for trait_type, values in trait_pool.items():
            choice = random.choices(
                list(values.keys()), weights=list(values.values()), k=1
            )[0]
            attributes.append({"trait_type": trait_type, "value": choice})
        tokens.append({"token_id": str(1000 + i), "attributes": attributes})
    return tokens


if __name__ == "__main__":
    sample = generate_sample_tokens()
    result = score_rarity(sample)

    print(f"Scored {len(result)} tokens.\n")
    print("Top 10 rarest:")
    print(result.head(10).to_string(index=False))
    print("\nMost common 5:")
    print(result.tail(5).to_string(index=False))