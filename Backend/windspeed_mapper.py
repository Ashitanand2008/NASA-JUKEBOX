"""
NASA Windspeed Image-to-Sound Converter
Member 3: Scientific Value Mapping and Data Analysis Module

Role:
    Converts RGB color values extracted from NASA scientific windspeed imagery
    (provided by Member 2) into estimated windspeed values in meters per second (m/s)
    using a calibrated NASA color legend (researched by Member 1).
    Calculates summary statistics and exports the data to CSV for Member 4 (Sound Synthesis).

Scientific & Mathematical Note:
    - Color Matching: Uses Euclidean distance in 3-dimensional RGB space:
          distance = sqrt((R1 - R2)^2 + (G1 - G2)^2 + (B1 - B2)^2)
      This finds the closest color in the legend without requiring machine learning.
    - Uncertainty / Reliability: Because scientific colorbars can be continuous or
      contain pixels corresponding to land masses, cloud cover, or interpolation
      artifacts, each match includes a distance score and confidence rating.
    - Illustrative Data: All sample legend colors and windspeed numbers in this file
      are illustrative placeholders for prototype development and testing.
      They are not authentic NASA measurements. Replace with Member 1's actual legend.
"""

import math
import csv
import os
import sys

# Optional NumPy support: falls back gracefully to standard Python math
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# ==============================================================================
# 1. ILLUSTRATIVE NASA COLOR LEGEND (MEMBER 1'S INPUT)
# ==============================================================================
# Each entry maps an RGB color tuple (Red, Green, Blue) to:
# - A human-readable color label
# - An approximate windspeed value in meters per second (m/s)
#
# IMPORTANT: These values are illustrative placeholders for prototype testing.
# Replace these with the actual NASA legend parameters identified by Member 1.
DEFAULT_NASA_LEGEND = [
    {"name": "Deep Blue",            "rgb": (20, 40, 160),   "windspeed_mps": 2.5},
    {"name": "Cyan / Light Blue",    "rgb": (40, 180, 220),  "windspeed_mps": 7.0},
    {"name": "Green",                "rgb": (50, 200, 70),   "windspeed_mps": 12.0},
    {"name": "Yellow-Green",         "rgb": (180, 220, 40),  "windspeed_mps": 16.5},
    {"name": "Yellow",               "rgb": (250, 230, 30),  "windspeed_mps": 21.0},
    {"name": "Orange",               "rgb": (245, 130, 20),  "windspeed_mps": 26.5},
    {"name": "Red",                  "rgb": (225, 30, 30),   "windspeed_mps": 32.0},
    {"name": "Dark Magenta / Purple","rgb": (130, 20, 120),  "windspeed_mps": 38.0},
]


# ==============================================================================
# 2. SAMPLE EXTRACTED REGIONS (MEMBER 2'S INPUT)
# ==============================================================================
# Sample RGB color values extracted from different image coordinates/regions.
# In the integrated pipeline, Member 2 will pass these directly or via file.
SAMPLE_EXTRACTED_REGIONS = [
    {"region_id": "REG_001", "region_name": "Calm Tropical Zone",      "rgb": (22, 45, 155)},   # Very close to Deep Blue (2.5 m/s)
    {"region_id": "REG_002", "region_name": "Mid-Atlantic Breeze",      "rgb": (48, 175, 210)},  # Very close to Cyan (7.0 m/s)
    {"region_id": "REG_003", "region_name": "Trade Wind Corridor",      "rgb": (55, 195, 75)},   # Very close to Green (12.0 m/s)
    {"region_id": "REG_004", "region_name": "Developing Depression",    "rgb": (240, 225, 35)},  # Very close to Yellow (21.0 m/s)
    {"region_id": "REG_005", "region_name": "Cyclone Outer Bands",      "rgb": (235, 120, 25)},  # Very close to Orange (26.5 m/s)
    {"region_id": "REG_006", "region_name": "Severe Hurricane Eye Wall", "rgb": (218, 35, 28)},  # Very close to Red (32.0 m/s)
    {"region_id": "REG_007", "region_name": "Extreme Gust Core",        "rgb": (125, 25, 115)},  # Very close to Purple (38.0 m/s)
    {"region_id": "REG_008", "region_name": "Continental Land / Cloud", "rgb": (128, 128, 128)}, # Gray: far from legend (tests tolerance)
]


# ==============================================================================
# 3. CORE SCIENTIFIC VALUE MAPPING FUNCTIONS
# ==============================================================================

def calculate_color_distance(rgb1, rgb2):
    """
    Computes Euclidean distance between two RGB colors in 3D color space.
    Formula: sqrt((R1 - R2)^2 + (G1 - G2)^2 + (B1 - B2)^2)

    Beginner explanation:
    Think of Red, Green, and Blue as X, Y, and Z axes on a graph.
    The formula calculates the straight-line distance between the two points,
    just like using a ruler in 3D space!

    - Distance = 0 means an exact identical color.
    - Distance < 30 means a very close, highly reliable match.
    - Distance 30 to 75 means an approximate match.
    - Distance > 75 means the pixel is far from the legend (e.g. land or cloud).
    """
    r1, g1, b1 = rgb1
    r2, g2, b2 = rgb2

    if HAS_NUMPY:
        arr1 = np.array([r1, g1, b1], dtype=float)
        arr2 = np.array([r2, g2, b2], dtype=float)
        return float(np.linalg.norm(arr1 - arr2))
    else:
        # Standard beginner-friendly Python using math.sqrt
        return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)


def match_color_to_windspeed(extracted_rgb, legend=None, distance_threshold=75.0):
    """
    Finds the closest color in the NASA legend to the extracted RGB value.

    Args:
        extracted_rgb: Tuple or list of (R, G, B) integers (0-255).
        legend: List of dicts with 'name', 'rgb', and 'windspeed_mps'.
        distance_threshold: Distance beyond which a match is marked approximate/low confidence.

    Returns:
        A dictionary containing:
        - matched_color_name: Name of closest legend color
        - matched_rgb: (R, G, B) of closest legend entry
        - color_distance: Euclidean distance (lower is better)
        - windspeed_mps: Estimated windspeed in m/s
        - confidence: 'High Confidence', 'Moderate (Approximate)', or 'Low / Potential Non-Data'
    """
    if legend is None:
        legend = DEFAULT_NASA_LEGEND

    best_match = None
    min_distance = float("inf")

    # Linear scan through the legend entries
    for item in legend:
        dist = calculate_color_distance(extracted_rgb, item["rgb"])
        if dist < min_distance:
            min_distance = dist
            best_match = item

    # Categorize match reliability
    if min_distance <= 25.0:
        confidence = "High Confidence"
    elif min_distance <= distance_threshold:
        confidence = "Moderate (Approximate)"
    else:
        confidence = "Low / Potential Non-Data (Land/Cloud)"

    return {
        "matched_color_name": best_match["name"],
        "matched_rgb": best_match["rgb"],
        "color_distance": round(min_distance, 2),
        "windspeed_mps": round(best_match["windspeed_mps"], 2),
        "confidence": confidence,
    }


def map_single_rgb(r, g, b, legend=None):
    """
    Convenience helper function for Member 5's User Interface:
    Takes individual R, G, B values and returns estimated windspeed (m/s).
    """
    match_info = match_color_to_windspeed((r, g, b), legend=legend)
    return match_info["windspeed_mps"]


def process_extracted_regions(regions, legend=None):
    """
    Processes a list of extracted regions, matching each to the NASA legend.

    Args:
        regions: List of dicts with 'region_id', 'region_name', and 'rgb'.
        legend: Optional custom legend list. Defaults to DEFAULT_NASA_LEGEND.

    Returns:
        List of processed region dicts with windspeed estimations.
    """
    if legend is None:
        legend = DEFAULT_NASA_LEGEND

    processed_results = []
    for reg in regions:
        match_info = match_color_to_windspeed(reg["rgb"], legend)
        result_item = {
            "region_id": reg.get("region_id", "N/A"),
            "region_name": reg.get("region_name", "Unnamed Region"),
            "extracted_rgb": reg["rgb"],
            "matched_color_name": match_info["matched_color_name"],
            "matched_rgb": match_info["matched_rgb"],
            "color_distance": match_info["color_distance"],
            "windspeed_mps": match_info["windspeed_mps"],
            "confidence": match_info["confidence"],
        }
        processed_results.append(result_item)

    return processed_results


# ==============================================================================
# 4. STATISTICAL ANALYSIS
# ==============================================================================

def calculate_windspeed_statistics(results):
    """
    Calculates minimum, maximum, and average windspeed across regions.
    Also separates high/moderate confidence data from low-confidence (non-data) regions.

    Args:
        results: List of processed region dicts.

    Returns:
        Dictionary with overall and confident statistics.
    """
    if not results:
        return {
            "total_count": 0,
            "min_windspeed_mps": 0.0,
            "max_windspeed_mps": 0.0,
            "avg_windspeed_mps": 0.0,
            "reliable_count": 0,
            "reliable_min_mps": 0.0,
            "reliable_max_mps": 0.0,
            "reliable_avg_mps": 0.0,
        }

    all_speeds = [r["windspeed_mps"] for r in results]
    reliable_speeds = [
        r["windspeed_mps"] for r in results 
        if not r["confidence"].startswith("Low")
    ]

    stats = {
        "total_count": len(all_speeds),
        "min_windspeed_mps": round(min(all_speeds), 2),
        "max_windspeed_mps": round(max(all_speeds), 2),
        "avg_windspeed_mps": round(sum(all_speeds) / len(all_speeds), 2),
        "reliable_count": len(reliable_speeds),
    }

    if reliable_speeds:
        stats["reliable_min_mps"] = round(min(reliable_speeds), 2)
        stats["reliable_max_mps"] = round(max(reliable_speeds), 2)
        stats["reliable_avg_mps"] = round(sum(reliable_speeds) / len(reliable_speeds), 2)
    else:
        stats["reliable_min_mps"] = 0.0
        stats["reliable_max_mps"] = 0.0
        stats["reliable_avg_mps"] = 0.0

    return stats


# ==============================================================================
# 5. DATA EXPORT (FOR MEMBER 4: SOUND SYNTHESIS)
# ==============================================================================

def export_to_csv(results, output_filepath="windspeed_output_for_member4.csv"):
    """
    Exports mapped windspeed values to a structured CSV file for Member 4.

    The CSV includes:
    - region_id: Unique region identifier
    - region_name: Descriptive area name
    - extracted_r, extracted_g, extracted_b: Color sent by Member 2
    - matched_color: Name of closest legend color
    - windspeed_mps: The critical numeric value Member 4 maps to audio pitch/sound
    - color_distance: Closeness of color match (Euclidean distance)
    - confidence: Match reliability status
    """
    fieldnames = [
        "region_id",
        "region_name",
        "extracted_r",
        "extracted_g",
        "extracted_b",
        "matched_color",
        "windspeed_mps",
        "color_distance",
        "confidence",
    ]

    with open(output_filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "region_id": r["region_id"],
                "region_name": r["region_name"],
                "extracted_r": r["extracted_rgb"][0],
                "extracted_g": r["extracted_rgb"][1],
                "extracted_b": r["extracted_rgb"][2],
                "matched_color": r["matched_color_name"],
                "windspeed_mps": r["windspeed_mps"],
                "color_distance": r["color_distance"],
                "confidence": r["confidence"],
            })

    return output_filepath


# ==============================================================================
# 6. LEGEND & INPUT LOADERS (FOR EASY REPLACEMENT BY USER/TEAM)
# ==============================================================================

def load_legend_from_csv(filepath):
    """
    Loads a custom NASA legend CSV file prepared by Member 1.
    Expected CSV columns: color_name, r, g, b, windspeed_mps
    """
    if not os.path.exists(filepath):
        print(f"[Info] Legend file '{filepath}' not found. Using default illustrative legend.")
        return DEFAULT_NASA_LEGEND

    legend = []
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            legend.append({
                "name": row["color_name"].strip(),
                "rgb": (int(row["r"]), int(row["g"]), int(row["b"])),
                "windspeed_mps": float(row["windspeed_mps"]),
            })
    return legend


def load_extracted_regions_from_csv(filepath):
    """
    Loads extracted region RGB data exported by Member 2.
    Expected CSV columns: region_id, region_name, r, g, b
    """
    if not os.path.exists(filepath):
        print(f"[Info] Input regions file '{filepath}' not found. Using sample data.")
        return SAMPLE_EXTRACTED_REGIONS

    regions = []
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            regions.append({
                "region_id": row["region_id"].strip(),
                "region_name": row["region_name"].strip(),
                "rgb": (int(row["r"]), int(row["g"]), int(row["b"])),
            })
    return regions


# ==============================================================================
# 7. FORMATTED TABLE DISPLAY
# ==============================================================================

def display_results_table(results, stats):
    """
    Displays a clear, human-readable terminal table showing extracted colors,
    matched NASA legend colors, estimated windspeed, and summary statistics.
    """
    print("\n" + "=" * 98)
    print("NASA WINDSPEED IMAGE-TO-SOUND CONVERTER - MEMBER 3 ANALYSIS RESULTS")
    print("=" * 98)
    print("Note: Values shown are illustrative approximations for testing, not official NASA data.")
    print("-" * 98)

    # Header
    header = f"{'Region ID':<10} | {'Region Name':<26} | {'Extracted RGB':<15} | {'Speed (m/s)':<11} | {'Match Quality':<25}"
    print(header)
    print("-" * 98)

    for item in results:
        rgb_str = f"({item['extracted_rgb'][0]},{item['extracted_rgb'][1]},{item['extracted_rgb'][2]})"
        speed_str = f"{item['windspeed_mps']:.1f} m/s"
        conf_str = item["confidence"]
        reg_name = item["region_name"][:26]
        row_str = f"{item['region_id']:<10} | {reg_name:<26} | {rgb_str:<15} | {speed_str:<11} | {conf_str:<25}"
        print(row_str)

    print("=" * 98)
    print("STATISTICAL SUMMARY (FOR SCIENTIFIC CONTEXT & MEMBER 4 SOUND MAPPING):")
    print(f"  * Total Regions Analyzed       : {stats['total_count']}")
    print(f"  * Overall Minimum Windspeed    : {stats['min_windspeed_mps']:.2f} m/s")
    print(f"  * Overall Maximum Windspeed    : {stats['max_windspeed_mps']:.2f} m/s")
    print(f"  * Overall Average Windspeed    : {stats['avg_windspeed_mps']:.2f} m/s")
    
    if stats["reliable_count"] < stats["total_count"]:
        print("-" * 98)
        print(f"  * Reliable Ocean Regions Only  : {stats['reliable_count']} regions (excluding Land/Clouds)")
        print(f"  * Ocean Minimum Windspeed      : {stats['reliable_min_mps']:.2f} m/s")
        print(f"  * Ocean Maximum Windspeed      : {stats['reliable_max_mps']:.2f} m/s")
        print(f"  * Ocean Average Windspeed      : {stats['reliable_avg_mps']:.2f} m/s")

    print("=" * 98)


# ==============================================================================
# 8. MAIN DEMO EXECUTION
# ==============================================================================

def main():
    """
    Main driver function demonstrating Member 3's complete workflow.
    """
    print("\n[Member 3 Module] Scientific Value Mapping and Data Analysis")
    print("=" * 60)

    # Step 1 & 2: Load Legend (Check for optional external CSV or use default)
    legend_file = "nasa_legend.csv"
    if os.path.exists(legend_file):
        print(f"-> Loading NASA legend from '{legend_file}'...")
        legend = load_legend_from_csv(legend_file)
    else:
        print("-> Using built-in illustrative NASA color legend.")
        legend = DEFAULT_NASA_LEGEND

    # Step 1: Load Extracted RGB Regions (from Member 2's CSV or sample list)
    regions_file = "extracted_regions.csv"
    if os.path.exists(regions_file):
        print(f"-> Loading Member 2 extracted regions from '{regions_file}'...")
        regions = load_extracted_regions_from_csv(regions_file)
    else:
        print("-> Using sample extracted regions (simulating Member 2 input).")
        regions = SAMPLE_EXTRACTED_REGIONS

    # Step 3, 4, 5: Compare colors and estimate windspeed values
    print("-> Mapping extracted RGB colors to closest NASA legend windspeeds...")
    results = process_extracted_regions(regions, legend)

    # Step 7: Calculate minimum, maximum, and average windspeed
    stats = calculate_windspeed_statistics(results)

    # Step 6: Display results table
    display_results_table(results, stats)

    # Step 8: Export results to CSV for Member 4
    output_csv = "windspeed_output_for_member4.csv"
    export_to_csv(results, output_csv)
    print(f"\n[Success] Output exported to '{output_csv}' for Member 4 (Sound Synthesis).")
    print("[Note] Estimated values are approximate nearest-color matches based on the illustrative legend.\n")


if __name__ == "__main__":
    main()
