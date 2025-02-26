import streamlit as st
from streamlit_local_storage import LocalStorage
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from db.database_handler import get_last_entry, get_entries_for_run, get_all_runs

st.set_page_config(layout="wide", page_title="Nutrient Recommendations")
st.title("Nutrient Recommendations")


# Define helper functions first to avoid NameError
def calculate_ph_down_ml(ph_deviation, volume_liters):
    """Calculates approximate pH down solution needed"""
    # This is a rough approximation - actual amount depends on water hardness and pH down strength
    strength_factor = 1.2  # Adjust based on pH solution strength
    return max(0.5, round(ph_deviation * volume_liters * strength_factor, 1))


def calculate_ph_up_ml(ph_deviation, volume_liters):
    """Calculates approximate pH up solution needed"""
    # This is a rough approximation - actual amount depends on water hardness and pH up strength
    strength_factor = 1.0  # Adjust based on pH solution strength
    return max(0.5, round(ph_deviation * volume_liters * strength_factor, 1))


def calculate_water_add(current_ec, target_ec, volume_liters):
    """Calculates water needed to dilute nutrient solution"""
    if current_ec <= target_ec:
        return 0

    # C1 * V1 = C2 * V2, where C2 = C1 * V1 / V2
    # So V2 = C1 * V1 / C2, and water to add = V2 - V1
    final_volume = current_ec * volume_liters / target_ec
    water_to_add = final_volume - volume_liters

    # Cap at reasonable values and round
    return min(round(water_to_add, 1), volume_liters)


def evaluate_water_temp(temp, plant_type):
    """Evaluates if water temperature is optimal for plant type"""
    # Temperature ranges by plant type
    temp_ranges = {
        "leafy_greens": {"min": 18, "max": 23, "optimal": 20},
        "fruiting": {"min": 20, "max": 26, "optimal": 23},
        "herbs": {"min": 18, "max": 24, "optimal": 21}
    }

    # Get range for current plant type, or use default
    range_data = temp_ranges.get(plant_type, {"min": 18, "max": 24, "optimal": 21})

    if temp < range_data["min"]:
        return "too_cold"
    elif temp > range_data["max"]:
        return "too_warm"
    else:
        return "optimal"


def calculate_nutrient_additions(ec_deficit, volume_liters, n_need, p_need, k_need, products, growth_stage,
                                 nutrient_strength="medium"):
    """
    Calculate nutrient additions based on required NPK levels
    Returns a dictionary of product names and ml to add
    """
    # Convert textual NPK needs to numeric scale (1-5)
    npk_scale = {"very_low": 1, "low": 2, "medium": 3, "high": 4, "very_high": 5}
    n_value = npk_scale.get(n_need, 3)
    p_value = npk_scale.get(p_need, 3)
    k_value = npk_scale.get(k_need, 3)

    # Filter products suitable for the current growth stage
    suitable_products = {}
    for product_name, product_data in products.items():
        if product_data.get("stage") in ["all", growth_stage]:
            suitable_products[product_name] = product_data

    if not suitable_products:
        # Fallback to all products if none match the current stage
        suitable_products = products

    # Score each product based on how well it matches NPK needs
    product_scores = {}
    for product_name, product_data in suitable_products.items():
        n_match = 5 - abs(npk_scale.get(product_data.get("n"), 3) - n_value)
        p_match = 5 - abs(npk_scale.get(product_data.get("p"), 3) - p_value)
        k_match = 5 - abs(npk_scale.get(product_data.get("k"), 3) - k_value)

        # Weight the scores based on importance
        product_scores[product_name] = (n_match * n_value + p_match * p_value + k_match * k_value) / (
                    n_value + p_value + k_value)

    # Select products to use based on scores
    selected_products = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)

    # Calculate amounts
    results = {}
    remaining_ec = ec_deficit

    # Get ml_per_liter based on selected strength
    ml_key = f"ml_per_liter_{nutrient_strength}"

    for product_name, score in selected_products[:2]:  # Use top 2 products
        # Calculate EC contribution per ml based on a standard conversion
        # This is a simplification; real-world values would need calibration
        ec_per_ml = 0.05  # Approximate EC increase per ml in a 1L solution

        # Get dosage from product data
        ml_per_liter = products[product_name].get(ml_key, 2.0)

        # Calculate amount to add
        # If this is the primary nutrient, give it 70% of the remaining EC deficit
        if product_name == selected_products[0][0]:
            ec_share = remaining_ec * 0.7
        else:
            ec_share = remaining_ec * 0.3

        ml_to_add = round((ec_share / ec_per_ml) * volume_liters / 10, 1)

        # Cap based on recommended dosage
        max_ml = ml_per_liter * volume_liters
        ml_to_add = min(ml_to_add, max_ml)

        if ml_to_add >= 0.5:  # Only include if it's at least 0.5ml
            results[product_name] = ml_to_add
            remaining_ec -= (ml_to_add * ec_per_ml * 10) / volume_liters

    return results


# Initialize local storage
local_storage = LocalStorage()

# Load settings
try:
    nutrient_settings = json.loads(local_storage.getItem("nutrient_recommendation_settings"))
    nutrient_profiles = json.loads(local_storage.getItem("nutrient_profiles"))
    nutrient_products = json.loads(local_storage.getItem("nutrient_products"))
    system_types = json.loads(local_storage.getItem("system_types"))
    username = local_storage.getItem("username")
    selected_run_id = local_storage.getItem("selected_run_id")
except Exception as e:
    st.error(f"Error loading settings: {e}. Please configure settings first.")
    st.stop()

# Check if recommendations are enabled
if not nutrient_settings.get("enabled", True):
    st.warning(
        "Nutrient recommendations are currently disabled. Go to Settings → Nutrient Recommendations to enable them.")
    st.stop()

# Get current run
runs = get_all_runs()
if not runs:
    st.warning("No hydroponic runs found. Please create a run first.")
    st.stop()

# If no run is selected, use the most recent one
if not selected_run_id and runs:
    selected_run_id = str(runs[0].id)
    local_storage.setItem("selected_run_id", selected_run_id)

# Add a run selector at the top of the page
current_run = None
run_options = {}
for run in runs:
    run_name = f"{run.name}: {run.start_date} - {run.end_date or 'In progress'}"
    run_options[str(run.id)] = run_name
    if str(run.id) == selected_run_id:
        current_run = run

selected_run_id = st.selectbox(
    "Select Run",
    options=list(run_options.keys()),
    format_func=lambda x: run_options[x],
    index=list(run_options.keys()).index(selected_run_id) if selected_run_id in run_options else 0
)

# Update the selected run in local storage when changed
if selected_run_id != local_storage.getItem("selected_run_id"):
    local_storage.setItem("selected_run_id", selected_run_id)
    st.success(f"Switched to run: {run_options[selected_run_id]}")
    st.experimental_rerun()

# Get the last entry for the current run
if selected_run_id:
    # First attempt to get entries from the selected run
    run_entries = get_entries_for_run(int(selected_run_id))
    if run_entries:
        last_entry = run_entries[-1]  # Get the most recent entry for the selected run
    else:
        last_entry = None
else:
    # Fallback to getting the last entry across all runs
    last_entry = get_last_entry()

if not last_entry:
    st.warning("No data entries found for the selected run. Please add data entries first.")
    st.stop()

# Get entries for the last 7 days to analyze trends
now = datetime.now()
week_ago = now - timedelta(days=7)
recent_entries = get_entries_for_run(int(selected_run_id), week_ago)
entries_df = pd.DataFrame([{
    'date': entry.date,
    'ph_initial': entry.ph_initial,
    'ec_initial': entry.ec_initial,
    'ph_final': entry.ph_final,
    'ec_final': entry.ec_final,
    'water_temp': entry.water_temp if hasattr(entry, 'water_temp') else None,
    'water_added': entry.water_added if hasattr(entry, 'water_added') else 0,
    'water_level': entry.water_level if hasattr(entry, 'water_level') else 0,
    'hydro_vega_added': entry.hydro_vega_added if hasattr(entry, 'hydro_vega_added') else 0,
    'hydro_flora_added': entry.hydro_flora_added if hasattr(entry, 'hydro_flora_added') else 0,
    'boost_added': entry.boost_added if hasattr(entry, 'boost_added') else 0,
    'rhizotonic_added': entry.rhizotonic_added if hasattr(entry, 'rhizotonic_added') else 0
} for entry in recent_entries])

# Calculate days since last nutrient change
if len(entries_df) > 0:
    # Check if nutrient columns exist in the dataframe
    nutrient_columns = ['hydro_vega_added', 'hydro_flora_added', 'boost_added']
    existing_columns = [col for col in nutrient_columns if col in entries_df.columns]

    if existing_columns:
        # Consider a nutrient change when significant nutrients were added
        nutrient_filter = pd.DataFrame(False, index=entries_df.index, columns=['is_change'])
        for col in existing_columns:
            nutrient_filter['is_change'] = nutrient_filter['is_change'] | (entries_df[col] > 0)

        nutrient_changes = entries_df[nutrient_filter['is_change']]

        if not nutrient_changes.empty:
            last_change_date = nutrient_changes['date'].max()
            days_since_change = (now.date() - last_change_date).days
        else:
            days_since_change = 0
    else:
        # If no nutrient columns exist, use the earliest entry date as fallback
        earliest_date = entries_df['date'].min()
        days_since_change = (now.date() - earliest_date).days
else:
    days_since_change = 0

# Get current system and plant profile settings
system_type = nutrient_settings.get("system_type", "dwc")
plant_type = nutrient_settings.get("plant_type", "leafy_greens")
growth_stage = nutrient_settings.get("growth_stage", "vegetative")
system_info = system_types.get(system_type, {"description": "Unknown", "ec_modifier": 1.0, "change_frequency_days": 14})
water_volume = nutrient_settings.get("water_volume_liters", 20)

# Get target values for the current plant type and growth stage
try:
    target_values = nutrient_profiles[plant_type][growth_stage]
    ph_target = target_values["ph_target"]
    ec_target = target_values["ec_target"] * system_info["ec_modifier"]  # Adjust EC based on system
    n_level = target_values["n"]
    p_level = target_values["p"]
    k_level = target_values["k"]
except:
    st.error("Could not find target values for the selected plant type and growth stage.")
    target_values = {"ph_target": 6.0, "ec_target": 1.2, "n": "medium", "p": "medium", "k": "medium"}
    ph_target = 6.0
    ec_target = 1.2
    n_level = "medium"
    p_level = "medium"
    k_level = "medium"

# Get current readings (from last entry)
current_ph = last_entry.ph_final
current_ec = last_entry.ec_final
water_temp = last_entry.water_temp if hasattr(last_entry, 'water_temp') else None

# Calculate deviations from target
ph_deviation = current_ph - ph_target

# Get base water EC to subtract from readings (per Canna grow guide)
base_water_ec = nutrient_settings.get("base_water_ec", 0.0)

# Adjust current EC by subtracting the base water EC
adjusted_current_ec = max(0, current_ec - base_water_ec)

# Calculate EC deviation using adjusted value
ec_deviation = adjusted_current_ec - ec_target
ph_tolerance = nutrient_settings.get("ph_tolerance", 0.3)
ec_tolerance = nutrient_settings.get("ec_tolerance", 0.3)

# Main dashboard
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Current Status")

    # Display current values in a pretty card
    status_cols = st.columns(2)
    with status_cols[0]:
        st.markdown(f"""
        ### System Information
        **Plant Type:** {plant_type.replace('_', ' ').title()}  
        **Growth Stage:** {growth_stage.replace('_', ' ').title()}  
        **System:** {system_info['description']}  
        **Water Volume:** {water_volume} liters  
        **Days Since Last Change:** {days_since_change} days
        """)

    with status_cols[1]:
        # Create gauges for pH and EC
        ph_status = "🟢 Good" if abs(ph_deviation) <= ph_tolerance else "🟠 Adjustment Needed"
        ec_status = "🟢 Good" if abs(ec_deviation) <= ec_tolerance else "🟠 Adjustment Needed"

        st.markdown(f"""
        ### Current Readings
        **pH:** {current_ph:.1f} (Target: {ph_target}) {ph_status}  
        **EC:** {current_ec:.1f} → {adjusted_current_ec:.1f}* (Target: {ec_target:.1f}) {ec_status}  
        **Water Temp:** {water_temp if water_temp else 'Not recorded'} °C

        *Adjusted EC after subtracting base water EC of {base_water_ec}
        """)

    # Show trend graphs
    if not entries_df.empty:
        st.subheader("Recent Trends")
        trend_tabs = st.tabs(["pH", "EC", "Combined"])

        with trend_tabs[0]:
            fig_ph = px.line(entries_df, x='date', y=['ph_initial', 'ph_final'],
                             title='pH Trend (Last 7 Days)')
            # Add target pH line
            fig_ph.add_hline(y=ph_target, line_dash="dash", line_color="green",
                             annotation_text=f"Target: {ph_target}")
            # Add tolerance range
            fig_ph.add_hline(y=ph_target + ph_tolerance, line_dash="dot", line_color="orange")
            fig_ph.add_hline(y=ph_target - ph_tolerance, line_dash="dot", line_color="orange")
            st.plotly_chart(fig_ph, use_container_width=True)

        with trend_tabs[1]:
            # Create a figure with multiple traces to show original and adjusted EC
            fig_ec = go.Figure()

            # Add original EC data
            fig_ec.add_trace(go.Scatter(
                x=entries_df['date'],
                y=entries_df['ec_final'],
                mode='lines+markers',
                name='Original EC',
                line=dict(color='blue')
            ))

            # Calculate and add adjusted EC data
            adjusted_ec_final = entries_df['ec_final'] - base_water_ec
            fig_ec.add_trace(go.Scatter(
                x=entries_df['date'],
                y=adjusted_ec_final,
                mode='lines+markers',
                name='Adjusted EC',
                line=dict(color='red', dash='dot')
            ))

            # Add target EC line
            fig_ec.add_hline(y=ec_target, line_dash="dash", line_color="green",
                             annotation_text=f"Target: {ec_target:.1f}")

            # Add tolerance range
            fig_ec.add_hline(y=ec_target + ec_tolerance, line_dash="dot", line_color="orange")
            fig_ec.add_hline(y=ec_target - ec_tolerance, line_dash="dot", line_color="orange")

            # Update layout
            fig_ec.update_layout(
                title='EC Trend (Last 7 Days)',
                xaxis_title='Date',
                yaxis_title='Electrical Conductivity (EC)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )

            st.plotly_chart(fig_ec, use_container_width=True)

        with trend_tabs[2]:
            # Create a combined plot
            fig_combined = go.Figure()

            # Add pH data
            fig_combined.add_trace(go.Scatter(x=entries_df['date'], y=entries_df['ph_final'],
                                              mode='lines+markers', name='pH Final',
                                              line=dict(color='blue')))

            # Add EC data with secondary y-axis
            fig_combined.add_trace(go.Scatter(x=entries_df['date'], y=entries_df['ec_final'],
                                              mode='lines+markers', name='EC Final',
                                              line=dict(color='red'),
                                              yaxis="y2"))

            # Add target lines
            fig_combined.add_hline(y=ph_target, line_dash="dash", line_color="blue",
                                   annotation_text=f"pH Target")

            # Update layout with secondary y-axis
            fig_combined.update_layout(
                title='pH and EC Trends',
                yaxis=dict(title='pH', side='left', range=[5, 8]),
                yaxis2=dict(title='EC', side='right', overlaying='y', range=[0, 3]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )

            st.plotly_chart(fig_combined, use_container_width=True)

with col2:
    st.subheader("Recommendations")

    # Create a recommendation card with actions to take
    rec_container = st.container(border=True)

    with rec_container:
        # System change recommendation based on schedule
        change_freq = system_info.get("change_frequency_days", 14)
        if days_since_change >= change_freq:
            st.warning(
                f"⚠️ **System Change Recommended**  \nIt has been {days_since_change} days since the last nutrient change. For {system_info['description']} systems, we recommend changing every {change_freq} days.")

        # pH adjustment recommendations
        if abs(ph_deviation) > ph_tolerance:
            st.markdown("### 🧪 pH Adjustment")

            if ph_deviation > 0:  # pH is too high
                adjustment_ml = calculate_ph_down_ml(ph_deviation, water_volume)
                st.markdown(
                    f"Current pH ({current_ph:.1f}) is **too high**. Add **{adjustment_ml:.1f} ml** of pH Down solution.")
            else:  # pH is too low
                adjustment_ml = calculate_ph_up_ml(abs(ph_deviation), water_volume)
                st.markdown(
                    f"Current pH ({current_ph:.1f}) is **too low**. Add **{adjustment_ml:.1f} ml** of pH Up solution.")

            st.info(
                "💡 **Tip:** Add pH adjusters gradually. Start with half the recommended amount, mix well, and retest before adding more.")

        # EC/nutrient recommendations
        if abs(ec_deviation) > ec_tolerance:
            st.markdown("### 🌱 Nutrient Adjustment")

            if ec_deviation > 0:  # EC is too high
                water_add_liters = calculate_water_add(adjusted_current_ec, ec_target, water_volume)
                st.markdown(
                    f"Current EC ({current_ec:.1f}, adjusted to {adjusted_current_ec:.1f}) is **too high**. Add **{water_add_liters:.1f} liters** of fresh water to dilute.")
            else:  # EC is too low
                # Calculate nutrients based on NPK needs
                nutrient_recs = calculate_nutrient_additions(
                    ec_target - adjusted_current_ec,
                    water_volume,
                    n_level,
                    p_level,
                    k_level,
                    nutrient_products,
                    growth_stage,
                    nutrient_settings.get("nutrient_strength", "medium")
                )

                for product, amount in nutrient_recs.items():
                    if amount > 0:
                        st.markdown(f"Add **{amount:.1f} ml** of **{product.replace('_', ' ').title()}**")

            st.info(
                "💡 **Tip:** Always add nutrients to your reservoir gradually, allowing for mixing between additions.")

        # If both pH and EC are in range
        if abs(ph_deviation) <= ph_tolerance and abs(ec_deviation) <= ec_tolerance:
            st.success("✅ **All parameters are within optimal range!**  \nNo adjustments needed at this time.")

        # Water temperature advice if available
        if water_temp:
            temp_status = evaluate_water_temp(water_temp, plant_type)
            if temp_status != "optimal":
                st.markdown("### 🌡️ Water Temperature")
                if temp_status == "too_cold":
                    st.warning(
                        f"Water temperature ({water_temp}°C) is on the cold side for {plant_type.replace('_', ' ')}. Consider using a water heater.")
                elif temp_status == "too_warm":
                    st.warning(
                        f"Water temperature ({water_temp}°C) is on the warm side for {plant_type.replace('_', ' ')}. Consider cooling options or adding extra oxygen.")

    # Next scheduled action
    st.subheader("Schedule")

    next_date = now.date() + timedelta(days=(change_freq - days_since_change))
    st.markdown(
        f"**Next solution change:** {next_date.strftime('%Y-%m-%d')} ({change_freq - days_since_change} days from now)")

    # Growth stage transition suggestion
    if growth_stage in nutrient_profiles[plant_type]:
        stages = list(nutrient_profiles[plant_type].keys())
        current_index = stages.index(growth_stage)

        if current_index < len(stages) - 1:
            next_stage = stages[current_index + 1]
            st.markdown(f"**Next growth stage:** {next_stage.replace('_', ' ').title()}")

            # Button to transition to next stage
            if st.button(f"Transition to {next_stage.replace('_', ' ').title()} Stage"):
                nutrient_settings["growth_stage"] = next_stage
                local_storage.setItem("nutrient_recommendation_settings", json.dumps(nutrient_settings))
                st.success(f"Growth stage updated to: {next_stage.replace('_', ' ').title()}")
                st.experimental_rerun()

# Add a section for advanced users who want more detailed recommendations
with st.expander("Detailed Nutrient Information"):
    st.markdown(f"""
    ### Current Target NPK Levels
    - **Nitrogen (N):** {n_level.replace('_', ' ').title()}
    - **Phosphorus (P):** {p_level.replace('_', ' ').title()}
    - **Potassium (K):** {k_level.replace('_', ' ').title()}

    ### EC Calculation
    - **Base Water EC:** {base_water_ec} (subtracted from readings)
    - **Measured EC:** {current_ec:.1f}
    - **Adjusted EC:** {adjusted_current_ec:.1f}
    - **Target EC:** {ec_target:.1f}
    - **Deficit/Excess:** {ec_deviation:.1f}

    ### Available Products
    """)

    # Show product table with their NPK levels
    product_data = []
    for product, details in nutrient_products.items():
        product_data.append({
            "Product": product.replace('_', ' ').title(),
            "N": details.get("n", "medium").replace('_', ' ').title(),
            "P": details.get("p", "medium").replace('_', ' ').title(),
            "K": details.get("k", "medium").replace('_', ' ').title(),
            "Best Stage": details.get("stage", "all").replace('_', ' ').title(),
            f"ml/L ({nutrient_settings.get('nutrient_strength', 'medium')})": details.get(
                f"ml_per_liter_{nutrient_settings.get('nutrient_strength', 'medium')}", 2.0)
        })

    st.dataframe(pd.DataFrame(product_data), use_container_width=True)

    st.markdown("""
    ### Notes on Nutrient Interactions
    - **EC (Electrical Conductivity)** measures the total dissolved salts in your solution
    - **pH** affects nutrient availability - some nutrients are locked out at certain pH levels
    - When adjusting, always change **one parameter at a time** and wait to see the effect
    """)