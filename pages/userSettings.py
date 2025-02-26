import streamlit as st
from streamlit_local_storage import LocalStorage
import json

st.set_page_config(layout="wide")
st.title("Settings")

local_storage = LocalStorage()

# Initialize default nutrient profiles if not existing
if local_storage.getItem("nutrient_profiles") is None:
    default_profiles = {
        "leafy_greens": {
            "seedling": {"ph_target": 5.8, "ec_target": 0.8, "n": "low", "p": "low", "k": "low"},
            "vegetative": {"ph_target": 5.8, "ec_target": 1.2, "n": "high", "p": "medium", "k": "medium"},
            "harvest": {"ph_target": 5.8, "ec_target": 1.4, "n": "high", "p": "medium", "k": "medium"}
        },
        "fruiting": {
            "seedling": {"ph_target": 5.8, "ec_target": 0.8, "n": "low", "p": "low", "k": "low"},
            "vegetative": {"ph_target": 6.0, "ec_target": 1.5, "n": "high", "p": "medium", "k": "medium"},
            "flowering": {"ph_target": 6.2, "ec_target": 2.0, "n": "medium", "p": "high", "k": "high"},
            "fruiting": {"ph_target": 6.0, "ec_target": 2.2, "n": "low", "p": "high", "k": "high"}
        },
        "herbs": {
            "seedling": {"ph_target": 5.6, "ec_target": 0.5, "n": "low", "p": "low", "k": "low"},
            "vegetative": {"ph_target": 5.8, "ec_target": 1.0, "n": "medium", "p": "medium", "k": "medium"},
            "harvest": {"ph_target": 5.8, "ec_target": 1.2, "n": "medium", "p": "medium", "k": "medium"}
        }
    }
    local_storage.setItem("nutrient_profiles", json.dumps(default_profiles))

# Initialize default nutrient products if not existing
if local_storage.getItem("nutrient_products") is None:
    default_products = {
        "hydro_vega": {
            "n": "high",
            "p": "medium",
            "k": "medium",
            "ml_per_liter_light": 1.5,
            "ml_per_liter_medium": 3.0,
            "ml_per_liter_heavy": 4.5,
            "stage": "vegetative"
        },
        "hydro_flora": {
            "n": "low",
            "p": "high",
            "k": "high",
            "ml_per_liter_light": 1.5,
            "ml_per_liter_medium": 3.0,
            "ml_per_liter_heavy": 4.5,
            "stage": "flowering"
        },
        "boost": {
            "n": "low",
            "p": "high",
            "k": "medium",
            "ml_per_liter_light": 0.5,
            "ml_per_liter_medium": 1.0,
            "ml_per_liter_heavy": 2.0,
            "stage": "flowering"
        },
        "rhizotonic": {
            "n": "low",
            "p": "low",
            "k": "low",
            "ml_per_liter_light": 1.0,
            "ml_per_liter_medium": 2.0,
            "ml_per_liter_heavy": 4.0,
            "stage": "all"
        }
    }
    local_storage.setItem("nutrient_products", json.dumps(default_products))

# Initialize default system types if not existing
if local_storage.getItem("system_types") is None:
    default_systems = {
        "dwc": {"description": "Deep Water Culture", "ec_modifier": 1.0, "change_frequency_days": 14},
        "nft": {"description": "Nutrient Film Technique", "ec_modifier": 0.8, "change_frequency_days": 7},
        "drip": {"description": "Drip System", "ec_modifier": 1.2, "change_frequency_days": 10},
        "ebb_flow": {"description": "Ebb and Flow", "ec_modifier": 1.1, "change_frequency_days": 10}
    }
    local_storage.setItem("system_types", json.dumps(default_systems))

# Initialize default recommendation settings if not existing
if local_storage.getItem("nutrient_recommendation_settings") is None:
    default_settings = {
        "enabled": True,
        "system_type": "dwc",
        "plant_type": "leafy_greens",
        "growth_stage": "vegetative",
        "ec_tolerance": 0.3,
        "ph_tolerance": 0.3,
        "aggressive_correction": False,
        "auto_adjust": True,
        "notification_frequency": "daily",
        "water_volume_liters": 20
    }
    local_storage.setItem("nutrient_recommendation_settings", json.dumps(default_settings))

# Load current settings
try:
    nutrient_settings = json.loads(local_storage.getItem("nutrient_recommendation_settings"))
    nutrient_profiles = json.loads(local_storage.getItem("nutrient_profiles"))
    nutrient_products = json.loads(local_storage.getItem("nutrient_products"))
    system_types = json.loads(local_storage.getItem("system_types"))
except:
    st.error("Error loading settings. Resetting to defaults.")
    local_storage.removeItem("nutrient_recommendation_settings")
    local_storage.removeItem("nutrient_profiles")
    local_storage.removeItem("nutrient_products")
    local_storage.removeItem("system_types")
    st.rerun()

# Create tabs for different settings sections
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["General", "Nutrient Recommendations", "Plant Profiles", "Products", "System Types"])

with tab1:
    general_form = st.form(key="general_settings_form")
    with general_form:
        username = general_form.text_input("Username", value=local_storage.getItem("username") or "")
        submit_general = general_form.form_submit_button("Save General Settings")

        if submit_general:
            local_storage.setItem("username", username)
            st.success("General settings saved")

with tab2:
    st.subheader("Nutrient Recommendation Settings")

    rec_form = st.form(key="nutrient_rec_settings_form")
    with rec_form:
        enable_recommendations = rec_form.checkbox("Enable Nutrient Recommendations",
                                                   value=nutrient_settings.get("enabled", True))

        col1, col2 = rec_form.columns(2)
        with col1:
            system_type = col1.selectbox("Hydroponic System Type",
                                         options=list(system_types.keys()),
                                         format_func=lambda x: system_types[x]["description"],
                                         index=list(system_types.keys()).index(
                                             nutrient_settings.get("system_type", "dwc")))

            plant_type = col1.selectbox("Plant Type",
                                        options=list(nutrient_profiles.keys()),
                                        format_func=lambda x: x.replace("_", " ").title(),
                                        index=list(nutrient_profiles.keys()).index(
                                            nutrient_settings.get("plant_type", "leafy_greens")))

            growth_stages = list(nutrient_profiles[plant_type].keys())
            growth_stage = col1.selectbox("Current Growth Stage",
                                          options=growth_stages,
                                          format_func=lambda x: x.replace("_", " ").title(),
                                          index=growth_stages.index(nutrient_settings.get("growth_stage",
                                                                                          "vegetative")) if nutrient_settings.get(
                                              "growth_stage", "vegetative") in growth_stages else 0)

        with col2:
            water_volume = col2.number_input("Reservoir Volume (liters)",
                                             min_value=1, max_value=1000,
                                             value=nutrient_settings.get("water_volume_liters", 20))

            ec_tolerance = col2.slider("EC Tolerance Range (±)",
                                       min_value=0.1, max_value=1.0, step=0.1,
                                       value=nutrient_settings.get("ec_tolerance", 0.3))

            ph_tolerance = col2.slider("pH Tolerance Range (±)",
                                       min_value=0.1, max_value=1.0, step=0.1,
                                       value=nutrient_settings.get("ph_tolerance", 0.3))

        col1, col2 = rec_form.columns(2)
        with col1:
            aggressive_correction = col1.checkbox("Aggressive Correction",
                                                  help="Make larger adjustments to quickly reach target values",
                                                  value=nutrient_settings.get("aggressive_correction", False))

            auto_adjust = col1.checkbox("Automatic Adjustment Calculations",
                                        help="Automatically calculate exact amount of nutrients/pH adjusters needed",
                                        value=nutrient_settings.get("auto_adjust", True))

        with col2:
            notification_frequency = col2.selectbox("Recommendation Frequency",
                                                    options=["every_reading", "daily", "only_when_needed"],
                                                    format_func=lambda x: {"every_reading": "Every Reading",
                                                                           "daily": "Daily Summary",
                                                                           "only_when_needed": "Only When Needed"}[x],
                                                    index=["every_reading", "daily", "only_when_needed"].index(
                                                        nutrient_settings.get("notification_frequency", "daily")))

        advanced_expander = rec_form.expander("Advanced Settings")
        with advanced_expander:
            environmental_factor = advanced_expander.slider("Environmental Stress Factor",
                                                            min_value=0.5, max_value=1.5, step=0.1,
                                                            value=nutrient_settings.get("environmental_factor", 1.0),
                                                            help="Adjust nutrient strength based on environmental stress (heat, light)")

            nutrient_strength = advanced_expander.select_slider("Default Nutrient Strength",
                                                                options=["light", "medium", "heavy"],
                                                                value=nutrient_settings.get("nutrient_strength",
                                                                                            "medium"))

            ec_strategy = advanced_expander.radio("EC Strategy",
                                                  options=["maintain", "gradual_increase", "stage_based"],
                                                  format_func=lambda x: {"maintain": "Maintain Stable EC",
                                                                         "gradual_increase": "Gradually Increase Over Time",
                                                                         "stage_based": "Follow Stage-Based Recommendations"}[
                                                      x],
                                                  index=["maintain", "gradual_increase", "stage_based"].index(
                                                      nutrient_settings.get("ec_strategy", "stage_based")))

            base_water_ec = advanced_expander.number_input("Base Water EC",
                                                          min_value=0.1, max_value=3.0, step=0.1,
                                                          value=nutrient_settings.get("base_water_ec", 0.5))

        submit_rec = rec_form.form_submit_button("Save Recommendation Settings")

        if submit_rec:
            # Update settings
            nutrient_settings = {
                "enabled": enable_recommendations,
                "system_type": system_type,
                "plant_type": plant_type,
                "growth_stage": growth_stage,
                "water_volume_liters": water_volume,
                "ec_tolerance": ec_tolerance,
                "ph_tolerance": ph_tolerance,
                "aggressive_correction": aggressive_correction,
                "auto_adjust": auto_adjust,
                "notification_frequency": notification_frequency,
                "environmental_factor": environmental_factor,
                "nutrient_strength": nutrient_strength,
                "ec_strategy": ec_strategy,
                "base_water_ec": base_water_ec
            }

            local_storage.setItem("nutrient_recommendation_settings", json.dumps(nutrient_settings))
            st.success("Nutrient recommendation settings saved")

with tab3:
    st.subheader("Plant Profiles")

    # Show current profiles in expandable sections
    for plant_type, stages in nutrient_profiles.items():
        with st.expander(f"{plant_type.replace('_', ' ').title()} Profile"):
            st.json(stages)

    # Form to add/edit profiles
    profile_form = st.form(key="profile_form")
    with profile_form:
        st.subheader("Add/Edit Plant Profile")

        edit_existing = profile_form.checkbox("Edit Existing Profile")

        if edit_existing:
            profile_to_edit = profile_form.selectbox("Select Profile to Edit",
                                                     options=list(nutrient_profiles.keys()),
                                                     format_func=lambda x: x.replace("_", " ").title())
        else:
            profile_name = profile_form.text_input("New Profile Name")

        st.markdown("#### Growth Stages")

        # Dynamic form for stages
        stages_container = st.container()

        num_stages = profile_form.number_input("Number of Growth Stages", min_value=1, max_value=5, value=3)

        stages_data = {}
        for i in range(num_stages):
            col1, col2, col3 = profile_form.columns(3)
            with col1:
                stage_name = col1.text_input(f"Stage {i + 1} Name", key=f"stage_name_{i}")
            with col2:
                ph_target = col2.slider(f"pH Target (Stage {i + 1})", min_value=5.0, max_value=7.0, step=0.1, value=5.8,
                                        key=f"ph_{i}")
                ec_target = col2.slider(f"EC Target (Stage {i + 1})", min_value=0.5, max_value=3.0, step=0.1, value=1.2,
                                        key=f"ec_{i}")
            with col3:
                n_level = col3.select_slider(f"Nitrogen (Stage {i + 1})",
                                             options=["very_low", "low", "medium", "high", "very_high"], value="medium",
                                             key=f"n_{i}")
                p_level = col3.select_slider(f"Phosphorus (Stage {i + 1})",
                                             options=["very_low", "low", "medium", "high", "very_high"], value="medium",
                                             key=f"p_{i}")
                k_level = col3.select_slider(f"Potassium (Stage {i + 1})",
                                             options=["very_low", "low", "medium", "high", "very_high"], value="medium",
                                             key=f"k_{i}")

            profile_form.divider()

            if stage_name:
                stages_data[stage_name.lower().replace(" ", "_")] = {
                    "ph_target": ph_target,
                    "ec_target": ec_target,
                    "n": n_level,
                    "p": p_level,
                    "k": k_level
                }

        submit_profile = profile_form.form_submit_button("Save Plant Profile")

        if submit_profile:
            if edit_existing:
                nutrient_profiles[profile_to_edit] = stages_data
                success_msg = f"Updated profile: {profile_to_edit}"
            else:
                if profile_name:
                    profile_key = profile_name.lower().replace(" ", "_")
                    nutrient_profiles[profile_key] = stages_data
                    success_msg = f"Added new profile: {profile_name}"
                else:
                    st.error("Please provide a profile name")

            local_storage.setItem("nutrient_profiles", json.dumps(nutrient_profiles))
            st.success(success_msg)

with tab4:
    st.subheader("Nutrient Products")

    # Show current products
    for product, details in nutrient_products.items():
        with st.expander(f"{product.replace('_', ' ').title()} Details"):
            st.json(details)

    # Form to add/edit products
    product_form = st.form(key="product_form")
    with product_form:
        st.subheader("Add/Edit Nutrient Product")

        edit_existing_product = product_form.checkbox("Edit Existing Product")

        if edit_existing_product:
            product_to_edit = product_form.selectbox("Select Product to Edit",
                                                     options=list(nutrient_products.keys()),
                                                     format_func=lambda x: x.replace("_", " ").title())
            current_values = nutrient_products[product_to_edit]
        else:
            product_name = product_form.text_input("New Product Name")
            current_values = {
                "n": "medium",
                "p": "medium",
                "k": "medium",
                "ml_per_liter_light": 1.0,
                "ml_per_liter_medium": 2.0,
                "ml_per_liter_heavy": 3.0,
                "stage": "all"
            }

        col1, col2 = product_form.columns(2)

        with col1:
            n_content = col1.select_slider("Nitrogen Content",
                                           options=["very_low", "low", "medium", "high", "very_high"],
                                           value=current_values.get("n", "medium"))

            p_content = col1.select_slider("Phosphorus Content",
                                           options=["very_low", "low", "medium", "high", "very_high"],
                                           value=current_values.get("p", "medium"))

            k_content = col1.select_slider("Potassium Content",
                                           options=["very_low", "low", "medium", "high", "very_high"],
                                           value=current_values.get("k", "medium"))

        with col2:
            ml_light = col2.number_input("ml per liter (Light)",
                                         min_value=0.1, max_value=10.0, step=0.1,
                                         value=current_values.get("ml_per_liter_light", 1.0))

            ml_medium = col2.number_input("ml per liter (Medium)",
                                          min_value=0.1, max_value=10.0, step=0.1,
                                          value=current_values.get("ml_per_liter_medium", 2.0))

            ml_heavy = col2.number_input("ml per liter (Heavy)",
                                         min_value=0.1, max_value=10.0, step=0.1,
                                         value=current_values.get("ml_per_liter_heavy", 3.0))

            recommended_stage = col2.selectbox("Recommended Growth Stage",
                                               options=["seedling", "vegetative", "flowering", "fruiting", "all"],
                                               index=["seedling", "vegetative", "flowering", "fruiting", "all"].index(
                                                   current_values.get("stage", "all")))

        submit_product = product_form.form_submit_button("Save Product")

        if submit_product:
            product_data = {
                "n": n_content,
                "p": p_content,
                "k": k_content,
                "ml_per_liter_light": ml_light,
                "ml_per_liter_medium": ml_medium,
                "ml_per_liter_heavy": ml_heavy,
                "stage": recommended_stage
            }

            if edit_existing_product:
                nutrient_products[product_to_edit] = product_data
                success_msg = f"Updated product: {product_to_edit}"
            else:
                if product_name:
                    product_key = product_name.lower().replace(" ", "_")
                    nutrient_products[product_key] = product_data
                    success_msg = f"Added new product: {product_name}"
                else:
                    st.error("Please provide a product name")

            local_storage.setItem("nutrient_products", json.dumps(nutrient_products))
            st.success(success_msg)

with tab5:
    st.subheader("Hydroponic System Types")

    # Show current system types
    for system, details in system_types.items():
        with st.expander(f"{details['description']} Details"):
            st.json(details)

    # Form to add/edit system types
    system_form = st.form(key="system_form")
    with system_form:
        st.subheader("Add/Edit System Type")

        edit_existing_system = system_form.checkbox("Edit Existing System Type")

        if edit_existing_system:
            system_to_edit = system_form.selectbox("Select System to Edit",
                                                   options=list(system_types.keys()),
                                                   format_func=lambda x: system_types[x]["description"])
            current_system = system_types[system_to_edit]
        else:
            system_key = system_form.text_input("System Key (no spaces)")
            system_description = system_form.text_input("System Description")
            current_system = {
                "description": "",
                "ec_modifier": 1.0,
                "change_frequency_days": 14
            }

        ec_modifier = system_form.slider("EC Strength Modifier",
                                         min_value=0.5, max_value=1.5, step=0.1,
                                         value=current_system.get("ec_modifier", 1.0),
                                         help="Adjusts nutrient strength based on system efficiency (lower = less concentrated)")

        change_frequency = system_form.number_input("Recommended Solution Change Frequency (days)",
                                                    min_value=1, max_value=30,
                                                    value=current_system.get("change_frequency_days", 14))

        submit_system = system_form.form_submit_button("Save System Type")

        if submit_system:
            system_data = {
                "ec_modifier": ec_modifier,
                "change_frequency_days": change_frequency
            }

            if edit_existing_system:
                system_data["description"] = current_system["description"]
                system_types[system_to_edit] = system_data
                success_msg = f"Updated system: {system_to_edit}"
            else:
                if system_key and system_description:
                    system_data["description"] = system_description
                    system_types[system_key] = system_data
                    success_msg = f"Added new system: {system_description}"
                else:
                    st.error("Please provide both system key and description")

            local_storage.setItem("system_types", json.dumps(system_types))
            st.success(success_msg)

# Summary container
summary_container = st.container(border=True)
with summary_container:
    st.subheader("Current Settings Summary")

    col1, col2 = st.columns(2)

    with col1:
        st.write("### General Settings")
        if local_storage.getItem("username") is None:
            st.write("Username not set")
        else:
            st.write(f"Username: {local_storage.getItem('username')}")

    with col2:
        st.write("### Nutrient Recommendations")
        st.write(f"Status: {'Enabled' if nutrient_settings.get('enabled', True) else 'Disabled'}")
        st.write(
            f"System: {system_types.get(nutrient_settings.get('system_type', 'dwc'), {}).get('description', 'Deep Water Culture')}")
        st.write(f"Plant Type: {nutrient_settings.get('plant_type', 'leafy_greens').replace('_', ' ').title()}")
        st.write(f"Growth Stage: {nutrient_settings.get('growth_stage', 'vegetative').replace('_', ' ').title()}")

        # Display target values for current settings
        try:
            current_profile = nutrient_profiles[nutrient_settings.get('plant_type', 'leafy_greens')]
            current_stage = nutrient_settings.get('growth_stage', 'vegetative')

            if current_stage in current_profile:
                targets = current_profile[current_stage]
                st.write(f"Target pH: {targets['ph_target']} (±{nutrient_settings.get('ph_tolerance', 0.3)})")
                st.write(f"Target EC: {targets['ec_target']} (±{nutrient_settings.get('ec_tolerance', 0.3)})")
        except:
            st.write("Could not display target values")

# Add explanation about the nutrient recommendation system
with st.expander("About the Nutrient Recommendation System"):
    st.write("""
    ## How the Nutrient Recommendation System Works

    This advanced system provides tailored recommendations based on multiple factors:

    ### Key Features:
    - **Plant-Specific Profiles**: Different plants need different nutrients at different growth stages
    - **Adaptive Recommendations**: Based on current pH/EC readings compared to target values
    - **System-Aware**: Adjusts recommendations based on your specific hydroponic setup
    - **Environmental Integration**: Takes into account environmental factors that affect nutrient uptake
    - **Smart Scheduling**: Recommends when to change solutions and add specific nutrients

    ### The Calculation Process:
    1. Compares current readings with target values for your plant type and growth stage
    2. Calculates needed adjustments based on your reservoir size
    3. Recommends specific product amounts based on their nutrient content
    4. Offers preventative advice to maintain optimal growing conditions

    Adjust the settings to match your specific growing style and equipment for best results.
    """)